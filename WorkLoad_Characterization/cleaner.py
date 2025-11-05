import csv
import re

def process_vmstat_output(input_file_path, output_file_path):
    """
    Legge l'output grezzo del comando vmstat, elimina tutte le righe di intestazione 
    e i separatori ripetuti, e scrive i dati con una singola intestazione CSV.
    """
    
    # 1. Definisci l'UNICA riga di intestazione che apparirà nel file CSV
    column_headers = [
        'r', 'b', 'swpd', 'free', 'buff', 'cache', 
        'si', 'so', 'bi', 'bo', 'in', 'cs', 
        'us', 'sy', 'id', 'wa', 'st','gu'
    ]
    
    valid_data = []

    try:
        # Uso 'latin-1' come suggerito per la compatibilità con l'encoding del file
        with open(input_file_path, 'r', encoding='latin-1') as infile:
            for line in infile:
                line = line.strip()

                # Condizioni per SCARTARE le righe che non sono dati:
                
                # a) Scarta righe vuote o righe di separazione ('----------')
                if not line or '---' in line:
                    continue
                
                # b) Scarta TUTTE le righe che contengono lettere (ovvero le intestazioni principali e secondarie)
                # Questo filtro è cruciale per eliminare le intestazioni ripetute di vmstat.
                if re.search(r'[a-zA-Z]', line):
                    continue
                
                # 2. Processa le righe di dati (solo numeri)
                
                # Split basato su uno o più spazi bianchi (per allineamento vmstat)
                fields = re.split(r'\s+', line)

                # Verifica che la riga abbia il numero corretto di campi (standard vmstat = 17)
                # Se i tuoi dati hanno un numero diverso, modifica il 17
                if len(fields) == 18:
                    valid_data.append(fields)
                

    except FileNotFoundError:
        print(f"Errore: File '{input_file_path}' non trovato.")
        return
    except UnicodeDecodeError:
        print(f"Errore: Problema di codifica. Prova a cambiare 'latin-1' con 'utf-8' o 'cp1252'.")
        return
    
    # 3. Scrivi i dati puliti nel file CSV
    try:
        # Scrive i dati con la singola riga di intestazione
        with open(output_file_path, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            
            # Scrivi SOLO UNA VOLTA le intestazioni definite all'inizio (Punto 1)
            writer.writerow(column_headers)
            
            # Scrivi tutti i dati numerici raccolti
            writer.writerows(valid_data)

        print(f"\n✅ Conversione completata con successo.")
        print(f"Dati scritti in '{output_file_path}' con {len(valid_data)} righe.")
        
    except IOError:
        print(f"Errore: Impossibile scrivere nel file di output '{output_file_path}'.")

# --- ISTRUZIONI PER L'USO ---
INPUT_FILENAME = 'vmstatWC.txt' 
OUTPUT_FILENAME = 'vmstat_cleaned.csv'

process_vmstat_output(INPUT_FILENAME, OUTPUT_FILENAME)