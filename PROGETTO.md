# CyberSegugio · Note di progetto (passaggio di consegne)

> **Questo file è condiviso da tutte le AI che lavorano al progetto**: Claude Code (lo legge tramite `CLAUDE.md`) e Cline con l'AI locale (lo legge tramite `.clinerules`).
> **Regola:** leggilo all'inizio di ogni sessione e **aggiornalo alla fine** (sezioni "Stato" e "Registro").

## Cos'è
Un'app **da terminale e desktop**, per **Windows e Ubuntu**, che aiuta nella sistemistica, nella sicurezza e nel controllo della rete.
Lo sviluppatore la costruisce mentre studia: **ogni capitolo del percorso di studio diventa un modulo**. Il percorso è in `..\Studio-Sistemista`.
Il nome viene dal "fiuto" del segugio, ed è dedicato a Titty, la sua cagnolina 🐶.

## Architettura (decisa il 2026-11-15)
```
 cybersegugio/
 ├── core/        ← il "motore": funzioni Python pure, una per modulo (sistema, processi, rete…)
 │                  restituiscono dati (dizionari/oggetti), NON stampano nulla
 ├── cli.py       ← comando da terminale (Typer): `cybersegugio <modulo> <azione>`
 ├── gui/         ← (più avanti) interfaccia desktop sopra lo stesso core
 └── ai/          ← (più avanti) assistente AI intercambiabile:
                    • Ollama in locale (predefinito, gratis)
                    • Claude: `claude -p` solo per uso personale, oppure chiave API
 tests/           ← test con pytest, uno per modulo
```
- **Linguaggio:** Python 3.12. **Multipiattaforma:** usare `psutil`, `pathlib`, `platform`; evitare comandi specifici di un solo sistema. Se servono, usare un ramo per Windows e uno per Linux.
- **Prima il core e la CLI**, poi la GUI sopra lo stesso core.

## Il README
Il `README.md` ha tre sezioni da tenere aggiornate a ogni modulo completato: **Cosa può fare oggi** (moduli funzionanti), **In sviluppo** (il modulo su cui si sta lavorando) e **Obiettivi** (moduli futuri). Deve restare chiaro che è un **progetto personale per esercitarsi con l'AI**.
**Tono:** serio e professionale in tutto il progetto (README, messaggi del programma, documentazione, commit). Niente emoji nei titoli, niente giochi di parole sul cane. L'unica eccezione è la **dedica a Titty in fondo al README**, che può avere una battuta.
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

## Roadmap (collegata al percorso di studio)
| Modulo | Collegato a | Funzioni | Stato |
|---|---|---|---|
| `sistema` | L1 · Come funziona un computer | CPU, core, RAM, dischi, sistema operativo, ultimo avvio | ⬜ da fare (primo modulo) |
| `converti` | L2 · Binario ed esadecimale | conversioni bin/dec/hex, IP in binario, MAC | ⬜ |
| `processi` | L3 · PowerShell: processi | elenco, ordinamento per RAM/CPU, ricerca, chiusura con conferma | ⬜ |
| `diagnosi` | L4 · Comandi di rete | scala di diagnosi: scheda → IP → gateway → Internet → DNS | ⬜ |
| `lan` | Fase 1 · Reti | dispositivi della rete di casa (ARP), calcolatore di subnet | ⬜ |
| `voip` | Fase 2 · VoIP | analisi delle chiamate SIP/RTP da file .pcap | ⬜ |
| `servizi` | Fase 3 · Sistemi | servizi, log, utenti, spazio su disco | ⬜ |
| `sicurezza` | Fase 4 · Cybersecurity | controllo dell'hardening, porte aperte sul proprio PC, analisi dei log | ⬜ |
| `ai` | trasversale | domande in linguaggio naturale sui risultati ("perché il PC è lento?") | ⬜ |
| `gui` | dopo i primi moduli | interfaccia desktop, con localizzatori per i test | ⬜ |
| `test-lab` | Fase 0 (VirtualBox) e Fase 1 (Reti) | VM di laboratorio per simulare i guasti: scheda scollegata, niente DHCP, gateway irraggiungibile, DNS errato, latenza e perdita di pacchetti con `tc netem`; test automatici su Windows e Ubuntu | ⬜ |

## Stato attuale
- 2026-11-15: progetto creato. Ci sono solo la documentazione e la struttura, **ancora nessun codice**.
- Git 2.56 e GitHub CLI installati. Repository pubblico: https://github.com/TommasoCapiferri/CyberSegugio (ramo `main`). Dopo ogni commit: `git push`.
- AI locale: Ollama 0.40.16, in ascolto solo su 127.0.0.1. Modello **`gemma4:12b-it-qat`** (7,2 GB) scaricato il 15/11: gira al 100% sulla GPU RTX 5070 a circa 68-71 token/s anche con contesto da 64k (7,7 GB occupati). Contesto predefinito impostato con `OLLAMA_CONTEXT_LENGTH=65536` (variabile d'ambiente dell'utente). Cline: da installare in VS Code e collegare a Ollama.

## Registro delle sessioni
| Data | Chi | Cosa è stato fatto |
|---|---|---|
| 2026-11-15 | [claude] | Creazione del progetto: PROGETTO.md, CLAUDE.md, .clinerules, README, licenza, .gitignore |
| 2026-11-15 | [claude] | Pubblicato su GitHub |
