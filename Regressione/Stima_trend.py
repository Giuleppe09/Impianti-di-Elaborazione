import numpy as np
import pandas as pd
from scipy import stats

# Nome del file CSV caricato
file_name = "HomeWork_Regression_VMres3.xlsx"

# Carica il DataFrame dal CSV
try:
    df = pd.read_excel(file_name)
except FileNotFoundError:
    print(f"ERRORE: File non trovato: {file_name}")
    exit()
except Exception as e:
    print(f"ERRORE durante la lettura del file: {e}")
    exit()

# --- DEBUG: Decommenta la linea seguente per vedere i nomi esatti delle colonne ---
# print("Nomi colonne disponibili:", df.columns.to_list())
# print("="*60) 

# --- CONFIGURAZIONE: Aggiorna questi nomi di colonna con quelli corretti dal tuo file ---
colonna_x = 'T(s)'  # Sostituisci con il nome corretto (es. 'Observation')
colonna_y = 'allocated heap'    # Sostituisci con il nome corretto (es. 'Byte Sent' o 'Byte_Sent')
# -----------------------------------------------------------------------------------

try:
    # Estraiamo i dati, gestendo eventuali NaN
    data_completi = df[[colonna_x, colonna_y]].dropna()
    y = data_completi[colonna_y].values
    x = data_completi[colonna_x].values
    
    # Calcolo della Pendenza di Theil-Sen (alpha=0.95 per CI 95%)
    res = stats.theilslopes(y, x, alpha=0.95)

    # --- Stampa dei risultati richiesti ---
    print(f"Stima Trend (Theil-Sen) - {colonna_y} vs {colonna_x}")
    print("-" * 40)
    print(f"Pendenza (slope): {res.slope}")
    print(f"Intercetta (intercept): {res.intercept}")
    print(f"Intervallo conf. inferiore pendenza (low_slope): {res.low_slope}")
    print(f"Intervallo conf. superiore pendenza (high_slope): {res.high_slope}")

    # --- PREDITTIVA (Opzionale) ---
    # Se la predizione di fallimento non è necessaria, commentare il blocco seguente (da qui fino a 'Fine Blocco Predittiva')

    # Impostare la soglia di fallimento (es. 1 GByte = 1 * 1024^3 bytes)
    FAILURE_THRESHOLD = 1073741824  
    secondi_in_anno = 60 * 60 * 24 * 365.25

    print("\n" + "-" * 40)
    print(f"Predizione di Fallimento (Soglia: {FAILURE_THRESHOLD})")

    # Verifica che la pendenza sia significativamente positiva
    if res.slope <= 0:
        print("Predizione non applicabile: la pendenza stimata è negativa o nulla.")
    elif res.low_slope <= 0:
        print(f"Predizione non affidabile: l'intervallo di confidenza della pendenza [{res.low_slope:.3f}, {res.high_slope:.3f}] include lo zero.")
        print("Non è possibile escludere che il tempo di fallimento sia infinito.")
    else:
        # Calcoli per il formato (Centro ± Margine)
        # Dati di input
        b = res.intercept
        T_num = FAILURE_THRESHOLD - b
        
        # Pendenza (Centro del CI e Margine)
        m_center = (res.high_slope + res.low_slope) / 2
        m_margin = (res.high_slope - res.low_slope) / 2
        
        # Tempo in secondi (Centro del CI e Margine)
        # Nota: T_fast e T_slow sono invertiti perché la pendenza è al denominatore
        T_fast = T_num / res.high_slope
        T_slow = T_num / res.low_slope
        T_center_sec = (T_slow + T_fast) / 2
        T_margin_sec = (T_slow - T_fast) / 2
        
        # Tempo in anni (Centro del CI e Margine)
        T_center_anni = T_center_sec / secondi_in_anno
        T_margin_anni = T_margin_sec / secondi_in_anno
        
        # Stampa formattata
        print(f"T_failure(s) = {FAILURE_THRESHOLD} - {b:.2f} / ({m_center:.2f} \u00B1 {m_margin:.2f}) == ({T_center_sec:.0f} \u00B1 {T_margin_sec:.0f})s = ({T_center_anni:.1f} \u00B1 {T_margin_anni:.1f}) anni")

    print("-" * 40)
    # --- Fine Blocco Predittiva ---


except KeyError as e:
    print(f"ERRORE (KeyError): Impossibile trovare la colonna specificata.")
    print(f"Dettaglio: {e}")
    print("Verifica che i nomi nelle variabili 'colonna_x' e 'colonna_y' corrispondano ESATTAMENTE")
    print("a quelli stampati da 'Nomi colonne disponibili' (controlla maiuscole e spazi).")
except Exception as e:
    print(f"Si è verificato un errore imprevisto: {e}")