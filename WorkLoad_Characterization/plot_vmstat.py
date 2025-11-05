import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# Colonne di Vmstat in ordine
vmstat_headers = "r b swpd free buff cache si so bi bo in cs us sy id wa st gu".split()
file_to_process = "vmStatWC.txt"
output_filename = 'vmStatWC_all_17_metrics_timeline_plots.png'

# --- Inizio Elaborazione Singolo File ---
print(f"Inizio l'elaborazione del file: {file_to_process}")

if not os.path.exists(file_to_process):
    print(f"ERRORE: File '{file_to_process}' non trovato.")
    print("Assicurati che lo script sia nella stessa directory del file di log.")
else:
    # Trova la riga di header per determinare quante righe saltare
    skip = 0
    try:
        with open(file_to_process, 'r') as file:
            for i, line in enumerate(file):
                # Cerca la riga che contiene l'header 'r', 'b', 'us', 'sy'
                if "r" in line and "b" in line and "us" in line and "sy" in line:
                    skip = i + 1  # Salta l'header e inizia dalla riga successiva
                    break
        
        if skip == 0:
            print(f"Header Vmstat non trovato in {file_to_process}. Impossibile procedere.")
        else:
            # Carica i dati
            df = pd.read_csv(file_to_process, skiprows=skip, sep="\s+", header=None, names=vmstat_headers, on_bad_lines='skip')
            
            # Converte tutto in numerico, scartando righe non valide
            df = df.apply(pd.to_numeric, errors='coerce').dropna()

            if df.empty:
                print(f"Nessun dato numerico valido trovato in {file_to_process}.")
            else:
                plot_df = df
                print("Dati pronti per il plot. Asse X = Tempo (Numero Misurazione).")
                
                # --- Creazione dei 17 grafici (1 per ogni metrica) ---
                
                # Abbiamo 17 metriche, usiamo un layout 6x3 (18 subplot totali)
                N_METRICS = len(vmstat_headers)
                N_COLS = 3
                N_ROWS = int(np.ceil(N_METRICS / N_COLS)) # 6 righe
                
                # Aumentiamo la dimensione del grafico per ospitare 17 subplot
                fig, axes = plt.subplots(nrows=N_ROWS, ncols=N_COLS, figsize=(18, 5 * N_ROWS))
                
                fig.suptitle(f'Analisi Temporale di TUTTE le 17 Metriche VMStat - {file_to_process}', fontsize=22, y=1.00)

                # Cicla su tutte le intestazioni vmstat_headers
                for i, col in enumerate(vmstat_headers):
                    row = i // N_COLS
                    col_idx = i % N_COLS
                    ax = axes[row, col_idx]
                    
                    # Colore dinamico (cicla attraverso i colori per distinguere i grafici)
                    color = plt.cm.get_cmap('tab10')(i % 10) 
                    
                    plot_df[col].plot(ax=ax, label=col, color=color)
                    ax.set_title(f'Metrica: {col}', fontsize=14)
                    ax.set_ylabel(col) 
                    ax.legend(loc='upper right')
                    ax.grid(True, linestyle='--', alpha=0.6)
                    ax.set_xlabel('Misurazione (Tempo)')

                # Rimuovi l'ultimo subplot vuoto (se ce n'è uno: 18 - 17 = 1)
                if N_ROWS * N_COLS > N_METRICS:
                    for i in range(N_METRICS, N_ROWS * N_COLS):
                        row = i // N_COLS
                        col_idx = i % N_COLS
                        fig.delaxes(axes[row, col_idx])

                # Migliora il layout per evitare sovrapposizioni
                plt.tight_layout(rect=[0, 0.03, 1, 0.98]) 
                
                # Salva il grafico
                plt.savefig(output_filename)
                print(f"\n✅ Grafico contenente TUTTE le 17 metriche salvato come '{output_filename}'")
                

    except Exception as e:
        print(f"Errore critico durante l'elaborazione del file {file_to_process}: {e}")

# --- Fine Elaborazione ---