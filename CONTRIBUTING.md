Ciao, grazie per aver preso in considerazione di contribuire a questo progetto!<br>
Ci sono molti modi per farlo, e per alcuni di essi non è necessario essere uno sviluppatore.

Puoi ad esempio [segnalare i cambiamenti di struttura](#segnalare-i-cambiamenti-di-struttura) dei canali/server, [scrivere guide o registrare video-esempi](#scrivere-guide-o-registrare-video-esempi) su alcune funzionalità "avanzate", dare consigli su funzionalità nuove o per migliorare quelle già presenti. 

# Segnalare i cambiamenti di struttura
KoD, alla fine, non è altro che un browser che estrapola dai siti le info richieste secondo regole ben precise, basate sulla struttura dei siti.<br>
I siti web cambiano, spesso, ciò che oggi funziona domani potrebbe non più funzionare, pertanto sono fondamentali le segnalazioni, ma esse per essere realmente utili devono:
- contenere il file di log (lo potete generare andando in Aiuto - Segnala un problema e seguendo le istruzioni)
- spiegare brevemente qual'è il problema e dove, ad esempio "cineblog da errore quando entro nella sezione Film", oppure "wstream non da nessun errore ma il video di fatto non parte"
- essere replicabili, se si tratta di cose che accadono una volta ogni tanto puoi provare a segnalare lo stesso, sperando che nel log ci sia qualche indizio. Se non c'è, nada

Prima di segnalare un problema assicurati che sia realmemte legato a KoD, sotto alcuni requisiti necessari:
- avere l'ultima versione di KoD, per controllare vai qui e confronta il numero con quello presente nella sezione aiuto: https://github.com/kodiondemand/addon/commits/stable
- avere una versione di kodi supportata, attualmente si tratta di 17.x e 18.x
- verificare che il problema non dipenda dal sito stesso: se esce il messaggio 'Apri nel Browser': apri il tuo Browser e prova se li il film o serie tv funziona, senno apri il menù contestuale (tasto c) e clicca su "apri nel browser"

Sei pregato di attenerti il più possibile a quanto descritto qua perchè un semplice "non funziona" fa solo perdere tempo.
Puoi fare tutte le segnalazioni nella sezione [issues](https://github.com/kodiondemand/addon/issues), cliccando su "new issue" appariranno dei template che ti guideranno nel processo.
Assicurati che qualcun'altro non abbia già effettuato la stessa segnalazione, nel caso avessi altro da aggiungere rispondi ad un issue già aperto piuttosto che farne uno nuovo.

# Scrivere guide o registrare video-esempi
Cerca di essere sintetico ma senza tralasciare le informazioni essenziali, una volta fatto mandalo pure sul [gruppo telegram](https://t.me/kodiondemand) taggando gli admin (@admin).<br>
Verrà preso in considerazione il prima possibile ed eventualmente inserito nella [wiki](https://github.com/kodiondemand/addon/wiki) o verrà creato un comando richiamabile nel gruppo.

# Consigli
Effettuali sempre nella sezione [issues](https://github.com/kodiondemand/addon/issues), miraccomando descrivi e fai esempi pratici.<br>

# Per sviluppatori

Di seguito tutte le info su come prendere confidenza col codice e come contribuire

## Da dove posso partire?
Un buon punto di partenza è [la wiki](https://github.com/kodiondemand/addon/wiki), qui è presente un minimo di documentazione sul funzionamento di KoD.<br>
Ti consigliamo vivamente, una volta compreso il funzionamento generale dell'addon (e prima di iniziare a sviluppare), di [forkare e clonare il repository](https://help.github.com/en/github/getting-started-with-github/fork-a-repo).<br>
Questo perchè, oltre al fatto di poter iniziare a mandare modifiche sul tuo account github, l'utilizzo di git abilita la [dev mode](https://github.com/kodiondemand/addon/wiki/dev-mode), che ti sarà di aiuto nelle tue attività.

## che cosa posso fare?
Puoi provare a fixare un bug che hai riscontrato, aggiungere un canale/server che ti interessa ecc..
Oppure puoi guardare nella sezione [Projects](https://github.com/kodiondemand/addon/projects) cosa è previsto e iniziare a svilupparlo!

## ho fatto le modifiche che volevo, e ora?
Pusha sul tuo fork le modifiche che hai fatto e manda una pull request. Se è la prima volta ecco qualche link che ti aiuterà:
- http://makeapullrequest.com/
- http://www.firsttimersonly.com/
- [How to Contribute to an Open Source Project on GitHub](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github).

Quando crei la pull request, ricordati di spiegare brevemente qual'è la modifica e perchè l'hai fatta.
Quando avremo tempo revisioneremo le modifiche, potremmo anche segnalarti alcuni problemi, nel caso prenditi pure il tutto il tempo che vuoi per sistemare (non è necessaria un'altra pull, tutti i commit verranno riportati nella prima).<br>
Quando sarà tutto a posto accetteremo la pull includendo le modifiche

## Regole per le collaborazioni:
- Se si riutilizza codice proveniente da altri addon è necessario citarne la fonte, per rispetto di chi ci ha lavorato, in caso contrario il pull request verrà respinto.
- Ogni modifica o novità inviata dev'essere testata, può capitare che vi sia sfuggito qualche bug (è normale), ma l'invio di materiale senza preventivi controlli non è gradito.
- I nuovi canali devono essere funzionanti e completi di tutte le feature, comprese videoteca ed autoplay, non verranno accettati finchè non lo saranno.
