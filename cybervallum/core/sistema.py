"""System information: CPU, memory, disks, operating system and last boot.

Linked to L1 of the study path ("How a computer works"). Read-only.

Every call to `psutil` and `platform` lives in a small private adapter (`_xxx()`)
that returns only plain types (dict, list, int, float, str, None). Tests replace
the adapters with `monkeypatch`, so they never read the real machine. All the
logic (renaming, "" -> None, skipping unreadable disks, dates) is in `get_info()`,
which is what the tests actually exercise.
"""

from __future__ import annotations

import platform
import time
from datetime import datetime, timezone
from typing import Any

import psutil

from cybervallum.core import registry


# --- Adapters: the ONLY functions that touch the real system ------------------------

def _os_info() -> dict[str, str]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "node": platform.node(),
    }


def _cpu_model() -> str:
    return platform.processor()


def _cpu_counts() -> dict[str, int | None]:
    return {"physical": psutil.cpu_count(logical=False), "logical": psutil.cpu_count()}


def _cpu_freq_mhz() -> float | None:
    freq = psutil.cpu_freq()  # None on some systems (e.g. some VMs)
    return float(freq.current) if freq is not None else None


def _cpu_percent() -> float:
    return float(psutil.cpu_percent(interval=0.5))


def _memory() -> dict[str, Any]:
    mem = psutil.virtual_memory()
    return {"total": mem.total, "available": mem.available, "percent": mem.percent}


def _partitions() -> list[dict[str, str]]:
    return [
        {"device": p.device, "mountpoint": p.mountpoint, "fstype": p.fstype}
        for p in psutil.disk_partitions(all=False)
    ]


def _disk_usage(mountpoint: str) -> dict[str, Any]:
    usage = psutil.disk_usage(mountpoint)
    return {"total": usage.total, "used": usage.used, "free": usage.free, "percent": usage.percent}


def _boot_time() -> float:
    return psutil.boot_time()


def _now() -> float:
    return time.time()


# --- Logic ---------------------------------------------------------------------------

def _none_if_empty(value: str | None) -> str | None:
    """`platform` returns "" when it cannot determine a value: report it as None."""
    return value or None


def _disks() -> list[dict[str, Any]]:
    disks = []
    for part in _partitions():
        try:
            usage = _disk_usage(part["mountpoint"])
        except OSError:  # e.g. empty CD drive on Windows; PermissionError is an OSError
            continue
        disks.append({
            "dispositivo": part["device"],
            "punto_montaggio": part["mountpoint"],
            "filesystem": _none_if_empty(part["fstype"]),
            "totale_byte": int(usage["total"]),
            "usato_byte": int(usage["used"]),
            "libero_byte": int(usage["free"]),
            "usato_percentuale": float(usage["percent"]),
        })
    return disks


def get_info() -> dict[str, Any]:
    """Return CPU, memory, disks, OS and boot data (format in docs/json.md)."""
    os_info = _os_info()
    counts = _cpu_counts()
    mem = _memory()
    boot = _boot_time()
    return {
        "sistema_operativo": {
            "nome": _none_if_empty(os_info["system"]),
            "release": _none_if_empty(os_info["release"]),
            "versione": _none_if_empty(os_info["version"]),
            "architettura": _none_if_empty(os_info["machine"]),
            "nome_host": _none_if_empty(os_info["node"]),
        },
        "cpu": {
            "modello": _none_if_empty(_cpu_model()),
            "core_fisici": counts["physical"],
            "core_logici": counts["logical"],
            "frequenza_mhz": _cpu_freq_mhz(),
            "uso_percentuale": _cpu_percent(),
        },
        "memoria": {
            "totale_byte": int(mem["total"]),
            "disponibile_byte": int(mem["available"]),
            "usata_percentuale": float(mem["percent"]),
        },
        "dischi": _disks(),
        "avvio": {
            "ultimo_avvio": datetime.fromtimestamp(boot, tz=timezone.utc).isoformat(),
            "uptime_s": int(_now() - boot),
        },
    }


@registry.action("sistema.info", "Informazioni su CPU, memoria, dischi, sistema operativo e avvio")
def _action_info() -> dict[str, Any]:
    return get_info()
