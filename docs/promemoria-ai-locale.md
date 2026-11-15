# Promemoria quotidiano: lavorare con l'AI locale

Da rileggere ogni giorno prima di aprire Cline. Le spiegazioni e gli episodi da cui vengono queste regole sono in [ai-locale.md](ai-locale.md).

## Prima di iniziare
1. **Task nuovo** in Cline (pulsante **+**). Uno per ogni lavoro, mai continuare un task vecchio.
2. **Modalità Act** (in Plan non può scrivere file) e ***Auto-approve* al minimo**: solo lettura e modifica dei file del progetto. Comandi, file esterni, browser e MCP spenti, **comprese le sotto-opzioni nascoste** ("all files", "all commands"). Ogni comando lo approvo io.
3. **`git status` pulito**: si parte da un commit, così ogni errore si annulla con `git restore`.
4. **File da rifare? Prima lo cancello io.** L'`editor` di Cline non sovrascrive un file esistente: pretende il testo vecchio esatto, e su un file rotto non lo trova mai.
5. **Un passo alla volta**: un file nuovo o una piccola aggiunta per messaggio, con il contenuto o i valori attesi già scritti nel prompt.

## Mentre lavora
6. **Approvo solo** `py_compile`, `pytest` e `vallum`. Tutto il resto (`python -c`, `powershell.exe -Command`, `Set-Content`, `Out-File`, `echo`) lo rifiuto con *Reject* e scrivo "usa l'editor".
7. **Contatore del contesto**: oltre la metà (circa 32k su 65k) finisco il passo e apro un task nuovo. Più il contesto è lungo, peggio segue le regole.
8. **Stop dopo 2 errori uguali**: la fermo io, non la lascio riprovare.

## Quando dice "ho finito" o "funziona"
9. **Non mi fido del riassunto, controllo i fatti:**
   ```
   git status --short
   git diff
   .venv\Scripts\python -m py_compile <file nuovo>
   .venv\Scripts\python -m pytest -q
   ```
10. **Segnali d'allarme**: `\"` nel codice, file `.old` / `.part` / `.final`, funzioni duplicate, file che non dovevano essere toccati, test di cose non richieste.
11. **Senza l'output vero di pytest non è finito.**

## Quando si incastra
12. **Ripristino, non rattoppo**: `git restore <file>` per i file modificati, cancello quelli nuovi rotti.
13. **Task nuovo** e messaggio con: cosa è stato ripristinato, cosa resta valido, da dove ripartire.
14. **Al secondo fallimento** passo il lavoro a Claude.

## Divisione del lavoro
- **Gemma**: file nuovi e isolati, test su un modello già scritto, piccole aggiunte guidate.
- **Claude**: prompt per Gemma, revisione dei commit `[locale]`, modifiche a più file collegati, problemi che Gemma non risolve.
- **Commit**: prima `[locale]` con il lavoro di Gemma così com'è, poi `[claude]` con le correzioni. Il push lo faccio dopo la revisione.
