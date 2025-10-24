import xml.etree.ElementTree as ET
import os

def modifica_jmx_throughput(file_input, nuovo_throughput, file_output):
    """
    Carica un file JMX, modifica tutti i timer CTT e salva un nuovo file.

    :param file_input: Percorso del file JMX originale.
    :param nuovo_throughput: Il nuovo valore di throughput (es. 1000.0).
    :param file_output: Percorso del file JMX da salvare.
    """
    try:
        # Registra il namespace per evitare problemi con alcuni JMX, anche se qui non sembra esserci
        # ET.register_namespace("", "http://jmeter.apache.org/JMeter/jmx")
        
        # Analizza il file XML
        tree = ET.parse(file_input)
        root = tree.getroot()

        # Formatta il nuovo valore come stringa con un decimale (es. "1000.0")
        valore_stringa = f"{float(nuovo_throughput):.1f}"
        
        contatore_modifiche = 0

        # Trova tutti gli elementi 'ConstantThroughputTimer' nel file
        # usiamo .// per cercare in tutto l'albero
        for timer in root.findall('.//ConstantThroughputTimer'):
            
            # Per ogni timer, trova l'elemento 'doubleProp' che contiene il nome 'throughput'
            # Usiamo find con un predicato XPath: cerca un doubleProp che ha un figlio 'name'
            # con il testo 'throughput'
            prop_throughput = timer.find("./doubleProp[name='throughput']")
            
            if prop_throughput is not None:
                # Se l'abbiamo trovato, cerca l'elemento 'value' al suo interno
                value_element = prop_throughput.find('value')
                if value_element is not None:
                    # Modifica il testo dell'elemento 'value'
                    value_element.text = valore_stringa
                    contatore_modifiche += 1
                else:
                    print(f"ATTENZIONE: Trovato timer ma non l'elemento 'value' in {file_input}")
            else:
                print(f"ATTENZIONE: Trovato ConstantThroughputTimer ma non 'doubleProp' con nome 'throughput' in {file_input}")

        if contatore_modifiche > 0:
            # Salva il file XML modificato
            # encoding='UTF-8' e xml_declaration=True sono importanti per mantenere il formato JMX
            tree.write(file_output, encoding='UTF-8', xml_declaration=True)
            print(f"Creato file: '{file_output}' (modificati {contatore_modifiche} timer a {valore_stringa} req/min)")
        else:
            print(f"ERRORE: Nessun timer CTT trovato o modificato in '{file_input}'. Nessun file creato.")

    except ET.ParseError as e:
        print(f"Errore durante l'analisi XML del file {file_input}: {e}")
    except FileNotFoundError:
        print(f"ERRORE: File di input non trovato: {file_input}")
    except Exception as e:
        print(f"Si è verificato un errore imprevisto: {e}")


# --- ESECUZIONE DELLO SCRIPT ---
if __name__ == "__main__":
    
    # 1. Salva il tuo file JMX originale nella stessa cartella di questo script
    #    con il nome 'test_plan_originale.jmx'
    #    (Puoi cambiare questo nome se preferisci)
    file_originale = 'test_plan_originale.jmx'

    # 2. Definisci qui tutti i valori di CTT per cui vuoi generare un file
    #    (Valori in richieste al minuto, 500.0 = 500/60 = 8.33 req/sec)
    valori_throughput = [
	1800,
	2400,
	1000,
	500,
	800,
	3500,
	4200,
	6000,
	7000,
	8000,
	9000
    ]

    # 3. Prefisso per i file di output
    nome_base_output = 'Test_Plan_CTT'

    # Controlla se il file originale esiste prima di iniziare
    if not os.path.exists(file_originale):
        print(f"ERRORE: Il file di input '{file_originale}' non è stato trovato.")
        print("Per favore, salva il tuo file .jmx in questa cartella con quel nome e riprova.")
    else:
        print(f"Trovato file originale: '{file_originale}'. Inizio la generazione dei file...")
        # Ciclo per generare tutti i file
        for valore in valori_throughput:
            # Crea un nome di file pulito, es: "Test_Plan_CTT_1000.jmx"
            nome_file_output = f"{nome_base_output}_{int(valore)}.jmx"
            
            # Chiama la funzione per creare il file
            modifica_jmx_throughput(file_originale, valore, nome_file_output)

        print("\nGenerazione completata.")
