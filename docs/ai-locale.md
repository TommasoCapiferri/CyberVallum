# Lavorare con l'AI locale (Gemma tramite Cline)

Questo documento raccoglie come si comporta l'AI locale nel progetto, i suoi punti deboli osservati e il modo di lavorarci che ne deriva. Si aggiorna ogni volta che si scopre un comportamento nuovo. Va letto prima di affidare a Gemma un nuovo modulo.

Configurazione attuale: Cline in VS Code, collegato a Ollama in locale, modello `gemma4:12b-it-qat` con contesto di 64k token (dettagli in `PROGETTO.md`, sezione "Stato attuale").

## Come lavora

Cline dà al modello alcuni strumenti: leggere file, modificarli con un editor (`write_to_file` per creare, `replace_in_file` per sostituire un pezzo), eseguire comandi nel terminale (`run_commands`). Il modello sceglie da solo quale strumento usare a ogni passo, legge il risultato e decide il passo successivo.

Gemma è un modello da 12 miliardi di parametri: veloce e gratuito, ma molto più piccolo di Claude. In pratica:

- scrive bene **codice nuovo e isolato** quando il prompt dà nomi, firme e formato esatti (`core/sistema.py`, scritto da zero, era quasi corretto);
- fatica a **modificare file esistenti** e a gestire più file collegati tra loro;
- quando qualcosa va storto, tende a **ripetere** lo stesso tentativo invece di cambiare strategia;
- **riassume il proprio lavoro con sicurezza**, anche quando il riassunto non corrisponde ai file.

## Punti deboli osservati

Episodio di riferimento: modulo `sistema`, 15/11/2026, commit `acc0728` (versione di Gemma) e `e0a6b16` (correzioni di Claude). Con `git show acc0728` si vede esattamente cosa aveva prodotto.

| Comportamento | Cosa è successo | Conseguenza |
|---|---|---|
| Modifica i file con PowerShell invece che con l'editor | In `registry.py` ha scritto `\"cybervallum.core.sistema\"` con l'escape letterale e ha indentato una riga a caso | `SyntaxError`: non si importava più niente, nessun test partiva |
| Riscrive file interi | Copie di `cli.py` in `cli.py.old`, `.part1`, `.final`; una funzione duplicata e troncata in fondo; un BOM all'inizio del file | File rotto e spazzatura nella cartella |
| Va in loop | 5 chiamate identiche a `run_commands`, poi Cline si è fermato da solo | Tempo perso, nessun progresso |
| Inventa la causa degli errori | Ha detto che VS Code bloccava il file; la causa probabile era `Get-Content f \| Set-Content f`, che legge e scrive lo stesso file nella stessa pipeline | Il piano di riparazione partiva da una diagnosi sbagliata |
| Non esegue i test | Ha scritto "il file è stabile e funzionante" senza aver mai lanciato pytest (che non sarebbe nemmeno partito) | Dichiarazione falsa di lavoro finito |
| Lascia passaggi a metà | Ha usato `@sistema_app.command` senza mai creare `sistema_app`; ha sostituito la stampa in italiano con `_print_json` | `NameError` all'avvio, output non conforme |
| Mette la logica nel posto sbagliato | Gli adattatori di `sistema.py` traducevano già i campi e convertivano `""` in `None` | Quella logica sta in codice che i test sostituiscono, quindi non viene mai testata |
| Salta i passi finali | Non ha scritto `tests/test_sistema.py` né la sezione di `docs/json.md` | Modulo senza test e senza contratto JSON |
| Vuole aggiornare `PROGETTO.md` troppo presto | Stava per segnare il modulo come fatto con il codice ancora rotto | Le note condivise diventerebbero false |

Cosa ha fatto bene, e va riconosciuto: la struttura di `sistema.py` (adattatori, `get_info()`, gestione dei dischi illeggibili) seguiva il prompt; ha capito da sola che `git checkout` era il modo giusto per ripristinare `cli.py`; quando le è stato chiesto ha spiegato i propri errori, anche se in parte con cause inventate.

## Come lavorarci

### 1. Dare compiti piccoli

Un prompt, un risultato verificabile. Invece di "fai il modulo con 6 file", meglio due o tre giri:

1. il file del core (nuovo, isolato: è quello che le riesce meglio);
2. i test di quel file, e farli girare;
3. le aggiunte a `registry.py`, `cli.py` e alla documentazione.

Fra un giro e l'altro: controllo dello sviluppatore e commit `[locale]`.

### 2. Scrivere il prompt in modo esplicito

Regole da mettere in ogni prompt (o in `.clinerules`, vedi sotto):

- **file solo con l'editor di Cline**, mai con comandi PowerShell (`Set-Content`, `Out-File`, `echo >`, here-string);
- nei file esistenti **solo aggiunte piccole** con `replace_in_file`, dicendo *dove* (es. "dopo la riga `app.add_typer(test_app, name="test")`"); mai riscrivere il file intero;
- **i comandi servono solo per eseguire** `pytest` e `vallum`;
- **dopo 2 tentativi falliti uguali, fermati** e mostra l'errore;
- **non dire che funziona senza mostrare l'output vero di pytest**;
- il commit lo fa solo quando la lista di controllo è tutta "sì", con `git add` dei soli file elencati, e **niente push**.

Funzionano meglio le istruzioni precise ("aggiungi questa riga qui") delle istruzioni di intento ("integra il comando nella CLI"). Il codice da copiare tale e quale (firme, nomi dei campi, fixture dei test) riduce molto gli errori.

### 3. Controllare i fatti, non il riassunto

Quando Gemma dice di aver finito, prima di crederle:

```
git status --short          # quali file ha toccato, file temporanei lasciati in giro
git diff                    # cosa ha cambiato davvero
.venv\Scripts\python -m pytest -q
```

Segnali d'allarme nel diff: `\"` nel codice Python, carattere invisibile `﻿` (BOM) all'inizio di un file, funzioni duplicate, file `.old` / `.bak` / `.part`, righe vuote sparite fra le funzioni.

### 4. Quando si incastra

- **Fermarla subito** al primo loop: lasciarla riprovare peggiora i file.
- **Ripristinare, non rattoppare:** `git restore <file>` riporta un file all'ultimo commit in un attimo; riparare un file rovinato a piccoli pezzi richiede molti passaggi, ognuno dei quali può sbagliare.
- Poi un messaggio che dice **cosa è stato ripristinato, cosa resta valido e da dove ripartire**, con le regole del punto 2.
- Se dopo un secondo tentativo è ancora incastrata, conviene passare il lavoro a Claude.

### 5. Dividere il lavoro fra le due AI

| Gemma (locale, gratis) | Claude Code (abbonamento, con limiti) |
|---|---|
| file nuovi e isolati con specifica precisa | architettura, prompt per Gemma |
| test seguendo un modello già scritto | revisione dei commit `[locale]` |
| piccole aggiunte guidate | modifiche a più file collegati, correzioni |
| documentazione su schema dato | problemi che Gemma non risolve in due tentativi |

Quando Claude corregge il lavoro di Gemma: prima un commit `[locale]` con il lavoro di Gemma così com'è (anche se non funziona, scritto nel messaggio), poi un commit `[claude]` con le correzioni. Così `git show` mostra separatamente gli errori e la soluzione, utile per imparare.

## Regole proposte per `.clinerules`

Da aggiungere se lo sviluppatore è d'accordo, così valgono per ogni attività senza ripeterle nei prompt:

```
- Crea e modifica i file SOLO con gli strumenti dell'editor di Cline, mai con comandi del terminale.
- Nei file esistenti fai modifiche piccole con replace_in_file; non riscrivere mai un file intero.
- Usa il terminale solo per eseguire i test e il programma, non per scrivere file.
- Se lo stesso comando o la stessa modifica fallisce 2 volte, fermati e mostra l'errore.
- Non dire che una cosa funziona se non hai mostrato l'output di pytest.
- Non fare mai git push.
```
