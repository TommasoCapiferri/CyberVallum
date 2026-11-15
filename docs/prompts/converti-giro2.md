# Prompt per Gemma: modulo `converti`, giro 2

Prompt preparati da Claude il 16/11/2026 e provati prima su una copia del progetto (96 test superati alla fine). Si incollano in Cline, modalità **Act**, uno alla volta; dopo ogni messaggio si controlla che i risultati corrispondano a quelli attesi.

Stato: messaggi A (passi 1-2), B (passo 3) e C (passi 4-5, commit `eadee4a`) **fatti**. Restano D ed E. Dal messaggio D i controlli usano anche `scripts\verifica.py`.

Come sono scritti (vedi [../ai-locale.md](../ai-locale.md)): ogni modifica a un file esistente è "TESTO VECCHIO = una riga corta e unica, TESTO NUOVO = la stessa riga più le aggiunte"; i segnaposto `# STEP-...` rendono unico il punto da sostituire; ogni passo ha controlli con il risultato atteso.

## Messaggio C (passi 4 e 5)

```text
CONTESTO: stiamo completando il modulo converti. I passi 1, 2 e 3 sono GIÀ FATTI e verificati: in cybervallum\cli.py esistono già converti_app, _print_numero e il comando "numero". NON rifarli e non toccare quel codice.
Prima di iniziare leggi cybervallum\cli.py con read_files e verifica che le righe "# STEP-4-IP" e "# STEP-5-MAC" compaiano UNA volta ciascuna. Se no, FERMATI e dimmelo senza modificare nulla.

Ora DUE passi. Regole: controllo dopo ciascuno; se un controllo fallisce FERMATI; se l'editor dice che il testo da sostituire non è unico o non esiste, FERMATI (non allargare la ricerca e non scegliere tu quale copia modificare).

PASSO 4. File cybervallum\cli.py: sostituisci SOLO la riga "# STEP-4-IP" con:

def _print_ip(dati: dict[str, Any]) -> None:
    tipo = "privato" if dati["privato"] else "pubblico"
    typer.echo(f"Indirizzo: {dati['indirizzo']} ({tipo})")
    typer.echo(f"Binario: {dati['binario']}")
    typer.echo(f"Esadecimale: {dati['esadecimale']}")
    typer.echo(f"Intero: {dati['intero']}")


@converti_app.command("ip")
def converti_ip(
    indirizzo: str = typer.Argument(..., help="Indirizzo IPv4, es. 192.168.1.10"),
    as_json: bool = JsonOpt,
) -> None:
    """Mostra un indirizzo IPv4 in binario, esadecimale e come intero."""
    _finish(registry.run("converti.ip", {"indirizzo": indirizzo}), as_json, _print_ip)

Controllo del passo 4:
- .venv\Scripts\python -m py_compile cybervallum\cli.py   (atteso: exit code 0)
- .venv\Scripts\vallum converti ip 192.168.1.10   (atteso: 4 righe, la prima "Indirizzo: 192.168.1.10 (privato)")

PASSO 5. File cybervallum\cli.py: sostituisci SOLO la riga "# STEP-5-MAC" con una funzione _print_mac(dati) e un comando "mac", sullo STESSO SCHEMA del passo 4:
- _print_mac stampa 4 righe:
    MAC: <dati['mac']>
    Binario: <dati['binario']>
    OUI (produttore): <dati['oui']>
    Tipo: <"unicast" se dati["unicast"] altrimenti "multicast">, <"amministrato localmente" se dati["amministrato_localmente"] altrimenti "universale (assegnato dal produttore)">
- il comando: @converti_app.command("mac"), funzione converti_mac con argomento indirizzo (help "Indirizzo MAC, es. 00:1A:2B:3C:4D:5E") e as_json: bool = JsonOpt; docstring """Mostra un indirizzo MAC in binario, con OUI e tipo."""; chiama registry.run("converti.mac", {"indirizzo": indirizzo}) e passa _print_mac a _finish.
Due righe vuote tra _print_mac e il comando.

Controllo del passo 5:
- .venv\Scripts\python -m py_compile cybervallum\cli.py   (atteso: exit code 0)
- .venv\Scripts\vallum converti mac 02-00-00-00-00-01   (atteso: ultima riga "Tipo: unicast, amministrato localmente")
- .venv\Scripts\vallum converti ip ciao   (atteso: "ERRORE: indirizzo IPv4 non valido: 'ciao'" ed exit code 1: è un errore VOLUTO, va bene così)
- .venv\Scripts\python -m pytest -q   (atteso: 91 passed)
Poi rileggi cli.py con read_files e verifica che: non ci siano righe "# STEP-"; "def converti_numero" compaia UNA sola volta; "def converti_ip" e "def converti_mac" compaiano una volta ciascuna.
Se una modifica è riuscita non ripeterla. Se stai per rifare la stessa modifica per la terza volta, FERMATI.

Riportami exit code e output di ogni controllo, poi FERMATI.
```

## Messaggio D (passo 6)

```text
CONTESTO: stiamo completando il modulo converti. I passi 1-5 sono GIÀ FATTI e verificati: in cybervallum\cli.py esistono i comandi "converti numero", "converti ip" e "converti mac". NON toccare cli.py. Ora i test della CLI: modifica SOLO tests\test_converti.py.
Prima di iniziare esegui .venv\Scripts\python scripts\verifica.py (atteso: "VERIFICA: OK" e "91 passed"). Se no, FERMATI e mostrami l'output senza modificare nulla.
Regole: se l'editor dice che il testo da sostituire non è unico o non esiste, FERMATI. Se una modifica è riuscita non ripeterla.

PASSO 6. Tre sostituzioni.
6a) TESTO VECCHIO:
import pytest
    TESTO NUOVO:
import json

import pytest
from typer.testing import CliRunner

6b) TESTO VECCHIO:
from cybervallum.core import converti, registry
    TESTO NUOVO:
from cybervallum import cli
from cybervallum.core import converti, registry

6c) TESTO VECCHIO:
def test_registry_ok():
    TESTO NUOVO:
def test_cli_numero_json():
    result = CliRunner().invoke(cli.app, ["converti", "numero", "0xFF", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["azione"] == "converti.numero"
    assert data["dati"]["decimale"] == 255


def test_cli_numero_testo():
    result = CliRunner().invoke(cli.app, ["converti", "numero", "0xFF"])
    assert result.exit_code == 0
    assert "Binario: 11111111 (8 bit)" in result.stdout


def test_cli_ip_errore():
    result = CliRunner().invoke(cli.app, ["converti", "ip", "ciao", "--json"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["stato"] == "errore"


def test_cli_mac_testo():
    result = CliRunner().invoke(cli.app, ["converti", "mac", "02-00-00-00-00-01"])
    assert result.exit_code == 0
    assert "amministrato localmente" in result.stdout


def test_cli_azioni_e_suite_registrate():
    result = CliRunner().invoke(cli.app, ["check", "list", "--json"])
    nomi = {a["nome"] for a in json.loads(result.stdout)["azioni"]}
    assert {"converti.numero", "converti.ip", "converti.mac"} <= nomi
    assert "converti" in {s["nome"] for s in registry.list_suites()}


def test_registry_ok():

Controllo del passo 6:
- .venv\Scripts\python -m py_compile tests\test_converti.py   (atteso: exit code 0)
- .venv\Scripts\python -m pytest -q tests\test_converti.py   (atteso: 38 passed)
- .venv\Scripts\python -m pytest -q   (atteso: 96 passed)
- .venv\Scripts\vallum test run converti   (atteso: "Suite converti: ok - passati 38")
- .venv\Scripts\python scripts\verifica.py   (atteso: "VERIFICA: OK" e "96 passed")

Riportami exit code e ultime righe di ogni controllo, poi FERMATI.
```

## Messaggio E (passo 7)

````text
CONTESTO: stiamo completando il modulo converti. I passi 1-6 sono GIÀ FATTI e verificati (comandi e test). Ultimo passo: la documentazione. Modifica SOLO docs\json.md.
Regole: se l'editor dice che il testo da sostituire non è unico o non esiste, FERMATI. Se una modifica è riuscita non ripeterla.

PASSO 7. Una sostituzione.
TESTO VECCHIO:
## Elenco delle azioni: `check list --json`
TESTO NUOVO:
### `dati` delle azioni `converti.*`

Le producono `converti numero|ip|mac --json` e `check run converti.<azione> --json`. Azioni in sola lettura; un input non valido dà `stato` = `errore` con il messaggio in italiano.

- `converti.numero` (parametro `valore`: `255`, `0xFF` o `0b1010`, intero non negativo):
  `{"input": "0xFF", "decimale": 255, "binario": "11111111", "esadecimale": "FF", "bit": 8}`
- `converti.ip` (parametro `indirizzo`, solo IPv4):
  `{"indirizzo": "192.168.1.10", "intero": 3232235786, "binario": "11000000.10101000.00000001.00001010", "esadecimale": "C0.A8.01.0A", "privato": true}`
- `converti.mac` (parametro `indirizzo`, formati `00:1A:2B:3C:4D:5E`, `00-1a-2b-3c-4d-5e`, `001A.2B3C.4D5E`):
  `{"mac": "00:1A:2B:3C:4D:5E", "binario": "00000000:00011010:...", "oui": "00:1A:2B", "unicast": true, "amministrato_localmente": false}`

## Elenco delle azioni: `check list --json`

Controllo: rileggi docs\json.md con read_files e verifica che la nuova sezione sia tra "### `dati` di `sistema.info`" e "## Elenco delle azioni", e che "## Elenco delle azioni" compaia UNA sola volta. Poi esegui .venv\Scripts\python scripts\verifica.py (atteso: "VERIFICA: OK").
Riportami l'esito e FERMATI. Non fare commit.
````

## Dopo il messaggio E
Revisione di Claude: `git diff`, pytest (96 attesi), prova dei comandi `vallum converti ...`, aggiornamento di README ("Funzionalità disponibili"), `PROGETTO.md` e `docs/ai-locale.md`, commit `[claude]` e push.
