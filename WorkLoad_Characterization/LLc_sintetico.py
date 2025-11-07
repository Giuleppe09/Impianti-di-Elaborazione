import pandas as pd

# --- Configurazione ---

# Questo è il file che hai caricato e che contiene i dati
file_input = "vmStatTestSintetico_PCA_Clustering.xlsx" 

# Nome del nuovo file che verrà creato
file_output = "LLc1.csv"

# Colonne che vuoi conservare per il test d'ipotesi
# (Basate sullo snippet del tuo file: 5 componenti + 1 colonna cluster)
colonne_da_tenere = [
    'Principale1', 
    'Principale2', 
    'Principale3', 
    'Principale4', 
    'Principale5',
    'PCA5_Cluster20' # La colonna con i cluster
]

# --- Esecuzione ---

print(f"Tentativo di leggere il file: '{file_input}'")

try:
    # Leggo il file CSV (che è il formato del file che hai caricato)
    data = pd.read_excel(file_input)
    print("File letto con successo.")
    
    # Verifico se tutte le colonne richieste esistono
    colonne_esistenti = data.columns.tolist()
    colonne_mancanti = [col for col in colonne_da_tenere if col not in colonne_esistenti]
    
    if colonne_mancanti:
        print("ERRORE: Impossibile procedere.")
        print(f"Le seguenti colonne richieste non sono state trovate nel file: {colonne_mancanti}")
        print(f"Le colonne disponibili sono: {colonne_esistenti}")
    else:
        # Seleziono solo le colonne desiderate
        output_data = data[colonne_da_tenere]
        
        # Salvo il nuovo file CSV
        output_data.to_csv(file_output, index=False)
        
        print("-" * 30)
        print(f"File '{file_output}' creato con successo.")
        print("Contiene SOLO le componenti principali e la colonna cluster.")
        print("Puoi usare questo file per il tuo test d'ipotesi.")
        print("\nEcco un'anteprima del file creato:")
        print(output_data.head())

except FileNotFoundError:
    print(f"ERRORE: File non trovato: '{file_input}'. Assicurati che sia stato caricato.")
except Exception as e:
    print(f"Si è verificato un errore inaspettato: {e}")