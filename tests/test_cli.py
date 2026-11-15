"""CLI tests: the --json output must follow the schema in docs/json.md."""

import json

import pytest
from typer.testing import CliRunner

from cybersegugio import cli
from cybersegugio.core import registry
from cybersegugio.core.registry import Param

runner = CliRunner()


def invoke(*args, input=None):
    return runner.invoke(cli.app, list(args), input=input)


def as_json(result):
    return json.loads(result.stdout)


def test_version():
    result = invoke("--version")
    assert result.exit_code == 0 and "cybersegugio" in result.stdout


def test_config_set_get_list_json(isolated_config):
    result = invoke("config", "set", "api.porta", "9200", "--json")
    assert result.exit_code == 0
    data = as_json(result)
    assert data["stato"] == "ok" and data["dati"]["valore"] == 9200

    data = as_json(invoke("config", "get", "api.porta", "--json"))
    assert data["azione"] == "config.get" and data["dati"] == {"chiave": "api.porta", "valore": 9200}

    data = as_json(invoke("config", "list", "--json"))
    keys = {s["chiave"] for s in data["dati"]["impostazioni"]}
    assert {"api.porta", "api.host", "ai.provider"} <= keys
    assert data["dati"]["file"] == str(isolated_config)


def test_config_human_output():
    invoke("config", "set", "ai.provider", "claude")
    result = invoke("config", "get", "ai.provider")
    assert result.exit_code == 0 and result.stdout.strip() == "claude"


def test_config_invalid_value_exit_code():
    result = invoke("config", "set", "api.host", "0.0.0.0", "--json")
    assert result.exit_code == 1
    assert as_json(result)["stato"] == "errore"


def test_check_list_json_contains_config_actions():
    data = as_json(invoke("check", "list", "--json"))
    names = {a["nome"] for a in data["azioni"]}
    assert {"config.list", "config.get", "config.set"} <= names


def test_check_run_with_params():
    data = as_json(invoke("check", "run", "config.get", "-p", "chiave=api.host", "--json"))
    assert data["stato"] == "ok" and data["dati"]["valore"] == "127.0.0.1"


def test_check_run_bad_param_format():
    result = invoke("check", "run", "config.get", "-p", "senzauguale")
    assert result.exit_code == 2  # usage error from Typer


def test_check_run_unknown_action():
    result = invoke("check", "run", "nessuno.nulla", "--json")
    assert result.exit_code == 1
    assert as_json(result)["errore"].startswith("azione sconosciuta")


@pytest.fixture
def system_action():
    """Temporarily register an action that 'modifies the system' in the app registry."""
    calls = []

    def fake(dry_run, nome="x"):
        calls.append(dry_run)
        return {"nome": nome, "fatto": not dry_run}

    registry.default_registry.add_action(
        registry.Action("prova.modifica", fake, "Azione di prova",
                        {"nome": Param(str, default="x")}, modifica_sistema=True)
    )
    yield calls
    registry.default_registry._actions.pop("prova.modifica")


def test_system_action_dry_run_by_default(system_action):
    data = as_json(invoke("check", "run", "prova.modifica", "--json"))
    assert data["dry_run"] is True and data["dati"]["fatto"] is False
    assert system_action == [True]


def test_system_action_refused_without_confirmation(system_action):
    result = invoke("check", "run", "prova.modifica", "--esegui", "--json")
    assert result.exit_code == 2
    assert as_json(result)["stato"] == "rifiutato"
    assert system_action == []


def test_system_action_interactive_confirmation(system_action):
    declined = invoke("check", "run", "prova.modifica", "--esegui", input="n\n")
    assert declined.exit_code == 2 and system_action == []
    accepted = invoke("check", "run", "prova.modifica", "--esegui", input="y\n")
    assert accepted.exit_code == 0 and system_action == [False]


def test_system_action_with_confirm_flag(system_action):
    data = as_json(invoke("check", "run", "prova.modifica", "--esegui", "--conferma", "--json"))
    assert data["stato"] == "ok" and data["dry_run"] is False


def test_test_list_json():
    data = as_json(invoke("test", "list", "--json"))
    assert {"tutti", "config", "registry", "cli"} <= {s["nome"] for s in data["suite"]}


def test_test_run_json_uses_registry(monkeypatch):
    xml = '<testsuites><testsuite><testcase classname="t" name="a"/></testsuite></testsuites>'

    def fake_runner(paths, junit_path, cwd):
        junit_path.write_text(xml, encoding="utf-8")
        return 0

    monkeypatch.setattr(registry.default_registry, "pytest_runner", fake_runner)
    result = invoke("test", "run", "config", "--json")
    assert result.exit_code == 0
    data = as_json(result)
    assert data["suite"] == "config" and data["stato"] == "ok" and data["passati"] == 1


def test_test_run_unknown_suite():
    result = invoke("test", "run", "nessuna", "--json")
    assert result.exit_code == 1 and as_json(result)["stato"] == "errore"
