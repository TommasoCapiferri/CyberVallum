# CyberVallum

Strumento da riga di comando, con interfaccia desktop in programma, per l'**analisi del sistema**, la **diagnostica di rete** e i **controlli di sicurezza** su Windows e Linux.
Raccoglie in un unico strumento le verifiche che un sistemista esegue di routine: risorse hardware, processi, connettività, dispositivi in rete, servizi e configurazione di sicurezza.

## Natura del progetto
CyberVallum è un **progetto personale di studio**, con tre obiettivi:
- **applicare in pratica** gli argomenti studiati su sistemi, reti e sicurezza: ciascun argomento diventa una funzione dello strumento;
- **sperimentare lo sviluppo software assistito dall'intelligenza artificiale**, combinando un modello eseguito in locale (Ollama con Gemma, tramite Cline in VS Code) per lo sviluppo quotidiano e Claude Code per l'architettura e la revisione del codice;
- **garantire la qualità tramite il testing automatico**: il prodotto avrà una sezione dedicata ai test automatici, che copre il motore di analisi, la riga di comando e l'interfaccia desktop. Comprende un laboratorio in macchine virtuali in cui si riproducono guasti di rete reali (DNS non funzionante, gateway irraggiungibile, perdita di pacchetti) per verificare che le diagnosi siano corrette. I dettagli sono nella sezione [Test automatici](#test-automatici-in-programma).

Non è un prodotto finito né un software destinato all'uso professionale: è un ambiente di sperimentazione che cresce in modo incrementale.

## Funzionalità disponibili
| Comando | Funzione |
|---|---|
| `vallum sistema info` | Sistema operativo, CPU (modello, core, frequenza, utilizzo), memoria, dischi e ultimo avvio |
| `vallum config list\|get\|set` | Lettura e modifica delle impostazioni, con validazione dei valori |
| `vallum check list\|run` | Elenco ed esecuzione dei controlli registrati |
| `vallum test list\|run` | Elenco ed esecuzione delle suite di test, con esito strutturato |

Ogni comando accetta l'opzione `--json`, che produce un output stabile documentato in [docs/json.md](docs/json.md). `cybervallum` e `vallum` sono lo stesso comando.

Installazione per lo sviluppo (Python 3.12):

```
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e .
```

## In sviluppo
| Modulo | Funzione |
|---|---|
| `converti` | Conversioni tra binario, decimale ed esadecimale; rappresentazione degli indirizzi IP |

## Obiettivi
| Modulo | Funzione |
|---|---|
| `processi` | Processi attivi e consumo di risorse |
| `diagnosi` | Diagnosi della connettività: interfaccia di rete, gateway, Internet, DNS |
| `lan` | Rilevamento dei dispositivi della rete locale, calcolo delle sottoreti |
| `voip` | Analisi delle chiamate SIP/RTP da catture di rete |
| `servizi` | Servizi, log e utenti |
| `sicurezza` | Verifiche di hardening e porte in ascolto sul sistema locale |
| `ai` | Interrogazione dei risultati in linguaggio naturale tramite un modello locale |
| `aggiornamenti` | Aggiornamento automatico e verificato dei dati di sicurezza (vulnerabilità note, indirizzi malevoli, regole di hardening), utilizzabile anche offline |
| `api` | API REST locale: ogni funzione dello strumento, comprese le impostazioni, i controlli e i test, è disponibile anche da script e strumenti di automazione |
| `gui` | Interfaccia desktop basata sullo stesso motore della riga di comando |

Lo stato dettagliato e il registro dello sviluppo sono disponibili in [PROGETTO.md](PROGETTO.md).

## Test automatici (in programma)
Il progetto è pensato per essere verificabile automaticamente fin dall'inizio, su tre livelli:

| Livello | Cosa si verifica | Strumenti |
|---|---|---|
| **Motore** | Le funzioni di analisi restituiscono dati strutturati, senza stampare a video: si verificano in isolamento, anche simulando le risposte del sistema | `pytest` |
| **Riga di comando** | Ogni comando prevede l'opzione `--json`, con un output leggibile da script, test e altri strumenti di automazione | `pytest` |
| **API** | Le impostazioni, i controlli e le suite di test sono disponibili anche tramite un'API REST locale, che restituisce gli stessi dati della riga di comando | `pytest` con il client di prova di FastAPI |
| **Interfaccia desktop** | Ogni elemento interattivo ha un **localizzatore stabile**, secondo la convenzione `<modulo>-<tipo>-<nome>` (es. `sistema-btn-aggiorna`) | `pywinauto` e `pytest-qt` per un'interfaccia Qt, oppure `Playwright` con attributi `data-testid` per un'interfaccia basata su tecnologie web |

### Laboratorio di simulazione dei guasti
Per verificare le funzioni di diagnostica in condizioni realistiche è previsto un ambiente dedicato, basato su **macchine virtuali** e separato dal sistema di sviluppo, in cui riprodurre in modo controllato i problemi più comuni:

| Scenario simulato | Tecnica |
|---|---|
| Interfaccia di rete scollegata | Disconnessione della scheda di rete virtuale della VM |
| Indirizzo IP assente (DHCP non disponibile) | Rete virtuale senza server DHCP; verifica del riconoscimento degli indirizzi 169.254.x.x |
| Gateway irraggiungibile | Regole del firewall nella VM o gateway inesistente |
| DNS non funzionante | Server DNS errato o non raggiungibile; risoluzione dei nomi alterata tramite il file `hosts` |
| Latenza, jitter e perdita di pacchetti | `tc netem` su una VM Linux che fa da router; su Windows strumenti come *clumsy* |
| Porte bloccate o servizi non in ascolto | Regole del firewall e arresto controllato dei servizi |

Gli stessi test vengono eseguiti su **Windows** e su **Ubuntu**.

## Uso responsabile
Le funzioni di analisi della rete devono essere utilizzate **esclusivamente su reti e sistemi di propria proprietà o per i quali si dispone di un'autorizzazione esplicita**.

## Licenza
Distribuito con licenza [MIT](LICENSE).

---

*Il nome.* Il *vallum*, in latino, era il terrapieno difensivo che circondava gli accampamenti militari romani: un argine di terra coronato da una palizzata di pali appuntiti (*valli*, da *vallus*, "palo") e preceduto da un fossato. Dalla stessa parola derivano l'italiano *vallo*, come nel Vallo di Adriano, e l'inglese *wall*. Come il vallum delimitava e proteggeva l'accampamento, questo strumento osserva e verifica il perimetro del proprio sistema e della propria rete.
