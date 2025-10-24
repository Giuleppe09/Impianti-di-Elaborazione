import pandas as pd
import numpy as np
from scipy.stats import zscore
import re

# --- 1. Lettura dei dati ---
try:
    # Leggi i dati originali
    data = pd.read_excel('output_completo.xlsx').values
    # Leggi il file unico con PCA e clustering
    df = pd.read_excel('output_completo_PCA_altriCluster.xlsx')
except FileNotFoundError as e:
    print(f"Errore: {e}. Assicurati che i file Excel siano nella stessa cartella dello script.")
    exit()
    
# --- 2. Separazione colonne PCA e Clustering ---
# Identifica le colonne PCA (Principale1, Principale2, ...)
pca_columns = [col for col in df.columns if col.startswith('Principale')]
# Identifica le colonne di clustering (PCA10_Cluster9, ...)
cluster_columns = [col for col in df.columns if col.startswith('PCA') and 'Cluster' in col]

print(f"Trovate {len(pca_columns)} colonne PCA")
print(f"Trovate {len(cluster_columns)} colonne di clustering")

# --- 3. Calcolo della Devianza Totale ---
# Normalizzazione dei dati (equivalente a zscore in MATLAB, da fare solo una volta)
data_norm = zscore(data)
# CORREZIONE: Sostituisce eventuali NaN (risultanti da colonne a varianza zero) con 0
data_norm = np.nan_to_num(data_norm)

# Calcolo della devianza totale (uguale per tutti)
mean_total = np.mean(data_norm, axis=0)
DEV_TOT = np.sum((data_norm - mean_total)**2)


# --- 4. Calcolo della Devianza post-PCA ---
print("\n" + "="*70)
print("ANALISI PCA")
print("="*70)

# Estrai i dati PCA come array NumPy
pca_data_full = df[pca_columns].values

# Devianza post-PCA (su tutte le componenti)
mean_pca = np.mean(pca_data_full, axis=0)
DEV_PCA = np.sum((pca_data_full - mean_pca)**2)
DEV_PCA_per = DEV_PCA / DEV_TOT # Percentuale di devianza mantenuta dopo la PCA

print(f"Devianza Totale (DEV_TOT):     {DEV_TOT:>12.2f}")
#Le componenti sono diverse, quindi non ha senso stampare DEV_PCA
#print(f"Devianza dopo PCA (DEV_PCA):   {DEV_PCA:>12.2f} ({DEV_PCA_per:.2%})")
#print(f"Devianza persa nella PCA:      {(1 - DEV_PCA_per):.2%}")

#Helper function to parse column names
def parse_column_name(col_name):
    """
    Estrae il numero di PCA e il numero di cluster dal nome della colonna.
    Es: 'PCA10_Cluster13' -> (10, 13)
    """
    match = re.match(r'PCA(\d+)_Cluster(\d+)', col_name)
    if match:
        n_pca = int(match.group(1))
        n_cluster = int(match.group(2))
        return n_pca, n_cluster
    return None, None

# --- 5. Funzione per calcolare le devianze per clustering ---
def calcola_devianze_cluster(pca_data, cluster_data, DEV_TOT, DEV_PCA, DEV_PCA_per):
    """
    Calcola le devianze intra e inter cluster per una configurazione.
    """
    # Assicura che cluster_data sia un vettore 1D
    cluster_data = cluster_data.flatten()
    # Prendo le colonne del file di clustering, quindi itero sul numero di colonne di clustering
    N_cluster = int(np.max(cluster_data))
    
    # Inizializzazione array per devianze
    W_list = np.zeros(N_cluster) # Devianza interna per ogni cluster
    B_list = np.zeros(N_cluster) # Devianza esterna per ogni cluster
    
    # Media globale per calcolo Between
    global_centroid_pca = np.mean(pca_data, axis=0)
    
    # Calcolo devianze per ogni cluster (le colonne)
    for i in range(1, N_cluster + 1):
        # Trova gli indici dei dati appartenenti al cluster corrente
        index = np.where(cluster_data == i)[0]
        
        if index.size > 0:
            # Estrae i dati dei cluster samples
            cluster_samples = pca_data[index, :]
            # Numero di elementi nel cluster
            n_ele = len(index)
            # Calcolo del centroide (media) del cluster
            centroid = np.mean(cluster_samples, axis=0)
            
            # Devianza Within
            W_list[i-1] = np.sum((cluster_samples - centroid)**2)
            
            # Devianza Between
            B_list[i-1] = n_ele * np.sum((centroid - global_centroid_pca)**2)
    
    W = np.sum(W_list)
    B = np.sum(B_list)
    
    # Calcolo percentuali
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
print("ANALISI CLUSTERING")
print("="*70)

for col_name in cluster_columns:
    n_pca, n_cluster = parse_column_name(col_name)
    
    if n_pca is None or n_cluster is None:
        print(f"Avviso: Colonna '{col_name}' non ha un formato valido, viene saltata.")
        continue
    
    try:
        # Estrai solo le prime n_pca componenti principali
        pca_data = pca_data_full[:, :n_pca]
        
        # Calcola DEV_PCA specifica per queste n_pca componenti
        mean_pca = np.mean(pca_data, axis=0)
        DEV_PCA = np.sum((pca_data - mean_pca)**2)
        DEV_PCA_per = DEV_PCA / DEV_TOT
        
        # Estrai i dati di clustering
        cluster_data = df[col_name].values.flatten()
        
        # Calcola le devianze
        risultato = calcola_devianze_cluster(pca_data, cluster_data, DEV_TOT, DEV_PCA, DEV_PCA_per)
        
        # Stampa risultati
        print(f"\n{'='*70}")
        print(f"CONFIGURAZIONE: {col_name}")
        print(f"{'='*70}")
        print(f"PCA: {n_pca} componenti | Cluster: {n_cluster}")
        print(f"Verifica (W+B)/DEV_PCA: {risultato['verifica']:.6f}")
        print("-" * 70)
        print(f"Devianza Intra-cluster (W):           {risultato['W']:>12.2f}")
        print(f"Devianza Inter-cluster (B):           {risultato['B']:>12.2f}")
        print("-" * 70)
        print(f"Devianza spiegata (PCA & Cluster):    {risultato['DEV_PCA_CL_per']:>6.2%}")
        print(f"Devianza persa (Lost):                {risultato['DEV_LOST_per']:>6.2%}")
        
        # Salva per esportazione
        risultati.append({
            'Configurazione': col_name,
            'N_PCA': n_pca,
            'N_Cluster': n_cluster,
            'Within (W)': risultato['W'],
            'Between (B)': risultato['B'],
            'DEV_Spiegata_%': risultato['DEV_PCA_CL_per'],
            'DEV_Persa_%': risultato['DEV_LOST_per'],
            'Verifica': risultato['verifica']
        })
        
    except Exception as e:
        print(f"\nErrore per {col_name}: {e}")
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
