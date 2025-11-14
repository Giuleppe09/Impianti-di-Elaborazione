import pandas as pd
import numpy as np
import re
from typing import Dict, Any

# --- 1. Lettura dei dati (Adattato a LLc.xlsx) ---
file_excel = 'LLReal_PCA7_Cluster14.xlsx'
file_csv = 'LLc.csv' # Assumiamo sia lo stesso nome del file CSV

try:
    try:
        df = pd.read_excel(file_excel)
        print(f"File '{file_excel}' caricato correttamente.")
    except FileNotFoundError:
        print(f"File '{file_excel}' non trovato. Tentativo con '{file_csv}'...")
        # Specifichiamo il separatore per il file CSV
        df = pd.read_csv(file_csv, sep=',') 
        print(f"File '{file_csv}' caricato correttamente.")
except FileNotFoundError as e:
    print(f"Errore: {e}. Assicurati che il file '{file_excel}' o '{file_csv}' sia nella stessa cartella dello script.")
    exit()
except Exception as e:
    print(f"Errore durante la lettura del file: {e}")
    exit()

# --- 2. Rilevamento Automatico Colonne ---
print("\n--- Rilevamento Automatico Colonne ---")
cluster_col_name = 'Cluster'
pca_columns = [col for col in df.columns if col.startswith('Principale')]

# Tutte le colonne che NON sono PCA e NON sono 'Cluster' sono feature originali
exclude_cols = set(pca_columns + [cluster_col_name])
original_feature_columns = [col for col in df.columns if col not in exclude_cols]

if not original_feature_columns:
    print("Errore: Impossibile trovare le colonne delle feature originali.")
    exit()
if not pca_columns:
    print("Errore: Impossibile trovare le colonne 'Principale'.")
    exit()
if cluster_col_name not in df.columns:
    print(f"Errore: Colonna '{cluster_col_name}' non trovata.")
    exit()

print(f"Trovate {len(original_feature_columns)} colonne originali: {', '.join(original_feature_columns)}")
print(f"Trovate {len(pca_columns)} colonne PCA: {', '.join(pca_columns)}")
print(f"Trovata colonna clustering: '{cluster_col_name}'")
print("------------------------------------------")


# --- 3. Calcolo DEV_TOT (ora basato sulle colonne corrette) ---
data = df[original_feature_columns].values.astype(float) 

# Calcola media e deviazione standard campionaria (ddof=1)
n_samples, p_features = data.shape
data_mean = np.mean(data, axis=0)
data_std = np.std(data, axis=0, ddof=1)
data_std_safe = np.where(data_std == 0, 1.0, data_std)
data_norm = (data - data_mean) / data_std_safe
data_norm = np.nan_to_num(data_norm, nan=0.0, posinf=0.0, neginf=0.0)

# Calcolo della devianza totale (TSS)
mean_total = np.mean(data_norm, axis=0)
DEV_TOT = np.sum((data_norm - mean_total)**2)

print(f"\n--- Calcolo Devianza Totale (TSS dati standardizzati) ---")
print(f"Info: Campioni (n) = {n_samples}, Feature (p) = {p_features}")
print(f"Info: DEV_TOT calcolata: {DEV_TOT:.2f}")
print(f"Info: Valore atteso (p * (n-1)): {p_features * (n_samples - 1):.2f}")
print(f"----------------------------------------------------------")


# --- 4. Calcolo Devianza PCA (con percentuale) ---
print("\n" + "="*70)
print("ANALISI PCA (basata sui punteggi importati)")
print("="*70)

# Calcola la devianza su TUTTI i dati PCA presenti nel file
pca_data_full = df[pca_columns].values
mean_pca_full = np.mean(pca_data_full, axis=0)
DEV_PCA_JMP_comparison = np.sum((pca_data_full - mean_pca_full)**2)

# Calcola la percentuale
DEV_PCA_per = DEV_PCA_JMP_comparison / DEV_TOT if DEV_TOT > 0 else 0

print(f"Devianza Totale (DEV_TOT, da originali): {DEV_TOT:>12.2f}")
print(f"Devianza dopo PCA (DEV_PCA, da JMP):   {DEV_PCA_JMP_comparison:>12.2f}")
print(f"% Varianza Spiegata (DEV_PCA / DEV_TOT): {DEV_PCA_per:>11.2%}")
print("\nQuesto è il valore da confrontare con il report PCA di JMP.")
print("="*70)


# --- 5. Funzione per calcolare le devianze per clustering ---
def calcola_devianze_cluster(pca_data, cluster_data) -> Dict[str, Any]:
    """
    Calcola le devianze intra e inter cluster, stampa W per cluster e la devianza relativa.
    """
    cluster_data = cluster_data.flatten()
    N_cluster = int(np.max(cluster_data)) if cluster_data.size > 0 else 0
    
    if N_cluster == 0 or N_cluster < 1:
        return {'W': 0, 'B': 0}

    W_list = np.zeros(N_cluster) 
    B_list = np.zeros(N_cluster) 
    
    global_centroid_pca = np.mean(pca_data, axis=0)
    
    print("\n--- Devianze Intra-Cluster (W) Dettagliate ---")
    
    for i in range(1, N_cluster + 1):
        index = np.where(cluster_data == i)[0]
        
        if index.size > 0:
            cluster_samples = pca_data[index, :]
            n_ele = len(index)
            centroid = np.mean(cluster_samples, axis=0)
            
            # Devianza Within
            W_current = np.sum((cluster_samples - centroid)**2)
            W_list[i-1] = W_current
            
            # Devianza Between
            B_list[i-1] = n_ele * np.sum((centroid - global_centroid_pca)**2)
            
            # Calcola la Devianza Relativa (W_attuale / N_elementi_cluster)
            W_relativa = W_current / n_ele if n_ele > 0 else 0
            
            # Stampa esplicativa
            print(f"Cluster {i:<2}: W = {W_current:>8.4f} | N = {n_ele:<4} | W/N (Densità) = {W_relativa:>7.4f}")
        else:
            print(f"Cluster {i}: Nessun elemento trovato.")
    print("---------------------------------------------")

    W = np.sum(W_list)
    B = np.sum(B_list)
    
    return {
        'W': W,
        'B': B,
    }

# --- 6. Processa il clustering singolo dal file ---
print("\n" + "="*70)
print(f"ANALISI CLUSTERING")
print("="*70)

risultati = []
n_pca_usati = len(pca_columns) 
# pca_data_full è già stato definito al passo 4
cluster_data_series = df[cluster_col_name].copy() 

try:
    # Pulizia e conversione in array NumPy
    cluster_data_clean_np = pd.to_numeric(cluster_data_series, errors='coerce').fillna(0).astype(int).values.flatten()
    
    # Logica per escludere cluster 0 o negativi
    valid_indices = np.where(cluster_data_clean_np > 0)[0]
    
    if len(valid_indices) < 2:
        print(f"Avviso: Colonna '{cluster_col_name}' ha meno di 2 punti validi. Saltata.")
        exit()
        
   
    # Filtra i dati PCA e i dati cluster (IMPORTANTE)
    pca_data_valid = pca_data_full[valid_indices, :]
    cluster_data_valid = cluster_data_clean_np[valid_indices]
    
    # Riorganizza etichette da 1 a N
    unique_labels = np.unique(cluster_data_valid)
    n_cluster_trovati = len(unique_labels)
    mapping = {label: i + 1 for i, label in enumerate(unique_labels)}
    cluster_data_valid_remapped = np.array([mapping[c] for c in cluster_data_valid])

    pca_data_cluster = pca_data_valid 

    # --- CALCOLO DEV_PCA_valid ---
    # Questa è la devianza totale di riferimento per l'analisi W+B
    # Calcolata solo sui dati validi (filtrati)
    mean_pca_valid = np.mean(pca_data_cluster, axis=0)
    DEV_PCA_valid = np.sum((pca_data_cluster - mean_pca_valid)**2)
    # --- FINE CALCOLO ---
    
    
    # Calcola le devianze e stampa i dettagli W
    risultato = calcola_devianze_cluster(
        pca_data_cluster, 
        cluster_data_valid_remapped
    )

    # --- CALCOLO PERCENTUALI (CORRETTO) ---
    W = risultato['W']
    B = risultato['B']
    # Verifica che (W+B) sia uguale a DEV_PCA_valid
    verifica_val = (W + B) / DEV_PCA_valid if DEV_PCA_valid > 0 else 0
    
    # Le percentuali corrette sono basate su DEV_PCA_valid
    W_per = W / DEV_PCA_valid if DEV_PCA_valid > 0 else 0
    B_per = B / DEV_PCA_valid if DEV_PCA_valid > 0 else 0
    # --- FINE CALCOLO ---

    # Stampa risultati riepilogativi
    print(f"\n{'='*70}")
    print(f"RIEPILOGO ANALISI CLUSTERING")
    print(f"{'='*70}")
    print(f"PCA: {n_pca_usati} componenti | Cluster: {n_cluster_trovati} ")
    print(f"Devianza Totale dei Componenti PCA: {DEV_PCA_valid:.2f}")
    print(f"Verifica (W+B)/DEV_PCA_valid: {verifica_val:.6f} (deve essere 1.0)")
    print("-" * 70)
    print(f"Devianza Intra-cluster Totale (**W**):   {W:>12.2f}")
    print(f"Devianza Inter-cluster Totale (**B**):   {B:>12.2f}")
    print("-" * 70)
    print(f"Devianza Spiegata (B / DEV_PCA_valid):  {B_per:>6.2%}")
    print(f"Devianza Persa (W / DEV_PCA_valid):    {W_per:>6.2%}")
    print("-" * 70)
    
    # Salva per esportazione
    risultati.append({
        'Configurazione': cluster_col_name,
        'N_PCA': n_pca_usati,
        'N_Cluster': n_cluster_trovati,
        'Within (W)': W,
        'Between (B)': B,
        'DEV_Totale_Originale': DEV_TOT, 
        'DEV_Totale_PCA_JMP': DEV_PCA_JMP_comparison, 
        'DEV_PCA_Spiegata_%': DEV_PCA_per, 
        'DEV_Totale_PCA_Validi': DEV_PCA_valid,
        'DEV_Clustering_Spiegata_%': B_per,
        'DEV_Clustering_Persa_%': W_per,
        'Verifica': verifica_val
    })
    
except Exception as e:
    print(f"\nErrore non gestito per {cluster_col_name}: {e}")
    

# --- 7. Esporta i risultati in un file Excel ---
if risultati:
    df_risultati = pd.DataFrame(risultati)
    output_file = 'risultati_devianze_LLc_finale_corretto.xlsx'
    df_risultati.to_excel(output_file, index=False)
    print(f"\n{'='*70}")
    print(f"Risultati salvati in: {output_file}")
    print(f"{'='*70}")
else:
    print("\nNessun risultato da salvare.")