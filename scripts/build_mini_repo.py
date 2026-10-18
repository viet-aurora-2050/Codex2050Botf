"""Baut KI_Taktik_GitHub_Repo_v2.zip: ein abhängigkeitsfreies Mini-Repo aus dem echten Repo.

Aufruf:  python scripts/build_mini_repo.py [AUSGABEORDNER]      (Standard: dist/)

Die Pakete `analyzer/` und `risiko/` sowie die passenden Tests werden direkt aus diesem Repo kopiert,
damit die ZIP nie vom Hauptprojekt abweicht. Bot-/API-Tests bleiben draussen (brauchen Telegram/FastAPI).
Vorlagen (index.html, README.md, Wrapper, CI) liegen in scripts/mini_repo/.
"""

import re
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VORLAGEN = REPO / "scripts" / "mini_repo"
WURZEL = "KI_Taktik_Repo_v2"
ZIP_NAME = "KI_Taktik_GitHub_Repo_v2.zip"

# Diese Tests laufen im Mini-Repo vollstaendig; bei den anderen wird ab dem Marker abgeschnitten.
GANZE_TESTS = ("test_bonus.py", "test_risiko.py", "test_risiko_statistik.py")
GEKUERZTE_TESTS = {"test_scan.py": "\nclass _Msg:", "test_profil.py": "\nclass _Msg:"}
_UNNOETIGE_IMPORTS = re.compile(r"import asyncio\n|import importlib\n|import importlib\.util\n|import os\n"
                                r"|from unittest import mock\n")


def _kuerze(name: str, marker: str) -> str:
    text = (REPO / "tests" / name).read_text(encoding="utf-8")
    kopf, gefunden, _ = text.partition(marker)
    if not gefunden:
        raise SystemExit(f"Marker {marker!r} fehlt in tests/{name} – Build-Skript anpassen.")
    kopf = _UNNOETIGE_IMPORTS.sub("", kopf)
    kopf = re.sub(r"HAT_TELEGRAM = .*?\n\n\n", "\n\n", kopf, flags=re.S)
    return kopf.rstrip() + '\n\n\nif __name__ == "__main__":\n    unittest.main()\n'


def baue(ausgabe: Path) -> Path:
    ausgabe.mkdir(parents=True, exist_ok=True)
    stage = ausgabe / WURZEL
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    for paket in ("analyzer", "risiko"):
        (stage / paket).mkdir()
        for f in sorted((REPO / paket).glob("*.py")):
            shutil.copy2(f, stage / paket / f.name)
    shutil.copy2(REPO / "ruff.toml", stage / "ruff.toml")

    tests = stage / "tests"
    tests.mkdir()
    (tests / "__init__.py").write_text("", encoding="utf-8")
    for name in GANZE_TESTS:
        shutil.copy2(REPO / "tests" / name, tests / name)
    for name, marker in GEKUERZTE_TESTS.items():
        (tests / name).write_text(_kuerze(name, marker), encoding="utf-8")

    shutil.copy2(VORLAGEN / "index.html", stage / "index.html")
    shutil.copy2(VORLAGEN / "README.md", stage / "README.md")
    shutil.copy2(VORLAGEN / "bonus_analyzer.py", stage / "bonus_analyzer.py")
    shutil.copy2(VORLAGEN / "gitignore.txt", stage / ".gitignore")
    (stage / ".github" / "workflows").mkdir(parents=True)
    shutil.copy2(VORLAGEN / "ci.yml", stage / ".github" / "workflows" / "ci.yml")

    for pc in stage.rglob("__pycache__"):
        shutil.rmtree(pc)
    ziel = ausgabe / ZIP_NAME
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(stage.rglob("*")):
            if f.is_file():
                z.write(f, Path(WURZEL) / f.relative_to(stage))
    return ziel


if __name__ == "__main__":
    print(baue(Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "dist"))
