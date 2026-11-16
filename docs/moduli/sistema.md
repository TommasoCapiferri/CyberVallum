# Modulo `sistema`

Informazioni sul computer: sistema operativo, CPU, memoria, dischi e ultimo avvio. Azione in sola lettura.

| Comando | Azione | Parametri |
|---|---|---|
| `vallum sistema info [--json]` | `sistema.info` | nessuno |

## `dati` di `sistema.info`

Lo producono `sistema info --json` e `check run sistema.info --json`. Il contenitore (`azione`, `stato`, `errore`...) è descritto in [../json.md](../json.md).

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
