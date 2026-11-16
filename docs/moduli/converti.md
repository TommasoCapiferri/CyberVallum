# Modulo `converti`

Conversioni tra basi numeriche e rappresentazione degli indirizzi IPv4 e MAC. Azioni in sola lettura; un input non valido dà `stato` = `errore` con il messaggio in italiano. Scritto dall'AI locale in due giri (prompt in [../prompts/converti-giro2.md](../prompts/converti-giro2.md)) e rivisto da Claude.

| Comando | Azione | Parametri |
|---|---|---|
| `vallum converti numero <valore> [--json]` | `converti.numero` | `valore`: `255`, `0xFF` o `0b1010`, intero non negativo |
| `vallum converti ip <indirizzo> [--json]` | `converti.ip` | `indirizzo`: solo IPv4 |
| `vallum converti mac <indirizzo> [--json]` | `converti.mac` | `indirizzo`: `00:1A:2B:3C:4D:5E`, `00-1a-2b-3c-4d-5e` o `001A.2B3C.4D5E` |

## `dati` delle azioni `converti.*`

Le producono `converti numero|ip|mac --json` e `check run converti.<azione> --json`. Il contenitore (`azione`, `stato`, `errore`...) è descritto in [../json.md](../json.md).

- `converti.numero`:
  `{"input": "0xFF", "decimale": 255, "binario": "11111111", "esadecimale": "FF", "bit": 8}`
- `converti.ip`:
  `{"indirizzo": "192.168.1.10", "intero": 3232235786, "binario": "11000000.10101000.00000001.00001010", "esadecimale": "C0.A8.01.0A", "privato": true}`
- `converti.mac`:
  `{"mac": "00:1A:2B:3C:4D:5E", "binario": "00000000:00011010:...", "oui": "00:1A:2B", "unicast": true, "amministrato_localmente": false}`
