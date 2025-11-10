import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Caricamento del file Excel
df = pd.read_excel(
    "Cronologia1.xlsx",
    header=0,  # La prima riga contiene i nomi delle colonne
    engine='openpyxl'
)

# Converti 'Numero di cluster' in intero (per sicurezza)
df['Numero di cluster'] = df['Numero di cluster'].astype(int)

# Estrai i dati da visualizzare (gli ultimi 80 punti)
dati_grafico = df[-80:]

# Creazione della figura e degli assi
fig, ax = plt.subplots(figsize=(15, 8))

# Traccia il grafico con lo stile desiderato
ax.plot(dati_grafico['Numero di cluster'], dati_grafico['Distanza'], 
        marker='o', linestyle='-', color='cyan', label='Distanza')
ax.fill_between(dati_grafico['Numero di cluster'], dati_grafico['Distanza'], 
                alpha=0.3, color='cyan')

# Impostazioni dei titoli e delle etichette
ax.set_xlabel('Number of Clusters', fontsize=14)
ax.set_ylabel('Distance', fontsize=14)
ax.set_title('Elbow Method', fontsize=16)

# Stile del grafico
ax.grid(True, which='major', linestyle='--', linewidth='0.5', color='white')
ax.legend()
ax.set_facecolor('grey')
fig.set_facecolor('white')

# Mostra tutti i numeri sull'asse X
min_cluster = dati_grafico['Numero di cluster'].min()
max_cluster = dati_grafico['Numero di cluster'].max()
all_cluster_ticks = np.arange(min_cluster, max_cluster + 1)
ax.set_xticks(all_cluster_ticks)
plt.xticks(rotation=90, fontsize=8)

# Adatta il layout
plt.tight_layout()

# Mostra il grafico
plt.show()