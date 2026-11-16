# Prompt per Gemma: modulo `processi` (parte in sola lettura)

Primo lavoro di Gemma nella sua **area** (vedi "Area dell'AI locale" in `PROGETTO.md`), preparato da Claude il 16/11/2026.

- **Dove:** cartella `..\CyberVallum-locale`, ramo `locale/processi`. In VS Code: *File → Open Folder* su quella cartella, poi Cline in modalità **Act**, un **task nuovo** per ogni messaggio (i messaggi sono autosufficienti).
- **Gradino di autonomia 3:** firme, campi JSON, regole e risultati attesi; il codice lo scrive Gemma. Fanno eccezione lo scheletro (passo 1) e l'adattatore di `psutil` (passo 2), dati per intero.
- **Giudice:** `.venv\Scripts\python scripts\verifica.py --area processi` dopo ogni passo. Il verificatore blocca da solo i file fuori area e il codice che modifica il sistema.
- **Dopo ogni messaggio** lo sviluppatore incolla la risposta a Claude, che controlla il diff (`git diff` nella cartella di Gemma) e fa il commit `[locale]` sul ramo.

Stato: nessun messaggio ancora inviato.

## Messaggio A (passo 1: scheletro dei quattro file)

```text
CONTESTO: sei nella cartella CyberVallum-locale, ramo locale/processi. Stai iniziando un modulo NUOVO, "processi". Un modulo è fatto di quattro file, e sono gli UNICI che puoi creare o modificare (gli altri sono comuni: non toccarli). In questo passo crei i quattro file come scheletro minimo.
Prima di iniziare esegui .venv\Scripts\python scripts\verifica.py --area processi (atteso: "VERIFICA: OK" e "121 passed"). Se no, FERMATI e mostrami l'output senza modificare nulla.
Regole: crea i file SOLO con editor; se un file esiste già, FERMATI e dimmelo.

PASSO 1. Crea questi quattro file con ESATTAMENTE questo contenuto.

File cybervallum\core\processi.py:
"""Running processes: list, sort and search (read only)."""

from __future__ import annotations

File cybervallum\comandi\processi.py:
"""Commands of the `processi` module: `vallum processi elenco|cerca`."""

from __future__ import annotations

import typer

app = typer.Typer(help="Processi attivi: elenco, ordinamento e ricerca.", no_args_is_help=True)

File tests\test_processi.py:
"""Tests of the `processi` module, with psutil replaced by fake data."""

File docs\moduli\processi.md:
# Modulo `processi`

Processi attivi: elenco, ordinamento e ricerca. Azioni in sola lettura.

Controllo del passo 1:
- .venv\Scripts\python scripts\verifica.py --area processi   (atteso: "VERIFICA: OK" e "121 passed"; nella riga "area del modulo processi" deve esserci [OK])
- .venv\Scripts\vallum --help   (atteso: nell'elenco dei comandi compare "processi")

Riportami exit code e ultime righe di ogni controllo, poi FERMATI.
```

## Messaggio B (passo 2: le funzioni del core)

```text
CONTESTO: modulo "processi", cartella CyberVallum-locale, ramo locale/processi. Il passo 1 è FATTO: esistono i quattro file del modulo come scheletro. Ora scrivi le funzioni in cybervallum\core\processi.py. Modifica SOLO quel file.
Prima di iniziare esegui .venv\Scripts\python scripts\verifica.py --area processi (atteso: "VERIFICA: OK"). Se no, FERMATI.
Modello da leggere (NON modificare): cybervallum\core\converti.py, per lo stile e per come si registrano le azioni.

PASSO 2. In cybervallum\core\processi.py scrivi:

2a) Gli import: "from typing import Any", "import psutil", "from cybervallum.core import registry".

2b) L'adattatore, che i test sostituiranno. Copialo ESATTAMENTE così, senza aggiungere logica:

def _read_processes() -> list[dict[str, Any]]:
    """Raw data of the running processes (replaced in tests)."""
    attrs = ["pid", "name", "username", "memory_info", "cpu_percent"]
    return [p.info for p in psutil.process_iter(attrs=attrs)]

Ogni elemento è un dizionario con le chiavi pid, name, username, memory_info, cpu_percent. Ognuna può valere None (processo di un altro utente). memory_info, se c'è, ha l'attributo rss (byte di memoria).

2c) La costante ORDINAMENTI = ("memoria", "cpu", "nome", "pid").

2d) Una funzione privata _riga(info) che trasforma un elemento grezzo in:
{"pid": int, "nome": str o None, "utente": str o None, "memoria_byte": int o None, "cpu_percentuale": float o None}
(memoria_byte = info["memory_info"].rss se memory_info non è None, altrimenti None).

2e) def elenco(ordina: str = "memoria", limite: int = 20) -> dict[str, Any]:
- ordina non in ORDINAMENTI -> ValueError("ordinamento non valido: 'x' (ammessi: memoria, cpu, nome, pid)") con al posto di x il valore ricevuto;
- limite minore di 1 o maggiore di 500 -> ValueError("limite non valido: 0 (da 1 a 500)") con il valore ricevuto;
- ordinamento: memoria e cpu dal più grande al più piccolo; nome in ordine alfabetico senza distinguere maiuscole e minuscole; pid dal più piccolo; i valori None vanno SEMPRE in fondo;
- restituisce {"ordinati_per": ordina, "totale": <numero di processi prima del limite>, "mostrati": <numero dopo il limite>, "processi": [<righe, al massimo limite>]}.

2f) def cerca(testo: str, limite: int = 20) -> dict[str, Any]:
- testo vuoto o solo spazi -> ValueError("testo di ricerca vuoto");
- limite come in elenco;
- tiene i processi il cui nome contiene il testo, senza distinguere maiuscole e minuscole (i nomi None non corrispondono mai), ordinati per memoria come in elenco;
- restituisce {"testo": testo senza spazi ai lati, "totale": ..., "mostrati": ..., "processi": [...]}.

2g) Due azioni nel registro, come in converti.py, con modifica_sistema NON indicato (quindi False):
- "processi.elenco", descrizione "Elenca i processi attivi, ordinati per memoria, CPU, nome o PID", params ordina = registry.Param(str, default="memoria", description="memoria, cpu, nome o pid") e limite = registry.Param(int, default=20, description="Quanti processi mostrare (da 1 a 500)"); chiama elenco.
- "processi.cerca", descrizione "Cerca i processi per nome", params testo = registry.Param(str, required=True, description="Parte del nome del processo") e limite come sopra; chiama cerca.

Controllo del passo 2:
- .venv\Scripts\python scripts\verifica.py --area processi   (atteso: "VERIFICA: OK", 121 passed)
- .venv\Scripts\vallum check run processi.elenco -p limite=3 --json   (atteso: "stato": "ok" e 3 processi)
- .venv\Scripts\vallum check run processi.elenco -p ordina=colore --json   (atteso: "stato": "errore" con "ordinamento non valido: 'colore' ..."; è un errore VOLUTO)
- .venv\Scripts\vallum check run processi.cerca -p testo=python --json   (atteso: "stato": "ok" e almeno un processo con "python" nel nome)

Riportami exit code e output di ogni controllo, poi FERMATI.
```

## Messaggio C (passo 3: i test)

```text
CONTESTO: modulo "processi", cartella CyberVallum-locale, ramo locale/processi. I passi 1 e 2 sono FATTI: cybervallum\core\processi.py ha elenco, cerca e le azioni processi.elenco e processi.cerca. Ora i test. Modifica SOLO tests\test_processi.py.
Prima di iniziare esegui .venv\Scripts\python scripts\verifica.py --area processi (atteso: "VERIFICA: OK", 121 passed). Se no, FERMATI.
Modello da leggere (NON modificare): tests\test_sistema.py, per come si sostituiscono i dati del sistema con monkeypatch.

PASSO 3. In tests\test_processi.py:
- una fixture "finti" che con monkeypatch sostituisce processi._read_processes con una funzione che restituisce SEMPRE questi 4 processi finti (memory_info si simula con types.SimpleNamespace(rss=...)):
  pid 10, name "python.exe", username "dev", rss 300, cpu 5.0
  pid 2, name "Code.exe", username "dev", rss 900, cpu 1.0
  pid 7, name "svchost.exe", username None, memory_info None, cpu None
  pid 4, name None, username None, rss 100, cpu 9.0
- un test per ognuno di questi comportamenti (attesi tra parentesi):
  1. elenco() per memoria (pid in ordine: 2, 10, 4, 7)
  2. elenco("cpu") (pid: 4, 10, 2, 7)
  3. elenco("nome") (pid: 2, 10, 7, 4: Code prima di python perché senza maiuscole/minuscole "code" < "python"; il nome None in fondo)
  4. elenco("pid") (pid: 2, 4, 7, 10)
  5. elenco(limite=2): totale 4, mostrati 2
  6. la riga del pid 7 ha memoria_byte None e utente None
  7. elenco("colore") solleva ValueError con "ordinamento non valido"
  8. elenco(limite=0) e elenco(limite=501) sollevano ValueError con "limite non valido" (usa pytest.mark.parametrize)
  9. cerca("PYTHON") trova solo il pid 10
  10. cerca("  exe ") trova 3 processi e "testo" vale "exe"
  11. cerca("   ") solleva ValueError con "testo di ricerca vuoto"
  12. registry.run("processi.elenco", {"limite": "2"}) ha stato "ok" e 2 processi (il registro converte "2" in intero)
  13. registry.run("processi.cerca", {}) ha stato "errore" (testo obbligatorio)
- nessun test deve leggere i processi veri del PC: tutti usano la fixture.

Controllo del passo 3:
- .venv\Scripts\python -m pytest -q tests\test_processi.py   (atteso: almeno 14 passed, 0 failed)
- .venv\Scripts\python scripts\verifica.py --area processi   (atteso: "VERIFICA: OK" e almeno 135 passed)

Riportami exit code e ultime righe di ogni controllo, poi FERMATI.
```

## Messaggio D (passi 4 e 5: comandi e documentazione)

```text
CONTESTO: modulo "processi", cartella CyberVallum-locale, ramo locale/processi. I passi 1-3 sono FATTI (core e test). Ora i comandi e la documentazione. Modifica SOLO cybervallum\comandi\processi.py e docs\moduli\processi.md.
Prima di iniziare esegui .venv\Scripts\python scripts\verifica.py --area processi (atteso: "VERIFICA: OK"). Se no, FERMATI.
Modelli da leggere (NON modificare): cybervallum\comandi\converti.py e docs\moduli\converti.md.

PASSO 4. In cybervallum\comandi\processi.py, sullo stesso schema di comandi\converti.py (import di Any, JsonOpt, finish e registry come lì):
- una funzione _print_processi(dati) che stampa:
  una riga di intestazione: "PID      MEMORIA (MB)  CPU %  NOME"
  una riga per processo: pid, memoria in MB con una cifra decimale (memoria_byte / 1024**2), cpu con una cifra decimale, nome; "n/d" al posto dei valori None
  una riga finale: "Mostrati <mostrati> processi su <totale>"
- comando "elenco" (funzione processi_elenco): opzioni --ordina (str, predefinito "memoria", help "memoria, cpu, nome o pid"), --limite (int, predefinito 20, help "Quanti processi mostrare (da 1 a 500)") e as_json: bool = JsonOpt; docstring """Elenca i processi attivi, ordinati per memoria, CPU, nome o PID."""; chiama registry.run("processi.elenco", {"ordina": ordina, "limite": limite}).
- comando "cerca" (funzione processi_cerca): argomento testo (help "Parte del nome del processo"), opzione --limite come sopra, as_json; docstring """Cerca i processi per nome."""; chiama registry.run("processi.cerca", {"testo": testo, "limite": limite}).

PASSO 5. In docs\moduli\processi.md, sullo schema di docs\moduli\converti.md, aggiungi sotto il testo che c'è già:
- la tabella "Comando | Azione | Parametri" con i due comandi;
- la sezione "## `dati` delle azioni `processi.*`" con un esempio JSON di processi.elenco e uno di processi.cerca, presi dall'output VERO di "vallum processi elenco --limite 2 --json" e "vallum processi cerca python --limite 1 --json" (solo la parte "dati");
- una riga che dice che i campi possono valere null per i processi di altri utenti e che cpu_percentuale alla prima lettura può essere 0.

Controllo dei passi 4 e 5:
- .venv\Scripts\vallum processi elenco --limite 5   (atteso: intestazione, 5 righe, "Mostrati 5 processi su ...")
- .venv\Scripts\vallum processi elenco --ordina colore   (atteso: "ERRORE: ordinamento non valido..." ed exit code 1: errore VOLUTO)
- .venv\Scripts\vallum processi cerca python --json   (atteso: "stato": "ok")
- .venv\Scripts\python scripts\verifica.py --area processi   (atteso: "VERIFICA: OK")

Riportami exit code e ultime righe di ogni controllo, poi FERMATI. Non fare commit.
```

## Dopo il messaggio D
Revisione di Claude sull'intero ramo (`git diff main...locale/processi`), prova dei comandi, unione con `git merge --no-ff`, poi su `main`: test dei comandi della CLI se mancano, l'azione di chiusura dei processi con conferma (`modifica_sistema=True`, fuori area), l'elenco in `docs/json.md`, il README, `PROGETTO.md`, `docs/ai-locale.md` e un episodio per lo studio `Studio-AI-Locale`.
