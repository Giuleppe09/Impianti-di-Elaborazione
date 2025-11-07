import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def load_requests_to_keep(txt_file):
    """
    Carica le richieste da mantenere dal file txt.
    Ritorna un set con i nomi completi delle richieste (es: "Request 2 Low 3")
    """
    requests = set()
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Normalizza gli spazi multipli in uno solo
                    normalized = ' '.join(line.split())
                    requests.add(normalized)
        print(f"[OK] Caricate {len(requests)} richieste da mantenere")
        for req in sorted(requests):
            print(f"      - {req}")
        return requests
    except Exception as e:
        print(f"[ERRORE] Errore nella lettura del file {txt_file}: {e}")
        sys.exit(1)

def filter_jmx_file(input_jmx, output_jmx, requests_to_keep):
    """
    Filtra il file JMX mantenendo solo le richieste specificate.
    Esegue due passaggi per assicurarsi di trovare tutte le richieste.
    """
    try:
        # Parse del file XML
        tree = ET.parse(input_jmx)
        root = tree.getroot()
        
        removed_count = 0
        kept_count = 0
        
        # PRIMO GIRO: Raccoglie tutte le richieste presenti
        print("\n[INFO] Primo giro - Scansione richieste...")
        all_requests_in_jmx = {}
        for elem in root.iter('HTTPSamplerProxy'):
            testname = elem.get('testname', '')
            testname_normalized = ' '.join(testname.split())
            all_requests_in_jmx[testname_normalized] = elem
            
        print(f"[INFO] Trovate {len(all_requests_in_jmx)} richieste totali nel JMX\n")
        
        # SECONDO GIRO: Rimuove quelle non richieste
        print("[INFO] Secondo giro - Filtro richieste...")
        for testname_normalized, elem in all_requests_in_jmx.items():
            # Controlla se questa richiesta deve essere mantenuta
            if testname_normalized in requests_to_keep:
                kept_count += 1
                print(f"  [+] Mantenuta: {testname_normalized}")
            else:
                # Rimuovi l'elemento e il suo hashTree associato
                parent = find_parent(root, elem)
                if parent is not None:
                    # Trova l'indice dell'elemento
                    idx = list(parent).index(elem)
                    # Rimuovi l'HTTPSamplerProxy
                    parent.remove(elem)
                    # Rimuovi il hashTree successivo se esiste
                    if idx < len(parent) and parent[idx].tag == 'hashTree':
                        parent.remove(parent[idx])
                    removed_count += 1
                    print(f"  [-] Rimossa: {testname_normalized}")
        
        # Salva il nuovo file JMX
        tree.write(output_jmx, encoding='UTF-8', xml_declaration=True)
        
        print(f"\n{'='*60}")
        print(f"Richieste mantenute: {kept_count}")
        print(f"Richieste rimosse: {removed_count}")
        
        # Verifica se ci sono richieste non trovate
        missing = requests_to_keep - set(all_requests_in_jmx.keys())
        if missing:
            print(f"\n[ATTENZIONE] Richieste non trovate nel JMX ({len(missing)}):")
            for req in sorted(missing):
                print(f"  [!] {req}")
        
        print(f"\nFile salvato: {output_jmx}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"[ERRORE] Errore nell'elaborazione del file JMX: {e}")
        sys.exit(1)

def find_parent(root, target):
    """
    Trova il parent di un elemento nell'albero XML.
    """
    for parent in root.iter():
        for child in parent:
            if child == target:
                return parent
    return None

def main():
    # File di default (hardcoded)
    input_jmx = "3_TestPlan_WC1.jmx"
    txt_file = "richieste_ordinate.txt"
    output_jmx = "TestPlan_Filtered.jmx"
    
    print(f"\n{'='*60}")
    print(f"JMETER TEST PLAN FILTER")
    print(f"{'='*60}")
    print(f"Input JMX: {input_jmx}")
    print(f"File richieste: {txt_file}")
    print(f"Output JMX: {output_jmx}")
    print(f"{'='*60}\n")
    
    # Verifica esistenza file
    if not Path(input_jmx).exists():
        print(f"[ERRORE] File non trovato: {input_jmx}")
        sys.exit(1)
    
    if not Path(txt_file).exists():
        print(f"[ERRORE] File non trovato: {txt_file}")
        sys.exit(1)
    
    # Carica le richieste da mantenere
    requests_to_keep = load_requests_to_keep(txt_file)
    
    # Filtra il file JMX
    print(f"\nElaborazione in corso...\n")
    filter_jmx_file(input_jmx, output_jmx, requests_to_keep)

if __name__ == "__main__":
    # Esegui semplicemente: python script.py
    main()