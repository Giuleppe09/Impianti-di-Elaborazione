import pandas as pd
import matplotlib.pyplot as plt
import glob
import re
from collections import defaultdict
import os
import statistics
import numpy as np # Importa numpy per la gestione dei tick

# --- FUNZIONE DI CALCOLO (INVARIATA) ---
def get_metrics_from_file(file_path):
    """
    Calcola le metriche per un singolo file, raggruppando per Thread Group,
    usando 300s fissi e mantenendo elapsed in MILLISECONDI.
    """
    try:
        df = pd.read_csv(file_path, encoding='latin1')
        if df.empty:
            print(f"    [CALC] File vuoto: {file_path}")
            return None
    except Exception as e:
        print(f"    [CALC] Errore lettura file {file_path}: {e}")
        return None

    df_success = df[df['success'] == True].copy()
    if df_success.empty:
        print(f"    [CALC] Nessuna richiesta 'success=True' in {file_path}")
        return None

    df_success['threadGroup'] = df_success['threadName'].apply(lambda x: re.match(r'(.+?) \d+-\d+', x).group(1) if re.match(r'(.+?) \d+-\d+', x) else 'Unknown')
    df_success = df_success[df_success['threadGroup'] != 'Unknown']
    grouped = df_success.groupby('threadGroup')

    thread_throughputs = []
    
    if grouped.ngroups == 0:
        print(f"    [CALC] Nessun Thread Group standard trovato in {file_path}, calcolo sul totale.")
        num_requests = len(df_success)
        throughput = num_requests / 300.0 
        thread_throughputs.append(throughput)
    else:
        for name, group in grouped:
            if group.empty:
                continue
            num_requests = len(group)
            throughput = num_requests / 300.0 
            thread_throughputs.append(throughput)

    if not thread_throughputs:
        print(f"    [CALC] Nessun throughput calcolato per {file_path}")
        return None

    s_throughputs = pd.Series(thread_throughputs)
    avg_throughput = s_throughputs.mean()
    med_throughput = s_throughputs.median()
    
    all_elapsed_ms = df_success['elapsed'].tolist()
    
    return avg_throughput, med_throughput, all_elapsed_ms

# --- FUNZIONE PARSING (INVARIATA) ---
def parse_filename(filename):
    """
    Analizza il nome del file per estrarre il valore CTT.
    Pattern atteso: Test_Plan_CTT_100_risultati.csv
    """
    base_filename = os.path.basename(filename)
    pattern = r'Test_Plan_CTT_(\d+)_risultati\.csv'
    match = re.search(pattern, base_filename)
    
    if match:
        ctt_val_str = match.group(1)
        ctt_val_int = int(ctt_val_str)
        ctt_name = f'CTT{ctt_val_str}' 
        
        return {
            'ctt_name': ctt_name,
            'ctt_val': ctt_val_int,
            'filename': filename
        }
    return None

# --- FUNZIONI CALCOLO CAPACITY (INVARIATE) ---

def find_knee_capacity(ctt_list, power_list):
    """
    Trova la Knee Capacity.
    Definizione: Punto di Massima Efficienza (Max Power).
    """
    if not power_list or not ctt_list:
        return 0, 0

    max_power = max(power_list)
    max_power_index = power_list.index(max_power)
    knee_ctt = ctt_list[max_power_index]
    
    return knee_ctt, max_power

def find_usable_capacity(ctt_list, throughput_list, power_list):
    """
    Trova la Usable Capacity.
    Definizione: Punto di Massima Performance (Max Throughput).
    """
    if not throughput_list or not ctt_list or not power_list:
        return 0, 0, 0

    max_throughput = max(throughput_list)
    max_throughput_index = throughput_list.index(max_throughput)
    usable_ctt = ctt_list[max_throughput_index]
    
    power_at_max_throughput = power_list[max_throughput_index]
    
    return usable_ctt, max_throughput, power_at_max_throughput

# --- FUNZIONE TICKS PERSONALIZZATI (INVARIATA) ---
def generate_custom_ticks(ctt_list):
    """
    Genera una lista di ticks da mostrare sull'asse X
    basandosi sulla lista di CTT disponibili e sulle regole:
    1. Ogni 100
    2. Ogni 50 (solo tra 250-450)
    3. Ogni 50 (solo tra 500-700)
    """
    ticks_to_show = set()
    for ctt_val in ctt_list:
        if ctt_val % 100 == 0:
            ticks_to_show.add(ctt_val)
        if (250 <= ctt_val <= 450) and (ctt_val % 50 == 0):
            ticks_to_show.add(ctt_val)
        if (500 <= ctt_val <= 700) and (ctt_val % 50 == 0):
            ticks_to_show.add(ctt_val)
            
    return sorted(list(ticks_to_show))
# --- FINE NUOVA FUNZIONE ---

# --- LOGICA PRINCIPALE (INVARIATA FINO AL PLOTTING) ---
def main():
    search_path = 'JMeter_Logs/*.csv'
    csv_files = glob.glob(search_path)
    
    if not csv_files:
        print(f"Nessun file CSV trovato nel percorso: {search_path}")
        return

    grouped_files = defaultdict(list)
    for csv_file in csv_files:
        if 'capacity_plots' in csv_file or 'capacity_test_summary.csv' in csv_file:
            continue
        parsed = parse_filename(csv_file)
        if parsed:
            grouped_files[parsed['ctt_name']].append(parsed['filename'])
        else:
            print(f"File saltato (non corrisponde al pattern 'Test_Plan_CTT_...'): {csv_file}")

    if not grouped_files:
        print("Nessun file CTT valido trovato da elaborare.")
        return

    results_list = []
    sorted_groups = sorted(grouped_files.items(), key=lambda item: int(re.search(r'\d+', item[0]).group()))

    for ctt_name, file_list in sorted_groups:
        if not file_list: continue
        file_path = file_list[0]
        print(f"\nElaborazione gruppo: {ctt_name} (file: {file_path})")
        metrics = get_metrics_from_file(file_path)
        
        if metrics:
            avg_throughput, med_throughput, all_elapsed_ms = metrics
            mean_elapsed_ms = statistics.mean(all_elapsed_ms) if all_elapsed_ms else 0
            median_elapsed_ms = statistics.median(all_elapsed_ms) if all_elapsed_ms else 0
            ctt_numeric_val = int(re.search(r'\d+', ctt_name).group())

            results_list.append({
                'ctt_val': ctt_numeric_val,
                'throughput_mean': avg_throughput,
                'elapsed_mean_ms': mean_elapsed_ms,
                'throughput_median': med_throughput,
                'elapsed_median_ms': median_elapsed_ms
            })
            print(f'Risultati per: {ctt_name}')
            print(f'  Avg Throughput: {avg_throughput:.2f} req/s | Avg Delay: {mean_elapsed_ms:.2f} ms')
            print(f'  Median Throughput: {med_throughput:.2f} req/s | Median Delay: {median_elapsed_ms:.2f} ms')
        else:
            print(f'  >> Nessun dato valido trovato per {ctt_name}, saltato.')

    if not results_list:
        print("\nNessun dato aggregato da plottare.")
        return

    results_list.sort(key=lambda x: x['ctt_val'])

    ctt = [r['ctt_val'] for r in results_list]
    throps_mean = [r['throughput_mean'] for r in results_list]
    elapsed_mean_ms = [r['elapsed_mean_ms'] for r in results_list]
    throps_median = [r['throughput_median'] for r in results_list]
    elapsed_median_ms = [r['elapsed_median_ms'] for r in results_list]

    power_mean = [(throps_mean[i] / elapsed_mean_ms[i]) if elapsed_mean_ms[i] > 0 else 0 for i in range(len(throps_mean))]
    power_median = [(throps_median[i] / elapsed_median_ms[i]) if elapsed_median_ms[i] > 0 else 0 for i in range(len(throps_median))]
    
    print("\n" + "="*40)
    print(" ANALISI PUNTI DI CAPACITY (Basati sulla MEDIA)")
    print("="*40)
    
    k_ctt_m, k_pow_m = find_knee_capacity(ctt, power_mean)
    u_ctt_m, u_thr_m, u_pow_m = find_usable_capacity(ctt, throps_mean, power_mean)
    
    print(f"  Knee Capacity (Max Efficienza):")
    print(f"    -> CTT = {k_ctt_m} (Power: {k_pow_m:.6f})")
    
    print(f"\n  Usable Capacity (Max Performance):")
    print(f"    -> CTT = {u_ctt_m} (Throughput: {u_thr_m:.4f} req/s)")
    print(f"    (A questo CTT, la Power era: {u_pow_m:.6f})")
    print("="*40)

    custom_ticks = generate_custom_ticks(ctt)
    
    print("\nGenerazione grafici con stile personalizzato...")

    # --- INIZIO BLOCCO STILE E PLOT MODIFICATO ---
    plt.style.use('default') 
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    
    fig, axs = plt.subplots(3, 1, figsize=(12, 18), sharex=True)
    fig.suptitle('Analisi Capacity Test JMeter (Media vs. Mediana)', fontsize=16, y=1.02, color='black')

    # Colori
    COLOR_THROUGHPUT_MEAN = '#00CED1'
    COLOR_THROUGHPUT_MEDIAN = '#AFEEEE'
    COLOR_DELAY_MEAN = '#32CD32'
    COLOR_DELAY_MEDIAN = '#98FB98'
    COLOR_POWER_MEAN = '#FF0000'
    COLOR_POWER_MEDIAN = '#FA8072'

    # Funzione helper per impostare i colori degli assi (per evitare codice duplicato)
    def setup_ax_style(ax):
        ax.grid(True, linestyle='--', alpha=0.6, color='gray')
        ax.legend(loc='best', frameon=False, labelcolor='black')
        ax.tick_params(axis='x', colors='black')
        ax.tick_params(axis='y', colors='black')
        ax.yaxis.label.set_color('black')
        ax.xaxis.label.set_color('black')
        ax.title.set_color('black')
        for spine in ax.spines.values():
            spine.set_color('black')

    # --- Grafico Throughput ---
    axs[0].plot(ctt, throps_mean, marker='o', linestyle='-', color=COLOR_THROUGHPUT_MEAN, label='Throughput (Media)', markersize=5)
    axs[0].plot(ctt, throps_median, marker='x', linestyle='--', color=COLOR_THROUGHPUT_MEDIAN, label='Throughput (Mediana)', markersize=5)
    axs[0].set_title('Throughput', color='black')
    axs[0].set_ylabel('Throughput (req/s)', color='black')
    axs[0].axvline(x=u_ctt_m, color='orange', linestyle=':', linewidth=2, label=f'Usable (Max Throughput): CTT {u_ctt_m}')
    setup_ax_style(axs[0])

    # --- Grafico Delay ---
    axs[1].plot(ctt, elapsed_mean_ms, marker='o', linestyle='-', color=COLOR_DELAY_MEAN, label='Delay (Media)', markersize=5)
    axs[1].plot(ctt, elapsed_median_ms, marker='x', linestyle='--', color=COLOR_DELAY_MEDIAN, label='Delay (Mediana)', markersize=5)
    axs[1].set_title('Delay (Response Time)', color='black')
    axs[1].set_ylabel('Delay (ms)', color='black')
    setup_ax_style(axs[1])

    # --- Grafico Power ---
    axs[2].plot(ctt, power_mean, marker='o', linestyle='-', color=COLOR_POWER_MEAN, label='Power (Basato su Media)', markersize=5)
    axs[2].plot(ctt, power_median, marker='x', linestyle='--', color=COLOR_POWER_MEDIAN, label='Power (Basato su Mediana)', markersize=5)
    axs[2].set_title('Power (Efficienza)', color='black')
    axs[2].set_xlabel('Constant Throughput Timer (valore nominale)', color='black')
    axs[2].set_ylabel('Power (Throughput / Delay_ms)', color='black')
    
    # EVIDENZIO I PUNTI SULLA CURVA DI POWER (MEDIA)
    axs[2].plot(k_ctt_m, k_pow_m, '*', markersize=18, color='yellow', markeredgecolor='black', label=f'Knee (Max Power): CTT {k_ctt_m}')
    axs[2].plot(u_ctt_m, u_pow_m, 'P', markersize=15, color='orange', markeredgecolor='black', label=f'Usable (Max Thr.): CTT {u_ctt_m}')

    # AGGIUNGO LE ANNOTAZIONI CON FRECCE
    axs[2].annotate(
        f'Knee Capacity\n(Max Efficienza)\nCTT: {k_ctt_m}',
        xy=(k_ctt_m, k_pow_m), 
        xytext=(k_ctt_m + 150, k_pow_m + 0.005), 
        ha='left',
        arrowprops=dict(facecolor='yellow', shrink=0.05, width=1, headwidth=8),
        bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=1, alpha=0.8),
        fontsize=9,
        color='black' 
    )
    axs[2].annotate(
        f'Usable Capacity\n(Max Throughput)\nCTT: {u_ctt_m}',
        xy=(u_ctt_m, u_pow_m), 
        xytext=(u_ctt_m + 150, u_pow_m + 0.002), 
        ha='left',
        arrowprops=dict(facecolor='orange', shrink=0.05, width=1, headwidth=8),
        bbox=dict(boxstyle="round,pad=0.3", fc="orange", ec="black", lw=1, alpha=0.8),
        fontsize=9,
        color='black' 
    )
    
    setup_ax_style(axs[2]) # Applica lo stile
    axs[2].legend(loc='upper right', frameon=False, labelcolor='black') # La legenda per la Power

    # --- Imposta i ticks personalizzati sull'ultimo asse (condiviso) ---
    axs[2].set_xticks(custom_ticks)
    # Ruota le etichette per evitare sovrapposizioni
    plt.setp(axs[2].get_xticklabels(), rotation=45, ha='right', fontsize=9)
    # --- FINE BLOCCO STILE E PLOT MODIFICATO ---

    plt.tight_layout(pad=3.0)
    
    output_image = 'capacity_plots_mean_vs_median.png'
    plt.savefig(output_image, bbox_inches='tight', facecolor='white') 
    print(f"Grafico salvato come: {output_image}")
    
    plt.show()

if __name__ == "__main__":
    main()