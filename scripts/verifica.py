"""Single verification command for the project (used by the local AI and by humans).

Runs every automatic check and prints one verdict: "VERIFICA: OK" (exit code 0)
or "VERIFICA: FALLITA" with the list of problems (exit code 1).

Usage:
    .venv\\Scripts\\python scripts\\verifica.py
    .venv\\Scripts\\python scripts\\verifica.py --con-segnaposto   # "# STEP-" markers allowed
    .venv\\Scripts\\python scripts\\verifica.py --area processi    # work of the local AI on module "processi"

With --area <m> (see "Area dell'AI locale" in PROGETTO.md) two more checks run:
- only the four files of the module may differ from the base branch (default: main);
- the code of the module must not change the system or use the network
  (no modifica_sistema=True, no network/subprocess imports, no kill/terminate...).
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE_DIRS = ["cybervallum", "tests", "scripts"]
TEXT_DIRS = CODE_DIRS + ["docs"]
JUNK_SUFFIXES = (".old", ".bak", ".orig", ".final", ".tmp")
MARKER = "# STEP-"


def _files(dirs: list[str], patterns: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for d in dirs:
        for pattern in patterns:
            found.extend((ROOT / d).rglob(pattern))
    return sorted(p for p in set(found) if "__pycache__" not in p.parts)


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def check_ruff() -> list[str]:
    cmd = [sys.executable, "-m", "ruff", "check", *CODE_DIRS, "--output-format", "concise", "--no-fix"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if proc.returncode == 0:
        return []
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip() and not ln.startswith(("Found", "[*]"))]
    return lines or [proc.stderr.strip() or "ruff non eseguito (installare con: pip install -e .[dev])"]


def check_markers() -> list[str]:
    problems = []
    for path in _files(CODE_DIRS, ("*.py",)):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.strip().startswith(MARKER):
                problems.append(f"{_rel(path)}:{n}: segnaposto rimasto: {line.strip()}")
    return problems


def check_bom() -> list[str]:
    files = _files(TEXT_DIRS, ("*.py", "*.md", "*.toml"))
    files += [ROOT / name for name in ("PROGETTO.md", "README.md", "pyproject.toml", ".clinerules")]
    return [f"{_rel(p)}: carattere BOM all'inizio del file" for p in files if p.exists() and p.read_bytes()[:3] == b"\xef\xbb\xbf"]


def check_junk() -> list[str]:
    junk = []
    for d in TEXT_DIRS:
        for path in (ROOT / d).rglob("*"):
            if path.is_file() and (path.suffix in JUNK_SUFFIXES or ".part" in path.name):
                junk.append(f"{_rel(path)}: file di copia da eliminare")
    return junk


def check_pytest() -> tuple[list[str], str]:
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    lines = proc.stdout.strip().splitlines()
    summary = lines[-1] if lines else proc.stderr.strip()
    if proc.returncode == 0:
        return [], summary
    failed = [ln for ln in lines if ln.startswith(("FAILED", "ERROR"))]
    return failed or [summary], summary


# --- Area of the local AI ----------------------------------------------------------

AREA_FILES = ("cybervallum/core/{m}.py", "cybervallum/comandi/{m}.py", "tests/test_{m}.py", "docs/moduli/{m}.md")
# Names that are not modules of the area: shared infrastructure or groups of cli.py.
PROTECTED_NAMES = frozenset({"config", "registry", "convert", "check", "test", "comandi"})
FORBIDDEN_IMPORTS = frozenset({
    "socket", "ssl", "subprocess", "requests", "httpx", "urllib", "http", "ftplib",
    "smtplib", "telnetlib", "paramiko", "scapy", "shutil", "ctypes", "winreg",
})
# Calls that change the system (processes, files, commands).
FORBIDDEN_CALLS = frozenset({
    "kill", "terminate", "suspend", "resume", "send_signal",
    "unlink", "rmdir", "rmtree", "write_text", "write_bytes", "chmod",
})
# Forbidden only as os.<name>: platform.system(), for example, only reads the OS name.
FORBIDDEN_OS_CALLS = frozenset({"system", "popen", "startfile", "remove", "rename", "kill"})
_MODULE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def area_files(module: str) -> set[str]:
    return {pattern.format(m=module) for pattern in AREA_FILES}


def check_area_name(module: str) -> list[str]:
    if not _MODULE_RE.match(module):
        return [f"nome di modulo non valido: {module!r} (solo lettere minuscole, cifre e _)"]
    if module in PROTECTED_NAMES:
        return [f"'{module}' non può essere un modulo dell'area: è una parte comune del progetto"]
    return []


def files_outside_area(module: str, changed: set[str]) -> list[str]:
    """Pure function: changed files (relative paths with /) that are not files of the module."""
    allowed = area_files(module)
    return [f"{path}: fuori dall'area del modulo {module}" for path in sorted(changed - allowed)]


def forbidden_code(source: str, filename: str) -> list[str]:
    """Pure function: constructs that the area must not contain."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []  # reported by ruff
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            names = []
        for name in names:
            if name.split(".")[0] in FORBIDDEN_IMPORTS:
                problems.append(f"{filename}:{node.lineno}: import di '{name}' non ammesso nell'area (rete, comandi o file)")
        if isinstance(node, ast.keyword) and node.arg == "modifica_sistema":
            if isinstance(node.value, ast.Constant) and node.value.value is True:
                problems.append(f"{filename}:{node.value.lineno}: modifica_sistema=True non ammesso nell'area (lo scrive Claude)")
        if isinstance(node, ast.Call):
            func = node.func
            called = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
            on_os = isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "os"
            if called in FORBIDDEN_CALLS or (on_os and called in FORBIDDEN_OS_CALLS):
                problems.append(f"{filename}:{node.lineno}: chiamata '{called}' non ammessa nell'area (modifica il sistema)")
    return problems


def _git(*args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout


def changed_files(base: str) -> tuple[set[str], str | None]:
    """Files that differ from the base branch: commits of this branch plus uncommitted work."""
    code, out = _git("diff", "--name-only", f"{base}...HEAD")
    if code != 0:
        return set(), f"ramo di riferimento '{base}' non trovato"
    changed = {line.strip() for line in out.splitlines() if line.strip()}
    _, status = _git("status", "--porcelain", "--untracked-files=all")
    for line in status.splitlines():
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        if path:
            changed.add(path)
    return changed, None


def check_area(module: str, base: str) -> list[str]:
    problems = check_area_name(module)
    if problems:
        return problems
    changed, error = changed_files(base)
    if error:
        return [error]
    problems = files_outside_area(module, changed)
    for rel in sorted(area_files(module)):
        path = ROOT / rel
        if rel.endswith(".py") and path.is_file():
            problems += forbidden_code(path.read_text(encoding="utf-8"), rel)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica automatica del progetto CyberVallum.")
    parser.add_argument("--con-segnaposto", action="store_true", help="non segnala le righe '# STEP-' (lavoro a metà)")
    parser.add_argument("--area", metavar="MODULO", help="lavoro dell'AI locale sul modulo MODULO (vedi PROGETTO.md)")
    parser.add_argument("--base", default="main", help="ramo di riferimento per --area (predefinito: main)")
    args = parser.parse_args()

    checks = [
        ("ruff (errori nel codice)", check_ruff),
        ("file di copia", check_junk),
        ("BOM", check_bom),
    ]
    if not args.con_segnaposto:
        checks.insert(1, ("segnaposto # STEP-", check_markers))
    if args.area:
        checks.append((f"area del modulo {args.area} (file e codice ammessi)", lambda: check_area(args.area, args.base)))

    total = 0
    for title, check in checks:
        problems = check()
        total += len(problems)
        print(f"[{'OK' if not problems else 'ERRORE'}] {title}")
        for p in problems:
            print(f"    {p}")

    problems, summary = check_pytest()
    total += len(problems)
    print(f"[{'OK' if not problems else 'ERRORE'}] pytest: {summary}")
    for p in problems:
        print(f"    {p}")

    print()
    print("VERIFICA: OK" if total == 0 else f"VERIFICA: FALLITA ({total} {'problema' if total == 1 else 'problemi'})")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
