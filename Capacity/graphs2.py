import pandas as pd
import matplotlib.pyplot as plt
import glob
import re
from collections import defaultdict
import os
import statistics

# --- FUNZIONE DI CALCOLO (INVARIATA) ---
# Questa funzione è già perfetta per il tuo caso d'uso,
# perché analizza i thread group DENTRO un singolo file.
def get_metrics_from_file(file_path):
    """
    Calcola le metriche per un singolo file, raggruppando per Thread Group,
    usando 300s fissi e mantenendo elapsed in MILLISECONDI.
    
    Restituisce:
    - (float) Media dei throughput dei gruppi
    - (float) Mediana dei throughput dei gruppi
    - (list) Lista di TUTTI gli elapsed (in MILLISECONDI) delle richieste success
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
        print(f"    [CALC] Nessun Thread Group trovato in {file_path}")
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

# --- FUNZIONE PARSING (MODIFICATA) ---
def parse_filename(filename):
    """
    Analizza il nome del file per estrarre il valore CTT.
    Pattern atteso: Test_Plan_CTT_100_risultati.csv
    """
    base_filename = os.path.basename(filename)
    # Cerca il pattern specifico: Test_Plan_CTT_(\d+)_risultati.csv
    # \d+ cattura una o più cifre (il valore CTT)
    # \.csv fa l'escape del punto prima di csv
    pattern = r'Test_Plan_CTT_(\d+)_risultati\.csv'
    match = re.search(pattern, base_filename)
    
    if match:
        ctt_val_str = match.group(1) # Es. '100'
        ctt_val_int = int(ctt_val_str)
        
        # Ricrea il 'ctt_name' (es. 'CTT100') per coerenza con il resto dello script
        ctt_name = f'CTT{ctt_val_str}' 
        
        return {
            'ctt_name': ctt_name,    # Es. 'CTT100'
            'ctt_val': ctt_val_int,  # Es. 100
            'filename': filename
        }
    return None

# --- LOGICA PRINCIPALE (MODIFICATA) ---
def main():
    # MODIFICA 1: Aggiornato il percorso della cartella
    search_path = 'JMeter_Logs/*.csv'
    csv_files = glob.glob(search_path)
    
    if not csv_files:
        print(f"Nessun file CSV trovato nel percorso: {search_path}")
        return

    grouped_files = defaultdict(list)
    for csv_file in csv_files:
        if 'capacity_plots' in csv_file or 'capacity_test_summary.csv' in csv_file:
            continue
            
        # MODIFICA 2: La nuova funzione parse_filename gestisce il nuovo pattern
        parsed = parse_filename(csv_file)
        
        if parsed:
            key = parsed['ctt_name']
            grouped_files[key].append(parsed['filename'])
        else:
            print(f"File saltato (non corrisponde al pattern 'Test_Plan_CTT_...'): {csv_file}")

    if not grouped_files:
        print("Nessun file CTT valido trovato da elaborare.")
        return

    results_list = []

    # Ordina i gruppi in base al valore numerico del CTT (es. CTT100, CTT200)
    # Questa logica funziona ancora perché 'parse_filename' ricrea 'CTT100'
    sorted_groups = sorted(grouped_files.items(), key=lambda item: int(re.search(r'\d+', item[0]).group()))

    # Itera su ogni gruppo CTT (ora con un solo file per gruppo)
    for ctt_name, file_list in sorted_groups:
        
        if not file_list:
            continue

        # Prendiamo il primo (e unico) file per questo gruppo CTT
        file_path = file_list[0]
        
        print(f"\nElaborazione gruppo: {ctt_name} (file: {file_path})")

        metrics = get_metrics_from_file(file_path)
        
        if metrics:
            avg_throughput, med_throughput, all_elapsed_ms = metrics
            
            mean_elapsed_ms = statistics.mean(all_elapsed_ms) if all_elapsed_ms else 0
            median_elapsed_ms = statistics.median(all_elapsed_ms) if all_elapsed_ms else 0
            
            # Estrae il valore numerico (es. 100) da 'CTT100'
            ctt_numeric_val = int(re.search(r'\d+', ctt_name).group())

            results_list.append({
                'ctt_val': ctt_numeric_val,
                'throughput_mean': avg_throughput,
                'elapsed_mean_ms': mean_elapsed_ms,
                'throughput_median': med_throughput,
                'elapsed_median_ms': median_elapsed_ms
            })

            print(f'Risultati per: {ctt_name}')
            print(f'  --- Basato sulla MEDIA ---')
            print(f'     Avg Throughput: {avg_throughput:.2f} req/s')
            print(f'     Avg Delay: {mean_elapsed_ms:.2f} ms')
            print(f'  --- Basato sulla MEDIANA ---')
            print(f'     Median Throughput: {med_throughput:.2f} req/s')
            print(f'     Median Delay: {median_elapsed_ms:.2f} ms (calcolata su {len(all_elapsed_ms)} richieste)')
        else:
            print(f'  >> Nessun dato valido trovato per {ctt_name}, saltato.')

    if not results_list:
        print("\nNessun dato aggregato da plottare.")
        return

    # --- SEZIONE PLOTTING (INVARIATA) ---
    results_list.sort(key=lambda x: x['ctt_val'])

    ctt = [r['ctt_val'] for r in results_list]
    throps_mean = [r['throughput_mean'] for r in results_list]
    elapsed_mean_ms = [r['elapsed_mean_ms'] for r in results_list]
    throps_median = [r['throughput_median'] for r in results_list]
    elapsed_median_ms = [r['elapsed_median_ms'] for r in results_list]

    power_mean = [(throps_mean[i] / elapsed_mean_ms[i]) if elapsed_mean_ms[i] > 0 else 0 for i in range(len(throps_mean))]
    power_median = [(throps_median[i] / elapsed_median_ms[i]) if elapsed_median_ms[i] > 0 else 0 for i in range(len(throps_median))]
    
    print("\nGenerazione grafici...")

    try:
        plt.style.use('https://github.com/dhaitz/matplotlib-stylesheets/raw/master/pitayasmoothie-dark.mplstyle')
        print("Stile 'pitayasmoothie-dark' caricato con successo.")
    except Exception as e_style:
        print(f"Warning: Impossibile caricare stile. Verrà usato quello di default.")

    fig, axs = plt.subplots(3, 1, figsize=(12, 18))
    fig.suptitle('Analisi Capacity Test JMeter (Media vs. Mediana)', fontsize=16, y=1.02)

    axs[0].plot(ctt, throps_mean, marker='o', linestyle='-', color='cyan', label='Throughput (Media)')
    axs[0].plot(ctt, throps_median, marker='x', linestyle='--', color='lightblue', label='Throughput (Mediana)')
    axs[0].set_title('Throughput')
    axs[0].set_ylabel('Throughput (req/s)')
    axs[0].grid(True, linestyle='--', alpha=0.6)
    axs[0].legend()

    axs[1].plot(ctt, elapsed_mean_ms, marker='o', linestyle='-', color='lime', label='Delay (Media)')
    axs[1].plot(ctt, elapsed_median_ms, marker='x', linestyle='--', color='lightgreen', label='Delay (Mediana)')
    axs[1].set_title('Delay (Response Time)')
    axs[1].set_ylabel('Delay (ms)')
    axs[1].grid(True, linestyle='--', alpha=0.6)
    axs[1].legend()

    axs[2].plot(ctt, power_mean, marker='o', linestyle='-', color='red', label='Power (Basato su Media)')
    axs[2].plot(ctt, power_median, marker='x', linestyle='--', color='lightcoral', label='Power (Basato su Mediana)')
    axs[2].set_title('Power (Efficienza)')
    axs[2].set_xlabel('Constant Throughput Timer (valore nominale)')
    axs[2].set_ylabel('Power (Throughput / Delay_ms)')
    axs[2].grid(True, linestyle='--', alpha=0.6)
    axs[2].legend()

    plt.tight_layout(pad=3.0)
    
    output_image = 'capacity_plots_mean_vs_median.png'
    plt.savefig(output_image, bbox_inches='tight')
    print(f"Grafico salvato come: {output_image}")
    
    plt.show()

if __name__ == "__main__":
    main()