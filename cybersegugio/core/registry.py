"""Registry of the actions (checks) and test suites that CyberSegugio can run.

Every module registers its actions here with a name `<module>.<action>`, a set of
typed parameters and the `modifica_sistema` flag. CLI, API and GUI never call module
functions directly: they go through `run()` and `run_suite()`, which always return
a plain dictionary with a stable schema (documented in docs/json.md).

Safety (rules 1 and 10 of PROGETTO.md): an action with `modifica_sistema=True` runs
in dry-run mode by default and really changes the system only when the caller passes
`dry_run=False` *and* `conferma=True`.
"""

from __future__ import annotations

import importlib
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from cybersegugio.core.convert import ConversionError, to_type, type_name

# Core modules that register actions on import. New modules are added here.
BUILTIN_MODULES: list[str] = [
    "cybersegugio.core.config",
]

# Project root (the folder that contains `cybersegugio/` and `tests/`).
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


class RegistryError(Exception):
    """Raised for programming errors: invalid names, duplicates, bad definitions."""


@dataclass(frozen=True)
class Param:
    """Definition of an action parameter."""

    type: type = str
    default: Any = None
    required: bool = False
    description: str = ""

    def describe(self) -> dict[str, Any]:
        return {
            "tipo": type_name(self.type),
            "predefinito": self.default,
            "obbligatorio": self.required,
            "descrizione": self.description,
        }


@dataclass(frozen=True)
class Action:
    name: str
    func: Callable[..., Any]
    description: str
    params: dict[str, Param] = field(default_factory=dict)
    modifica_sistema: bool = False

    @property
    def module(self) -> str:
        return self.name.split(".", 1)[0]

    def describe(self) -> dict[str, Any]:
        return {
            "nome": self.name,
            "modulo": self.module,
            "descrizione": self.description,
            "modifica_sistema": self.modifica_sistema,
            "parametri": {name: p.describe() for name, p in self.params.items()},
        }


@dataclass(frozen=True)
class Suite:
    """A pytest test suite: a list of paths relative to the project root."""

    name: str
    description: str
    paths: tuple[str, ...]

    def describe(self) -> dict[str, Any]:
        return {"nome": self.name, "descrizione": self.description, "percorsi": list(self.paths)}


# --- System call wrapper (replaceable in tests) -------------------------------------

def _run_pytest(paths: list[str], junit_path: Path, cwd: Path) -> int:
    """Run pytest in a separate process and write a junit-xml report. Return the exit code."""
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         f"--junitxml={junit_path}", *paths],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return completed.returncode


def _parse_junit(junit_path: Path) -> dict[str, Any]:
    """Read a junit-xml report and count passed, failed and skipped tests."""
    root = ET.parse(junit_path).getroot()
    details: list[dict[str, Any]] = []
    counts = {"passati": 0, "falliti": 0, "saltati": 0}
    for case in root.iter("testcase"):
        test_id = "::".join(part for part in (case.get("classname"), case.get("name")) if part)
        outcome, message = "passato", None
        for child in case:
            if child.tag in ("failure", "error"):
                outcome, message = "fallito", child.get("message")
                break
            if child.tag == "skipped":
                outcome, message = "saltato", child.get("message")
                break
        counts[{"passato": "passati", "fallito": "falliti", "saltato": "saltati"}[outcome]] += 1
        details.append({"test": test_id, "esito": outcome, "messaggio": message})
    return {**counts, "dettagli": details}


# --- Registry -----------------------------------------------------------------------

class Registry:
    def __init__(self) -> None:
        self._actions: dict[str, Action] = {}
        self._suites: dict[str, Suite] = {}
        # Replaceable in tests: function that launches pytest.
        self.pytest_runner: Callable[[list[str], Path, Path], int] = _run_pytest
        self.project_root: Path = PROJECT_ROOT

    # Actions ------------------------------------------------------------------------

    def action(
        self,
        name: str,
        description: str,
        params: dict[str, Param] | None = None,
        modifica_sistema: bool = False,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator that registers a function as the action `name`."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.add_action(Action(name, func, description, dict(params or {}), modifica_sistema))
            return func

        return decorator

    def add_action(self, action: Action) -> None:
        if not _NAME_RE.match(action.name):
            raise RegistryError(f"nome di azione non valido: {action.name!r} (formato: modulo.azione)")
        if action.name in self._actions:
            raise RegistryError(f"azione già registrata: {action.name}")
        if action.modifica_sistema and "dry_run" in action.params:
            raise RegistryError(f"{action.name}: 'dry_run' è gestito dal registro, non va dichiarato")
        self._actions[action.name] = action

    def list_actions(self) -> list[dict[str, Any]]:
        return [self._actions[name].describe() for name in sorted(self._actions)]

    def get_action(self, name: str) -> Action | None:
        return self._actions.get(name)

    def run(
        self,
        name: str,
        params: dict[str, Any] | None = None,
        *,
        dry_run: bool | None = None,
        conferma: bool = False,
    ) -> dict[str, Any]:
        """Run an action and return the result envelope. Never raises for user errors."""
        start = time.perf_counter()
        action = self._actions.get(name)
        effective_dry_run = bool(action and action.modifica_sistema and dry_run is not False)

        def envelope(stato: str, dati: Any = None, errore: str | None = None) -> dict[str, Any]:
            return {
                "azione": name,
                "stato": stato,
                "modifica_sistema": bool(action and action.modifica_sistema),
                "dry_run": effective_dry_run,
                "durata_s": round(time.perf_counter() - start, 4),
                "dati": dati,
                "errore": errore,
            }

        if action is None:
            return envelope("errore", errore=f"azione sconosciuta: {name}")

        try:
            kwargs = self._bind_params(action, params or {})
        except ValueError as exc:
            return envelope("errore", errore=str(exc))

        if action.modifica_sistema:
            if not effective_dry_run and not conferma:
                return envelope(
                    "rifiutato",
                    errore="questa azione modifica il sistema: serve una conferma esplicita",
                )
            kwargs["dry_run"] = effective_dry_run

        try:
            data = action.func(**kwargs)
        except ValueError as exc:  # user error (bad value, unknown key...): message as is
            return envelope("errore", errore=str(exc))
        except Exception as exc:  # the envelope must always come back to the caller
            return envelope("errore", errore=f"{type(exc).__name__}: {exc}")
        return envelope("ok", dati=data)

    @staticmethod
    def _bind_params(action: Action, raw: dict[str, Any]) -> dict[str, Any]:
        unknown = sorted(set(raw) - set(action.params))
        if unknown:
            raise ValueError(f"parametri sconosciuti per {action.name}: {', '.join(unknown)}")
        kwargs: dict[str, Any] = {}
        for pname, spec in action.params.items():
            if pname in raw:
                try:
                    kwargs[pname] = to_type(raw[pname], spec.type)
                except ConversionError as exc:
                    raise ValueError(f"parametro '{pname}': {exc}") from None
            elif spec.required:
                raise ValueError(f"parametro obbligatorio mancante: {pname}")
            else:
                kwargs[pname] = spec.default
        return kwargs

    # Test suites --------------------------------------------------------------------

    def add_suite(self, name: str, description: str, paths: list[str] | tuple[str, ...]) -> None:
        if name in self._suites:
            raise RegistryError(f"suite già registrata: {name}")
        self._suites[name] = Suite(name, description, tuple(paths))

    def list_suites(self) -> list[dict[str, Any]]:
        return [self._suites[name].describe() for name in sorted(self._suites)]

    def run_suite(self, name: str) -> dict[str, Any]:
        """Run a test suite with pytest and return the result envelope."""
        start = time.perf_counter()

        def envelope(stato: str, errore: str | None = None, **counts: Any) -> dict[str, Any]:
            return {
                "suite": name,
                "stato": stato,
                "durata_s": round(time.perf_counter() - start, 4),
                "passati": counts.get("passati", 0),
                "falliti": counts.get("falliti", 0),
                "saltati": counts.get("saltati", 0),
                "dettagli": counts.get("dettagli", []),
                "errore": errore,
            }

        suite = self._suites.get(name)
        if suite is None:
            return envelope("errore", errore=f"suite sconosciuta: {name}")
        missing = [p for p in suite.paths if not (self.project_root / p).exists()]
        if missing:
            return envelope("errore", errore=f"percorsi dei test non trovati: {', '.join(missing)}")

        with tempfile.TemporaryDirectory() as tmp:
            junit_path = Path(tmp) / "report.xml"
            try:
                code = self.pytest_runner(list(suite.paths), junit_path, self.project_root)
            except OSError as exc:
                return envelope("errore", errore=f"impossibile avviare pytest: {exc}")
            if not junit_path.exists():
                return envelope("errore", errore=f"pytest non ha prodotto un report (codice {code})")
            try:
                counts = _parse_junit(junit_path)
            except ET.ParseError as exc:
                return envelope("errore", errore=f"report di pytest non leggibile: {exc}")

        stato = "ok" if code == 0 and counts["falliti"] == 0 else "fallito"
        return envelope(stato, **counts)

    # Module loading -----------------------------------------------------------------

    def load_modules(self, modules: list[str] | None = None) -> None:
        """Import the core modules so that they register their actions (idempotent)."""
        for module in modules if modules is not None else BUILTIN_MODULES:
            importlib.import_module(module)


# Default registry used by the whole application.
default_registry = Registry()
default_registry.add_suite("tutti", "Tutti i test del progetto", ["tests"])
default_registry.add_suite("config", "Test delle impostazioni", ["tests/test_config.py"])
default_registry.add_suite("registry", "Test del registro", ["tests/test_registry.py"])
default_registry.add_suite("cli", "Test della riga di comando", ["tests/test_cli.py"])

action = default_registry.action
add_suite = default_registry.add_suite
list_actions = default_registry.list_actions
list_suites = default_registry.list_suites
run = default_registry.run
run_suite = default_registry.run_suite
load_modules = default_registry.load_modules
