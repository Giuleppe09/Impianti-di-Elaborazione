import pandas as pd
import re
import os

def process_doe_results(files):
    """
    Carica e aggrega i risultati del DOE da più file CSV, 
    calcola il Response Time, il Throughput e aggiunge la metrica CTT.

    Args:
        files (list): Lista dei nomi dei file CSV delle ripetizioni.

    Returns:
        pd.DataFrame: DataFrame finale aggregato e processato.
    """
    
    EXECUTION_TIME_S = 300 # Tempo di esecuzione fisso per il calcolo del Throughput
    
    # --- 1. Caricamento e Concatenazione dei Dati ---
    dfs = []
    print("Caricamento e concatenazione dei file...")
    for file in files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except FileNotFoundError:
            print(f"Errore: File non trovato: {file}")
            return None
    
    if not dfs:
        print("Nessun dato caricato. Interruzione.")
        return None
    
    df_combined = pd.concat(dfs, ignore_index=True)
    
    # --- 2. Estrazione e Pulizia del Thread Group Number ---
    # Estrae l'ID del gruppo principale (1, 2, o 3) dal campo 'threadName'
    print("Estrazione del Thread Group ID...")
    try:
        df_combined['Thread_Group_Number'] = df_combined['threadName'].str.extract(r'(\d+)-\d+')[0].astype(int)
    except Exception as e:
        print(f"Errore nell'estrazione del Thread Group Number: {e}")
        return None

    # --- 3. Calcolo del Throughput (Richieste/sec) ---
    print("Calcolo del Throughput...")
    # Calcolo del conteggio totale delle richieste per ogni gruppo (chiave: label + Thread_Group_Number)
    df_counts = df_combined.groupby(['label', 'Thread_Group_Number']).size().reset_index(name='Request_Count')
    df_counts['Throughput'] = df_counts['Request_Count'] / EXECUTION_TIME_S
    
    # --- 4. Calcolo della Media delle Metriche (Response Time incluso) ---
    
    # Colonne numeriche rilevanti per la media
    columns_to_average = [
        'elapsed', 'bytes', 'sentBytes', 'grpThreads', 'allThreads',
        'Latency', 'IdleTime', 'Connect'
    ]
    
    # Esegue il raggruppamento e la media
    columns_for_grouping_and_averaging = ['label', 'Thread_Group_Number'] + columns_to_average
    df_avg = df_combined[columns_for_grouping_and_averaging].groupby(
        ['label', 'Thread_Group_Number']
    ).mean().reset_index()

    # --- 5. Aggiunta della Colonna CTT e Merge del Throughput ---
    print("Aggiunta della colonna CTT e unione del Throughput...")
    
    # Aggiunta della colonna 'CTT'
    ctt_mapping = {1: 150, 2: 300, 3: 450}
    df_avg['CTT'] = df_avg['Thread_Group_Number'].map(ctt_mapping)

    # Merge del Throughput
    df_final = pd.merge(df_avg, df_counts[['label', 'Thread_Group_Number', 'Throughput']], 
                       on=['label', 'Thread_Group_Number'], how='left')

    # --- 6. Ridenominazione e Riordinamento delle Colonne ---
    
    # Rinomina 'elapsed' in 'Response_Time_ms' (in millisecondi, come richiesto)
    df_final.rename(columns={'elapsed': 'Response_Time_ms'}, inplace=True)

    # Definisce il nuovo ordine di colonne
    required_cols = ['CTT', 'label', 'Response_Time_ms', 'Throughput']
    other_cols = [col for col in df_final.columns if col not in required_cols]
    new_column_order = required_cols + other_cols
    
    df_final = df_final[new_column_order]
    
    return df_final

# --- Esecuzione dello Script ---

# Nomi dei file di input forniti
input_files = [
    "TestPlan_DOE_Ripetizione_1_risultati.csv",
    "TestPlan_DOE_Ripetizione_2_risultati.csv",
    "TestPlan_DOE_Ripetizione_3_risultati.csv"
]

# Nome del file di output (formato Excel)
output_excel_filename = 'TestPlan_DOE_Risultati_Finali.xlsx'

# Esecuzione della funzione principale
df_results = process_doe_results(input_files)

if df_results is not None:
    # --- 7. Salvataggio nel Formato Excel ---
    print(f"\nSalvataggio del risultato finale in {output_excel_filename}...")
    try:
        df_results.to_excel(output_excel_filename, index=False)
        print("Operazione completata con successo.")
        print(f"File salvato: {output_excel_filename}")
        print("\nAnteprima dei risultati:")
        print(df_results.head())
    except Exception as e:
        print(f"Errore durante il salvataggio in Excel: {e}")