import pandas as pd
import numpy as np

'''
GENERAZIONE WORKLOAD SINTETICO - VERSIONE AUTOMATIZZATA E COMPLETA

Questo script identifica la riga più vicina al centroide per ciascun cluster,
utilizzando le componenti principali per il calcolo.
L'output finale è un file Excel (.xlsx) che contiene automaticamente tutte le 
colonne che precedono 'Principale1', più la colonna del cluster.
'''

# ==============================================================================
# --- IMPOSTAZIONI UTENTE (MODIFICA SOLO QUESTA SEZIONE) ---
# ==============================================================================

# 1. Nome del file Excel di input
file_excel = "LLSinth_PCA7_Cluster13.xlsx"

# 2. Numero di componenti principali da usare come feature per il calcolo.
numero_componenti = 7

# 3. Nome esatto della colonna che contiene i cluster da analizzare.
colonna_cluster = "Cluster"

# ==============================================================================
# --- INIZIO SCRIPT (NON MODIFICARE DA QUI IN POI) ---
# ==============================================================================

print("Avvio dello script...")

# --- 1. Lettura dati e validazione iniziale ---
try:
    data = pd.read_excel(file_excel)
except FileNotFoundError:
    print(f"ERRORE: Il file '{file_excel}' non è stato trovato. Assicurati che sia nella stessa cartella.")
    exit()

# --- 2. Rilevamento automatico delle colonne e validazione ---
try:
    # Genera i nomi delle colonne delle componenti principali
    feature_columns = [f"Principale{i}" for i in range(1, numero_componenti + 1)]

    # Rileva le colonne reali e aggiunge la colonna del cluster
    prima_componente_idx = data.columns.get_loc("Principale1")
    colonne_reali_output = data.columns[:prima_componente_idx].tolist()
    colonne_finali_output = colonne_reali_output + [colonna_cluster]
    
    if not colonne_reali_output:
        raise ValueError("Nessuna colonna trovata prima di 'Principale1'. Controlla il formato del file Excel.")

    # Controllo che tutte le colonne necessarie esistano
    colonne_necessarie = feature_columns + [colonna_cluster]
    colonne_mancanti = [col for col in colonne_necessarie if col not in data.columns]
    if colonne_mancanti:
        raise ValueError(f"Le seguenti colonne non sono state trovate: {colonne_mancanti}")

except (ValueError, KeyError) as e:
    print(f"ERRORE di configurazione o formato file: {e}")
    exit()

print(f" Parametri utilizzati:")
print(f"  - File: {file_excel}")
print(f"  - Feature per calcolo: {numero_componenti} (da 'Principale1' a 'Principale{numero_componenti}')")
print(f"  - Colonna cluster: '{colonna_cluster}'")
print(f"  - Colonne di output: {len(colonne_reali_output)} colonne reali + la colonna cluster")


# --- 3. Calcolo dei centroidi e identificazione delle righe rappresentative ---
closest_rows = []
clusters = data[colonna_cluster].unique()

print(f"\nTrovati {len(clusters)} cluster unici. Inizio calcolo...")

for cluster in clusters:
    cluster_data = data[data[colonna_cluster] == cluster]
    
    if len(cluster_data) == 1:
        closest_row = cluster_data.iloc[0]
    else:
        cluster_values = cluster_data[feature_columns].values
        centroid = np.mean(cluster_values, axis=0)
        distances = np.linalg.norm(cluster_values - centroid, axis=1)
        closest_row_index = np.argmin(distances)
        closest_row = cluster_data.iloc[closest_row_index]
        
    closest_rows.append(closest_row)

# --- 4. Salvataggio dei risultati ---
closest_rows_df = pd.DataFrame(closest_rows)
output_df = closest_rows_df[colonne_finali_output]

# ★★★ MODIFICA 1: Il nome del file ora finisce con .xlsx ★★★
output_filename = f"WORKLOAD_SINTETICO_{numero_componenti}PC_{colonna_cluster}.xlsx"

# ★★★ MODIFICA 2: Usa to_excel() invece di to_csv() per salvare in formato Excel ★★★
output_df.to_excel(output_filename, index=False)

print(f"\n Operazione completata con successo!")
print(f"Il workload sintetico è stato salvato nel file Excel: {output_filename}")