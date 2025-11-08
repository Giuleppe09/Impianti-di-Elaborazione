# ===============================================
# CONFIGURAZIONE
# ===============================================

# --- Directory di Lavoro ---
# $PSScriptRoot è una variabile automatica di PowerShell
# che punta alla directory in cui si trova questo script.
$WorkDir = $PSScriptRoot 
Write-Host "Directory di lavoro impostata su: $WorkDir"

# --- JMeter Configuration (Host) ---
$JMeterEXEC_PATH = "C:\Users\giuse\Desktop\Impianti\apache-jmeter-5.6.3\bin\jmeter.bat"
$JMX_DIR = $WorkDir # Usa la cartella dello script
$JTL_DIR = $WorkDir # Usa la cartella dello script

# --- Configurazione Esecuzione ---
$jmxFileToRun = "TestPlan5.jmx"
$jtlOutputFileName = "WorkLoad_Real.csv" # Nome del file JTL di output

$testDurationMinutes = 25

# ===============================================
# PREPARAZIONE
# ===============================================

# Verifica che la directory JMX esista
if (-not (Test-Path $JMX_DIR)) {
     Write-Warning "ERRORE: La directory dei JMX $JMX_DIR non esiste."
     Read-Host "Premi Invio per uscire"
     exit 1
}

# --- Verifica File JMX Singolo ---
$currentJmxPath = Join-Path $JMX_DIR $jmxFileToRun
if (-not (Test-Path $currentJmxPath)) {
    Write-Warning "ERRORE: Il file JMX $currentJmxPath non è stato trovato."
    Read-Host "Premi Invio per uscire"
    exit 1
}

# --- Percorso JTL completo ---
$jtlOutputPath = Join-Path $JTL_DIR $jtlOutputFileName
if (Test-Path $jtlOutputPath) {
    Write-Warning "Rilevato vecchio file JTL. Lo rimuovo: $jtlOutputPath"
    Remove-Item $jtlOutputPath
}

# ===============================================
# ESECUZIONE JMETER
# ===============================================

Write-Host "========================================================"
Write-Host " AVVIO TEST JMETER: $jmxFileToRun"
Write-Host " Durata prevista: $testDurationMinutes minuti"
Write-Warning "RICORDA: Avvia vmstat SUL SERVER ADESSO!"
Write-Host "========================================================"
Write-Host ""
# Pausa per darti il tempo di avviare vmstat
Read-Host "Premi Invio per avviare JMeter..."


# --- Argomenti per JMeter (come ARRAY) ---
$jmeterArgsList = @(
    "-n",
    "-t", $currentJmxPath,
    "-l", $jtlOutputPath
)

Write-Host "Avvio di JMETER (locale) in corso..."
Write-Host "Log JTL: $jtlOutputPath"
Write-Host "Il test è in esecuzione. Attendi $testDurationMinutes minuti..."

# --- Esecuzione diretta ---
# Avvia JMeter, attende che finisca (-Wait) e non mostra finestre extra (-NoNewWindow)
$jmeterProcess = Start-Process -FilePath $JMeterEXEC_PATH -ArgumentList $jmeterArgsList -Wait -NoNewWindow -PassThru

Write-Host ""
if ($jmeterProcess.ExitCode -eq 0) {
    Write-Host "Esecuzione JMeter completata con successo."
} else {
    Write-Warning "ERRORE: JMeter ha terminato con codice $($jmeterProcess.ExitCode)"
}

# ===============================================
# FINE
# ===============================================

Write-Host ""
Write-Host "========================================================"
Write-Host " TEST JMETER COMPLETATO."
Write-Host "Risultati JMeter: $jtlOutputPath"
Write-Warning "Ricorda di copiare manualmente il file 'vmstat_log.csv' dal server."
Write-Host "========================================================"

Read-Host "Premi Invio per chiudere"