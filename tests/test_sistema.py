"""Tests of the `sistema` module: every adapter is faked, the real PC is never read."""

import json

import pytest
from typer.testing import CliRunner

from cybervallum import cli
from cybervallum.core import registry, sistema

runner = CliRunner()

GB = 1024**3


@pytest.fixture
def fake_system(monkeypatch):
    """Replace ALL the adapters of core.sistema with fixed values."""
    fakes = {
        "_os_info": lambda: {"system": "Windows", "release": "11", "version": "10.0.26200",
                             "machine": "AMD64", "node": "PC"},
        "_cpu_model": lambda: "CPU di prova",
        "_cpu_counts": lambda: {"physical": 8, "logical": 16},
        "_cpu_freq_mhz": lambda: 3600.0,
        "_cpu_percent": lambda: 12.5,
        "_memory": lambda: {"total": 32 * GB, "available": 16 * GB, "percent": 50.0},
        "_partitions": lambda: [{"device": "C:\\", "mountpoint": "C:\\", "fstype": "NTFS"}],
        "_disk_usage": lambda m: {"total": 1000, "used": 400, "free": 600, "percent": 40.0},
        "_boot_time": lambda: 1_800_000_000.0,
        "_now": lambda: 1_800_003_600.0,
    }
    for name, fake in fakes.items():
        monkeypatch.setattr(sistema, name, fake)
    return monkeypatch


def test_get_info_exact_format(fake_system):
    assert sistema.get_info() == {
        "sistema_operativo": {"nome": "Windows", "release": "11", "versione": "10.0.26200",
                              "architettura": "AMD64", "nome_host": "PC"},
        "cpu": {"modello": "CPU di prova", "core_fisici": 8, "core_logici": 16,
                "frequenza_mhz": 3600.0, "uso_percentuale": 12.5},
        "memoria": {"totale_byte": 32 * GB, "disponibile_byte": 16 * GB, "usata_percentuale": 50.0},
        "dischi": [{"dispositivo": "C:\\", "punto_montaggio": "C:\\", "filesystem": "NTFS",
                    "totale_byte": 1000, "usato_byte": 400, "libero_byte": 600,
                    "usato_percentuale": 40.0}],
        "avvio": {"ultimo_avvio": "2027-01-15T08:00:00+00:00", "uptime_s": 3600},
    }


@pytest.mark.parametrize("error", [PermissionError, OSError])
def test_unreadable_disk_is_skipped(fake_system, error):
    fake_system.setattr(sistema, "_partitions", lambda: [
        {"device": "C:\\", "mountpoint": "C:\\", "fstype": "NTFS"},
        {"device": "D:\\", "mountpoint": "D:\\", "fstype": ""},
    ])

    def usage(mountpoint):
        if mountpoint == "D:\\":
            raise error("unità non pronta")
        return {"total": 1000, "used": 400, "free": 600, "percent": 40.0}

    fake_system.setattr(sistema, "_disk_usage", usage)
    assert [d["dispositivo"] for d in sistema.get_info()["dischi"]] == ["C:\\"]


def test_missing_values_become_none(fake_system):
    fake_system.setattr(sistema, "_cpu_freq_mhz", lambda: None)
    fake_system.setattr(sistema, "_cpu_counts", lambda: {"physical": None, "logical": 16})
    fake_system.setattr(sistema, "_cpu_model", lambda: "")
    fake_system.setattr(sistema, "_os_info", lambda: {"system": "Linux", "release": "", "version": "",
                                                      "machine": "x86_64", "node": ""})
    info = sistema.get_info()
    assert info["cpu"]["frequenza_mhz"] is None
    assert info["cpu"]["core_fisici"] is None
    assert info["cpu"]["modello"] is None
    assert info["sistema_operativo"]["release"] is None
    assert info["sistema_operativo"]["nome_host"] is None


def test_registry_run_is_read_only(fake_system):
    result = registry.run("sistema.info")
    assert result["stato"] == "ok"
    assert result["dry_run"] is False and result["modifica_sistema"] is False
    assert result["dati"]["avvio"]["uptime_s"] == 3600


def test_cli_json(fake_system):
    result = runner.invoke(cli.app, ["sistema", "info", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["azione"] == "sistema.info" and data["errore"] is None
    assert data["dati"]["cpu"]["core_logici"] == 16


def test_cli_human_output(fake_system):
    result = runner.invoke(cli.app, ["sistema", "info"])
    assert result.exit_code == 0
    out = result.stdout
    assert "Sistema operativo: Windows 11 (AMD64), host PC" in out
    assert "CPU: CPU di prova, 8 core fisici / 16 logici, 3600 MHz, uso 12.5%" in out
    assert "Memoria: 16.0 GB disponibili su 32.0 GB (usata 50.0%)" in out
    assert "attivo da 1 h 0 min" in out


def test_cli_human_output_missing_values(fake_system):
    fake_system.setattr(sistema, "_cpu_freq_mhz", lambda: None)
    fake_system.setattr(sistema, "_cpu_counts", lambda: {"physical": None, "logical": 16})
    result = runner.invoke(cli.app, ["sistema", "info"])
    assert result.exit_code == 0
    assert "n/d core fisici" in result.stdout and "n/d MHz" in result.stdout


def test_action_and_suite_are_registered():
    result = runner.invoke(cli.app, ["check", "list", "--json"])
    assert "sistema.info" in {a["nome"] for a in json.loads(result.stdout)["azioni"]}
    assert "sistema" in {s["nome"] for s in registry.list_suites()}
