README – makewordlist.py


1) Descrizione

`makewordlist.py` è uno script Python avanzato per generare **wordlist personalizzate** basate su dati OSINT o su insiemi di parole scelti dall’utente. È pensato per **CTF, laboratori TryHackMe o HackTheBox**, e per usi didattici in ambito di sicurezza informatica.
Lo script consente di creare combinazioni di parole con varianti di maiuscole/minuscole, sostituzioni *leet*, aggiunta di numeri, anni, simboli e concatenazioni tra termini.

>  Usa questo script **solo in contesti autorizzati o formativi**. L’uso su sistemi reali senza consenso è illegale.

--------------------------------------------------------------------------------------------------------------------------------------------


2) Requisiti

* Python 3.8+
* Nessuna libreria esterna richiesta (tutto standard library)

--------------------------------------------------------------------------------------------------------------------------------------------


3) Utilizzo di base

1. Crea un file di input (es. `osint_terms.txt`) con **una parola per riga**, ad esempio:

   
   alex
   bianca
   ciao
   

2. Lancia lo script:

   
   python3 makewordlist.py --in osint_terms.txt --out osint_wordlist.txt
   

Questo genererà una wordlist di base con alcune varianti semplici.

--------------------------------------------------------------------------------------------------------------------------------------------

4) Opzioni principali

| Opzione                       | Descrizione                                                                        

| `--in`                     				    | Percorso del file di input (.txt o .rtf)                                           
| `--out`                  		          | Nome del file di output                                                             
| `--min` / `--max`    					        | Lunghezza minima e massima delle parole generate                                   
| `--toggle-case`  					            | Genera permutazioni di maiuscole/minuscole (es. `aLex`, `AlEx`)                     
| `--case-max`     					            | Numero massimo di caratteri su cui applicare `--toggle-case`                       
| `--leet`               				        | Attiva sostituzioni leet (a→4, e→3, i→1, o→0, s→5, t→7)                            
| `--years`          					          | Specifica intervalli o anni (es. `1990-1995,2001`) per creare suffissi (`alex1991`) 
| `--nums`          					          | Aggiunge numeri comuni separati da virgole (default include `123`, `1990`, ecc.)    
| `--suffix` / `--prefix`  					    | Aggiunge simboli a fine/inizio parola (es. `!`, `@`, `#`)                           
| `--combos-depth`   					          | Livello di concatenazione tra parole (`1`=nessuna, `2`=coppie, `3`=triple)          
| `--max-terms-combo`   				        | Numero massimo di combinazioni da generare (limita esplosione)                      
| `--max-output`        					      | Numero massimo di righe da scrivere nel file di output                              

--------------------------------------------------------------------------------------------------------------------------------------------


5) Esempi pratici

A) Generazione completa con varianti e concatenazioni a coppie


python3 makewordlist.py --in osint_terms.txt --out osint_wordlist.txt \
  --toggle-case --case-max 6 --leet \
  --years 1990-1995,2001,2005 \
  --suffix "!@#" \
  --min 6 --max 20 \
  --combos-depth 2 --max-terms-combo 30000


Genera migliaia di combinazioni come:


alex1990
AlEx1991!
aLex2005
bianca1990
biAnca1995@
biancaalex
ciaobianca90




B) Variante compatta

Solo numeri, anni e coppie, senza permutazioni di case:


python3 makewordlist.py --in osint_terms.txt --out osint_compact.txt \
  --years 1995,2000,2001-2003 --suffix "!" --min 6 --max 20 --combos-depth 2




C) Triple concatenazioni (output molto grande)


python3 makewordlist.py --in osint_terms.txt --out osint_big.txt \
  --toggle-case --case-max 5 --leet \
  --years 1988-1992 \
  --suffix "!@#" --prefix "$" \
  --combos-depth 3 --max-terms-combo 100000 \
  --max-output 1000000


>  Usalo solo con poche parole in input! Le triple generano rapidamente milioni di righe.

--------------------------------------------------------------------------------------------------------------------------------------------


6) Consigli pratici

* Mantieni `--case-max` basso (5–8) per evitare esplosioni.
* Imposta `--max-output` se vuoi solo un campione per test.
* Usa `awk '!seen[$0]++'` per unire più file senza duplicati:

  
  cat osint_wordlist.txt rockyou.txt | awk '!seen[$0]++' > final_prioritized.txt
  


* Se hai file RTF: puoi convertirli in `.txt` con

  
  textutil -convert txt -output osint_terms.txt osint_terms.rtf



## Esempi di combinazioni generate

…
alex1990
Alex1991
ALEX1995
alEx90
biAnca1992!
bianca2001
ciao1990
ciaoalex1995
biancaalex90
…



## Limitazioni e performance

* L’attivazione simultanea di `--toggle-case`, `--leet`, `--years` e `--combos-depth 3` può produrre file da **milioni di righe**. Usa `--max-output` per limitarlo.
* In caso di crash per memoria piena, riduci: `--case-max`, `--combos-depth`, o i range di `--years`.



## Esecuzione rapida (default sicuro)


python3 makewordlist.py --in osint_terms.txt --out osint_wordlist.txt --toggle-case --case-max 6 --min 6 --max 20 --combos-depth 2


--------------------------------------------------------------------------------------------------------------------------------------------


Autore: Enea Bertolini
Scopo: utilizzo etico e formativo in ambienti controllati.
