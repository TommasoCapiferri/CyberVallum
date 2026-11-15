"""Convert raw values (usually strings from the CLI or JSON from the API) to Python types.

Shared by `config` and `registry`, so the entry points (CLI, API, GUI) can pass
values through untouched and all the parsing logic stays in the core.
"""

from __future__ import annotations

from typing import Any

_TRUE = {"true", "1", "si", "sì", "yes", "on"}
_FALSE = {"false", "0", "no", "off"}

TYPE_NAMES = {str: "str", int: "int", float: "float", bool: "bool", list: "list", object: "any"}


class ConversionError(ValueError):
    """Raised when a value cannot be converted to the requested type."""


def type_name(typ: type) -> str:
    return TYPE_NAMES.get(typ, typ.__name__)


def to_type(value: Any, typ: type) -> Any:
    """Return `value` converted to `typ` (str, int, float, bool, list of str, or object = as is)."""
    if typ is object:
        return value
    if typ is bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in _TRUE | _FALSE:
            return value.strip().lower() in _TRUE
        raise ConversionError(f"valore non valido per un booleano: {value!r} (usa true o false)")

    if typ is int:
        if isinstance(value, bool):  # bool is a subclass of int: reject it explicitly
            raise ConversionError(f"atteso un numero intero, ricevuto {value!r}")
        if isinstance(value, int):
            return value
        try:
            return int(str(value).strip())
        except ValueError:
            raise ConversionError(f"atteso un numero intero, ricevuto {value!r}") from None

    if typ is float:
        if isinstance(value, bool):
            raise ConversionError(f"atteso un numero, ricevuto {value!r}")
        try:
            return float(str(value).strip().replace(",", "."))
        except ValueError:
            raise ConversionError(f"atteso un numero, ricevuto {value!r}") from None

    if typ is list:
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value]
        if isinstance(value, str):
            # Comma-separated list; an empty string means an empty list.
            return [item.strip() for item in value.split(",") if item.strip()]
        raise ConversionError(f"attesa una lista, ricevuto {value!r}")

    if typ is str:
        if isinstance(value, str):
            return value
        raise ConversionError(f"attesa una stringa, ricevuto {value!r}")

    raise ConversionError(f"tipo non supportato: {type_name(typ)}")
