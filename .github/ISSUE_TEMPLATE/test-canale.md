---
name: Test Canale
about: Pagina per il test di un canale
title: ''
labels: Test Canale
assignees: ''

---
Documento Template per il Test del canale

Specifica, dove possibile, il tipo di problema che incontri, anche se non è presente alcuna voce per indicarlo.
Se hai **suggerimenti/consigli/dubbi sul test**...Proponili e/o Chiedi! Scrivendo un commento a questo stesso issue, che trovi in fondo, dopo questa pagina.

**Avvertenze:**

Per il test dei canali **DEVI**:
- utilizzare la versione **[BETA](https://kodiondemand.github.io/repo/KoD-installer-BETA.zip)** di KOD!
- **ABILITARE IL DEBUG PER I LOG**

**Per eseguire il test, ricordati di titolarlo con il nome del canale da te scelto, e salvare la pagina cliccando sul bottone verde in basso "SUBMIT NEW ISSUE"**

**Ogni volta che hai un ERRORE con avviso di LOG. Puoi scegliere se:
 ALLEGARE IMMEDIATAMENTE il file kodi.log nel punto, della pagina, in cui sei nel test
 Allegare il file kodi.log a fine pagina.**

**Per poter scrivere o allegare file nella pagina devi:**
    - cliccare sui [ ... ] in alto a destra della scheda 
    - Edit. Da questo momento puoi scrivere e/o inviare file.
Dopodiché clicca sul bottone verde "Update comment" per continuare il test nel modo consueto o per terminarlo!

Se hai problemi non previsti dal test, segnalali aggiungendoli in fondo al test.

**SE VEDI I QUADRATINI MA NON RIESCI A CLICCARLI... DEVI CLICCARE SUL BOTTONE VERDE "SUBMIT NEW ISSUE"**

***
I file relativi al canale li trovi:
- su browser:
[Apre la pagina dei Canali](https://github.com/kodiondemand/addon/tree/master/channels)
- sul device:
[nella specifica cartella](https://github.com/kodiondemand/addon/wiki/Percorsi-sui-diversi-S.O.) , .kodi/addons/channels.
Per aprirli non servono programmi particolari un semplice editor di testo è sufficiente.

**Test N.1**: Controllo del file .json

Occorrente: file .json

**1. Indica la coerenza delle voci presenti in "language" con i contenuti presenti sul sito:**
valori: ita, sub-ita (sub-ita)

- [ ] coerenti
- [ ] non coerenti

Se non sono coerenti il test è FALLITO, continua comunque a revisionare il resto

**2. Icone del canale**
Controlla sia presente qualcosa, tra le " " di thumbnail e banner, e che le immagini appaiano su KoD

**in thumbnail:**
- [ ] Presente 
- [ ] Assente

**in banner:**
- [ ] Presente 
- [ ] Assente

**3. Verifica la coerenza delle voci presenti in "categories" con i contenuti presenti sul sito:**

Riepilogo voci:

	movie, tvshow, anime, documentary, sub, adult

(se il sito contiene film e serie, devono esserci sia movie che tvshow, se contiene solo film, solo movie)

- [ ] Corrette
- [ ] 1 o più Errata/e
- [ ] Assenti - Non sono presenti voci in categories, in questo caso non puoi continuare il test.

Se le voci sono: Assenti, dopo aver compilato la risposta, salva il test e **NON** proseguire.
**TEST FALLITO**

***

**Test su KOD.**

Entra in KOD -> Canali. Nella lista accedi al canale che stai testando.
**N.B.**: Il nome del canale è il campo **name** nel file .json.

**Test N.2: Pagina Canale**

**1. Cerca o Cerca Film...**
Cerca un titolo a caso in KOD e lo stesso titolo sul sito. Confronta i risultati.

- [ ] OK
- indica il tipo di problema

**Sezione FILM (se il sito non ha film elimina questa parte)**

**TestN.3: Pagina dei Titoli**
*Test da effettuare mentre sei dentro un menu del canale (film, serietv, in corso ecc..)*.
Voci nel menu contestuale di KOD. Posizionati su di un titolo e controlla se hai le seguenti voci, nel menu contestuale (tasto c o tenendo enter premuto):

**1. Aggiungi Film in videoteca**

- [ ] Si
- [ ] No

**2. Scarica Film (devi avere il download abilitato)**

- [ ] Si
- [ ] No

**Fine test menu contestuale**

**Fondo pagina dei titoli**

**3. Paginazione, controlla ci sia la voce "Successivo" (se non c'è controlla sul sito se è presente)**

- [ ] Sì
- [ ] NO

**Dentro un titolo

**4. Entra nella pagina del titolo e verifica ci sia almeno 1 server:**

- [ ] Si
- [ ] No

**5. Eventuali problemi riscontrati**
- scrivi qui il problema/i 

**Sezione Serie TV (se il sito non ha serietv elimina questa parte)**

Test da effettuare mentre sei nella pagina dei titoli.
Per ogni titolo verifica ci siano le voci nel menu contestuale.

**1. Aggiungi Serie in videoteca**

- [ ] Si
- [ ] No

**2. Scarica Stagione (devi avere il download abilitato)**

- [ ] Si
- [ ] No

**3. Scarica Serie (devi avere il download abilitato)**

- [ ] Si
- [ ] No

**4. Cerca o Cerca Serie...**
Cerca un titolo a caso in KOD e lo stesso titolo sul sito. Confronta i risultati.

- [ ] Ok
- indica il tipo di problema

**5. Entra nella pagina della serie,  verifica che come ultima voce ci sia "Aggiungi in videoteca":**

- [ ] Si, appare
- [ ] Non appare

**6. Entra nella pagina dell'episodio, **NON** deve apparire la voce "Aggiungi in videoteca":**

- [ ] Si, appare
- [ ] Non appare

**7. Eventuali problemi riscontrati**
- scrivi qui il problema/i 

**Sezione Anime (se il sito non ha anime elimina questa parte)**

Test da effettuare mentre sei nella pagina dei titoli. Per ogni titolo verifica ci siano le voci nel menu contestuale.

**1. Rinumerazione (se gli episodi non appaiono nella forma 1x01)**

- [ ] Si
- [ ] No

**2. Aggiungi Serie in videoteca**

- [ ] Si
- [ ] No

**3. Aggiungi 2-3 titoli in videoteca.**
- [ ] Aggiunti correttamente
- [Indica eventuali problemi] (copia-incolla per tutti i titoli con cui hai avuto il problema)

- COPIA qui l'ERRORE dal LOG

**4. Scarica Serie**

- [ ] Si
- [ ] No

**5. Cerca o Cerca Serie...**
Cerca un titolo a caso in KOD e lo stesso titolo sul sito. Confronta i risultati.

- [ ] Ok
- indica il tipo di problema

**6. Entra nella pagina della serie, verifica che come ultima voce ci sia "Aggiungi in videoteca":**

- [ ] Appare
- [ ] Non appare

**7. Entra nella pagina dell'episodio, NON ci deve essere la voce "Aggiungi in videoteca":**

- [ ] Non appare
- [ ] Appare

**8. Eventuali problemi riscontrati**
- scrivi qui il problema/i

** TEST PER IL CONFRONTO TRA SITO E CANALE **

**TestN.4: Pagina Sito - Menu Canale**

Occorrente: Browser, KOD! e il file canale.py ( da browser o da file )
Avviso:
- Sul Browser disattiva eventuali componenti aggiuntivi che bloccano i JS (javascript), li riattivi alla fine del test.

Entra in ogni menu e controlla che i risultati, delle prime 5-6 pagine, siano gli stessi che trovi sul sito, comprese le varie info (ita/sub-ita, qualità ecc..), inoltre entra, se ci sono, nei menu dei generi - anni - lettera, verifica che cliccando su una voce si visualizzino i titoli.

  *Copia questa sezione per ogni voce che presenta problemi:*

- [ ] Voce menu ( del canale dove riscontri errori)

Titoli non corrispondenti:

- [ ] Il totale dei Titoli è diverso da quello del sito. Alcuni Titoli non compaiono.
- [ ] Appaiono titoli per pagine informative o link a siti esterni. Es: Avviso agli utenti.
- [ ] La lingua, del titolo, è diversa da quella riportata dal sito
- [ ] Non è indicato in 1 o più titoli che sono SUB-ITA
- [ ] Cliccando su "Successivo" non si visualizzano titoli
- [ ] Non è indicata la qualità: Hd-DVD/rip e altri, nonostante sul sito siano presenti

- [ ] NO


  *Fine Copia*

  
**Test.N5: Ricerca Globale**

Per questo test ti consiglio di inserire come UNICO sito quello che stai testando, come canale incluso in: Ricerca Globale -> scegli i canali da includere
Il test è già compilato con le spunte, dato che devi copiarlo solo in caso di errori. Togli la spunta dove funziona.
Si consiglia di cercare almeno a fino 5 titoli. O perlomeno non fermarti al 1°.

Cerca 5 FILM a tuo piacimento, se il titolo non esce controlla confrontando i risultati sul sito...:

 *Copia questa sezione per ogni voce che presenta problemi*

controlla ci siano queste voci se titolo è un FILM:

- [ ] inserisci il titolo cercato che da problemi
- [x] Aggiungi in videoteca
- [x] Scarica Film

  *Fine Copia*

controlla ci siano queste voci se titolo è una SERIE/ANIME:  
  
  *Copia questa sezione per ogni voce che presenta problemi*

controlla ci siano queste voci se titolo è un FILM:

- [ ] inserisci il titolo cercato che da problemi
- [x] Aggiungi in videoteca
- [x] Scarica Serie
- [x] Scarica Stagione

- [ ] inserisci il titolo cercato che da problemi

  *Fine Copia*
  
  
Se il canale ha la parte Novità (questa stringa avvisa che NON è presente: "not_active": ["include_in_newest"]).

**Test.N6: Novità.**
Per questo test ti consiglio di inserire come UNICO sito quello che stai testando, come canale incluso in: Novità -> categoria (film, serie o altro )

- [ ] Descrivere il problema

Fine TEST!

Grazie mille da parte di tutto il team KoD!
