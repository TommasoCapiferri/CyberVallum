"""Helpers shared by every command group: the --json option, output and exit codes.

Command files contain NO logic: they call `core.registry` and print the result,
human-readable or as stable JSON with `--json` (schema in docs/json.md).
"""

from __future__ import annotations

import json
from typing import Any, Callable

import typer

JsonOpt = typer.Option(False, "--json", help="Output in JSON stabile (vedi docs/json.md).")

# 0 = ok, 1 = error or failed tests, 2 = refused (missing confirmation).
EXIT_CODES = {"ok": 0, "errore": 1, "fallito": 1, "rifiutato": 2}


def print_json(data: Any) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def finish(result: dict[str, Any], as_json: bool, human: Callable[[Any], None] | None = None) -> None:
    """Print an action envelope and exit with the matching code."""
    if as_json:
        print_json(result)
    elif result["stato"] == "ok":
        if human is not None:
            human(result["dati"])
        else:
            prefix = "[simulazione] " if result.get("dry_run") else ""
            typer.echo(f"{prefix}{result['azione']}: completato in {result['durata_s']} s")
            typer.echo(json.dumps(result["dati"], ensure_ascii=False, indent=2, default=str))
    else:
        typer.echo(f"{result['stato'].upper()}: {result['errore']}", err=True)
    raise typer.Exit(EXIT_CODES.get(result["stato"], 1))
