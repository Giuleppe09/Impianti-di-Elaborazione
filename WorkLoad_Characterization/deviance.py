import pandas as pd
import numpy as np
from scipy.stats import zscore
import re
from typing import Dict, Any

# --- 1. Lettura dei dati ---
try:
    # Leggi i dati originali
    data_df = pd.read_excel('preprocessing/vmstat_cleaned_preprocessing.xls')
    data = data_df.values # Estrae i valori come array NumPy
    
    # Leggi il file unico con PCA e clustering
    df = pd.read_excel('preprocessing/Componenti_Principali_Cluster.xlsx')
except FileNotFoundError as e:
    print(f"Errore: {e}. Assicurati che i file Excel siano nella stessa cartella dello script.")
    exit()

# --- 2. Normalizzazione e Calcolo Devianza Totale ---
# zscore restituisce un array NumPy
data_norm = zscore(data, axis=0) 
# Gestisce il caso di colonne a varianza zero (che restituiscono NaN dopo zscore)
data_norm = np.nan_to_num(data_norm)

# Calcolo della devianza totale (uguale per tutti)
mean_total = np.mean(data_norm, axis=0)
DEV_TOT = np.sum((data_norm - mean_total)**2)

# --- 3. Separazione colonne PCA e Clustering ---
pca_columns = [col for col in df.columns if col.startswith('Principale')]
cluster_columns = [col for col in df.columns if col.startswith('PCA') and 'Cluster' in col] 

print(f"Trovate {len(pca_columns)} colonne PCA")
print(f"Trovate {len(cluster_columns)} colonne di clustering")

# --- 4. Calcolo della Devianza post-PCA su tutte le componenti ---
print("\n" + "="*70)
print("ANALISI PCA")
print("="*70)

pca_data_full = df[pca_columns].values
mean_pca = np.mean(pca_data_full, axis=0)
DEV_PCA = np.sum((pca_data_full - mean_pca)**2)
DEV_PCA_per = DEV_PCA / DEV_TOT 

print(f"Devianza Totale (DEV_TOT):     {DEV_TOT:>12.2f}")
print(f"Devianza dopo PCA (DEV_PCA):   {DEV_PCA:>12.2f} ({DEV_PCA_per:.2%})")
print(f"Devianza persa nella PCA:      {(1 - DEV_PCA_per):.2%}")

# Helper function to parse column names
def parse_column_name(col_name):
    match = re.match(r'PCA(\d+)_Cluster(\d+)', col_name)
    if match:
        n_pca = int(match.group(1))
        n_cluster = int(match.group(2))
        return n_pca, n_cluster
    return None, None

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
            W_relativa = W_current / n_ele
            
            # Stampa esplicativa
            print(f"Cluster {i:<2}: W = {W_current:>8.4f} | N = {n_ele:<4} | W/N (Densità) = {W_relativa:>7.4f}")
        else:
            print(f"Cluster {i}: Nessun elemento trovato.")
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
        'verifica': (W + B) / DEV_PCA
    }

# --- 6. Processa tutte le colonne di clustering ---
risultati = []

print("\n" + "="*70)
print("ANALISI CLUSTERING - Risultati Dettagliati")
print("="*70)

for col_name in cluster_columns:
    n_pca, n_cluster = parse_column_name(col_name)
    
    if n_pca is None or n_cluster is None:
        print(f"Avviso: Colonna '{col_name}' non rispetta il formato 'PCAX_ClusterY', viene saltata.")
        continue
    
    cluster_data_series = df[col_name].copy() 
    
    try:
        # Pulizia e conversione in array NumPy
        cluster_data_clean_np = pd.to_numeric(cluster_data_series, errors='coerce').fillna(0).astype(int).values.flatten()
        
        valid_indices = np.where(cluster_data_clean_np > 0)[0]
        
        if len(valid_indices) < 2:
            print(f"Avviso: Colonna '{col_name}' ha meno di 2 punti validi. Saltata.")
            continue
            
        pca_data_valid = pca_data_full[valid_indices, :]
        cluster_data_valid = cluster_data_clean_np[valid_indices]
        
        unique_labels = np.unique(cluster_data_valid)
        
        mapping = {label: i + 1 for i, label in enumerate(unique_labels)}
        cluster_data_valid_remapped = np.array([mapping[c] for c in cluster_data_valid])

        pca_data = pca_data_valid[:, :n_pca]
        
        mean_pca_valid = np.mean(pca_data, axis=0)
        DEV_PCA_valid = np.sum((pca_data - mean_pca_valid)**2)
        DEV_PCA_per_valid = DEV_PCA_valid / DEV_TOT
        
        # Calcola le devianze e stampa i dettagli W
        risultato = calcola_devianze_cluster(pca_data, cluster_data_valid_remapped, DEV_TOT, DEV_PCA_valid, DEV_PCA_per_valid)

        # Stampa risultati riepilogativi
        print(f"\n{'='*70}")
        print(f"RIEPILOGO CONFIGURAZIONE: {col_name}")
        print(f"{'='*70}")
        print(f"PCA: {n_pca} componenti | Cluster: {len(unique_labels)} (Etichette Valide)")
        print(f"Verifica (W+B)/DEV_PCA: {risultato['verifica']:.6f}")
        print("-" * 70)
        print(f"Devianza Intra-cluster Totale (**W**):   {risultato['W']:>12.2f}")
        print(f"Devianza Inter-cluster Totale (**B**):   {risultato['B']:>12.2f}")
        print("-" * 70)
        print(f"Devianza spiegata (**B/DEV_TOT**):       {risultato['DEV_PCA_CL_per']:>6.2%}")
        print(f"Devianza persa (**W/DEV_TOT** + Persa PCA):{risultato['DEV_LOST_per']:>6.2%}")
        
        # Salva per esportazione
        risultati.append({
            'Configurazione': col_name,
            'N_PCA': n_pca,
            'N_Cluster': len(unique_labels),
            'Within (W)': risultato['W'],
            'Between (B)': risultato['B'],
            'DEV_Spiegata_%': risultato['DEV_PCA_CL_per'],
            'DEV_Persa_%': risultato['DEV_LOST_per'],
            'Verifica': risultato['verifica']
        })
        
    except Exception as e:
        print(f"\nErrore non gestito per {col_name}: {e}")
        continue
    

# --- 7. Esporta i risultati in un file Excel ---
if risultati:
    df_risultati = pd.DataFrame(risultati)
    output_file = 'risultati_devianze.xlsx'
    df_risultati.to_excel(output_file, index=False)
    print(f"\n{'='*70}")
    print(f"Risultati salvati in: {output_file}")
    print(f"{'='*70}")
else:
    print("\nNessun risultato da salvare.")