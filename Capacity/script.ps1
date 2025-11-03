# ===============================================
# CONFIGURAZIONE
# ===============================================

# --- JMeter Configuration (Host) ---
$JMeterEXEC_PATH = "C:\Users\giuse\Desktop\Impianti\apache-jmeter-5.6.3\bin\jmeter.bat"
# --- Modifica: Specifica la CARTELLA dei Test Plan ---
$JMX_DIR = "C:\Users\giuse\Desktop\Impianti\Progetto\Impianti-di-Elaborazione\Capacity\test_Plan"
$JTL_DIR = "C:\Users\giuse\Desktop\Impianti\Progetto\Impianti-di-Elaborazione\Capacity\JMeter_Logs"

# --- VM Configuration (Guest SSH) ---
$guestIP = "192.168.184.134" 
$guestUser = "giuleppe"
$guestPass = ConvertTo-SecureString "2406" -AsPlainText -Force 

# --- VMSTAT Settings ---
$vmstatSamplingRate = 1        

# ===============================================
# PREPARAZIONE
# ===============================================
Import-Module Posh-SSH -ErrorAction Stop

# Directory di destinazione per i log vmstat sul GUEST
$vmstatGuestDir = "/home/giuleppe/proveLLP2"

# --- MODIFICA CHIAVE: Ricerca e Ordinamento ---
# Cerca tutti i file .jmx e li ordina in base al numero CTT nel nome
Write-Host "Ricerca file .jmx e ordinamento per CTT..."
$jmxFiles = Get-ChildItem -Path $JMX_DIR -Filter *.jmx | Sort-Object @{Expression={
    # --- MODIFICATO PER CORRISPONDERE A "Test_Plan_CTT_x" ---
    $match = [regex]::Match($_.Name, 'Test_Plan_CTT_(\d+)') 
    if ($match.Success) {
        # Converte il numero trovato (es. "100") in un intero per l'ordinamento
        [int]$match.Groups[1].Value
    } else {
        # Se un file non ha il pattern, viene messo in fondo alla lista
        Write-Warning "File $($_.Name) non contiene il pattern 'Test_Plan_CTT_[numero]' e sarà messo alla fine."
        999999 
    }
}} # --- CORREZIONE: Rimosso "-Ascending" da questa riga ---

if (-not $jmxFiles) {
    Write-Warning "ERRORE: Nessun file .jmx trovato nella directory $JMX_DIR"
    Read-Host "Premi Invio per uscire"
    exit 1
}

# Crea la directory di output JTL se non esiste (una sola volta)
if (-not (Test-Path $JTL_DIR)) {
    Write-Host "Creazione directory risultati: $JTL_DIR"
    New-Item -Path $JTL_DIR -ItemType Directory | Out-Null
}

Write-Host "========================================================"
Write-Host " AVVIO BATTERIA DI TEST (IN ORDINE DI CTT CRESCENTE)"
Write-Host " Trovati $($jmxFiles.Count) file JMX. Ordine di esecuzione:"
# Mostra l'ordine di esecuzione
$jmxFiles | ForEach-Object { Write-Host " - $($_.Name)" }
Write-Host "========================================================"
Write-Host ""

# ===============================================
# ESECUZIONE SINCRONIZZATA - INIZIO CICLO
# ===============================================

# Itera su ogni file JMX trovato (già ordinato per CTT)
foreach ($jmxFile in $jmxFiles) {

    # --- Calcolo Nomi File e Variabili (per questo ciclo) ---
    $currentJmxPath = $jmxFile.FullName
    # Il nome del file (senza estensione) include già il CTT
    $jmxFileName = [System.IO.Path]::GetFileNameWithoutExtension($currentJmxPath) 
    
    $vmstatLogFileGuest = "$vmstatGuestDir/$jmxFileName" + "_vmstat_log.txt"
    $jtlPathHost = "$JTL_DIR\$jmxFileName" + "_risultati.csv"
    
    # Argomento -Jthreads RIMOSSO
    $jmeterArgs = "-n -t `"$currentJmxPath`" -l `"$jtlPathHost`""
    
    # Comando vmstat con stop dinamico (via PID)
    $vmstatCommand = "nohup vmstat $vmstatSamplingRate > $vmstatLogFileGuest 2>&1 & echo $!"

    Write-Host "--------------------------------------------------------"
    Write-Host "Avvio Test: $jmxFileName"
    Write-Host "--------------------------------------------------------"

    # --- Fase 1: Creazione Credenziali e Sessione SSH ---
    Write-Host "(GUEST) FASE 1: Creazione sessione SSH per $guestUser@$guestIP..."
    $sshCred = New-Object System.Management.Automation.PSCredential($guestUser, $guestPass)
    $sshSession = New-SSHSession -ComputerName $guestIP -Credential $sshCred -AcceptKey -ErrorAction SilentlyContinue

    if (-not $sshSession) {
        Write-Warning "ERRORE CRITICO: Creazione sessione SSH fallita. Salto il test $jmxFileName."
        Continue # Salta al prossimo file JMX nel ciclo
    }

    # --- Fase 1.5: Avvio di vmstat sul Guest (Background) ---
    Write-Host "(GUEST) Avvio di vmstat (verrà fermato dopo JMeter)..."
    Write-Host "(GUEST) Comando: $vmstatCommand"
    $vmstatPID = $null
    try {
        # Esegui il comando e salva l'output (che contiene il PID)
        $sshResult = Invoke-SshCommand -SSHSession $sshSession -Command $vmstatCommand -ErrorAction Stop
        # Estrai solo l'output numerico (il PID)
        $vmstatPID = $sshResult.Output.Trim() | Where-Object { $_ -match "^\d+$" } | Select-Object -First 1

        if (-not $vmstatPID) {
            Write-Warning "ERRORE CRITICO: Impossibile ottenere il PID di vmstat. Output: $($sshResult.Output)"
            Remove-SSHSession -SSHSession $sshSession
            Continue # Salta al prossimo file JMX nel ciclo
        }
        Write-Host "(GUEST) vmstat avviato con PID: $vmstatPID"
    } catch {
        Write-Warning "ERRORE CRITICO: Esecuzione comando vmstat fallita. Salto il test $jmxFileName."
        Remove-SSHSession -SSHSession $sshSession
        Continue # Salta al prossimo file JMX nel ciclo
    }

    # --- Fase 2: Avvio di JMeter sull'Host ---
    Write-Host ""
    Write-Host "(HOST) FASE 2: Avvio di JMeter per $jmxFileName (attende la fine)..."
    
    # Avvia JMeter e attende che termini
    $jmeterProcess = Start-Process -FilePath $JMeterEXEC_PATH -ArgumentList $jmeterArgs -NoNewWindow -PassThru -Wait

    Write-Host "(HOST) Test JMeter $jmxFileName Completato."

    # --- Fase 3: Stop di vmstat sul Guest (SINCRONIZZAZIONE) ---
    Write-Host ""
    Write-Host "(GUEST) FASE 3: Termino vmstat (PID: $vmstatPID)..."
    try {
        Invoke-SshCommand -SSHSession $sshSession -Command "kill $vmstatPID" -ErrorAction Stop
        Write-Host "(GUEST) Processo vmstat terminato."
    } catch {
        Write-Warning "AVVISO: Impossibile terminare il processo vmstat (PID: $vmstatPID) sul guest. Potrebbe rimanere in esecuzione."
    }

    # --- Fase 4: Chiusura Sessione ---
    Remove-SSHSession -SSHSession $sshSession
    Write-Host "(GUEST) Sessione SSH chiusa."
    Write-Host ""
    Write-Host "RISULTATI SALVATI:"
    Write-Host " - JMeter (Host): $jtlPathHost"
    Write-Host " - vmstat (Guest): $vmstatLogFileGuest (NON SCARICATO)"
    Write-Host ""

} # --- Fine del ciclo foreach ---

Write-Host "========================================================"
Write-Host " TUTTI I TEST SONO STATI COMPLETATI."
Write-Host "========================================================"

Read-Host "Premi Invio per chiudere"