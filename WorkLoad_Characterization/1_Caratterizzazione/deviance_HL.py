import pandas as pd
import numpy as np
import re
from typing import Dict, Any

# --- 1. Lettura dei dati (Adattato a WorkloadCharacterization...) ---
file_csv = 'WorkLoad_Real.xlsx'

try:
    df = pd.read_excel(file_csv)
    print(f"File '{file_csv}' caricato correttamente.")
except FileNotFoundError as e:
    print(f"Errore: {e}. Assicurati che il file '{file_csv}' sia nella stessa cartella dello script.")
    exit()
except Exception as e:
    print(f"Errore durante la lettura del file: {e}")
    exit()

# Colonne originali (prima della PCA)
# NOTA: Inferite dal file. Esclude 'success' (bool) e le colonne 'object'.
original_feature_columns = [
    'elapsed', 'bytes', 'sentBytes', 'grpThreads', 
    'allThreads', 'Latency', 'IdleTime', 'Connect'
]

# Verifica che le colonne esistano
missing_cols = [col for col in original_feature_columns if col not in df.columns]
if missing_cols:
    print(f"Errore: Colonne originali mancanti nel file: {missing_cols}")
    exit()

data = df[original_feature_columns].values.astype(float) # Estrae i valori come array NumPy

# --- 2. Normalizzazione (ddof=1) e Calcolo Devianza Totale (CORRETTO per JMP) ---

# Calcola media e deviazione standard campionaria (ddof=1)
n_samples, p_features = data.shape
data_mean = np.mean(data, axis=0)
data_std = np.std(data, axis=0, ddof=1)

# Gestisce colonne con varianza zero (std dev = 0)
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
print("Nota: I due valori dovrebbero essere molto simili.")
print(f"----------------------------------------------------------")


# --- 3. Separazione colonne PCA e Clustering ---
# Trova automaticamente le colonne 'PrincipaleX'
pca_columns = [col for col in df.columns if col.startswith('Principale')]
# Nome colonna cluster specifico di questo file
cluster_col_name = 'Cluster' 

print(f"Trovate {len(pca_columns)} colonne PCA: {', '.join(pca_columns)}")
if cluster_col_name in df.columns:
    print(f"Trovata colonna di clustering: '{cluster_col_name}'")
else:
    print(f"Errore: Colonna '{cluster_col_name}' non trovata. Script interrotto.")
    exit()

# --- 4. Calcolo della Devianza post-PCA su tutte le componenti ---
print("\n" + "="*70)
print("ANALISI PCA (basata sui punteggi importati)")
print("="*70)

pca_data_full = df[pca_columns].values
mean_pca = np.mean(pca_data_full, axis=0)
DEV_PCA = np.sum((pca_data_full - mean_pca)**2)
DEV_PCA_per = DEV_PCA / DEV_TOT 

print(f"Devianza Totale (DEV_TOT):     {DEV_TOT:>12.2f}")
print(f"Devianza dopo PCA (DEV_PCA):   {DEV_PCA:>12.2f} ({DEV_PCA_per:.2%})")
print(f"Devianza persa nella PCA:      {(1 - DEV_PCA_per):.2%}")
print("\nNota: La 'Devianza dopo PCA' è la % di varianza spiegata dai")
print(f"{len(pca_columns)} componenti. Questo valore ora dovrebbe corrispondere a JMP.")


# --- 5. Funzione per calcolare le devianze per clustering (OTTIMIZZATA) ---
def calcola_devianze_cluster(pca_data, cluster_data, DEV_TOT, DEV_PCA, DEV_PCA_per) -> Dict[str, Any]:
    """
    Calcola le devianze intra e inter cluster, stampa W per cluster e la devianza relativa.
    """
    cluster_data = cluster_data.flatten()
    N_cluster = int(np.max(cluster_data)) if cluster_data.size > 0 else 0
    
    if N_cluster == 0 or N_cluster < 1:
        return {'W': 0, 'B': 0, 'DEV_PCA_CL_per': 0, 'DEV_LOST_per': 1, 'verifica': 0}

    W_list = np.zeros(N_cluster) 
    B_list = np.zeros(N_cluster) 
    
    global_centroid_pca = np.mean(pca_data, axis=0)
    
    print("\n--- Devianze Intra-Cluster (W) Dettagliate ---")
    
    # I cluster JMP possono partire da 1. Assumiamo che 0 sia 'non clusterizzato'
    # o semplicemente iteriamo sulle etichette uniche > 0
    
    unique_labels = np.unique(cluster_data[cluster_data > 0])
    N_cluster = len(unique_labels)
    
    for i, cluster_label in enumerate(unique_labels):
        index = np.where(cluster_data == cluster_label)[0]
        
        if index.size > 0:
            cluster_samples = pca_data[index, :]
            n_ele = len(index)
            centroid = np.mean(cluster_samples, axis=0)
            
            # Devianza Within
            W_current = np.sum((cluster_samples - centroid)**2)
            W_list[i] = W_current # Usa l'indice 'i'
            
            # Devianza Between
            B_list[i] = n_ele * np.sum((centroid - global_centroid_pca)**2)
            
            # Calcola la Devianza Relativa (W_attuale / N_elementi_cluster)
            W_relativa = W_current / n_ele
            
            # Stampa esplicativa
            print(f"Cluster {cluster_label:<2}: W = {W_current:>8.4f} | N = {n_ele:<4} | W/N (Densità) = {W_relativa:>7.4f}")
        else:
            print(f"Cluster {cluster_label}: Nessun elemento trovato.")
    print("---------------------------------------------")

    W = np.sum(W_list)
    B = np.sum(B_list)
    
    DEV_PCA_CL_per = B / DEV_TOT
    DEV_LOST_per = (1 - DEV_PCA_per) + (W / DEV_TOT)
    
    return {
        'W': W,
        'B': B,
        'DEV_PCA_CL_per': DEV_PCA_CL_per,
        'DEV_LOST_per': DEV_LOST_per,
        'verifica': (W + B) / DEV_PCA if DEV_PCA > 0 else 0
    }

# --- 6. Processa il clustering singolo dal file ---
print("\n" + "="*70)
print(f"ANALISI CLUSTERING: '{cluster_col_name}'")
print("="*70)

risultati = []
n_pca_usati = len(pca_columns) # Assumiamo siano state usate tutte le componenti

cluster_data_series = df[cluster_col_name].copy() 

try:
    # Pulizia e conversione in array NumPy
    cluster_data_clean_np = pd.to_numeric(cluster_data_series, errors='coerce').fillna(0).astype(int).values.flatten()
    
    # Logica per escludere cluster 0 o negativi
    # JMP di solito etichetta da 1 in su. 0 potrebbe essere rumore o non assegnato.
    valid_indices = np.where(cluster_data_clean_np > 0)[0]
    
    if len(valid_indices) < 2:
        print(f"Avviso: Colonna '{cluster_col_name}' ha meno di 2 punti validi (cluster > 0). Saltata.")
        exit()
        
    print(f"Trovati {len(valid_indices)} campioni validi (cluster > 0) su {len(cluster_data_clean_np)} totali.")
    
    # Filtra i dati PCA e i dati cluster
    pca_data_valid = pca_data_full[valid_indices, :]
    cluster_data_valid = cluster_data_clean_np[valid_indices]
    
    unique_labels = np.unique(cluster_data_valid)
    n_cluster_trovati = len(unique_labels)
    
    # Non è necessario rimappare le etichette se la funzione 'calcola_devianze_cluster'
    # itera già sulle etichette uniche trovate (come modificato sopra).
    
    # Assumiamo che il clustering sia stato fatto su TUTTE le componenti PCA
    pca_data_cluster = pca_data_valid # Usiamo tutti i N componenti trovati

    # Ricalcoliamo la DEV_PCA per i *soli dati validi*
    mean_pca_valid = np.mean(pca_data_cluster, axis=0)
    DEV_PCA_valid = np.sum((pca_data_cluster - mean_pca_valid)**2)
    DEV_PCA_per_valid = DEV_PCA_valid / DEV_TOT 
    
    # Calcola le devianze e stampa i dettagli W
    risultato = calcola_devianze_cluster(
        pca_data_cluster, 
        cluster_data_valid, # Passiamo le etichette originali (1, 2, 3...)
        DEV_TOT, 
        DEV_PCA_valid,
        DEV_PCA_per_valid
    )

    # Stampa risultati riepilogativi
    print(f"\n{'='*70}")
    print(f"RIEPILOGO CONFIGURAZIONE: {cluster_col_name}")
    print(f"{'='*70}")
    print(f"PCA: {n_pca_usati} componenti | Cluster: {n_cluster_trovati} (Etichette Valide)")
    print(f"Verifica (W+B)/DEV_PCA_valid: {risultato['verifica']:.6f} (deve essere ~1.0)")
    print("-" * 70)
    print(f"Devianza Intra-cluster Totale (**W**):   {risultato['W']:>12.2f}")
    print(f"Devianza Inter-cluster Totale (**B**):   {risultato['B']:>12.2f}")
    print("-" * 70)
    
    W_per_PCA = risultato['W'] / DEV_PCA_valid if DEV_PCA_valid > 0 else 0
    
    print(f"Rapporto W / DEV_PCA_valid (Dev. persa NEL clustering): {W_per_PCA:>6.2%}")
    print("-" * 70)
    print(f"Devianza spiegata (B/DEV_TOT):       {risultato['DEV_PCA_CL_per']:>6.2%}")
    print(f"Devianza persa (W/DEV_TOT + Persa PCA):{risultato['DEV_LOST_per']:>6.2%}")
    
    # Salva per esportazione
    risultati.append({
        'Configurazione': cluster_col_name,
        'N_PCA': n_pca_usati,
        'N_Cluster': n_cluster_trovati,
        'Within (W)': risultato['W'],
        'Between (B)': risultato['B'],
        'DEV_Spiegata_%': risultato['DEV_PCA_CL_per'],
        'DEV_Persa_%': risultato['DEV_LOST_per'],
        'Verifica': risultato['verifica'],
        'W_su_DEV_PCA_%': W_per_PCA
    })
    
except Exception as e:
    print(f"\nErrore non gestito per {cluster_col_name}: {e}")
    

# --- 7. Esporta i risultati in un file Excel ---
if risultati:
    df_risultati = pd.DataFrame(risultati)
    output_file = 'risultati_devianze_workload_HL.xlsx'
    df_risultati.to_excel(output_file, index=False)
    print(f"\n{'='*70}")
    print(f"Risultati salvati in: {output_file}")
    print(f"{'='*70}")
else:
    print("\nNessun risultato da salvare.")