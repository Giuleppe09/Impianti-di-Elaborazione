# ===============================================
# CONFIGURAZIONE
# ===============================================

# --- JMeter Configuration (Host) ---
$JMeterEXEC_PATH = "C:\Users\giuse\Desktop\Impianti\apache-jmeter-5.6.3\bin\jmeter.bat"
$JMX_DIR = "C:\Users\giuse\Desktop\Impianti\Progetto\Impianti-di-Elaborazione\Capacity\test_Plan"
$JTL_DIR = "C:\Users\giuse\Desktop\Impianti\Progetto\Impianti-di-Elaborazione\Capacity\JMeter_Logs"

# --- Impostazioni Esecuzione ---
$repetitions = 3 # Numero di volte che ogni test plan deve essere eseguito

# --- MODIFICA: Definisci i nomi ESATTI dei file JMX da eseguire ---
$jmxFileNames = @(
    "Fairness_test_fair.jmx",
    "Fairness_test_unfair.jmx",
    "Fairness_test_unfair_UtentiVariabili.jmx"
)

# ===============================================
# PREPARAZIONE
# ===============================================

# Verifica che la directory JMX esista
if (-not (Test-Path $JMX_DIR)) {
     Write-Warning "ERRORE: La directory dei JMX $JMX_DIR non esiste."
     Read-Host "Premi Invio per uscire"
     exit 1
}

# Crea la directory di output JTL se non esiste (una sola volta)
if (-not (Test-Path $JTL_DIR)) {
    Write-Host "Creazione directory risultati: $JTL_DIR"
    New-Item -Path $JTL_DIR -ItemType Directory | Out-Null
}

Write-Host "========================================================"
Write-Host " AVVIO BATTERIA DI TEST (FAIRNESS)"
Write-Host " Esecuzione di $repetitions ripetizioni per ognuno dei seguenti test:"
$jmxFileNames | ForEach-Object { Write-Host " - $_" }
Write-Host "========================================================"
Write-Host ""

# ===============================================
# ESECUZIONE - INIZIO CICLO
# ===============================================

# Itera su ogni file JMX definito nell'array
foreach ($jmxName in $jmxFileNames) {

    $currentJmxPath = Join-Path $JMX_DIR $jmxName
    
    # Verifica che il file JMX specifico esista
    if (-not (Test-Path $currentJmxPath)) {
        Write-Warning "ERRORE: File $currentJmxPath non trovato. Salto questo test."
        Continue # Salta al prossimo file JMX
    }

    # Prende il nome base del file (es. "Fairness_test_fair")
    $jmxFileNameBase = [System.IO.Path]::GetFileNameWithoutExtension($currentJmxPath)
    
    Write-Host "--------------------------------------------------------"
    Write-Host "Inizio test per: $jmxName"
    Write-Host "--------------------------------------------------------"

    # --- Ciclo interno per le ripetizioni ---
    for ($i = 1; $i -le $repetitions; $i++) {
    
        Write-Host "Avvio Ripetizione $i di $repetitions per $jmxName..."
        
        # --- Nome file JTL univoco per ogni ripetizione ---
        $jtlPathHost = "$JTL_DIR\$jmxFileNameBase" + "_rep_$i" + "_risultati.csv"
        
        $jmeterArgs = "-n -t `"$currentJmxPath`" -l `"$jtlPathHost`""
        
        # --- FASE ESECUZIONE JMETER (locale) ---
        Write-Host "(HOST) Avvio di JMeter... (attende la fine)"
        Write-Host "(HOST) Log JTL: $jtlPathHost"
        
        # Avvia JMeter e attende che termini
        $jmeterProcess = Start-Process -FilePath $JMeterEXEC_PATH -ArgumentList $jmeterArgs -NoNewWindow -PassThru -Wait
        
        Write-Host "(HOST) Ripetizione $i completata."
        Write-Host ""
        
    } # --- Fine ciclo ripetizioni ---
    
    Write-Host "Tutte le $repetitions ripetizioni per $jmxName sono completate."
    Write-Host ""

} # --- Fine ciclo file JMX ---

Write-Host "========================================================"
Write-Host " TUTTI I TEST SONO STATI COMPLETATI."
Write-Host "========================================================"

Read-Host "Premi Invio per chiudere"
