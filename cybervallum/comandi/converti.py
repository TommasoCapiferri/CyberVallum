"""Commands of the `converti` module: `vallum converti numero|ip|mac`."""

from __future__ import annotations

from typing import Any

import typer

from cybervallum.comandi._comune import JsonOpt, finish
from cybervallum.core import registry

app = typer.Typer(help="Conversioni tra basi numeriche, indirizzi IPv4 e MAC.", no_args_is_help=True)


def _print_numero(dati: dict[str, Any]) -> None:
    typer.echo(f"Decimale: {dati['decimale']}")
    typer.echo(f"Binario: {dati['binario']} ({dati['bit']} bit)")
    typer.echo(f"Esadecimale: {dati['esadecimale']}")


@app.command("numero")
def converti_numero(
    valore: str = typer.Argument(..., help="Numero: 255, 0xFF o 0b1010"),
    as_json: bool = JsonOpt,
) -> None:
    """Converte un numero tra decimale, binario ed esadecimale."""
    finish(registry.run("converti.numero", {"valore": valore}), as_json, _print_numero)


def _print_ip(dati: dict[str, Any]) -> None:
    tipo = "privato" if dati["privato"] else "pubblico"
    typer.echo(f"Indirizzo: {dati['indirizzo']} ({tipo})")
    typer.echo(f"Binario: {dati['binario']}")
    typer.echo(f"Esadecimale: {dati['esadecimale']}")
    typer.echo(f"Intero: {dati['intero']}")


@app.command("ip")
def converti_ip(
    indirizzo: str = typer.Argument(..., help="Indirizzo IPv4, es. 192.168.1.10"),
    as_json: bool = JsonOpt,
) -> None:
    """Mostra un indirizzo IPv4 in binario, esadecimale e come intero."""
    finish(registry.run("converti.ip", {"indirizzo": indirizzo}), as_json, _print_ip)


def _print_mac(dati: dict[str, Any]) -> None:
    typer.echo(f"MAC: {dati['mac']}")
    typer.echo(f"Binario: {dati['binario']}")
    typer.echo(f"OUI (produttore): {dati['oui']}")
    tipo = "unicast" if dati["unicast"] else "multicast"
    amministrato = "amministrato localmente" if dati["amministrato_localmente"] else "universale (assegnato dal produttore)"
    typer.echo(f"Tipo: {tipo}, {amministrato}")


@app.command("mac")
def converti_mac(
    indirizzo: str = typer.Argument(..., help="Indirizzo MAC, es. 00:1A:2B:3C:4D:5E"),
    as_json: bool = JsonOpt,
) -> None:
    """Mostra un indirizzo MAC in binario, con OUI e tipo."""
    finish(registry.run("converti.mac", {"indirizzo": indirizzo}), as_json, _print_mac)
