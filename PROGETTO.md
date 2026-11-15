# CyberVallum · Note di progetto (passaggio di consegne)

> **Questo file è condiviso da tutte le AI che lavorano al progetto**: Claude Code (lo legge tramite `CLAUDE.md`) e Cline con l'AI locale (lo legge tramite `.clinerules`).
> **Regola:** leggilo all'inizio di ogni sessione e **aggiornalo alla fine** (sezioni "Stato" e "Registro").

## Cos'è
Un'app **da terminale e desktop**, per **Windows e Ubuntu**, che aiuta nella sistemistica, nella sicurezza e nel controllo della rete.
Lo sviluppatore la costruisce mentre studia: **ogni capitolo del percorso di studio diventa un modulo**. Il percorso è in `..\Studio-Sistemista-CyberSecurity`.
Il nome viene dal latino *vallum*, il terrapieno difensivo degli accampamenti romani (vedi la nota in fondo al README). Fino al 15/11/2026 il progetto si chiamava CyberSegugio.

## Architettura (decisa il 2026-11-15)
```
 cybervallum/
 ├── core/        ← il "motore": funzioni Python pure, una per modulo (sistema, processi, rete…)
 │                  restituiscono dati (dizionari/oggetti), NON stampano nulla
 │   ├── config.py    ← UNICO punto per leggere, validare e salvare le impostazioni
 │   └── registry.py  ← elenco dei controlli e dei test eseguibili, con un solo punto di avvio
 ├── cli.py       ← comando da terminale (Typer): `cybervallum <modulo> <azione>` (abbreviato: `vallum`)
 ├── api/         ← (più avanti) API REST locale (FastAPI) sopra lo stesso core
 ├── gui/         ← (più avanti) interfaccia desktop sopra lo stesso core
 └── ai/          ← (più avanti) assistente AI intercambiabile:
                    • Ollama in locale (predefinito, gratis)
                    • Claude: `claude -p` solo per uso personale, oppure chiave API
 tests/           ← test con pytest, uno per modulo
```
- **Linguaggio:** Python 3.12. **Multipiattaforma:** usare `psutil`, `pathlib`, `platform`; evitare comandi specifici di un solo sistema. Se servono, usare un ramo per Windows e uno per Linux.
- **Prima il core e la CLI**, poi l'API e la GUI sopra lo stesso core.
- **Un solo motore, tre ingressi:** CLI, API e GUI non contengono logica. Chiamano `core.config` per le impostazioni e `core.registry` per avviare controlli e test, e restituiscono lo stesso JSON.

### Come si aggiunge un modulo (es. `sistema`)
1. File `cybervallum/core/<modulo>.py`. Le chiamate al sistema (`psutil`, `platform`, comandi) stanno in piccole funzioni private (`_read_cpu()`, ...) che i test sostituiscono con `monkeypatch`. Le funzioni pubbliche restituiscono dizionari e non stampano.
2. Si registrano le azioni con `@registry.action("<modulo>.<azione>", "descrizione", params={...}, modifica_sistema=False)`. Le azioni con `modifica_sistema=True` ricevono il parametro `dry_run` dal registro.
3. Si aggiunge `"cybervallum.core.<modulo>"` a `BUILTIN_MODULES` in `core/registry.py` e una suite con `default_registry.add_suite(...)`.
4. In `cli.py` si aggiunge un gruppo di comandi che chiama solo `registry.run(...)` e `_finish(...)`, con l'opzione `--json`.
5. Si scrive `tests/test_<modulo>.py` con i mock e si documenta il formato di `dati` in `docs/json.md`.
6. Per eventuali impostazioni del modulo si usa `config.register_setting(Setting(...))`. Mai leggere file o variabili d'ambiente direttamente.

**Ambiente di sviluppo:** `py -3.12 -m venv .venv`, poi `.venv\Scripts\python -m pip install -e .` e `.venv\Scripts\python -m pytest`. Il formato `--json` è documentato in `docs/json.md`.

## Il README
Il `README.md` ha tre sezioni da tenere aggiornate a ogni modulo completato: **Cosa può fare oggi** (moduli funzionanti), **In sviluppo** (il modulo su cui si sta lavorando) e **Obiettivi** (moduli futuri). Deve restare chiaro che è un **progetto personale per esercitarsi con l'AI**.
**Tono:** serio e professionale in tutto il progetto (README, messaggi del programma, documentazione, commit). Niente emoji e niente giochi di parole. In fondo al README c'è una breve nota sull'origine del nome.
**Prima di pubblicare** modifiche al README o a testi pubblici, mostrale allo sviluppatore e attendi il suo ok.

## Regole del codice
1. **Sola lettura come impostazione predefinita.** Ogni funzione che modifica il sistema (ferma processi, cambia configurazioni) chiede conferma esplicita e ha un'opzione `--dry-run`.
2. **Scansioni e test di rete SOLO sulla rete dello sviluppatore e sul suo laboratorio.** Mai bersagli esterni. Le funzioni di scansione rifiutano gli IP pubblici, a meno di un flag esplicito.
3. **Nessun segreto nel repository:** chiavi API in variabili d'ambiente o in un file `.env`, che è già nel `.gitignore`.
4. **Ogni modulo ha il suo test.**
5. Codice e commenti in **inglese**, messaggi all'utente in **italiano**.
6. **Commit con prefisso:** `[locale]` se il lavoro l'ha fatto l'AI locale, `[claude]` se l'ha fatto Claude Code, `[io]` se l'ha fatto lo sviluppatore.
7. **Una AI alla volta**, e un commit prima di passare all'altra.
8. **Testabilità fin dall'inizio:**
   - il **core** non stampa e non legge input: restituisce dati. Le chiamate al sistema (psutil, comandi di rete) stanno dietro piccole funzioni che si possono **sostituire nei test** (mock), così i test non dipendono dal PC su cui girano;
   - ogni comando della CLI ha l'opzione **`--json`**, con un output stabile e documentato;
   - **GUI:** ogni elemento interattivo ha un **localizzatore stabile** con la convenzione `<modulo>-<tipo>-<nome>` (es. `sistema-btn-aggiorna`, `diagnosi-tabella-risultati`). Tipi: `btn`, `campo`, `tabella`, `etichetta`, `menu`, `scheda`. In Qt va impostato sia `objectName` sia `accessibleName`; in un'interfaccia web, `data-testid`;
   - la scelta della GUI (Qt con pywinauto/pytest-qt, oppure tecnologia web con Playwright) si fa quando si arriva al modulo `gui`. Lo sviluppatore conosce già Playwright.
9. **Simulazione dei guasti solo in VM:** le prove che rompono la rete (scheda scollegata, DNS errato, `tc netem`, firewall) si fanno **solo nelle macchine virtuali del laboratorio**, mai sul PC di sviluppo né sulla rete di casa.
10. **API first: ogni funzione è disponibile anche via API.** Una funzione è completa solo quando è registrata in `core.registry` e quindi raggiungibile da CLI e API (e dalla GUI quando ci sarà). Niente funzioni solo da GUI o solo da CLI. Così lo strumento è automatizzabile e aperto a script, test, altre applicazioni e all'assistente `ai`.
    **Impostazioni, controlli e test comandabili da fuori:**
    - **impostazioni:** nessun modulo legge file o variabili per conto suo; tutto passa da `core.config`, che valida i valori e li salva in `config.toml` (i segreti restano nel `.env`). CLI: `cybervallum config list|get|set`;
    - **controlli:** ogni azione di un modulo si registra in `core.registry` con nome (`<modulo>.<azione>`), parametri e il flag `modifica_sistema`. CLI: `cybervallum check list` e `cybervallum check run <modulo>.<azione> --json`;
    - **test:** anche le suite di test (pytest e scenari del `test-lab`) si avviano dal registro e producono un esito JSON: stato, durata, test passati e falliti, dettagli. CLI: `cybervallum test run <suite> --json`;
    - **API REST (modulo `api`):** gli stessi comandi via HTTP, con versione nel percorso (`/api/v1/…`): `GET /health`, `GET|PUT /config`, `GET /checks`, `POST /checks/{nome}`, `POST /tests` (restituisce l'id di un'esecuzione), `GET /tests/{id}` (stato ed esito). Le operazioni lunghe sono asincrone: si avviano e poi si interroga lo stato;
    - **sicurezza dell'API:** in ascolto **solo su `127.0.0.1`** (nel `test-lab` solo sulla rete interna delle VM), con un token preso dal `.env`; le azioni con `modifica_sistema` valgono le regole 1 e 2: `dry_run` vero per default ed esecuzione reale solo con `"conferma": true` esplicito. "Aperta" significa estendibile e automatizzabile, **non** esposta su Internet.
11. **Dati di sicurezza aggiornati automaticamente (modulo `aggiornamenti`):**
    - lo strumento scarica **dati, mai codice**: elenchi di vulnerabilità (es. NVD/CVE, catalogo CISA KEV), liste di indirizzi e domini malevoli, regole di hardening, porte e servizi noti. Ciò che viene scaricato non si esegue mai;
    - le **fonti** sono configurabili in `core.config`, solo **HTTPS**, con verifica dell'integrità (hash o firma, quando la fonte li fornisce) e del formato prima di usarle;
    - i dati vanno in una **cache locale con versione e data**; se l'aggiornamento fallisce resta valida l'ultima versione buona, e lo strumento funziona anche **offline**;
    - aggiornamento a richiesta o pianificato (`cybervallum aggiornamenti run`, `POST /api/v1/aggiornamenti`), con stato consultabile (`GET /api/v1/aggiornamenti`): fonte, versione, data, esito;
    - nessuna telemetria: le richieste verso le fonti non inviano dati sul PC o sulla rete dello sviluppatore; si rispettano le condizioni d'uso e i limiti di frequenza di ogni fonte (chiavi API nel `.env`);
    - i moduli (`sicurezza`, `lan`, `ai`…) leggono questi dati solo tramite il core, per esempio per segnalare un software installato con vulnerabilità note o una connessione verso un indirizzo segnalato.

## Roadmap (collegata al percorso di studio)
| Modulo | Collegato a | Funzioni | Stato |
|---|---|---|---|
| `sistema` | L1 · Come funziona un computer | CPU, core, RAM, dischi, sistema operativo, ultimo avvio | ✅ `sistema info` pronto (15/11) |
| `converti` | L2 · Binario ed esadecimale | conversioni bin/dec/hex, IP in binario, MAC | ⬜ |
| `processi` | L3 · PowerShell: processi | elenco, ordinamento per RAM/CPU, ricerca, chiusura con conferma | ⬜ |
| `diagnosi` | L4 · Comandi di rete | scala di diagnosi: scheda → IP → gateway → Internet → DNS | ⬜ |
| `lan` | Fase 1 · Reti | dispositivi della rete di casa (ARP), calcolatore di subnet | ⬜ |
| `voip` | Fase 2 · VoIP | analisi delle chiamate SIP/RTP da file .pcap | ⬜ |
| `servizi` | Fase 3 · Sistemi | servizi, log, utenti, spazio su disco | ⬜ |
| `sicurezza` | Fase 4 · Cybersecurity | controllo dell'hardening, porte aperte sul proprio PC, analisi dei log | ⬜ |
| `ai` | trasversale | domande in linguaggio naturale sui risultati ("perché il PC è lento?") | ⬜ |
| `config` | trasversale, con `sistema` | modulo unico delle impostazioni e registro dei controlli e dei test, comandi `config`, `check` e `test` della CLI | ✅ base pronta (15/11) |
| `aggiornamenti` | Fase 4 · Cybersecurity | download pianificato e verificato dei dati di sicurezza (CVE, CISA KEV, liste di indirizzi malevoli, regole di hardening) in una cache locale con versioni | ⬜ |
| `api` | dopo i primi moduli | API REST locale (FastAPI) per impostazioni, controlli e test; documentazione automatica OpenAPI; test con pytest e il client di prova di FastAPI | ⬜ |
| `gui` | dopo i primi moduli | interfaccia desktop, con localizzatori per i test | ⬜ |
| `test-lab` | Fase 0 (VirtualBox) e Fase 1 (Reti) | VM di laboratorio per simulare i guasti: scheda scollegata, niente DHCP, gateway irraggiungibile, DNS errato, latenza e perdita di pacchetti con `tc netem`; test automatici su Windows e Ubuntu | ⬜ |

## Stato attuale
- 2026-11-15: progetto creato.
- 2026-11-15: **progetto rinominato da CyberSegugio a CyberVallum**: pacchetto `cybervallum`, comandi `cybervallum` e `vallum` (equivalenti), variabile `CYBERVALLUM_CONFIG`, impostazioni in `%APPDATA%\CyberVallum\`.
- 2026-11-15: **base del codice pronta** (passo 1): `pyproject.toml`, `core/convert.py`, `core/config.py` (impostazioni validate in `config.toml`; host dell'API solo loopback, fonti solo HTTPS), `core/registry.py` (azioni `<modulo>.<azione>`, dry-run e conferma per `modifica_sistema`, suite pytest con esito JSON), `cli.py` (`config list|get|set`, `check list|run`, `test list|run`, tutti con `--json`), `docs/json.md`. 49 test superati.
- 2026-11-15: **modulo `sistema` pronto** (passo 3): `core/sistema.py` (adattatori di psutil/platform sostituiti nei test, azione `sistema.info` in sola lettura), comando `vallum sistema info [--json]`, suite `sistema`, formato in `docs/json.md`. 58 test superati. La prima versione di Gemma (commit `[locale]`) non funzionava: corretta da Claude nel commit `[claude]` successivo. Miglioramenti possibili: nome commerciale della CPU su Windows, `ultimo_avvio` senza microsecondi.
- Git 2.56 e GitHub CLI installati. Repository pubblico: https://github.com/TommasoCapiferri/CyberVallum (ramo `main`). Dopo ogni commit: `git push`.
- AI locale: Ollama 0.40.16, in ascolto solo su 127.0.0.1. Modello **`gemma4:12b-it-qat`** (7,2 GB) scaricato il 15/11: gira al 100% sulla GPU RTX 5070 a circa 68-71 token/s anche con contesto da 64k (7,7 GB occupati). Contesto predefinito impostato con `OLLAMA_CONTEXT_LENGTH=65536` (variabile d'ambiente dell'utente). Cline installato in VS Code e collegato a Ollama (provider Ollama, modello `gemma4:12b-it-qat`, contesto 65536, timeout 300000 ms); prima prova superata il 15/11 (Gemma riassume correttamente progetto, primo modulo, regole dei test e dei commit; trascura i mock e `--json`).

## Prossimi passi
1. ✅ **[claude] Base del progetto:** `pyproject.toml` (Python 3.12, dipendenze `psutil`, `typer`, `pytest`), pacchetto `cybervallum/` con `core/config.py` (impostazioni in `config.toml`, validazione, `list/get/set`), `core/registry.py` (registrazione delle azioni `<modulo>.<azione>` con parametri e flag `modifica_sistema`, avvio unico che restituisce un dizionario), `cli.py` con i comandi `config`, `check list`, `check run … --json`, `test run … --json`; cartella `tests/` con i test di config e registry. Commit `[claude]`.
2. **[claude] Istruzioni per Cline:** un prompt pronto da incollare per il modulo `sistema`: funzioni del core dietro piccoli adattatori di `psutil`/`platform` sostituibili nei test, registrazione nel registro, comando `cybervallum sistema info --json`, test con mock. Ricordare a Gemma mock e `--json`, che nel riassunto aveva trascurato.
3. ✅ **[locale] Modulo `sistema`:** scritto da Gemma, non funzionante (commit `[locale]` acc0728); corretto e completato da Claude (commit `[claude]`).
4. ✅ **[claude] Revisione** del modulo `sistema`, fatta insieme al passo 3; README aggiornato (comandi disponibili, `converti` in sviluppo).
5. **Prima di dare a Gemma il prossimo modulo**, leggere `docs/ai-locale.md` (come lavora l'AI locale, i suoi punti deboli, come scriverle i prompt).

## Registro delle sessioni
| Data | Chi | Cosa è stato fatto |
|---|---|---|
| 2026-11-15 | [claude] | Creazione del progetto: PROGETTO.md, CLAUDE.md, .clinerules, README, licenza, .gitignore |
| 2026-11-15 | [claude] | Pubblicato su GitHub |
| 2026-11-15 | [claude] | Regole e roadmap del testing automatico (localizzatori, `test-lab`); Cline collegato a Ollama |
| 2026-11-15 | [claude] | Regola 10: impostazioni, controlli e test comandabili da CLI e API; moduli `config` e `api` nella roadmap; regola 11 e modulo `aggiornamenti` (dati di sicurezza scaricati e verificati) |
| 2026-11-15 | [claude] | Passo 1: base del codice (config, registry, CLI con `--json`, test, docs/json.md) |
| 2026-11-15 | [claude] | Rinomina del progetto in CyberVallum (pacchetto, comandi, configurazione, documentazione) |
| 2026-11-15 | [locale] | Modulo `sistema`, prima versione: `core/sistema.py` quasi corretto; `registry.py` e `cli.py` rovinati modificandoli con PowerShell; test e documentazione non scritti; mai eseguito pytest |
| 2026-11-15 | [claude] | Correzione e completamento del modulo `sistema`: registry, CLI con stampa in italiano, adattatori senza logica, `tests/test_sistema.py`, `docs/json.md` |
