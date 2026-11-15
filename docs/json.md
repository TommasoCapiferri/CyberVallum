# Formato JSON dell'output

Ogni comando della CLI ha l'opzione `--json`. Il formato descritto qui è **stabile**: script, test, API e GUI possono basarsi su di esso. Una modifica incompatibile (un campo rimosso o rinominato) va annotata qui e nel registro di `PROGETTO.md`. I campi nuovi si possono aggiungere senza preavviso.

## Codici di uscita

| Codice | Significato |
|---|---|
| 0 | `ok` |
| 1 | `errore` (azione o suite) oppure `fallito` (test non superati) |
| 2 | `rifiutato` (azione che modifica il sistema senza conferma) oppure errore di sintassi del comando |

## Esito di un'azione

Lo producono `check run <modulo>.<azione> --json` e `config list|get|set --json`, che sono scorciatoie per le azioni `config.*`. È lo stesso dizionario restituito da `core.registry.run()`.

```json
{
  "azione": "config.get",
  "stato": "ok",
  "modifica_sistema": false,
  "dry_run": false,
  "durata_s": 0.001,
  "dati": { "chiave": "api.porta", "valore": 9000 },
  "errore": null
}
```

| Campo | Tipo | Note |
|---|---|---|
| `azione` | stringa | nome `<modulo>.<azione>` richiesto |
| `stato` | `ok` \| `errore` \| `rifiutato` | |
| `modifica_sistema` | bool | se l'azione può modificare il sistema |
| `dry_run` | bool | `true` se l'azione è stata solo simulata; sempre `false` per le azioni di sola lettura |
| `durata_s` | numero | secondi |
| `dati` | qualsiasi | risultato dell'azione (il formato dipende dal modulo, documentato nel modulo); `null` se c'è un errore |
| `errore` | stringa \| null | messaggio in italiano |

Le azioni con `modifica_sistema` sono simulate per impostazione predefinita. L'esecuzione reale richiede `--esegui --conferma`: con il solo `--esegui`, la CLI chiede conferma in modo interattivo, mentre con `--json` restituisce `rifiutato`.

### `dati` delle azioni `config.*`

- `config.list`: `{"file": "<percorso>", "impostazioni": [{"chiave", "valore", "predefinito", "tipo", "descrizione", "origine": "file"|"predefinito", "errore"}]}`
- `config.get`: `{"chiave", "valore"}`
- `config.set`: `{"chiave", "valore", "file"}`

### `dati` di `sistema.info`

Lo producono `sistema info --json` e `check run sistema.info --json`. Azione in sola lettura.

```json
{
  "sistema_operativo": { "nome": "Windows", "release": "11", "versione": "10.0.26200",
                         "architettura": "AMD64", "nome_host": "PC" },
  "cpu": { "modello": "...", "core_fisici": 8, "core_logici": 16,
           "frequenza_mhz": 3600.0, "uso_percentuale": 12.5 },
  "memoria": { "totale_byte": 34359738368, "disponibile_byte": 17179869184, "usata_percentuale": 50.0 },
  "dischi": [ { "dispositivo": "C:\\", "punto_montaggio": "C:\\", "filesystem": "NTFS",
                "totale_byte": 1000, "usato_byte": 400, "libero_byte": 600, "usato_percentuale": 40.0 } ],
  "avvio": { "ultimo_avvio": "2026-11-15T08:00:00+00:00", "uptime_s": 3600 }
}
```

- I byte sono interi, le percentuali numeri decimali, `ultimo_avvio` è una data ISO 8601 in UTC e `uptime_s` sono secondi interi.
- Valgono `null` quando il sistema non li fornisce: le stringhe di `sistema_operativo`, `cpu.modello`, `cpu.core_fisici`, `cpu.frequenza_mhz` e `dischi[].filesystem`.
- I dischi che non si possono leggere (per esempio un lettore CD vuoto) non compaiono nell'elenco.
- `cpu.modello` viene da `platform.processor()`: su Windows è la sigla tecnica (es. "AMD64 Family 25 Model 33..."), non il nome commerciale.

## Elenco delle azioni: `check list --json`

```json
{ "azioni": [ { "nome": "config.get", "modulo": "config", "descrizione": "...",
               "modifica_sistema": false,
               "parametri": { "chiave": { "tipo": "str", "predefinito": null,
                                          "obbligatorio": true, "descrizione": "..." } } } ] }
```

I tipi dei parametri sono `str`, `int`, `float`, `bool`, `list` (dalla CLI, valori separati da virgole) e `any`.

## Elenco delle suite: `test list --json`

```json
{ "suite": [ { "nome": "tutti", "descrizione": "...", "percorsi": ["tests"] } ] }
```

## Esito di una suite: `test run <suite> --json`

```json
{
  "suite": "tutti",
  "stato": "ok",
  "durata_s": 0.89,
  "passati": 49,
  "falliti": 0,
  "saltati": 0,
  "dettagli": [ { "test": "tests.test_cli::test_version", "esito": "passato", "messaggio": null } ],
  "errore": null
}
```

`stato` vale `ok`, `fallito` (almeno un test non superato) oppure `errore` (suite sconosciuta, percorsi mancanti, pytest non avviabile). `esito` vale `passato`, `fallito` oppure `saltato`.
