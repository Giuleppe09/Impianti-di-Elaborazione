import pandas as pd
import re # Importato per l'ordinamento naturale

def analizza_assegnazione_unica(file_csv):
    """
    Analizza il file CSV di contingenza, trova la riga "Conteggio" per ogni cluster,
    e assegna a ogni cluster la richiesta con il conteggio più alto,
    garantendo che ogni richiesta sia assegnata a un solo cluster.
    
    Utilizza un approccio "greedy":
    1. Trova l'accoppiamento (cluster, richiesta) con il valore di conteggio più alto in assoluto.
    2. Assegna quella richiesta a quel cluster.
    3. Rimuove quel cluster e quella richiesta dalla lista delle possibilità.
    4. Ripete fino a quando tutti i cluster hanno un'assegnazione.
    """
    try:
        # Carica il file CSV
        # MODIFICA: La tua versione caricava un .xlsx, mantengo pd.read_excel
        df = pd.read_excel(file_csv)
        print(f"File '{file_csv}' caricato con successo.")
        
        # Definisci le colonne chiave
        colonna_cluster = df.columns[0] # 'Cluster'
        colonna_etichetta = df.columns[1] # 'Cella'
        
        # 1. Filtra per le righe "Conteggio"
        df_conteggi = df[df[colonna_etichetta] == 'Conteggio'].copy()
        
        if df_conteggi.empty:
            print("Errore: Impossibile trovare righe con 'Cella' uguale a 'Conteggio'.")
            return None # Modificato per restituire None in caso di errore

        print(f"\nTrovate {len(df_conteggi)} righe di 'Conteggio'.")

        # 2. Prepara il DataFrame dei conteggi
        df_conteggi = df_conteggi.set_index(colonna_cluster)
        colonne_richieste = [col for col in df_conteggi.columns if col != colonna_etichetta]
        
        # Converti in numerico, gestendo errori
        df_counts_only = df_conteggi[colonne_richieste].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        n_clusters = len(df_counts_only)
        if n_clusters == 0:
            print("Nessun dato di conteggio trovato dopo il filtraggio.")
            return None # Modificato per restituire None
            
        # 3. Trasforma la matrice (Cluster x Richieste) in una lista ordinata
        all_counts_series = df_counts_only.stack()
        all_counts_series = all_counts_series.sort_values(ascending=False)
        
        print("\n--- ANALISI ASSEGNAZIONE UNICA (Approccio Greedy) ---")
        print("Assegnazione prioritaria in base al conteggio più alto disponibile...")

        # 4. Esegui l'assegnazione
        assignments = {}
        used_clusters = set()
        used_requests = set()

        for (cluster, request), value in all_counts_series.items():
            if cluster not in used_clusters and request not in used_requests:
                assignments[cluster] = (request, value)
                used_clusters.add(cluster)
                used_requests.add(request)

            if len(assignments) == n_clusters:
                break
        
        # 5. Stampa i risultati in ordine di cluster per leggibilità
        print("\n--- RISULTATI FINALI ASSEGNAZIONE UNICA ---")
        for cluster_id in sorted(assignments.keys()):
            richiesta, valore = assignments[cluster_id]
            print(f"Cluster {cluster_id}:")
            print(f"  -> Richiesta assegnata: {richiesta}")
            print(f"  -> Conteggio: {valore}")
            
        if len(assignments) < n_clusters:
            unassigned = set(df_counts_only.index) - used_clusters
            print(f"\nATTENZIONE: Non è stato possibile assegnare una richiesta unica ai seguenti cluster: {unassigned}")

        print("\nAnalisi completata.")
        return assignments

    except FileNotFoundError:
        print(f"Errore: File '{file_csv}' non trovato.")
        return None
    except Exception as e:
        print(f"Si è verificato un errore imprevisto: {e}")
        return None

# --- NUOVA SEZIONE PER SCRITTURA FILE TXT ---

def natural_sort_key(s):
    """
    Funzione chiave per l'ordinamento "naturale".
    Permette di ordinare 'Richiesta 2' prima di 'Richiesta 10'.
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]

# Nome del file Excel da analizzare
file_da_analizzare = "Contingenza.xlsx"
nome_file_output = "richieste_ordinate.txt"

# Esegui l'analisi e cattura i risultati
risultati_assegnazione = analizza_assegnazione_unica(file_da_analizzare)

# Verifica se l'analisi ha prodotto risultati prima di scrivere il file
if risultati_assegnazione:
    # 1. Estrai solo i nomi delle richieste
    richieste_assegnate = [valore[0] for valore in risultati_assegnazione.values()]
    
    # 2. Ordina le richieste utilizzando l'ordinamento naturale
    richieste_ordinate = sorted(richieste_assegnate, key=natural_sort_key)
    
    # 3. Scrivi su file .txt
    try:
        with open(nome_file_output, 'w', encoding='utf-8') as f:
            for richiesta in richieste_ordinate:
                f.write(f"{richiesta}\n")
        
        print(f"\n--- Output File ---")
        print(f"File '{nome_file_output}' creato con successo.")
        print(f"Contiene {len(richieste_ordinate)} richieste ordinate.")

    except Exception as e:
        print(f"\nErrore durante la scrittura del file di output: {e}")
else:
    print("\nNessun risultato di assegnazione da scrivere su file.")

# --- FINE SCRIPT ---