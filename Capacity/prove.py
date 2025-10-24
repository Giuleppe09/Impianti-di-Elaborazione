import pandas as pd
import re

def calculate_metrics_per_threadgroup(file_path):
    """
    Calcola throughput (durata fissa 300s), media/mediana elapsed (in secondi),
    stampa il NUMERO DI RIGA di inizio/fine e il conteggio delle label
    per ogni thread group.
    """
    try:
        df = pd.read_csv(file_path, encoding='latin1')
        if df.empty:
            print(f"File vuoto: {file_path}")
            return None
    except Exception as e:
        print(f"Errore nella lettura del file {file_path}: {e}")
        return None

    # Filtra solo le richieste andate a buon fine
    df_success = df[df['success'] == True].copy()
    if df_success.empty:
        print(f"Nessuna richiesta andata a buon fine in {file_path}")
        return None

    # Estrai il nome del thread group (es. 'Thread Group 1')
    df_success['threadGroup'] = df_success['threadName'].apply(lambda x: re.match(r'(.+?) \d+-\d+', x).group(1) if re.match(r'(.+?) \d+-\d+', x) else 'Unknown')
    
    df_success = df_success[df_success['threadGroup'] != 'Unknown']
    grouped = df_success.groupby('threadGroup')

    # Liste per le metriche finali
    thread_throughputs = []
    thread_mean_elapseds_sec = [] 
    thread_median_elapseds_sec = []

    print(f"--- Calcolo Metriche per il file: {file_path} ---")

    if grouped.ngroups == 0:
        print("Nessun Thread Group trovato con il pattern atteso (es. 'Thread Group 1 1-1').")
        return

    for name, group in grouped:
        if group.empty:
            continue
            
        # --- INIZIO E FINE (per la stampa) ---
        start_row_index = group['timeStamp'].idxmin()
        start_row_file = start_row_index + 2 
        
        end_row_index = (group['timeStamp'] + group['elapsed']).idxmax()
        end_row_file = end_row_index + 2
        
        # --- Durata Fissa per Throughput ---
        duration_sec_per_throughput = 300.0

        # Calcolo Throughput per il gruppo
        num_requests = len(group)
        throughput = num_requests / duration_sec_per_throughput
        thread_throughputs.append(throughput)
        
        # --- MODIFICA: Calcolo Elapsed (Medio e Mediana) in SECONDI ---
        mean_elapsed_sec = (group['elapsed'].mean()) / 1000.0
        median_elapsed_sec = (group['elapsed'].median()) / 1000.0
        
        thread_mean_elapseds_sec.append(mean_elapsed_sec)
        thread_median_elapseds_sec.append(median_elapsed_sec)

        # --- MODIFICA: Conteggio Label per Gruppo ---
        label_counts = group['label'].value_counts()
        
        print(f"\n  - Gruppo: '{name}'")
        
        # --- MODIFICA: Stampa INIZIO/FINE (solo riga) ---
        print(f"    INIZIO (prima richiesta): Riga {start_row_file}")
        print(f"    FINE   (ultima richiesta): Riga {end_row_file}")
        
        # --- MODIFICA: Stampa Conteggio Richieste ---
        print("    Conteggio Richieste per Tipo:")
        for label_name, count in label_counts.items():
            print(f"      - {label_name}: {count}")
        
        print(f"    Numero Totale Richieste: {num_requests}")
        print(f"    Durata usata (fissa): {duration_sec_per_throughput:.2f} s")
        print(f"    Throughput (calcolato): {throughput:.2f} req/s")
        # --- MODIFICA: Stampa Elapsed in SECONDI ---
        print(f"    Elapsed Medio (calcolato): {mean_elapsed_sec:.3f} s")
        print(f"    Elapsed Mediano (calcolato): {median_elapsed_sec:.3f} s")


    if not thread_throughputs:
        print("\nNessuna metrica calcolata.")
        return None

    # --- MODIFICA: Calcolo Medie e Mediane FINALI ---
    # Converti le liste in Series Pandas per calcolare facilmente la mediana
    s_throughputs = pd.Series(thread_throughputs)
    s_mean_elapseds = pd.Series(thread_mean_elapseds_sec)
    s_median_elapseds = pd.Series(thread_median_elapseds_sec)

    # Calcolo metriche finali
    avg_throughput = s_throughputs.mean()
    med_throughput = s_throughputs.median()
    
    avg_of_mean_elapsed = s_mean_elapseds.mean()
    med_of_mean_elapsed = s_mean_elapseds.median()

    avg_of_median_elapsed = s_median_elapseds.mean()
    med_of_median_elapsed = s_median_elapseds.median()
    
    
    print("\n\n--- Risultato Finale (Medie e Mediane delle metriche dei gruppi) ---")
    
    print("\n  Throughput (req/s):")
    print(f"    Valori individuali: {[round(t, 2) for t in thread_throughputs]}")
    print(f"    Media:   {avg_throughput:.2f} req/s")
    print(f"    Mediana: {med_throughput:.2f} req/s")
    
    print("\n  Tempi di Risposta MEDI (s):")
    print(f"    Valori individuali: {[round(e, 3) for e in thread_mean_elapseds_sec]}")
    print(f"    Media dei valori medi:   {avg_of_mean_elapsed:.3f} s")
    print(f"    Mediana dei valori medi: {med_of_mean_elapsed:.3f} s")

    print("\n  Tempi di Risposta MEDIANI (s):")
    print(f"    Valori individuali: {[round(e, 3) for e in thread_median_elapseds_sec]}")
    print(f"    Media dei valori mediani:   {avg_of_median_elapsed:.3f} s")
    print(f"    Mediana dei valori mediani: {med_of_median_elapsed:.3f} s")
    
    return True # Ritorna successo

# --- ESECUZIONE ---
# Assicurati che 'CTT2400.csv' sia nella stessa cartella dello script
file_to_process = 'CTT1200.csv' 
metrics = calculate_metrics_per_threadgroup(file_to_process)

if metrics:
    print("\n\nScript completato con successo.")
else:
    print(f"\n\nScript completato con errori o nessun dato trovato in {file_to_process}.")
