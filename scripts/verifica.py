"""Single verification command for the project (used by the local AI and by humans).

Runs every automatic check and prints one verdict: "VERIFICA: OK" (exit code 0)
or "VERIFICA: FALLITA" with the list of problems (exit code 1).

Usage:
    .venv\\Scripts\\python scripts\\verifica.py
    .venv\\Scripts\\python scripts\\verifica.py --con-segnaposto   # "# STEP-" markers allowed
"""

from __future__ import annotations

import argparse
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica automatica del progetto CyberVallum.")
    parser.add_argument("--con-segnaposto", action="store_true", help="non segnala le righe '# STEP-' (lavoro a metà)")
    args = parser.parse_args()

    checks = [
        ("ruff (errori nel codice)", check_ruff),
        ("file di copia", check_junk),
        ("BOM", check_bom),
    ]
    if not args.con_segnaposto:
        checks.insert(1, ("segnaposto # STEP-", check_markers))

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
