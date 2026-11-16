"""Tests of scripts/verifica.py: the rules of the local AI area (pure functions, no git)."""

import importlib.util
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parent.parent / "scripts" / "verifica.py"
_spec = importlib.util.spec_from_file_location("verifica", _PATH)
verifica = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verifica)


def test_file_dell_area():
    assert verifica.area_files("processi") == {
        "cybervallum/core/processi.py", "cybervallum/comandi/processi.py",
        "tests/test_processi.py", "docs/moduli/processi.md",
    }


def test_solo_file_dell_area_ok():
    assert verifica.files_outside_area("processi", verifica.area_files("processi")) == []


def test_file_fuori_area():
    problems = verifica.files_outside_area("processi", {"cybervallum/core/processi.py", "cybervallum/cli.py"})
    assert len(problems) == 1 and problems[0].startswith("cybervallum/cli.py")


@pytest.mark.parametrize("nome", ["config", "registry", "test", "Processi", "1abc", "pro-cessi"])
def test_nomi_non_ammessi(nome):
    assert verifica.check_area_name(nome)


def test_codice_in_sola_lettura_ok():
    source = (
        "import platform\nimport psutil\n"
        "@registry.action('processi.elenco', 'x', modifica_sistema=False)\n"
        "def elenco():\n    return [p.info for p in psutil.process_iter()], platform.system()\n"
    )
    assert verifica.forbidden_code(source, "p.py") == []


@pytest.mark.parametrize("source", [
    "import subprocess\n",
    "from urllib.request import urlopen\n",
    "import socket as s\n",
    "@registry.action('processi.chiudi', 'x', modifica_sistema=True)\ndef f(): pass\n",
    "def f(p):\n    p.kill()\n",
    "def f(p):\n    p.terminate()\n",
    "import os\nos.system('dir')\n",
    "from pathlib import Path\nPath('x').write_text('y')\n",
])
def test_codice_non_ammesso(source):
    assert verifica.forbidden_code(source, "p.py")
