# ===============================================
# CONFIGURAZIONE
# ===============================================

# --- JMeter Configuration (Host) ---
$JMeterEXEC_PATH = "C:\Users\giuse\Desktop\Impianti\apache-jmeter-5.6.3\bin\jmeter.bat"
# --- Directory dello script (dove si trova anche il Test Plan) ---
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$JMX_FILE = Join-Path $SCRIPT_DIR "TestPlan_DOE.jmx"
$RESULTS_DIR = $SCRIPT_DIR

# --- VM Configuration (Guest SSH) ---
$guestIP = "192.168.184.134" 
$guestUser = "giuleppe"
$guestPass = ConvertTo-SecureString "2406" -AsPlainText -Force 

# --- VMSTAT Settings ---
$vmstatSamplingRate = 1        

# --- Numero di ripetizioni ---
$NUM_RIPETIZIONI = 3

# ===============================================
# PREPARAZIONE
# ===============================================
Import-Module Posh-SSH -ErrorAction Stop

# Directory di destinazione per i log vmstat sul GUEST
$vmstatGuestDir = "/home/giuleppe/DOE"

# Verifica che il file JMX esista
if (-not (Test-Path $JMX_FILE)) {
    Write-Warning "ERRORE: File Test Plan non trovato: $JMX_FILE"
    Read-Host "Premi Invio per uscire"
    exit 1
}

Write-Host "========================================================"
Write-Host " AVVIO BATTERIA DI TEST - $NUM_RIPETIZIONI RIPETIZIONI"
Write-Host " Test Plan: $JMX_FILE"
Write-Host "========================================================"
Write-Host ""

# ===============================================
# ESECUZIONE SINCRONIZZATA - CICLO RIPETIZIONI
# ===============================================

for ($ripetizione = 1; $ripetizione -le $NUM_RIPETIZIONI; $ripetizione++) {

    # --- Calcolo Nomi File per questa ripetizione ---
    $jmxFileName = "TestPlan_DOE_Ripetizione_$ripetizione"
    
    $vmstatLogFileGuest = "$vmstatGuestDir/$jmxFileName" + "_vmstat_log.txt"
    $jtlPathHost = "$RESULTS_DIR\$jmxFileName" + "_risultati.csv"
    
    $jmeterArgs = "-n -t `"$JMX_FILE`" -l `"$jtlPathHost`""
    
    # Comando vmstat con stop dinamico (via PID)
    $vmstatCommand = "nohup vmstat $vmstatSamplingRate > $vmstatLogFileGuest 2>&1 & echo $!"

    Write-Host "--------------------------------------------------------"
    Write-Host "RIPETIZIONE $ripetizione di $NUM_RIPETIZIONI"
    Write-Host "--------------------------------------------------------"

    # --- Fase 1: Creazione Credenziali e Sessione SSH ---
    Write-Host "(GUEST) FASE 1: Creazione sessione SSH per $guestUser@$guestIP..."
    $sshCred = New-Object System.Management.Automation.PSCredential($guestUser, $guestPass)
    $sshSession = New-SSHSession -ComputerName $guestIP -Credential $sshCred -AcceptKey -ErrorAction SilentlyContinue

    if (-not $sshSession) {
        Write-Warning "ERRORE CRITICO: Creazione sessione SSH fallita. Salto la ripetizione $ripetizione."
        Continue
    }

    # --- Fase 1.5: Avvio di vmstat sul Guest (Background) ---
    Write-Host "(GUEST) Avvio di vmstat (verrà fermato dopo JMeter)..."
    Write-Host "(GUEST) Comando: $vmstatCommand"
    $vmstatPID = $null
    try {
        $sshResult = Invoke-SshCommand -SSHSession $sshSession -Command $vmstatCommand -ErrorAction Stop
        $vmstatPID = $sshResult.Output.Trim() | Where-Object { $_ -match "^\d+$" } | Select-Object -First 1

        if (-not $vmstatPID) {
            Write-Warning "ERRORE CRITICO: Impossibile ottenere il PID di vmstat. Output: $($sshResult.Output)"
            Remove-SSHSession -SSHSession $sshSession
            Continue
        }
        Write-Host "(GUEST) vmstat avviato con PID: $vmstatPID"
    } catch {
        Write-Warning "ERRORE CRITICO: Esecuzione comando vmstat fallita. Salto la ripetizione $ripetizione."
        Remove-SSHSession -SSHSession $sshSession
        Continue
    }

    # --- Fase 2: Avvio di JMeter sull'Host ---
    Write-Host ""
    Write-Host "(HOST) FASE 2: Avvio di JMeter per ripetizione $ripetizione (attende la fine)..."
    
    # Avvia JMeter e attende che termini
    $jmeterProcess = Start-Process -FilePath $JMeterEXEC_PATH -ArgumentList $jmeterArgs -NoNewWindow -PassThru -Wait

    Write-Host "(HOST) Test JMeter ripetizione $ripetizione completato."

    # --- Fase 3: Stop di vmstat sul Guest (SINCRONIZZAZIONE) ---
    Write-Host ""
    Write-Host "(GUEST) FASE 3: Termino vmstat (PID: $vmstatPID)..."
    try {
        Invoke-SshCommand -SSHSession $sshSession -Command "kill $vmstatPID" -ErrorAction Stop
        Write-Host "(GUEST) Processo vmstat terminato."
    } catch {
        Write-Warning "AVVISO: Impossibile terminare il processo vmstat (PID: $vmstatPID) sul guest."
    }

    # --- Fase 4: Chiusura Sessione ---
    Remove-SSHSession -SSHSession $sshSession
    Write-Host "(GUEST) Sessione SSH chiusa."
    Write-Host ""
    Write-Host "RISULTATI SALVATI:"
    Write-Host " - JMeter (Host): $jtlPathHost"
    Write-Host " - vmstat (Guest): $vmstatLogFileGuest"
    Write-Host ""

}

Write-Host "========================================================"
Write-Host " TUTTE LE $NUM_RIPETIZIONI RIPETIZIONI COMPLETATE"
Write-Host "========================================================"

Read-Host "Premi Invio per chiudere"