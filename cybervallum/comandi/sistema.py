"""Commands of the `sistema` module: `vallum sistema info`."""

from __future__ import annotations

from typing import Any

import typer

from cybervallum.comandi._comune import JsonOpt, finish
from cybervallum.core import registry

app = typer.Typer(help="Informazioni sul sistema.", no_args_is_help=True)


def _nd(value: Any) -> str:
    """Show None as "n/d" (non disponibile)."""
    return "n/d" if value is None else str(value)


def _gb(n_bytes: int) -> str:
    return f"{n_bytes / 1024**3:.1f}"


def _print_sistema(dati: dict[str, Any]) -> None:
    so, cpu, mem, avvio = dati["sistema_operativo"], dati["cpu"], dati["memoria"], dati["avvio"]
    typer.echo(f"Sistema operativo: {_nd(so['nome'])} {_nd(so['release'])} "
               f"({_nd(so['architettura'])}), host {_nd(so['nome_host'])}")
    freq = "n/d" if cpu["frequenza_mhz"] is None else f"{cpu['frequenza_mhz']:.0f}"
    typer.echo(f"CPU: {_nd(cpu['modello'])}, {_nd(cpu['core_fisici'])} core fisici / "
               f"{_nd(cpu['core_logici'])} logici, {freq} MHz, uso {cpu['uso_percentuale']}%")
    typer.echo(f"Memoria: {_gb(mem['disponibile_byte'])} GB disponibili su {_gb(mem['totale_byte'])} GB "
               f"(usata {mem['usata_percentuale']}%)")
    for d in dati["dischi"]:
        typer.echo(f"Disco {d['dispositivo']} ({_nd(d['filesystem'])}): {_gb(d['libero_byte'])} GB liberi "
                   f"su {_gb(d['totale_byte'])} GB (usato {d['usato_percentuale']}%)")
    ore, resto = divmod(avvio["uptime_s"], 3600)
    typer.echo(f"Ultimo avvio: {avvio['ultimo_avvio']} (attivo da {ore} h {resto // 60} min)")


@app.command("info")
def sistema_info(as_json: bool = JsonOpt) -> None:
    """Mostra CPU, memoria, dischi, sistema operativo e ultimo avvio."""
    finish(registry.run("sistema.info"), as_json, _print_sistema)
