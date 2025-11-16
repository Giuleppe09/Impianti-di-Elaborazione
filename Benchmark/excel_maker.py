#!/usr/bin/env python3
"""
Script per analizzare i risultati del benchmark nbody e creare un file Excel
strutturato per l'import su JMP, con grafici comparativi.
"""

import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def extract_numbers_from_file(filepath):
    """
    Estrae i valori di tempo dal file nel formato "Time: XXX ms".
    """
    times = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Pattern per catturare "Time: 123456 ms"
                match = re.search(r'Time:\s*(\d+)\s*ms', line, re.IGNORECASE)
                if match:
                    time_ms = int(match.group(1))
                    times.append(time_ms)
    except Exception as e:
        print(f"Errore nella lettura di {filepath}: {e}")
    
    return times

def process_benchmark_directory(base_dir):
    """
    Processa la directory dei risultati e restituisce un DataFrame.
    
    Struttura attesa:
    base_dir/
        500000_corpi/
            1_run.txt
            2_run.txt
            ...
        1000000_corpi/
            ...
    """
    results = []
    
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Errore: Directory {base_dir} non trovata!")
        return None
    
    # Trova tutte le sottocartelle (es: 500000_corpi, 1000000_corpi, etc.)
    subdirs = sorted([d for d in base_path.iterdir() if d.is_dir()])
    
    if not subdirs:
        print(f"Nessuna sottocartella trovata in {base_dir}")
        return None
    
    print(f"Trovate {len(subdirs)} configurazioni di corpi:\n")
    
    for subdir in subdirs:
        # Estrae il numero di corpi dal nome della cartella
        match = re.search(r'(\d+)_corpi', subdir.name)
        if not match:
            print(f"Cartella ignorata (formato nome non valido): {subdir.name}")
            continue
        
        n_bodies = int(match.group(1))
        print(f"Processando: {n_bodies} corpi...")
        
        # Trova tutti i file _run.txt nella sottocartella
        run_files = sorted(subdir.glob('*_run.txt'), 
                          key=lambda x: int(re.search(r'(\d+)_run', x.name).group(1)))
        
        for run_file in run_files:
            # Estrae il numero della run
            run_match = re.search(r'(\d+)_run', run_file.name)
            run_number = int(run_match.group(1))
            
            # Estrae i numeri dal file
            values = extract_numbers_from_file(run_file)
            
            if values:
                # Calcola la media
                mean_value = np.mean(values)
                
                results.append({
                    'N_Bodies': n_bodies,
                    'Run': run_number,
                    'Mean_Time_ms': mean_value,
                    'N_Samples': len(values),
                    'StdDev_ms': np.std(values, ddof=1) if len(values) > 1 else 0,
                    'Min_ms': np.min(values),
                    'Max_ms': np.max(values)
                })
            else:
                print(f"  WARNING: Nessun valore trovato in {run_file.name}")
    
    if not results:
        print("Nessun dato valido trovato!")
        return None
    
    # Crea DataFrame
    df = pd.DataFrame(results)
    
    # Ordina per numero di corpi e poi per run
    df = df.sort_values(['N_Bodies', 'Run']).reset_index(drop=True)
    
    return df

def create_jmp_excel(df, output_file='risultati_nbody_per_JMP.xlsx'):
    """
    Crea un file Excel ottimizzato per l'import su JMP.
    Formato principale: 37 righe (run) x N colonne (configurazioni N_Bodies)
    """
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet 1: FORMATO PRINCIPALE - Run per righe, N_Bodies per colonne
        # Questo è il formato che vuoi per JMP: 37 campioni per ogni colonna
        pivot_main = df.pivot(index='Run', columns='N_Bodies', values='Mean_Time_ms')
        
        # Rinomina le colonne in modo più leggibile
        pivot_main.columns = [f'{int(col)}_bodies' for col in pivot_main.columns]
        pivot_main.index.name = 'Run'
        
        pivot_main.to_excel(writer, sheet_name='Dati_per_JMP')
        
        # Sheet 2: Dati completi (formato long) per analisi alternative
        df.to_excel(writer, sheet_name='Dati_Completi_Long', index=False)
        
        # Sheet 3: Statistiche riassuntive per configurazione
        summary = df.groupby('N_Bodies').agg({
            'Mean_Time_ms': ['mean', 'std', 'min', 'max', 'count'],
            'StdDev_ms': 'mean'
        }).round(2)
        summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
        summary.to_excel(writer, sheet_name='Statistiche_Summary')
    
    print(f"\n✓ File Excel creato: {output_file}")
    print(f"  - Sheet 'Dati_per_JMP': 37 run x N_Bodies colonne (FORMATO PRINCIPALE)")
    print(f"  - Sheet 'Dati_Completi_Long': formato long alternativo")
    print(f"  - Sheet 'Statistiche_Summary': statistiche aggregate")

def create_comparison_plots(df_dict, output_dir='grafici_confronto'):
    """
    Crea grafici boxplot comparativi tra diversi dataset.
    
    Args:
        df_dict: dizionario con chiave=nome (es. 'Crist', 'Suso') e valore=DataFrame
        output_dir: directory dove salvare i grafici
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Ottieni tutte le configurazioni N_Bodies presenti
    all_bodies = set()
    for df in df_dict.values():
        all_bodies.update(df['N_Bodies'].unique())
    all_bodies = sorted(all_bodies)
    
    print(f"\n{'='*60}")
    print("CREAZIONE GRAFICI COMPARATIVI")
    print(f"{'='*60}\n")
    
    # Crea un grafico per ogni configurazione di N_Bodies
    for n_bodies in all_bodies:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Prepara i dati per il boxplot
        data_to_plot = []
        labels = []
        colors = []
        
        # Palette colori personalizzabile
        color_palette = ['#90EE90', '#FFB6C6', '#87CEEB', '#FFD700', '#DDA0DD']
        
        for idx, (name, df) in enumerate(df_dict.items()):
            subset = df[df['N_Bodies'] == n_bodies]['Mean_Time_ms']
            if len(subset) > 0:
                data_to_plot.append(subset.values)
                labels.append(f'avg_t_{name.lower()}')
                colors.append(color_palette[idx % len(color_palette)])
        
        if not data_to_plot:
            print(f"  Nessun dato per {n_bodies} corpi, skip...")
            plt.close(fig)
            continue
        
        # Crea il boxplot
        bp = ax.boxplot(data_to_plot, 
                        labels=labels,
                        patch_artist=True,
                        widths=0.6,
                        showmeans=True,
                        meanprops=dict(marker='^', markerfacecolor='darkgreen', 
                                      markersize=10, markeredgecolor='darkgreen'))
        
        # Colora i box
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        
        # Stile del grafico
        ax.set_ylabel('Valori', fontsize=12)
        ax.set_title(f'Confronto {n_bodies/1e6:.0f}M corpi', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        
        # Salva il grafico
        filename = f'{output_dir}/confronto_{n_bodies}_corpi.png'
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        print(f"  ✓ Creato: {filename}")
    
    print(f"\n{'='*60}")
    print(f"Grafici salvati in: {output_dir}/")
    print(f"{'='*60}")

def load_multiple_benchmarks(directories):
    """
    Carica risultati da multiple directory di benchmark.
    
    Args:
        directories: dizionario {nome: path} es. {'Crist': 'Crist_Results', 'Suso': 'Suso_Results'}
    
    Returns:
        dizionario {nome: DataFrame}
    """
    results = {}
    
    for name, path in directories.items():
        print(f"\n{'='*60}")
        print(f"Caricamento dati: {name}")
        print(f"{'='*60}")
        df = process_benchmark_directory(path)
        if df is not None:
            results[name] = df
            print(f"✓ {name}: {len(df)} righe caricate")
        else:
            print(f"✗ {name}: errore nel caricamento")
    
    return results

def main():
    """
    Funzione principale.
    """
    print("="*60)
    print("ANALISI RISULTATI BENCHMARK NBODY")
    print("="*60 + "\n")
    
    # Configurazione - MODIFICA QUESTI PATH
    benchmarks = {
        'Suso': 'Suso_Results',      # Directory risultati Suso
        'Crist': 'Crist_Results',    # Directory risultati Crist
    }
    
    # Carica tutti i benchmark
    all_data = load_multiple_benchmarks(benchmarks)
    
    if not all_data:
        print("\n✗ Nessun dato caricato. Verifica i path delle directory.")
        return
    
    # Crea Excel separati per ogni benchmark
    print(f"\n{'='*60}")
    print("CREAZIONE FILE EXCEL")
    print(f"{'='*60}")
    
    for name, df in all_data.items():
        output_file = f"risultati_{name}_per_JMP.xlsx"
        create_jmp_excel(df, output_file)
    
    # Crea grafici comparativi
    if len(all_data) > 1:
        create_comparison_plots(all_data, output_dir='grafici_confronto')
    else:
        print("\n(Solo un benchmark caricato, skip grafici comparativi)")
    
    print("\n" + "="*60)
    print("✓ ELABORAZIONE COMPLETATA CON SUCCESSO!")
    print("="*60)

if __name__ == "__main__":
    main()