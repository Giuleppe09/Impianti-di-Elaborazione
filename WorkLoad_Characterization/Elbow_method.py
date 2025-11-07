import pandas as pd
import matplotlib.pyplot as plt
import numpy as np # Importiamo numpy per creare l'elenco di numeri

# Caricamento del CSV
nomi_colonne = ['Numero di cluster', 'Distanza', 'Leader', 'Subordinato']
df = pd.read_csv(
    "Workload_clustering.csv",
    sep=';',
    decimal=',',
    engine='python',
    header=None,
    skiprows=1,
    names=nomi_colonne
)

# Estrai i dati da visualizzare (gli ultimi 80 punti)
dati_grafico = df[-80:]

# Creazione della figura e degli assi
fig, ax = plt.subplots(figsize=(15, 8)) # Aumentiamo le dimensioni per una migliore leggibilità

# Traccia il grafico con lo stile desiderato
ax.plot(dati_grafico['Numero di cluster'], dati_grafico['Distanza'], marker='o', linestyle='-', color='cyan', label='Distanza')
ax.fill_between(dati_grafico['Numero di cluster'], dati_grafico['Distanza'], alpha=0.3, color='cyan')

# Impostazioni dei titoli e delle etichette
ax.set_xlabel('Number of Clusters', fontsize=14)
ax.set_ylabel('Distance', fontsize=14)
ax.set_title('Elbow Method', fontsize=16)

# Stile del grafico
ax.grid(True, which='major', linestyle='--', linewidth='0.5', color='white')
ax.legend()
ax.set_facecolor('grey')
fig.set_facecolor('white')

# --- MODIFICA PER MOSTRARE TUTTI I NUMERI SULL'ASSE X ---

# 1. Determina il range dei cluster da visualizzare
min_cluster = dati_grafico['Numero di cluster'].min()
max_cluster = dati_grafico['Numero di cluster'].max()

# 2. Crea un elenco di ogni numero intero in quel range
all_cluster_ticks = np.arange(min_cluster, max_cluster + 1)

# 3. Imposta queste tacche sull'asse X
ax.set_xticks(all_cluster_ticks)

# 4. Ruota le etichette per evitare che si sovrappongano
plt.xticks(rotation=90, fontsize=8) # Ruota di 90 gradi e riduce la dimensione del font

# --- Fine della modifica ---

# Adatta il layout per assicurarti che tutto sia visibile
plt.tight_layout()

# Mostra il grafico
plt.show()
