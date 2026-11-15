# CyberSegugio

Strumento da riga di comando, con interfaccia desktop in programma, per l'**analisi del sistema**, la **diagnostica di rete** e i **controlli di sicurezza** su Windows e Linux.
Raccoglie in un unico strumento le verifiche che un sistemista esegue di routine: risorse hardware, processi, connettività, dispositivi in rete, servizi e configurazione di sicurezza.

## Natura del progetto
CyberSegugio è un **progetto personale di studio**, con due obiettivi:
- **applicare in pratica** gli argomenti studiati su sistemi, reti e sicurezza: ciascun argomento diventa una funzione dello strumento;
- **sperimentare lo sviluppo software assistito dall'intelligenza artificiale**, combinando un modello eseguito in locale (Ollama con Gemma, tramite Cline in VS Code) per lo sviluppo quotidiano e Claude Code per l'architettura e la revisione del codice.

Non è un prodotto finito né un software destinato all'uso professionale: è un ambiente di sperimentazione che cresce in modo incrementale.

## Funzionalità disponibili
Il progetto è in fase iniziale e **non dispone ancora di funzionalità utilizzabili**.
Sono definiti la struttura, le regole di sviluppo e la roadmap.

## In sviluppo
| Modulo | Funzione |
|---|---|
| `sistema` | CPU, core, memoria, dischi, sistema operativo, ultimo avvio |

## Obiettivi
| Modulo | Funzione |
|---|---|
| `converti` | Conversioni tra binario, decimale ed esadecimale; rappresentazione degli indirizzi IP |
| `processi` | Processi attivi e consumo di risorse |
| `diagnosi` | Diagnosi della connettività: interfaccia di rete, gateway, Internet, DNS |
| `lan` | Rilevamento dei dispositivi della rete locale, calcolo delle sottoreti |
| `voip` | Analisi delle chiamate SIP/RTP da catture di rete |
| `servizi` | Servizi, log e utenti |
| `sicurezza` | Verifiche di hardening e porte in ascolto sul sistema locale |
| `ai` | Interrogazione dei risultati in linguaggio naturale tramite un modello locale |
| `gui` | Interfaccia desktop basata sullo stesso motore della riga di comando |

Lo stato dettagliato e il registro dello sviluppo sono disponibili in [PROGETTO.md](PROGETTO.md).

## Uso responsabile
Le funzioni di analisi della rete devono essere utilizzate **esclusivamente su reti e sistemi di propria proprietà o per i quali si dispone di un'autorizzazione esplicita**.

## Licenza
Distribuito con licenza [MIT](LICENSE).

---

*Dedicato a Titty, la mia cagnolina, a cui il progetto deve il nome.*
*Lei trova qualsiasi cosa nascosta in casa al primo colpo: questo strumento ha ancora molta strada da fare per raggiungerla.* 🐶
