import platform
import time
from datetime import datetime, timezone
from typing import Any, Optional

import psutil

from cybervallum.core import registry

def _os_info() -> dict[str, str]:
    system = platform.system()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()
    node = platform.node()
    
    return {
        "nome": system if system else None,
        "release": release if release else None,
        "versione": version if version else None,
        "architettura": machine if machine else None,
        "nome_host": node if node else None,
    }

def _cpu_model() -> str:
    # platform.processor() can be empty or differ between OS
    model = platform.processor()
    return model if model else "Unknown"

def _cpu_counts() -> dict[str, Optional[int]]:
    return {
        "physical": psutil.cpu_count(logical=False),
        "logical": psutil.cpu_count(),
    }

def _cpu_freq_mhz() -> Optional[float]:
    freq = psutil.cpu_freq()
    if freq:
        return freq.current
    return None

def _cpu_percent() -> float:
    return psutil.cpu_percent(interval=0.5)

def _memory() -> dict[str, Any]:
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "available": mem.available,
        "percent": mem.percent,
    }

def _partitions() -> list[dict[str, str]]:
    partitions = psutil.disk_partitions(all=False)
    return [
        {
            "device": p.device,
            "mountpoint": p.mountpoint,
            "fstype": p.fstype,
        }
        for p in partitions
    ]

def _disk_usage(mountpoint: str) -> dict[str, Any]:
    usage = psutil.disk_usage(mountpoint)
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "percent": usage.percent,
    }

def _boot_time() -> float:
    return psutil.boot_time()

def _now() -> float:
    return time.time()

def get_info() -> dict[str, Any]:
    os_data = _os_info()
    # Clean empty strings to None as requested
    for key in ["nome", "release", "versione", "architettura", "nome_host"]:
        if os_data[key] == "":
            os_data[key] = None

    cpu_counts = _cpu_counts()
    cpu_data = {
        "modello": _cpu_model(),
        "core_fisici": cpu_counts["physical"],
        "core_logici": cpu_counts["logical"],
        "frequenza_mhz": _cpu_freq_mhz(),
        "uso_percentuale": _cpu_percent(),
    }

    mem_data = _memory()
    mem_info = {
        "totale_byte": mem_data["total"],
        "disponibile_byte": mem_data["available"],
        "usata_percentuale": mem_data["percent"],
    }

    dischi_info = []
    for p in _partitions():
        try:
            usage = _disk_usage(p["mountpoint"])
            dischi_info.append({
                "dispositivo": p["device"],
                "punto_montaggio": p["mountpoint"],
                "filesystem": p["fstype"],
                "totale_byte": usage["total"],
                "usato_byte": usage["used"],
                "libero_byte": usage["free"],
                "usato_percentuale": usage["percent"],
            })
        except (OSError, PermissionError):
            continue

    boot = _boot_time()
    now = _now()
    ultimo_avvio = datetime.fromtimestamp(boot, tz=timezone.utc).isoformat()
    uptime_s = int(now - boot)

    return {
        "sistema_operativo": {
            "nome": os_data["nome"],
            "release": os_data["release"],
            "versione": os_data["versione"],
            "architettura": os_data["architettura"],
            "nome_host": os_data["nome_host"],
        },
        "cpu": cpu_data,
        "memoria": mem_info,
        "dischi": dischi_info,
        "avvio": {
            "ultimo_avvio": ultimo_avvio,
            "uptime_s": uptime_s,
        },
    }

@registry.action("sistema.info", "Informazioni su CPU, memoria, dischi, sistema operativo e avvio")
def _action_info() -> dict[str, Any]:
    return get_info()
