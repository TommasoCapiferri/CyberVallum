"""Architecture contract: every module is complete and lives only in its own files.

A module <m> is made of four files, and nothing else is needed to add it:
    cybervallum/core/<m>.py, cybervallum/comandi/<m>.py, tests/test_<m>.py, docs/moduli/<m>.md
(see "Area dell'AI locale" in PROGETTO.md).
"""

from pathlib import Path

import pytest

from cybervallum import cli, comandi
from cybervallum.core import registry

ROOT = Path(__file__).resolve().parent.parent

# Core modules with actions whose commands and docs are shared (cli.py, docs/json.md).
SHARED_MODULES = {"config"}

MODULES = [name.rsplit(".", 1)[1] for name in registry.discover_modules()]
USER_MODULES = [m for m in MODULES if m not in SHARED_MODULES]


def test_moduli_trovati():
    assert {"config", "sistema", "converti"} <= set(MODULES)
    assert "registry" not in MODULES and "convert" not in MODULES


@pytest.mark.parametrize("modulo", USER_MODULES)
def test_modulo_completo(modulo):
    for path in (f"cybervallum/comandi/{modulo}.py", f"tests/test_{modulo}.py", f"docs/moduli/{modulo}.md"):
        assert (ROOT / path).is_file(), f"il modulo {modulo} non ha {path}"


def test_ogni_file_di_comandi_ha_il_suo_modulo():
    for name, _ in comandi.discover():
        assert name in USER_MODULES, f"cybervallum/comandi/{name}.py senza cybervallum/core/{name}.py"


def test_gruppi_della_cli():
    groups = {g.name for g in cli.app.registered_groups}
    assert {"config", "check", "test"} | set(USER_MODULES) <= groups


def test_azioni_con_il_nome_del_loro_modulo():
    registry.load_modules()
    for nome in (a["nome"] for a in registry.list_actions()):
        action = registry.default_registry.get_action(nome)
        modulo = action.func.__module__.rsplit(".", 1)[1]
        if action.func.__module__.startswith("cybervallum.core."):
            assert nome.startswith(f"{modulo}."), f"{nome} è definita in {action.func.__module__}"


def test_ogni_modulo_ha_la_sua_suite():
    registry.load_modules()
    suites = {s["nome"] for s in registry.list_suites()}
    assert set(USER_MODULES) <= suites
