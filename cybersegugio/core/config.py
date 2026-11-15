"""Settings of CyberSegugio: the ONLY place that reads, validates and saves them.

Settings are declared (key `section.name`, type, default, description, validator)
and stored in `config.toml`. Modules never read files or environment variables on
their own: they call `get_setting()`. Secrets (API keys, tokens) do NOT live here:
they stay in the `.env` file, which is never committed.

Location of `config.toml`:
- the path in the CYBERSEGUGIO_CONFIG environment variable, if set;
- Windows: %APPDATA%\\CyberSegugio\\config.toml
- Linux:   $XDG_CONFIG_HOME/cybersegugio/config.toml (default ~/.config/...)
"""

from __future__ import annotations

import ipaddress
import os
import platform
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import tomli_w

from cybersegugio.core import registry
from cybersegugio.core.convert import ConversionError, to_type, type_name

ENV_CONFIG_PATH = "CYBERSEGUGIO_CONFIG"


class ConfigError(ValueError):
    """Raised for unknown keys, invalid values or an unreadable config file."""


@dataclass(frozen=True)
class Setting:
    key: str
    type: type
    default: Any
    description: str
    validator: Callable[[Any], None] | None = None
    choices: tuple[Any, ...] | None = None

    def validate(self, value: Any) -> Any:
        """Convert and validate `value`; return the clean value or raise ConfigError."""
        try:
            clean = to_type(value, self.type)
        except ConversionError as exc:
            raise ConfigError(f"{self.key}: {exc}") from None
        if self.choices is not None and clean not in self.choices:
            allowed = ", ".join(map(str, self.choices))
            raise ConfigError(f"{self.key}: valore non ammesso {clean!r} (ammessi: {allowed})")
        if self.validator is not None:
            try:
                self.validator(clean)
            except ValueError as exc:
                raise ConfigError(f"{self.key}: {exc}") from None
        return clean


# --- Validators ---------------------------------------------------------------------

def _loopback_host(value: str) -> None:
    # Rule 10: the local API listens only on the loopback interface.
    if value == "localhost":
        return
    try:
        if ipaddress.ip_address(value).is_loopback:
            return
    except ValueError:
        pass
    raise ValueError("sono ammessi solo indirizzi locali (127.0.0.1, ::1 o localhost)")


def _port(value: int) -> None:
    if not 1024 <= value <= 65535:
        raise ValueError("la porta deve essere compresa tra 1024 e 65535")


def _http_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"URL non valido: {value!r}")


def _https_urls(values: list[str]) -> None:
    # Rule 11: security data sources must use HTTPS.
    for value in values:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"le fonti devono usare HTTPS: {value!r}")


# --- Declared settings --------------------------------------------------------------

_SETTINGS: dict[str, Setting] = {}


def register_setting(setting: Setting) -> None:
    """Declare a new setting. Modules call this to add their own options."""
    section, _, name = setting.key.partition(".")
    if not section or not name or "." in name:
        raise ConfigError(f"chiave non valida: {setting.key!r} (formato: sezione.nome)")
    if setting.key in _SETTINGS:
        raise ConfigError(f"impostazione già dichiarata: {setting.key}")
    setting.validate(setting.default)  # the default itself must be valid
    _SETTINGS[setting.key] = setting


for _setting in (
    Setting("ai.provider", str, "ollama", "Assistente AI da usare", choices=("ollama", "claude")),
    Setting("ai.modello", str, "gemma4:12b-it-qat", "Modello usato con Ollama"),
    Setting("ai.ollama_url", str, "http://127.0.0.1:11434", "Indirizzo del server Ollama", _http_url),
    Setting("api.host", str, "127.0.0.1", "Indirizzo di ascolto dell'API locale", _loopback_host),
    Setting("api.porta", int, 8765, "Porta dell'API locale", _port),
    Setting("rete.consenti_ip_pubblici", bool, False,
            "Consente scansioni verso IP pubblici (sconsigliato)"),
    Setting("aggiornamenti.fonti", list, [], "Fonti HTTPS dei dati di sicurezza", _https_urls),
):
    register_setting(_setting)


# --- File access (small wrappers, replaceable in tests) -----------------------------

def _is_windows() -> bool:
    return platform.system() == "Windows"


def config_path() -> Path:
    """Return the path of config.toml for this user and platform."""
    override = os.environ.get(ENV_CONFIG_PATH)
    if override:
        return Path(override)
    if _is_windows():
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / "CyberSegugio" / "config.toml"
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "cybersegugio" / "config.toml"


def _read_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise ConfigError(f"impossibile leggere {path}: {exc}") from None


def _write_file(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".toml.tmp")
    with tmp.open("wb") as fh:
        tomli_w.dump(data, fh)
    tmp.replace(path)  # atomic: a crash never leaves a half-written config


def _stored_value(data: dict[str, Any], key: str) -> tuple[bool, Any]:
    section, _, name = key.partition(".")
    table = data.get(section)
    if isinstance(table, dict) and name in table:
        return True, table[name]
    return False, None


# --- Public API ---------------------------------------------------------------------

def _require(key: str) -> Setting:
    setting = _SETTINGS.get(key)
    if setting is None:
        raise ConfigError(f"impostazione sconosciuta: {key}")
    return setting


def get_setting(key: str) -> Any:
    """Return the current value of a setting (from config.toml, or its default)."""
    setting = _require(key)
    found, value = _stored_value(_read_file(config_path()), key)
    return setting.validate(value) if found else setting.default


def list_settings() -> list[dict[str, Any]]:
    """Return every declared setting with its current value and origin."""
    data = _read_file(config_path())
    result = []
    for key in sorted(_SETTINGS):
        setting = _SETTINGS[key]
        found, raw = _stored_value(data, key)
        entry: dict[str, Any] = {
            "chiave": key,
            "valore": setting.default,
            "predefinito": setting.default,
            "tipo": type_name(setting.type),
            "descrizione": setting.description,
            "origine": "predefinito",
            "errore": None,
        }
        if found:
            try:
                entry["valore"], entry["origine"] = setting.validate(raw), "file"
            except ConfigError as exc:  # keep listing the others, flag the broken one
                entry["errore"] = str(exc)
        result.append(entry)
    return result


def set_setting(key: str, value: Any) -> dict[str, Any]:
    """Validate and save a setting. `value` may be a string (as typed on the CLI)."""
    setting = _require(key)
    clean = setting.validate(value)
    path = config_path()
    data = _read_file(path)
    section, _, name = key.partition(".")
    data.setdefault(section, {})[name] = clean
    _write_file(path, data)
    return {"chiave": key, "valore": clean, "file": str(path)}


# --- Registered actions (reachable from CLI and API, rule 10) -----------------------

@registry.action("config.list", "Elenca le impostazioni e i loro valori")
def _action_list() -> dict[str, Any]:
    return {"file": str(config_path()), "impostazioni": list_settings()}


@registry.action(
    "config.get",
    "Legge il valore di un'impostazione",
    params={"chiave": registry.Param(str, required=True, description="Chiave sezione.nome")},
)
def _action_get(chiave: str) -> dict[str, Any]:
    return {"chiave": chiave, "valore": get_setting(chiave)}


@registry.action(
    "config.set",
    "Imposta e salva il valore di un'impostazione",
    params={
        "chiave": registry.Param(str, required=True, description="Chiave sezione.nome"),
        "valore": registry.Param(object, required=True, description="Nuovo valore"),
    },
)
def _action_set(chiave: str, valore: Any) -> dict[str, Any]:
    return set_setting(chiave, valore)
