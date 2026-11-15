"""Command line interface: `cybervallum <group> <command>`.

This file contains NO logic: it parses the command line, calls `core.registry`
(and through it `core.config`) and prints the result, either human-readable
or as stable JSON with `--json` (schema in docs/json.md).

Exit codes: 0 = ok, 1 = error or failed tests, 2 = refused (missing confirmation).
"""

from __future__ import annotations

import json
from typing import Any, Optional

import typer

from cybervallum import __version__
from cybervallum.core import registry

app = typer.Typer(
    help="CyberVallum: sistemistica, sicurezza e controllo della rete.",
    no_args_is_help=True,
    add_completion=False,
)
config_app = typer.Typer(help="Impostazioni (config.toml).", no_args_is_help=True)
check_app = typer.Typer(help="Controlli registrati: elenco ed esecuzione.", no_args_is_help=True)
test_app = typer.Typer(help="Suite di test: elenco ed esecuzione.", no_args_is_help=True)
sistema_app = typer.Typer(help="Informazioni sul sistema.", no_args_is_help=True)
app.add_typer(config_app, name="config")
app.add_typer(check_app, name="check")
app.add_typer(test_app, name="test")
app.add_typer(sistema_app, name="sistema")
converti_app = typer.Typer(help="Conversioni tra basi numeriche, indirizzi IPv4 e MAC.", no_args_is_help=True)
app.add_typer(converti_app, name="converti")

JsonOpt = typer.Option(False, "--json", help="Output in JSON stabile (vedi docs/json.md).")

EXIT_CODES = {"ok": 0, "errore": 1, "fallito": 1, "rifiutato": 2}


# --- Output helpers -----------------------------------------------------------------

def _print_json(data: Any) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _finish(result: dict[str, Any], as_json: bool, human: Any = None) -> None:
    """Print an action envelope and exit with the matching code."""
    if as_json:
        _print_json(result)
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


# --- sistema ------------------------------------------------------------------------

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


@sistema_app.command("info")
def sistema_info(as_json: bool = JsonOpt) -> None:
    """Mostra CPU, memoria, dischi, sistema operativo e ultimo avvio."""
    _finish(registry.run("sistema.info"), as_json, _print_sistema)


# --- converti -----------------------------------------------------------------------

def _print_numero(dati: dict[str, Any]) -> None:
    typer.echo(f"Decimale: {dati['decimale']}")
    typer.echo(f"Binario: {dati['binario']} ({dati['bit']} bit)")
    typer.echo(f"Esadecimale: {dati['esadecimale']}")


@converti_app.command("numero")
def converti_numero(
    valore: str = typer.Argument(..., help="Numero: 255, 0xFF o 0b1010"),
    as_json: bool = JsonOpt,
) -> None:
    """Converte un numero tra decimale, binario ed esadecimale."""
    _finish(registry.run("converti.numero", {"valore": valore}), as_json, _print_numero)


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


def _print_mac(dati: dict[str, Any]) -> None:
    typer.echo(f"MAC: {dati['mac']}")
    typer.echo(f"Binario: {dati['binario']}")
    typer.echo(f"OUI (produttore): {dati['oui']}")
    tipo = "unicast" if dati["unicast"] else "multicast"
    amministrato = "amministrato localmente" if dati["amministrato_localmente"] else "universale (assegnato dal produttore)"
    typer.echo(f"Tipo: {tipo}, {amministrato}")


@converti_app.command("mac")
def converti_mac(
    indirizzo: str = typer.Argument(..., help="Indirizzo MAC, es. 00:1A:2B:3C:4D:5E"),
    as_json: bool = JsonOpt,
) -> None:
    """Mostra un indirizzo MAC in binario, con OUI e tipo."""
    _finish(registry.run("converti.mac", {"indirizzo": indirizzo}), as_json, _print_mac)


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
