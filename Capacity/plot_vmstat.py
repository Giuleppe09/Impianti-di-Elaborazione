import pandas as pd
import matplotlib.pyplot as plt
import glob
import re
import os
import numpy as np

# Colonne di Vmstat in ordine
vmstat_headers = "r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st gu".split()

data_to_plot = []
file_pattern = "Test_Plan_CTT_*_vmstat_log.txt"
# Usa glob.glob per trovare i file e sorted() per ordinarli
files = sorted(glob.glob(file_pattern)) 

if not files:
    print(f"ATTENZIONE: Nessun file trovato con il pattern: {file_pattern}")
    print("Assicurati che lo script sia nella stessa directory dei file di log.")
else:
    print(f"Trovati {len(files)} file. Inizio l'elaborazione...")
    
    for f in files:
        # Estrae il valore CTT dal nome del file
        match = re.search(r'CTT_(\d+)_vmstat_log\.txt', f)
        if not match:
            print(f"Impossibile estrarre CTT da {f}. Salto.")
            continue
        ctt = int(match.group(1))
        
        # Trova la riga di header per determinare quante righe saltare
        skip = 0
        try:
            with open(f, 'r') as file:
                for i, line in enumerate(file):
                    # Cerca la riga che contiene l'header 'r', 'b', 'us', 'sy'
                    if "r" in line and "b" in line and "us" in line and "sy" in line:
                        skip = i + 1  # Salta l'header e inizia dalla riga successiva
                        break
            
            if skip == 0:
                print(f"Header Vmstat non trovato in {f}. Salto.")
                continue

            # --- Risolto il warning ---
            # Sostituito 'delim_whitespace=True' con 'sep="\s+"'
            # \s+ è un'espressione regolare che significa "uno o più spazi"
            df = pd.read_csv(f, skiprows=skip, sep="\s+", header=None, names=vmstat_headers, on_bad_lines='skip')
            
            # Converte tutto in numerico, scartando righe non valide
            df = df.apply(pd.to_numeric, errors='coerce').dropna()

            if df.empty:
                print(f"Nessun dato numerico valido trovato in {f}.")
                continue
                
           
            # Meglio .mean() o .median()
            median_metrics = df.mean()
            median_metrics['CTT'] = ctt  # Aggiunge il CTT come colonna
            data_to_plot.append(median_metrics)

        except Exception as e:
            print(f"Errore durante l'elaborazione del file {f}: {e}")

# Se abbiamo dati, procediamo con il plot
if data_to_plot:
    # Crea il DataFrame finale
    plot_df = pd.DataFrame(data_to_plot)
    plot_df = plot_df.sort_values(by='CTT') # Ordina i dati per CTT
    plot_df.set_index('CTT', inplace=True) # Usa CTT come asse X
    
    print("\Dati aggregati pronti per il plot.")
    
    # --- Creazione dei 6 grafici ---
    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(16, 18))
    # Titolo aggiornato per riflettere l'uso della mediana
    fig.suptitle('Analisi VMStat al variare del carico (CTT)', fontsize=20, y=1.03)

    # 1. Grafico "procs" (r)
    ax = axes[0, 0]
    plot_df['r'].plot(ax=ax, marker='o', label='Waiting processes', color='blue')
    ax.set_title('Waiting processes (procs: r)')
    ax.legend()
    ax.grid(True)
    ax.set_ylabel('Conteggio') 

    # 2. Grafico "memory" (swpd, free, buff, cache)
    ax = axes[0, 1]
    plot_df['swpd'].plot(ax=ax, marker='o', label='Virtual Memory (swpd)', color='blue')
    plot_df['free'].plot(ax=ax, marker='o', label='Free Memory (free)', color='orange')
    plot_df['buff'].plot(ax=ax, marker='o', label='Buffer Memory (buff)', color='green')
    plot_df['cache'].plot(ax=ax, marker='o', label='Cache Memory (cache)', color='red')
    ax.set_title('Utilizzo Memoria (memory)')
    ax.set_ylabel('KB') 
    ax.legend()
    ax.grid(True)

    # 3. Grafico "swap" (si, so)
    ax = axes[1, 0]
    plot_df['si'].plot(ax=ax, marker='o', label='Virtual Memory Swapped-in (si)', color='blue')
    plot_df['so'].plot(ax=ax, marker='o', label='Virtual Memory Swapped-out (so)', color='orange')
    ax.set_title('Attività di Swap (swap)')
    ax.set_ylabel('kb/s') 
    ax.legend()
    ax.grid(True)

    # 4. Grafico "io" (bi, bo)
    ax = axes[1, 1]
    plot_df['bi'].plot(ax=ax, marker='o', label='Memory blocks read (bi)', color='blue')
    plot_df['bo'].plot(ax=ax, marker='o', label='Memory blocks written (bo)', color='orange')
    ax.set_title('Attività I/O (io)')
    ax.set_ylabel('Blocks/s') 
    ax.legend()
    ax.grid(True)

    # 5. Grafico "system" (in, cs)
    ax = axes[2, 0]
    plot_df['in'].plot(ax=ax, marker='o', label='Interrupt per second (in)', color='blue')
    plot_df['cs'].plot(ax=ax, marker='o', label='Context-switches per second (cs)', color='orange')
    ax.set_title('Eventi di Sistema (system)')
    ax.set_ylabel('Eventi/s') 
    ax.legend()
    ax.grid(True)

    # 6. Grafico "cpu" (us, sy, id, wa)
    ax = axes[2, 1]
    plot_df['us'].plot(ax=ax, marker='o', label='User Time (us)', color='blue')
    plot_df['sy'].plot(ax=ax, marker='o', label='Kernel Time (sy)', color='orange')
    plot_df['id'].plot(ax=ax, marker='o', label='Idle Time (id)', color='green')
    plot_df['wa'].plot(ax=ax, marker='o', label='I/O Waiting Time (wa)', color='red')
    ax.set_title('Utilizzo CPU (cpu)')
    ax.set_ylabel('%') 
    ax.legend()
    ax.grid(True)

    # Imposta l'etichetta X "CTT" per tutti i grafici
    plt.setp(axes, xlabel='Valore CTT')
    
    # Migliora il layout per evitare sovrapposizioni
    plt.tight_layout(rect=[0, 0.03, 1, 0.98]) # Aggiusta per il titolo principale
    
    # Nome file aggiornato
    output_filename = 'vmstat_analysis_plots.png'
    plt.savefig(output_filename)
    print(f"Grafico (mediana) salvato come '{output_filename}'")

else:
    print("Nessun dato è stato elaborato, nessun grafico generato.")