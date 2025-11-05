import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Caricamento del CSV -> MODIFICATO per file Excel (.xlsx)
nomi_colonne = ['Numero di cluster', 'Distanza', 'Leader', 'Subordinato']

# **USARE pd.read_excel INVECE DI pd.read_csv**
# I file Excel non usano `sep`, `engine` o `decimal` come in read_csv.
# Se il tuo file Excel ha una riga di intestazione, usa header=0 (la prima riga).
# Se non ha intestazione e i dati iniziano subito, prova header=None.
# Qui usiamo 'header=None' e 'skiprows=1' come nel tuo codice originale,
# ma `pd.read_excel` carica l'intero foglio, quindi `skiprows` funziona in modo diverso
# e potresti non averne bisogno se il file è ben formato.

# Tentativo 1 (più vicino al tuo intento originale):
try:
    df = pd.read_excel(
        "Cronologia_Clustering.xlsx",
        header=None,
        skiprows=1,  # Salta la prima riga se contiene titoli non voluti
        names=nomi_colonne
    )
    # Se i dati in Excel usano la virgola come separatore decimale,
    # potresti dover fare una conversione *dopo* il caricamento.
    # Ad esempio, convertendo la colonna 'Distanza' da stringa a float,
    # sostituendo la virgola con il punto, se necessario.
    # df['Distanza'] = df['Distanza'].astype(str).str.replace(',', '.').astype(float)

except ValueError:
    # Se il tuo file Excel usa una virgola come separatore decimale,
    # la conversione potrebbe non essere necessaria se i dati sono stati
    # salvati correttamente, ma in caso contrario, potresti dover
    # leggere il file come se fosse CSV (che genera l'errore originale)
    # o fare una pulizia dei dati dopo il caricamento con read_excel.
    # **Nota:** il `UnicodeDecodeError` è quasi sempre per il file .xlsx usato con read_csv.
    print("Errore: Impossibile leggere il file come Excel, ricontrolla il formato o i parametri.")
    # Se l'errore persiste, devi assicurarti che il file
    # "Cronologia_Clustering.xlsx" sia un vero file Excel e non un file
    # CSV rinominato, o che i tuoi dati siano nella prima sheet.

# --- Il resto del codice rimane invariato ---

# Estrai i dati da visualizzare (gli ultimi 80 punti)
dati_grafico = df[-80:]

# Creazione della figura e degli assi
fig, ax = plt.subplots(figsize=(15, 8))

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
plt.xticks(rotation=90, fontsize=8)

# --- Fine della modifica ---

# Adatta il layout per assicurarti che tutto sia visibile
plt.tight_layout()

# Mostra il grafico
plt.show()