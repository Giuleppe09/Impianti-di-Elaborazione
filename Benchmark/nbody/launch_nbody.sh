#!/bin/bash
#--Valori Fissi
TOTAL_RUNS=37	#File da creare, runs consecutive.
RIPETIZIONI=5	#5 ripetizioni per ogni file.
ARRAY_BODIES=(500000 1000000 2000000 10000000)
TIMEOUT_SECONDI=3
BASE_RESULT_DIR="Suso_Results"
mkdir -p "$BASE_RESULT_DIR"

echo "Avvio di $TOTAL_RUNS esecuzioni totali.."


#Ciclo esterno
for n_corpi in ${ARRAY_BODIES[@]} 
do
	#Sottocartelle
	CURRENT_DIR="$BASE_RESULT_DIR/${n_corpi}_corpi"
	mkdir -p "$CURRENT_DIR"
	echo "Test per $n_corpi.."
	for((i=1;i<=$TOTAL_RUNS;i++))
	do
		OUTPUT_FILE="$CURRENT_DIR/${i}_run.txt"
		echo "Esecuzione $i di $TOTAL_RUNS.."
	
		#Redirezione dell'output.
		{
			for((counter=$RIPETIZIONI; counter >0; counter--))
			do
				./nbodySim "$n_corpi"
				sleep $TIMEOUT_SECONDI #facciamo riprendere un pò..
			done
			printf "\n"
		} > $OUTPUT_FILE
	done

	echo "Fine_Esecuzione ${n_corpi}"
done

echo "Tutti i benchmark sono stati completati"
