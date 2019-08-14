---
name: Test Canale
about: Documento per il test del canale
title: ''
labels: 'Test Canale'
assignees: ''
projects: https://github.com/greko17/addon/issues/new?title=Test+Canale&projects=greko17/1
---


Di ogni test mantieni la voce dell'esito e cancella le altre, dove occorre aggiungi informazioni. Specifica, dove possibile, il tipo di problema che incontri in quel test.
Se hai suggerimenti/consigli/dubbi sui test...Proponili e/o chiedi!
 
***

Test N°.1: Lista Canali

Cosa serve: il file .json

1. Verifica del canale nelle sezioni indicate nel file .json, voce "categories".

- [ ] Tutte
- [ ] Alcune - Indicare le sezioni dove manca il canale
- [ ] Nessuna - Voce Canale mancante nella lista. In questo caso non puoi continuare il test.

2. Icone del canale [ ]

- [ ] Presenti
- [ ] Non Presenti

***

Test N°.2: Configura Canale 

1. Presenza della voce "Configura Canale"

- [ ] Si
- [ ] No

2. Voci presenti in Configura Canale

a. Cerca Informazioni extra (Default: Attivo)

- [ ] Si
- [ ] No

b. Includi in Novità (Default: Attivo)

- [ ] Si
- [ ] No

c. Includi in Novità - Italiano (Default: Attivo)

- [ ] Si
- [ ] No

d. Includi in ricerca globale (Default: Attivo)

- [ ] Si
- [ ] No

e. Verifica se i link esistono (Default: Attivo)

- [ ] Si
- [ ] No

f. Numero de link da verificare (Default: 10)

- [ ] Si
- [ ] No

g. Mostra link in lingua (Default: Non filtrare)

- [ ] Si
- [ ] No

***

Test N°.3: Voci menu nella pagina del Canale

1. Configurazione Autoplay

- [ ] Si
- [ ] No

2. Configurazione Canale

- [ ] Si
- [ ] No

***

Test N°.4: Confronto Sito - Pagina Canale

Cosa serve: il file .py, consultare la def mainlist()

Promemoria: 
della mainlist la struttura è:

( 'Voce menu1', ['/url/', etc, etc])
( 'Voce menu2', ['', etc, etc])
Dove url è una stringa aggiuntiva da aggiungere all'url principale, se in url appare '' allora corrisponde all'indirizzo principale del sito.

Questo Test confronta i titoli che trovi accedendo alle voci di menu del canale con quello che vedi nella corrispettiva pagina del sito.

- [Voce menu con problemi - Tipo di problema] ( copiare per tutte le voci che non hanno corrispondenza )
Tipo di problema = mancano dei titoli, i titoli sono errati, ai titoli corrispondono locandine errate o altro


I test successivi sono divisi a seconda si tratta di film, serie tv o anime.
Cancella le sezioni non interessate dal canale. Verificale dalla voce "categories" del file .json.

**Sezione FILM

Test da effettuare mentre sei nella pagina dei titoli. Per ogni titolo verfica ci siano le voci nel menu contestuale.

1. Aggiungi Film in videoteca

- [ ] Si
- [ ] No

Aggiungi 2-3 titoli in videoteca. Verificheremo successivamente la videoteca.
- [ ] Aggiunti correttamente
- [Indica eventuali problemi] (copia-incolla per tutti i titoli con cui hai avuto il problema)

2. Scarica Film

- [Si] 
- [No]

3. Paginazione ( cliccare sulla voce "Successivo" e verifica la 2° pagina nello stesso modo in cui lo hai fatto per la 1°)

- [Ok] 
- [X - indica il tipo di problema]

4. Cerca o Cerca Film...
Cerca un titolo a caso in KOD e lo stesso titolo sul sito. Confronta i risultati.

- [Ok]
- [X - indica il tipo di problema]

5. Entra nella pagina del titolo, verifica che come ultima voce ci sia "Aggiungi in videoteca":

- [Si, appare]
- [Non appare]

6. Eventuali problemi riscontrati
- [ scrivi qui il problema/i ]

**Sezione Serie TV

Test da effettuare mentre sei nella pagina dei titoli. Per ogni titolo verfica ci siano le voci nel menu contestuale.

1. Aggiungi Serie in videoteca

- [Si] 
- [No]

2. Aggiungi 2-3 titoli in videoteca. Verificheremo successivamente la videoteca.
- [Aggiunti correttamente]
- [Indica eventuali problemi] (copia-incolla per tutti i titoli con cui hai avuto il problema)

3. Scarica Serie

- [Si] 
- [No]

4. Cerca o Cerca Serie...
Cerca un titolo a caso in KOD e lo stesso titolo sul sito. Confronta i risultati.

- [Ok]
- [X - indica il tipo di problema]

5. Entra nella pagina della serie,  verifica che come ultima voce ci sia "Aggiungi in videoteca":

- [Non appare]
- [Si, appare]

6. Entra nella pagina dell'episodio, NON deve apparire la voce "Aggiungi in videoteca":

- [Non appare]
- [Si, appare]

7. Eventuali problemi riscontrati
- [ scrivi qui il problema/i ]

**Sezione Anime

Test da effettuare mentre sei nella pagina dei titoli. Per ogni titolo verfica ci siano le voci nel menu contestuale.

1. Aggiungi Serie in videoteca

- [Si] 
- [No]

2. Aggiungi 2-3 titoli in videoteca. Verificheremo successivamente la videoteca.
- [Aggiunti correttamente]
- [Indica eventuali problemi] (copia-incolla per tutti i titoli con cui hai avuto il problema)

3. Scarica Serie

- [Si] 
- [No]

4. Rinumerazione

- [Si] 
- [No]

5. Cerca o Cerca Serie...
Cerca un titolo a caso in KOD e lo stesso titolo sul sito. Confronta i risultati.

- [Ok]
- [X - indica il tipo di problema]

6. Entra nella pagina della serie,  verifica che come ultima voce ci sia "Aggiungi in videoteca":

- [Si, appare]
- [Non appare]

7. Entra nella pagina dell'episodio, NON deve apparire la voce "Aggiungi in videoteca":

- [Non appare]
- [Si, appare]

8. Eventuali problemi riscontrati
- [ scrivi qui il problema/i ]

**Fine test del canale preso singolarmente!!!
