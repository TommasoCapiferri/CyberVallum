# Lavorare con l'AI locale (Gemma tramite Cline)

La versione breve, da rileggere ogni giorno, è [promemoria-ai-locale.md](promemoria-ai-locale.md).

Questo documento raccoglie come si comporta l'AI locale nel progetto, i suoi punti deboli osservati e il modo di lavorarci che ne deriva. Si aggiorna ogni volta che si scopre un comportamento nuovo. Va letto prima di affidare a Gemma un nuovo modulo.

Configurazione attuale: Cline in VS Code, collegato a Ollama in locale, modello `gemma4:12b-it-qat` con contesto di 64k token (dettagli in `PROGETTO.md`, sezione "Stato attuale").

## Configurazione di Cline e Ollama

### Modalità Plan e Act
Interruttore **Plan / Act** in basso nel pannello di Cline.
- **Plan**: sola lettura. Gemma legge, cerca nel codice e fa domande, ma non ha lo strumento `editor`. Se un prompt le chiede di scrivere un file, prova a chiamare strumenti inesistenti (`write_to_file`) e Cline li blocca con `AI_NoSuchToolError`. Serve per farsi spiegare un piano prima di eseguirlo.
- **Act**: ha anche `editor` e può modificare i file. Si usa per i passi già scritti nel prompt.

### Strumenti disponibili (versione di Cline del 15/11/2026)
`read_files`, `search_codebase`, `editor`, `run_commands`, `ask_question`, `fetch_web_content` e quattro strumenti `composio_*`.
- **Composio** è un servizio che collega l'AI ad account esterni (GitHub, Gmail, Slack...). Non è un server MCP installato da noi: lo porta Cline stesso. Il file dei server MCP è vuoto (`"mcpServers": {}`) e nessun account è collegato, quindi oggi non può agire, ma i suoi strumenti restano visibili al modello.
- `fetch_web_content` scarica pagine web: rischio di *prompt injection* (istruzioni nascoste nel testo di una pagina).

### Approvazione automatica (*Auto-approve*): privilegio minimo
| Voce nell'interfaccia | Chiave nel file | Valore | Perché |
|---|---|---|---|
| Read project files | `readFiles` | on | leggere il progetto non è rischioso |
| sotto-opzione: Read all files | `readFilesExternally` | **off** | file fuori dal progetto: non servono |
| Edit project files | `editFiles` | on | nel progetto ogni errore si annulla con git |
| sotto-opzione: Edit all files | `editFilesExternally` | **off** | fuori dal progetto git non protegge |
| Execute safe commands | `executeSafeCommands` | **off** | "sicuro" lo decide il modello |
| sotto-opzione: Execute all commands | `executeAllCommands` | **off** | il permesso più pericoloso |
| Use browser | `useBrowser` | **off** | pagine web, prompt injection |
| Use MCP servers | `useMcp` | **off** | qualsiasi strumento esterno |

Impostazioni generali: **Web Search off**. *MCP Display Mode* riguarda solo come vengono mostrati i risultati, non la sicurezza.

**Trappola dell'interfaccia:** le sotto-opzioni ("all files", "all commands") si vedono solo quando la voce principale è spuntata. Togliendo la spunta alla voce principale, la sotto-opzione sparisce dalla vista **ma resta attiva** nel file. Il 15/11/2026 `executeAllCommands` era `true` con la voce principale spenta: per questo Gemma lanciava comandi senza chiedere. Prima si spegne la sotto-opzione, poi la voce principale.

### Dove sono i file di configurazione
In `C:\Users\tomma\.cline\data\`:
- `globalState.json`: approvazioni automatiche (`autoApprovalSettings`), modalità corrente, timeout;
- `settings\global-settings.json`: Web Search (`tools.web_search.enabled`), aggiornamenti automatici, telemetria (`telemetryOptOut`);
- `settings\cline_mcp_settings.json`: server MCP (vuoto);
- `settings\providers.json`: provider e modello (contiene credenziali: non va aperto davanti ad altri né condiviso);
- `sessions\`: la cronologia dei task.

Il file si può modificare a mano (copia di sicurezza: `globalState.json.bak-2026-11-15`), ma Cline tiene le impostazioni in memoria e può riscriverle alla modifica successiva. Dopo un cambio a mano: ricaricare VS Code (*Developer: Reload Window*) e ricontrollare il file.

### Exit code sbagliati (shell integration)
Cline legge output ed exit code dei comandi attraverso la *shell integration* di VS Code. Con Windows PowerShell 5.1 e l'ambiente virtuale attivato all'apertura del terminale, la lettura a volte fallisce: Cline riporta **exit code 1 con output vuoto** anche quando il comando è riuscito, oppure "Command completion could not be observed".
- Verificato il 15/11/2026: `py_compile` segnalato da Cline con exit code 1, mentre nel terminale `$LASTEXITCODE` valeva `0`.
- Per controllare a mano, subito dopo un comando nel terminale: `$LASTEXITCODE` (0 = riuscito).
- **Soluzione (verificata il 15/11/2026):** impostazioni di Cline → sezione **Terminal** → **Terminal Execution Mode: Background Exec**. Cline avvia i comandi come processo figlio, senza il terminale di VS Code, e riceve output ed exit code veri. Prova fatta: `py_compile` su un file corretto -> exit code 0; su un file inesistente -> exit code 1 con `[Errno 2] No such file or directory`. L'output dei comandi si vede nella chat di Cline, non più nel pannello del terminale.
- **Default Terminal Profile** resta su *Default* (Windows PowerShell 5.1). Cline elenca anche profili non installati: scegliendone uno assente, ogni comando fallisce.
- **Tentativo che NON ha funzionato (15/11/2026):** disattivare l'attivazione automatica del venv nei terminali (`"python.terminal.activateEnvironment": false` in `.vscode/settings.json`). Il terminale di Cline è partito senza `(.venv)`, ma l'exit code era ancora 1. Modifica annullata. Causa più probabile: la shell integration di Windows PowerShell 5.1 non passa l'exit code a Cline.

### Da capire (to-do)
- [x] Exit code sbagliati: risolto con *Background Exec* (vedi sopra).
- [x] **Fatto il 15/11/2026:** PowerShell 7.7.0 è il terminale predefinito di VS Code (verificato con `$PSVersionTable.PSVersion`). Resta da provare il profilo *PowerShell 7* anche in Cline.
- (storico) PowerShell 7 come terminale predefinito. È già installato (15/11/2026, pacchetto MSIX via winget, comando `pwsh`), ma VS Code non lo elencava perché era aperto da prima dell'installazione: chiuderlo e riaprirlo. Provare, con la stessa prova dei due `py_compile`, il profilo *PowerShell 7* in Cline ed eventualmente come terminale predefinito di VS Code.
- [ ] Verificare nell'interfaccia di Cline dove sono esattamente le sotto-opzioni "Read all files", "Edit all files", "Execute all commands", e annotarlo qui.
- [ ] Controllare dopo un riavvio di VS Code che le modifiche fatte a mano in `globalState.json` siano rimaste.
- [ ] Capire da dove arrivano gli strumenti `composio_*` e se si possono disattivare del tutto (impostazioni di Cline, account Cline).
- [ ] Decidere sulla telemetria di Cline: oggi `telemetryOptOut` è `false`, cioè Cline invia dati d'uso. Per un progetto di sicurezza conviene valutare di disattivarla.
- [ ] Valutare `autoUpdateEnabled`: gli aggiornamenti automatici possono cambiare gli strumenti e i nomi (come `editor` al posto di `write_to_file`) senza preavviso.

## Come lavora

Cline dà al modello alcuni strumenti: `read_files` per leggere, `editor` per creare e modificare i file, `run_commands` per eseguire comandi nel terminale. Nei prompt vanno usati questi nomi; `write_to_file` e `replace_in_file` sono di altre versioni di Cline e qui non esistono.

Come funziona `editor` (scoperto il 15/11/2026):
- **file che non esiste**: basta il testo nuovo e il file viene creato;
- **file che esiste**: serve anche il testo vecchio esatto da sostituire, e se non corrisponde carattere per carattere (spazi, ritorni a capo, `\"`) la modifica fallisce con "No replacement performed".

Per questo un file rotto non si "riscrive": **lo si cancella** (in VS Code o con `git restore` se era già nel repository) e poi Gemma lo ricrea da zero. Le modifiche a file esistenti devono sostituire pezzi piccoli e unici, come i segnaposto `# STEP-...`. Il modello sceglie da solo quale strumento usare a ogni passo, legge il risultato e decide il passo successivo.

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

### Secondo episodio: modulo `converti`, giro 1 (15/11/2026)

Le regole erano sia nel prompt sia in `.clinerules` ("file solo con l'editor, mai con il terminale"). Gemma le ha ignorate comunque:

- `converti.py` era di circa 6100 caratteri, vicino al limite dell'editor di Cline. Probabilmente è per questo che Gemma è tornata al terminale.
- Ha lanciato `powershell.exe -Command "python -c \"\"\" ...file intero... \"\"\""`, cioè codice Python dentro tre livelli di virgolette. PowerShell ha chiuso la stringa alla prima virgoletta e poi ha eseguito **ogni riga del file Python come se fosse un comando PowerShell** (`import os` -> "comando non riconosciuto", `@pytest...` -> "operatore di splatting").
- Risultato: `converti.py` e `test_converti.py` creati con `\"` al posto di `"` e illeggibili da Python. Nessun commit.
- Ha anche fatto cose fuori dal prompt: test della CLI per un comando che ancora non esiste, e parametri di `parametrize` con nomi diversi da quelli della funzione (`input` invece di `input_str`).

Lezioni:

- **Le regole scritte non bastano**: quando l'editor le sembra scomodo, Gemma torna al terminale. Serve un blocco *tecnico*: in Cline, nelle impostazioni di approvazione automatica (*Auto-approve*), disattivare **Execute commands**. Così ogni comando aspetta il tuo "Approve", e quelli che scrivono file (`python -c`, `Set-Content`, `Out-File`, `echo >`, `powershell.exe -Command`) si rifiutano con *Reject*.
- **File grandi a pezzi**: si crea prima uno scheletro piccolo con dei segnaposto (`# STEP-2-HERE`), poi ogni funzione si aggiunge sostituendo il segnaposto con `editor`. Ogni modifica resta sotto il limite dell'editor.
- **Controllo dopo ogni file**: `.venv\Scripts\python -m py_compile <file>` (senza virgolette, quindi Gemma non lo può rovinare) rivela subito i `\"`.

### Terzo episodio: modulo `converti`, giro 1 rifatto a passi (15/11/2026, riuscito)

Dopo le contromisure (task nuovo, file rotti cancellati, *Auto-approve* al minimo, *Background Exec*, scheletro con segnaposto), Gemma ha completato **9 passi senza nessun file rotto e nessun loop**: commit `c41dae9` (core) e `598a9e6` (test), 82 test superati.

- Passi 1-5 uno alla volta, poi 6-7 e 8-9 a coppie, con un controllo dopo ogni passo (`py_compile` o pytest con il numero di test atteso).
- Il codice dato per intero (passi 1, 2, 3, 4, 6) è stato copiato correttamente; anche i test descritti solo a parole (passi 7, 8, 9) li ha scritti bene.
- Restano due difetti, piccoli: **dichiarazioni non verificate** ("esattamente due righe vuote", erano 4 e 3) e **asserzioni deboli** nei test (`assert r["errore"] != ""` passa anche con `None`). Li ha corretti Claude nella revisione, insieme a un caso non coperto dal prompt (`int()` accetta `"1_000"` e `"+5"`).

Cosa ha funzionato e va ripetuto:
- **Numeri attesi nel prompt** ("attesa: 15 passed"): Gemma e lo sviluppatore verificano a colpo d'occhio.
- **Una prova che deve fallire** per verificare uno strumento (il `py_compile` su un file inesistente): un controllo che passa sempre non dimostra niente.
- **Due passi per messaggio** solo se sono dello stesso tipo e con un controllo in mezzo; se un messaggio da due passi va storto, si torna a uno.
- **Commit di sicurezza** a metà giro (dopo il core, prima dei test).

### Quarto episodio: `converti`, giro 2 (15/11/2026)

- Passi 1-2 (modifiche a `registry.py` e `cli.py`, file esistenti): corretti al primo colpo con il formato "TESTO VECCHIO = una riga corta e unica / TESTO NUOVO = la stessa riga più le aggiunte".
- Aggiunta non richiesta: una riga nel registro di `PROGETTO.md` ("Modulo converti collegato al registro e alla CLI"), **falsa** (i comandi CLI non esistevano ancora), con data sbagliata ed emoji. Causa: `.clinerules` diceva "alla fine aggiorna PROGETTO.md", in contrasto con il prompt. **Lezione: le regole permanenti e i prompt non devono contraddirsi**; `.clinerules` ora dice che `PROGETTO.md` lo aggiorna Claude e che, in caso di conflitto, vale il prompt.

### Cosa ha fatto bene

Nel primo episodio, e va riconosciuto: la struttura di `sistema.py` (adattatori, `get_info()`, gestione dei dischi illeggibili) seguiva il prompt; ha capito da sola che `git checkout` era il modo giusto per ripristinare `cli.py`; quando le è stato chiesto ha spiegato i propri errori, anche se in parte con cause inventate.

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
- nei file esistenti **solo aggiunte piccole** con `editor`, dicendo *dove* (es. "dopo la riga `app.add_typer(test_app, name="test")`"); mai riscrivere il file intero;
- **i comandi servono solo per eseguire** `pytest` e `vallum`;
- **dopo 2 tentativi falliti uguali, fermati** e mostra l'errore;
- **non dire che funziona senza mostrare l'output vero di pytest**;
- il commit lo fa solo quando la lista di controllo è tutta "sì", con `git add` dei soli file elencati, e **niente push**.

Funzionano meglio le istruzioni precise ("aggiungi questa riga qui") delle istruzioni di intento ("integra il comando nella CLI"). Il codice da copiare tale e quale (firme, nomi dei campi, fixture dei test) riduce molto gli errori.

### 2b. Bloccare il terminale in Cline

Nelle impostazioni di Cline (*Auto-approve*), **Execute commands** va tenuto disattivato. Si approva a mano solo `pytest`, `py_compile` e `vallum`; tutto il resto si rifiuta con *Reject* e un messaggio tipo "usa l'editor". È l'unica difesa che funziona davvero: vedi il secondo episodio.

### 2c. Gestire il contesto

La *context window* è la memoria di lavoro del task: istruzioni di sistema di Cline, `.clinerules`, messaggi, file letti, output dei comandi e risposte. In Ollama è impostata a 65.536 token (`OLLAMA_CONTEXT_LENGTH`), e Cline mostra quanto ne è occupato.

- **Un task nuovo per ogni lavoro** (pulsante **+** in Cline), e un task nuovo appena qualcosa va storto: un contesto pieno di tentativi falliti spinge Gemma a ripeterli.
- **Oltre la metà (circa 32k)** si finisce il passo e si apre un task nuovo. I modelli piccoli seguono peggio le istruzioni iniziali molto prima di arrivare al limite.
- **Prompt autosufficienti**: invece di "leggi PROGETTO.md e docs/...", conviene mettere nel prompt solo quello che serve al passo. Ogni file letto occupa contesto.
- Resettare il contesto non cambia i file del progetto: si azzera solo la memoria di Gemma.

### 3. Controllare i fatti, non il riassunto

Quando Gemma dice di aver finito, prima di crederle:

```
git status --short          # quali file ha toccato, file temporanei lasciati in giro
git diff                    # cosa ha cambiato davvero
.venv\Scripts\python -m pytest -q
```

Controllo veloce dei file nuovi, che non compaiono in `git diff` finché non si fa `git add`: aprirli in VS Code oppure eseguire `.venv\Scripts\python -m py_compile <file>`.

Segnali d'allarme nel diff: `\"` nel codice Python, carattere invisibile `﻿` (BOM) all'inizio di un file, funzioni duplicate, file `.old` / `.bak` / `.part`, righe vuote sparite fra le funzioni.

### 3b. Loop senza errori: `converti`, giro 2, messaggio C (15/11/2026)

Il messaggio C cominciava con "PASSO 3 verificato", ma era incollato in un **task nuovo** di Cline, senza la conversazione dei messaggi A e B. Gemma l'ha letto come un ordine e ha **rifatto il passo 3**, pur notando che il codice "era già presente". Poi `# STEP-4-IP` non era più unico (i doppioni li aveva creati lei), ne ha dato la colpa a "modifiche precedenti" e ha pianificato di allargare il testo da cercare. Alla domanda "sei andata in loop?" ha risposto "No". In tutto, invece di scrivere `ip` e `mac`, Gemma ha incollato **due volte** in fondo a `cli.py` il blocco `converti` già esistente (`_print_numero`, `converti_numero` e i segnaposto), lasciando 3 copie di `# STEP-4-IP` e `# STEP-5-MAC`. Ogni modifica con `editor` era **riuscito**: la regola "se fallisce 2 volte, fermati" non scattava. Inoltre `py_compile` passava (in Python ridefinire una funzione è lecito) e pytest restava a 91. Lo rivelava solo `vallum converti ip` ("No such command 'ip'").

Lezioni:
- la regola anti-loop deve contare le **ripetizioni**, non solo i fallimenti (aggiunta in `.clinerules`);
- nei controlli del prompt servono verifiche sul **risultato** (il comando esiste, una funzione compare una sola volta), non solo sulla sintassi;
- una modifica riuscita non va ripetuta: rileggere il file una volta e passare ai controlli;
- **ogni messaggio per un task nuovo deve stare in piedi da solo**: dire cosa è già fatto, cosa non toccare, e far controllare lo stato del file prima di iniziare;
- "testo non unico" è un segnale di stop, non un problema da aggirare.

Esito del messaggio C riscritto (autosufficiente): passi 4 e 5 corretti al primo colpo. Il passo 5 Gemma l'ha **scritto da sola** dalla descrizione e dall'esempio del passo 4; unico difetto, 3 righe vuote invece di 2.

### 3c. Il verificatore: `scripts\verifica.py` (15/11/2026)

Il punto debole di Gemma è **giudicare il proprio lavoro** (dichiara "fatto" o "non sono in loop" contro i fatti). Per renderla più autonoma il giudizio lo dà un programma:

```
.venv\Scripts\python scripts\verifica.py                  # tutto
.venv\Scripts\python scripts\verifica.py --con-segnaposto # lavoro a metà, "# STEP-" ammessi
```

Controlla: **ruff** (nomi non definiti F821, funzioni duplicate F811, import inutili, errori di sintassi, righe vuote fra le funzioni E30), segnaposto `# STEP-` rimasti, file `.old`/`.bak`/`.part`, BOM, pytest. Stampa `VERIFICA: OK` (exit 0) o `VERIFICA: FALLITA` con l'elenco (exit 1). Le regole di ruff sono poche di proposito (in `pyproject.toml`): solo errori veri, niente stile, perché ogni segnalazione superflua è un'occasione di loop.

Avrebbe scoperto da solo: i doppioni del messaggio C, `sistema_app` mai creato nel modulo `sistema`, le righe vuote in più. Regola in `.clinerules`: hai finito solo con `VERIFICA: OK`; stesso errore 2 volte, fermati. Ruff si installa con `.venv\Scripts\python -m pip install -e .[dev]`.

Prossimi gradini di autonomia: (1) codice da copiare, (2) descrizione con esempio (passo 5 di `converti`), (3) solo firme, campi JSON e risultati attesi (modulo `processi`), (4) solo obiettivo e controlli, con piano in modalità Plan rivisto da Claude. Da provare per ultimo: una variante del modello con `temperature` più bassa (ora è 1), confrontata sullo stesso passo.

### 4. Quando si incastra

- **Fermarla subito** al primo loop: lasciarla riprovare peggiora i file.
- **Ripristinare, non rattoppare:** `git restore <file>` riporta un file all'ultimo commit in un attimo; riparare un file rovinato a piccoli pezzi richiede molti passaggi, ognuno dei quali può sbagliare.
- Poi un messaggio che dice **cosa è stato ripristinato, cosa resta valido e da dove ripartire**, con le regole del punto 2.
- Se dopo un secondo tentativo è ancora incastrata, conviene passare il lavoro a Claude.

### 4b. Costo e modo di lavorare con Claude

I token di Gemma sono gratuiti (girano sulla GPU), ma **non riducono quelli di Claude**: con prompt che contengono il codice completo, una verifica di Claude a ogni passo e una conversazione lunga, Claude consuma più che a scrivere il modulo da solo. Per `converti`, il 15/11/2026, il costo è stato più alto.

Scelta dello sviluppatore (15/11/2026): **per ora conta imparare, non risparmiare**. Si lavora verificando insieme gli output a ogni passo e migliorando insieme il modo di usare l'AI locale.

Quando servirà risparmiare:
- prompt di **specifica** (firma, esempi, errori, test attesi) invece che di codice;
- controlli intermedi fatti dallo sviluppatore con i risultati attesi scritti nel prompt; Claude solo a fine giro;
- **una sessione di Claude nuova per ogni lavoro**: in una conversazione lunga ogni turno rilegge tutto il contesto;
- a Gemma i lavori con specifica corta e codice lungo o ripetitivo.

I prompt pronti si salvano in `docs/prompts/`, così sopravvivono alla fine della sessione di Claude e restano come esempio.

### 5. Dividere il lavoro fra le due AI

| Gemma (locale, gratis) | Claude Code (abbonamento, con limiti) |
|---|---|
| file nuovi e isolati con specifica precisa | architettura, prompt per Gemma |
| test seguendo un modello già scritto | revisione dei commit `[locale]` |
| piccole aggiunte guidate | modifiche a più file collegati, correzioni |
| documentazione su schema dato | problemi che Gemma non risolve in due tentativi |

Quando Claude corregge il lavoro di Gemma: prima un commit `[locale]` con il lavoro di Gemma così com'è (anche se non funziona, scritto nel messaggio), poi un commit `[claude]` con le correzioni. Così `git show` mostra separatamente gli errori e la soluzione, utile per imparare.

## Regole in `.clinerules`

Aggiunte il 15/11/2026: valgono per ogni attività, senza ripeterle nei prompt (nei prompt lunghi conviene comunque ricordarle):

```
- Crea e modifica i file SOLO con gli strumenti dell'editor di Cline, mai con comandi del terminale.
- Nei file esistenti fai modifiche piccole con `editor`; non riscrivere mai un file intero.
- Usa il terminale solo per eseguire i test e il programma, non per scrivere file.
- Se lo stesso comando o la stessa modifica fallisce 2 volte, fermati e mostra l'errore.
- Non dire che una cosa funziona se non hai mostrato l'output di pytest.
- Non fare mai git push.
```
