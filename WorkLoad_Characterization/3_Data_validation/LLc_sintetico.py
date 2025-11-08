import pandas as pd
import os

# --- Configurazione Automatica ---

# 1. Rileva automaticamente il file caricato
# (Aggiornato al nome del file che hai effettivamente caricato)
file_input = "LLSint.xlsx" 

# 2. Crea un nome di output dinamico
try:
    file_base_name = os.path.splitext(file_input)[0].split(" ")[0] # Prende 'LLc'
except:
    file_base_name = "output"

# === MODIFICA QUI ===
# Cambiato il nome del file di output in .xlsx
file_output = f"{file_base_name}_PCA_Cluster_Subset.xlsx"

# --- Esecuzione ---

print(f"Tentativo di leggere il file: '{file_input}'")

try:
    # Logica di caricamento flessibile (prima Excel, poi CSV)
    try:
        data = pd.read_excel(file_input)
        print("File letto con successo come Excel.")
    except Exception as e_excel:
        # Se fallisce (es. perché è un CSV), prova a leggerlo come CSV
        print(f"Lettura Excel fallita (Errore: {e_excel}), tentativo come CSV...")
        data = pd.read_csv(file_input)
        print("File letto con successo come CSV.")
    
    colonne_esistenti = data.columns.tolist()
    
    # 3. Rilevamento automatico delle colonne
    print("\n--- Rilevamento Colonne Automatico ---")
    
    # Colonna Cluster (Sempre l'ultima colonna, come richiesto)
    cluster_col_name = colonne_esistenti[-1]
    print(f"Colonna Cluster rilevata: '{cluster_col_name}' (L'ultima colonna)")
    
    # Colonne PCA (Tutte quelle che iniziano con 'Principale')
    pca_columns = [col for col in colonne_esistenti if col.startswith('Principale')]
    
    if not pca_columns:
        print("ERRORE: Impossibile procedere.")
        print("Nessuna colonna che inizia con 'Principale' è stata trovata.")
        print(f"Le colonne disponibili sono: {colonne_esistenti}")
        exit()
        
    print(f"Colonne PCA rilevate ({len(pca_columns)}): {', '.join(pca_columns)}")

    # Definisci l'elenco finale delle colonne da tenere
    colonne_da_tenere = pca_columns + [cluster_col_name]
    
    # 4. Selezione e Salvataggio
    
    # Seleziono solo le colonne desiderate
    output_data = data[colonne_da_tenere]
    
    # === MODIFICA QUI ===
    # Salvo il nuovo file in formato Excel
    # Assicurati di avere 'openpyxl' installato (pip install openpyxl)
    output_data.to_excel(file_output, index=False)
    
    print("-" * 30)
    print(f"File '{file_output}' (Excel) creato con successo.")
    print("Contiene SOLO le componenti principali e la colonna cluster rilevate.")
    print("\nEcco un'anteprima dei dati salvati (prime 5 righe):")
    # uso .to_string() per garantire una formattazione corretta
    print(output_data.head().to_string()) 

except FileNotFoundError:
    print(f"ERRORE: File non trovato: '{file_input}'. Assicurati che sia stato caricato.")
except ImportError:
    print("ERRORE: Manca la libreria 'openpyxl'.")
    print("Per salvare in Excel, esegui: pip install openpyxl")
except Exception as e:
    print(f"Si è verificato un errore inaspettato: {e}")