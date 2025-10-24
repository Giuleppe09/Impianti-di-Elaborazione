#!/bin/bash
# --- CONFIGURAZIONE ---
COLLECTL_CMD="sudo collectl -scmdnf -i 2 -oT -P -f performance_log" # log ogni 2 secondi
#cdn sono di default collezionati.
TOTAL_DURATION_SECONDS=3600 #qua metti ore
PHASE_DURATION_SECONDS=900 # qua metti 15 minuti, questi sono al momento tutti secondi
CRITICAL_TEMP=95
TEMP_SENSOR_CORE="Package id 0" #modificato da peppe
cleanup() {
    echo -e "\n--- Terminazione di tutti i processi di benchmark. ---"
    sudo kill "$COLLECTL_PID" 2>/dev/null
    # Uccidi tutti i PID di stress (incluso stress-ng che è sempre attivo)
    kill "$MONITOR_PID" "$NODY_PID" "$FIO_PID" "$STRESS_PID" 2>/dev/null
    rm -f test_file_fio.bin
    echo "Pulizia completata."
    exit 0
}

trap cleanup EXIT INT TERM

# --- FUNZIONE DI MONITORAGGIO TEMPERATURA ---
monitor_temp() {
    echo "Avviato monitoraggio temperatura critica ($CRITICAL_TEMP°C)."
    while true; do
        TEMP_STR=$(sensors | grep "$TEMP_SENSOR_CORE" | grep -oP '\+\K[0-9]+' | head -1)
        if (( TEMP_STR >= CRITICAL_TEMP )); then
            echo "🔥🔥 ATTENZIONE! Raggiunta la temperatura critica ($TEMP_STR°C)."
            #cleanup
        fi
        sleep 5 
    done
}

# --- AVVIO ESPERIMENTO ---

echo "--- Avvio Stress Test Ciclico (Memoria Costante + CPU/IO Alternati) per 60 minuti ---"

# 1. Avvia il monitoraggio e collectl
monitor_temp &
MONITOR_PID=$!

$COLLECTL_CMD &
COLLECTL_PID=$!
echo "PID collectl: $COLLECTL_PID"

# 2. AVVIA LO STRESS DI MEMORIA (COSTANTE) -- 2 processi, 1GB ciascuno
stress-ng --vm 2 --vm-bytes 1G --timeout "$TOTAL_DURATION_SECONDS" &
STRESS_PID=$!
echo "PID stress-ng (Memoria Costante): $STRESS_PID"
echo "Inizio ciclo..."
sleep 5 # Lascia tempo ai processi di avviarsi

# 3. Ciclo di 4 fasi (4 * 15 minuti = 60 minuti)
for i in 1 2 3 4; do
    
    # --- FASE CPU-BOUND (fasi dispari) ---
    if (( i % 2 != 0 )); then
        echo "--> Fase $i (CPU-MEM Bound) - Avvio Nbody."
        ./launch_nbody.sh -r 50 -n 50000000 &
        NODY_PID=$!
        sleep "$PHASE_DURATION_SECONDS"
        
        # Dopo 15 minuti, termina Nbody
        kill "$NODY_PID" 2>/dev/null
        
    # --- FASE I/O-BOUND (fasi pari) ---
    else
        echo "--> Fase $i (I/O-MEM Bound) - Avvio FIO."
        # FIO viene eseguito per la durata esatta della fase
        fio --name=io-phase --filename=test_file_fio.bin --size=5G --rw=write --bs=1M --runtime "$PHASE_DURATION_SECONDS" --time_based
        
        # Pulizia del file I/O
        rm -f test_file_fio.bin
    fi
done

# La funzione cleanup viene chiamata automaticamente alla fine del tempo o dal kill switch.
echo "Ciclo completato. Terminazione dei processi..."
