from pathlib import Path

import pytest

from cybersegugio.core.registry import Param, Registry, RegistryError

ENVELOPE_KEYS = {"azione", "stato", "modifica_sistema", "dry_run", "durata_s", "dati", "errore"}
SUITE_KEYS = {"suite", "stato", "durata_s", "passati", "falliti", "saltati", "dettagli", "errore"}


@pytest.fixture
def reg():
    """An empty registry, independent from the application one."""
    r = Registry()

    @r.action("demo.somma", "Somma due numeri",
              params={"a": Param(int, required=True), "b": Param(int, default=10)})
    def somma(a, b):
        return {"risultato": a + b}

    @r.action("demo.rompi", "Solleva un'eccezione")
    def rompi():
        raise RuntimeError("guasto simulato")

    calls = []

    @r.action("demo.cancella", "Azione che modifica il sistema", modifica_sistema=True)
    def cancella(dry_run):
        calls.append(dry_run)
        return {"cancellato": not dry_run}

    r.calls = calls
    return r


def test_run_ok_envelope(reg):
    result = reg.run("demo.somma", {"a": "5"})
    assert set(result) == ENVELOPE_KEYS
    assert result["stato"] == "ok"
    assert result["dati"] == {"risultato": 15}
    assert result["errore"] is None
    assert result["dry_run"] is False


def test_unknown_action(reg):
    result = reg.run("demo.nonce")
    assert set(result) == ENVELOPE_KEYS
    assert result["stato"] == "errore"
    assert "sconosciuta" in result["errore"]


def test_parameter_errors(reg):
    assert "mancante" in reg.run("demo.somma")["errore"]
    assert "sconosciuti" in reg.run("demo.somma", {"a": 1, "c": 2})["errore"]
    assert "intero" in reg.run("demo.somma", {"a": "tre"})["errore"]


def test_exception_becomes_error_envelope(reg):
    result = reg.run("demo.rompi")
    assert result["stato"] == "errore"
    assert "guasto simulato" in result["errore"]


def test_system_changes_are_dry_run_by_default(reg):
    result = reg.run("demo.cancella")
    assert result["stato"] == "ok"
    assert result["dry_run"] is True
    assert result["dati"] == {"cancellato": False}
    assert reg.calls == [True]


def test_real_execution_needs_confirmation(reg):
    refused = reg.run("demo.cancella", dry_run=False)
    assert refused["stato"] == "rifiutato"
    assert reg.calls == []  # the function was never called

    done = reg.run("demo.cancella", dry_run=False, conferma=True)
    assert done["stato"] == "ok"
    assert done["dry_run"] is False
    assert reg.calls == [False]


def test_list_actions_describes_params(reg):
    actions = {a["nome"]: a for a in reg.list_actions()}
    assert actions["demo.somma"]["modulo"] == "demo"
    assert actions["demo.somma"]["parametri"]["a"] == {
        "tipo": "int", "predefinito": None, "obbligatorio": True, "descrizione": "",
    }
    assert actions["demo.cancella"]["modifica_sistema"] is True


@pytest.mark.parametrize("name", ["senza_punto", "Demo.Maiuscole", "a.b.c", "demo."])
def test_invalid_names(reg, name):
    with pytest.raises(RegistryError):
        reg.action(name, "x")(lambda: None)


def test_duplicate_and_reserved_param(reg):
    with pytest.raises(RegistryError):
        reg.action("demo.somma", "doppia")(lambda: None)
    with pytest.raises(RegistryError):
        reg.action("demo.x", "x", params={"dry_run": Param(bool)}, modifica_sistema=True)(lambda: None)


# --- Test suites (pytest is replaced by a fake runner: no real subprocess) ----------

JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="3">
  <testcase classname="tests.test_a" name="test_ok"/>
  <testcase classname="tests.test_a" name="test_ko"><failure message="assert 1 == 2"/></testcase>
  <testcase classname="tests.test_a" name="test_skip"><skipped message="non su Windows"/></testcase>
</testsuite></testsuites>"""


def _fake_runner(xml, code, seen=None):
    def runner(paths, junit_path: Path, cwd: Path):
        if seen is not None:
            seen.append((paths, cwd))
        if xml is not None:
            junit_path.write_text(xml, encoding="utf-8")
        return code
    return runner


@pytest.fixture
def suite_reg(tmp_path):
    (tmp_path / "tests").mkdir()
    r = Registry()
    r.project_root = tmp_path
    r.add_suite("unit", "Test unitari", ["tests"])
    return r


def test_run_suite_parses_report(suite_reg, tmp_path):
    seen = []
    suite_reg.pytest_runner = _fake_runner(JUNIT, 1, seen)
    result = suite_reg.run_suite("unit")
    assert set(result) == SUITE_KEYS
    assert result["stato"] == "fallito"
    assert (result["passati"], result["falliti"], result["saltati"]) == (1, 1, 1)
    failed = [d for d in result["dettagli"] if d["esito"] == "fallito"]
    assert failed == [{"test": "tests.test_a::test_ko", "esito": "fallito", "messaggio": "assert 1 == 2"}]
    assert seen == [(["tests"], tmp_path)]


def test_run_suite_all_passed(suite_reg):
    xml = '<testsuites><testsuite><testcase classname="t" name="a"/></testsuite></testsuites>'
    suite_reg.pytest_runner = _fake_runner(xml, 0)
    result = suite_reg.run_suite("unit")
    assert result["stato"] == "ok" and result["passati"] == 1 and result["errore"] is None


def test_run_suite_errors(suite_reg):
    assert suite_reg.run_suite("nessuna")["stato"] == "errore"

    suite_reg.pytest_runner = _fake_runner(None, 4)  # pytest crashed, no report
    result = suite_reg.run_suite("unit")
    assert result["stato"] == "errore" and "report" in result["errore"]

    suite_reg.pytest_runner = _fake_runner("<non xml", 1)
    assert "non leggibile" in suite_reg.run_suite("unit")["errore"]

    suite_reg.add_suite("assente", "Percorso mancante", ["tests/test_nonce.py"])
    assert "non trovati" in suite_reg.run_suite("assente")["errore"]


def test_duplicate_suite(suite_reg):
    with pytest.raises(RegistryError):
        suite_reg.add_suite("unit", "doppia", ["tests"])
