"""Command line interface: `cybervallum <group> <command>`.

This file contains NO logic: it parses the command line, calls `core.registry`
(and through it `core.config`) and prints the result, either human-readable
or as stable JSON with `--json` (schema in docs/json.md).

Here live only the shared groups `config`, `check` and `test`. The commands of each
module are in `cybervallum/comandi/<modulo>.py` and are added automatically.

Exit codes: 0 = ok, 1 = error or failed tests, 2 = refused (missing confirmation).
"""

from __future__ import annotations

from typing import Any, Optional

import typer

from cybervallum import __version__, comandi
from cybervallum.comandi._comune import EXIT_CODES, JsonOpt, finish, format_value, print_json
from cybervallum.core import registry

app = typer.Typer(
    help="CyberVallum: sistemistica, sicurezza e controllo della rete.",
    no_args_is_help=True,
    add_completion=False,
)
config_app = typer.Typer(help="Impostazioni (config.toml).", no_args_is_help=True)
check_app = typer.Typer(help="Controlli registrati: elenco ed esecuzione.", no_args_is_help=True)
test_app = typer.Typer(help="Suite di test: elenco ed esecuzione.", no_args_is_help=True)
app.add_typer(config_app, name="config")
app.add_typer(check_app, name="check")
app.add_typer(test_app, name="test")

# Module command groups (cybervallum/comandi/<modulo>.py), found automatically.
for _name, _group in comandi.discover():
    app.add_typer(_group, name=_name)

# Short aliases used by the commands below.
_finish, _print_json, _format_value = finish, print_json, format_value


def _parse_params(items: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in items:
        key, sep, value = item.partition("=")
        if not sep or not key:
            raise typer.BadParameter(f"formato atteso chiave=valore, ricevuto {item!r}")
        params[key.strip()] = value
    return params


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"cybervallum {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True, help="Mostra la versione."
    ),
) -> None:
    registry.load_modules()


# --- config -------------------------------------------------------------------------

@config_app.command("list")
def config_list(as_json: bool = JsonOpt) -> None:
    """Elenca le impostazioni con valore, origine e descrizione."""

    def human(data: dict[str, Any]) -> None:
        typer.echo(f"File: {data['file']}")
        for s in data["impostazioni"]:
            mark = " (modificata)" if s["origine"] == "file" else ""
            typer.echo(f"  {s['chiave']} = {_format_value(s['valore'])}{mark}")
            typer.echo(f"      {s['descrizione']}")
            if s["errore"]:
                typer.echo(f"      ATTENZIONE: valore nel file non valido: {s['errore']}")

    _finish(registry.run("config.list"), as_json, human)


@config_app.command("get")
def config_get(chiave: str = typer.Argument(..., help="Chiave sezione.nome"), as_json: bool = JsonOpt) -> None:
    """Mostra il valore di un'impostazione."""
    _finish(registry.run("config.get", {"chiave": chiave}), as_json,
            lambda d: typer.echo(_format_value(d["valore"])))


@config_app.command("set")
def config_set(
    chiave: str = typer.Argument(..., help="Chiave sezione.nome"),
    valore: str = typer.Argument(..., help="Nuovo valore (liste separate da virgole)"),
    as_json: bool = JsonOpt,
) -> None:
    """Imposta e salva un'impostazione, dopo averla validata."""
    _finish(registry.run("config.set", {"chiave": chiave, "valore": valore}), as_json,
            lambda d: typer.echo(f"{d['chiave']} = {_format_value(d['valore'])} (salvato in {d['file']})"))


# --- check --------------------------------------------------------------------------

@check_app.command("list")
def check_list(as_json: bool = JsonOpt) -> None:
    """Elenca i controlli registrati."""
    actions = registry.list_actions()
    if as_json:
        _print_json({"azioni": actions})
        return
    for a in actions:
        flag = "  [modifica il sistema]" if a["modifica_sistema"] else ""
        typer.echo(f"{a['nome']}{flag}")
        typer.echo(f"    {a['descrizione']}")
        for pname, p in a["parametri"].items():
            req = "obbligatorio" if p["obbligatorio"] else f"predefinito: {p['predefinito']}"
            typer.echo(f"    -p {pname}=<{p['tipo']}>  {p['descrizione']} ({req})")


@check_app.command("run")
def check_run(
    nome: str = typer.Argument(..., help="Nome del controllo: modulo.azione"),
    param: list[str] = typer.Option([], "--param", "-p", help="Parametro chiave=valore (ripetibile)."),
    dry_run: bool = typer.Option(
        True, "--dry-run/--esegui",
        help="Per le azioni che modificano il sistema: simula (predefinito) o esegui davvero.",
    ),
    conferma: bool = typer.Option(False, "--conferma", help="Conferma l'esecuzione reale senza domanda."),
    as_json: bool = JsonOpt,
) -> None:
    """Esegue un controllo registrato."""
    params = _parse_params(param)
    action = registry.default_registry.get_action(nome)
    if action is not None and action.modifica_sistema and not dry_run and not conferma and not as_json:
        conferma = typer.confirm(f"{nome} modificherà il sistema. Procedere?", default=False)
    _finish(registry.run(nome, params, dry_run=dry_run, conferma=conferma), as_json)


# --- test ---------------------------------------------------------------------------

@test_app.command("list")
def test_list(as_json: bool = JsonOpt) -> None:
    """Elenca le suite di test registrate."""
    suites = registry.list_suites()
    if as_json:
        _print_json({"suite": suites})
        return
    for s in suites:
        typer.echo(f"{s['nome']}: {s['descrizione']} ({', '.join(s['percorsi'])})")


@test_app.command("run")
def test_run(suite: str = typer.Argument(..., help="Nome della suite"), as_json: bool = JsonOpt) -> None:
    """Esegue una suite di test e ne riporta l'esito."""
    result = registry.run_suite(suite)
    if as_json:
        _print_json(result)
    elif result["errore"]:
        typer.echo(f"ERRORE: {result['errore']}", err=True)
    else:
        for d in result["dettagli"]:
            if d["esito"] != "passato":
                typer.echo(f"  {d['esito'].upper()}: {d['test']}  {d['messaggio'] or ''}")
        typer.echo(
            f"Suite {result['suite']}: {result['stato']} - passati {result['passati']}, "
            f"falliti {result['falliti']}, saltati {result['saltati']} - {result['durata_s']} s"
        )
    raise typer.Exit(EXIT_CODES.get(result["stato"], 1))


if __name__ == "__main__":
    app()
