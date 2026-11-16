"""Command groups of the CLI, one file per module: `cybervallum/comandi/<modulo>.py`.

Each file defines `app = typer.Typer(...)` with the commands of its module. `cli.py`
finds them by itself with `discover()`, so adding a module never touches `cli.py`
(see "Area dell'AI locale" in PROGETTO.md). Files starting with "_" are helpers.
"""

from __future__ import annotations

import importlib
import pkgutil

import typer

# Command groups defined in cli.py: a module file with one of these names would clash.
RESERVED_NAMES = frozenset({"config", "check", "test"})


def discover() -> list[tuple[str, typer.Typer]]:
    """Return (name, Typer app) for every command module, sorted by name."""
    found: list[tuple[str, typer.Typer]] = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda i: i.name):
        if info.name.startswith("_"):
            continue
        if info.name in RESERVED_NAMES:
            raise RuntimeError(f"cybervallum/comandi/{info.name}.py: nome riservato a un gruppo di cli.py")
        module = importlib.import_module(f"{__name__}.{info.name}")
        group = getattr(module, "app", None)
        if not isinstance(group, typer.Typer):
            raise RuntimeError(f"{module.__name__}: manca 'app = typer.Typer(...)'")
        found.append((info.name, group))
    return found
