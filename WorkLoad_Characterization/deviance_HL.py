import pandas as pd
import numpy as np
from scipy.stats import zscore
import re

print("Script di adattamento 'deviance.py' avviato (nuova esecuzione con file aggiornato).")

# --- 1. Definizione delle colonne ---
# Manteniamo la stessa ipotesi per le colonne originali
ORIGINAL_DATA_COLUMNS = ['elapsed', 'bytes', 'sentBytes', 'allThreads', 'Latency', 'Connect']

print(f"Colonne dati originali definite: {ORIGINAL_DATA_COLUMNS}")

# --- 2. Lettura dei dati ---
try:
    # Il nome del file è lo stesso, ma ora caricherà la nuova versione
    file_name = 'WorkloadCharacterization_Results_PCA5_Cluster13.xlsx'
    df = pd.read_excel(file_name)
    
    print(f"\nFile CSV '{file_name}' caricato con successo.")
    print(f"Righe: {len(df)}, Colonne: {len(df.columns)}")
    print("\nIntestazione del DataFrame (prime 5 righe):")
    print(df.head())
    print("\nInformazioni sul DataFrame:")
    df.info()

except FileNotFoundError as e:
    print(f"Errore: {e}. Assicurati che il file CSV sia nella stessa cartella dello script.")
    exit()
except Exception as e:
    print(f"Errore durante la lettura del file: {e}")
    exit()

# --- 3. Separazione colonne PCA e Clustering ---
# Identifica le colonne PCA (Principale1, Principale2, ...)
pca_columns = [col for col in df.columns if col.startswith('Principale')]
# Identifica la colonna di clustering
cluster_column = 'PCA5_Cluster13'

# Verifica che le colonne esistano
if not pca_columns:
    print("Errore: Nessuna colonna 'Principale' trovata.")
    exit()
if cluster_column not in df.columns:
    print(f"Errore: Colonna '{cluster_column}' non trovata.")
    exit()

print(f"\nTrovate {len(pca_columns)} colonne PCA: {pca_columns}")
print(f"Trovata 1 colonna di clustering: {cluster_column}")

# --- 4. Calcolo della Devianza Totale (dai dati originali) ---
try:
    # Seleziona solo le colonne dei dati originali
    data_original = df[ORIGINAL_DATA_COLUMNS]
    
    # Normalizzazione dei dati (zscore)
    data_norm = zscore(data_original.values)
    # Sostituisce eventuali NaN (risultanti da colonne a varianza zero) con 0
    data_norm = np.nan_to_num(data_norm)
    
    # Calcola la Devianza Totale (somma dei quadrati dei dati normalizzati)
    DEV_TOT = np.sum(data_norm ** 2)
    
    print(f"\n--- CALCOLO DEVIANZA TOTALE ---")
    print(f"Dati originali (shape): {data_norm.shape}")
    print(f"Devianza Totale (DEV_TOT): {DEV_TOT:.2f}")

except KeyError:
    print(f"\nERRORE: Una o più colonne in {ORIGINAL_DATA_COLUMNS} non trovate nel CSV.")
    print("Per favore, modifica la lista 'ORIGINAL_DATA_COLUMNS' nello script con i nomi corretti.")
    exit()
except Exception as e:
    print(f"Errore durante il calcolo della DEV_TOT: {e}")
    exit()

# --- 5. Calcolo W, B, e DEV_PCA (per la singola configurazione) ---
try:
    # Dettagli della configurazione
    n_pca = len(pca_columns)
    n_cluster = df[cluster_column].nunique()
    col_name = f"PCA{n_pca}_Cluster{n_cluster}"
    
    print(f"\n--- ANALISI CONFIGURAZIONE: {col_name} ---")
    
    # Estrai i dati necessari
    X_pca = df[pca_columns].values
    clusters = df[cluster_column]
    
    # Calcola la Devianza spiegata dalla PCA
    DEV_PCA = np.sum(X_pca ** 2)

    # Calcola W (Within-cluster) e B (Between-cluster)
    G = np.mean(data_norm, axis=0)
    W = 0.0
    B = 0.0
    
    cluster_labels = sorted(clusters.unique())
    print(f"Calcolo W e B per {n_cluster} cluster (etichette: {cluster_labels})...")
    
    for k in cluster_labels:
        X_k = data_norm[clusters == k, :]
        
        if X_k.shape[0] > 0:
            g_k = np.mean(X_k, axis=0)
            n_k = X_k.shape[0]
            W += np.sum((X_k - g_k) ** 2)
            B += n_k * np.sum((g_k - G) ** 2)

    # --- 6. Stampa dei risultati ---
    
    # Percentuali
    DEV_Spiegata_Cluster_per = B / DEV_TOT
    DEV_Persa_Cluster_per = W / DEV_TOT
    
    DEV_Spiegata_PCA_per = DEV_PCA / DEV_TOT
    DEV_Persa_PCA_per = (DEV_TOT - DEV_PCA) / DEV_TOT
    
    verifica_Huygens = (W + B) / DEV_TOT

    print(f"\n{'='*70}")
    print(f"RISULTATI PER CONFIGURAZIONE: {col_name}")
    print(f"{'='*70}")
    
    print("\n--- RIEPILOGO DEVIAZIONE TOTALE ---")
    print(f"Devianza Totale (DEV_TOT):           {DEV_TOT:>15.2f} (100.00%)")
    print(f"Verifica (W+B) / DEV_TOT:            {verifica_Huygens:>15.6f} (Dovrebbe essere 1.0)")
    
    print("\n--- ANALISI CLUSTERING (sui dati originali) ---")
    print(f"Devianza Spiegata (Inter-cluster, B): {B:>15.2f} ({DEV_Spiegata_Cluster_per:>8.2%})")
    print(f"Devianza Persa (Intra-cluster, W):    {W:>15.2f} ({DEV_Persa_Cluster_per:>8.2%})")
    print(f"  -> (W + B):                         {(W+B):>15.2f}")

    print("\n--- ANALISI PCA ---")
    print(f"Devianza Spiegata (DEV_PCA):          {DEV_PCA:>15.2f} ({DEV_Spiegata_PCA_per:>8.2%})")
    print(f"Devianza Persa (Residua PCA):         {(DEV_TOT - DEV_PCA):>15.2f} ({DEV_Persa_PCA_per:>8.2%})")
    
    print("\n--- RISPOSTA ALLE DOMANDE ---")
    print(f"1. Devianza spiegata per cluster:     {B:>15.2f} ({DEV_Spiegata_Cluster_per:.2%}) (Vedi 'B' sopra)")
    print(f"2. Devianza persa per cluster:        {W:>15.2f} ({DEV_Persa_Cluster_per:.2%}) (Vedi 'W' sopra)")
    print(f"\nLa 'devianza persa fra cluster e PCA' è la 'Devianza Persa (Intra-cluster, W)'.")

except Exception as e:
    print(f"\nSi è verificato un errore durante l'analisi: {e}")

print("\nScript terminato.")