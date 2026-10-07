"""Prüft das statische Frontend (docs/): Inline-JavaScript-Syntax und JSON-Dateien.

Aufruf:  python scripts/check_frontend.py        (benötigt `node` für die Syntaxprüfung)

Fängt u. a. kaputte Skripte vor dem Deploy ab, ohne einen Browser zu brauchen.
Grundlegende Barrierefreiheit wird mitgeprüft: lang-Attribut, viewport, <title>.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"


def pruefe_html(pfad: Path) -> list[str]:
    fehler: list[str] = []
    html = pfad.read_text(encoding="utf-8")
    if not re.search(r"<html[^>]*\blang=", html):
        fehler.append("fehlendes lang-Attribut auf <html>")
    if 'name="viewport"' not in html:
        fehler.append("fehlendes viewport-Meta")
    if not re.search(r"<title>[^<]+</title>", html):
        fehler.append("fehlender <title>")
    node = shutil.which("node")
    if not node:
        fehler.append("node nicht gefunden – JavaScript-Syntax nicht geprüft")
        return fehler
    for i, js in enumerate(re.findall(r"<script>(.*?)</script>", html, re.S), 1):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(js)
        r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
        Path(f.name).unlink(missing_ok=True)
        if r.returncode != 0:
            fehler.append(f"Skript {i}: {r.stderr.strip().splitlines()[0] if r.stderr else 'Syntaxfehler'}")
    return fehler


def pruefe_json(pfad: Path) -> list[str]:
    try:
        json.loads(pfad.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"ungültiges JSON: {exc}"]
    return []


def main() -> int:
    probleme = 0
    for pfad in sorted(DOCS.glob("*.html")) + sorted(DOCS.glob("*.json")):
        fehler = pruefe_html(pfad) if pfad.suffix == ".html" else pruefe_json(pfad)
        status = "OK " if not fehler else "FEHLER"
        print(f"{status} {pfad.relative_to(DOCS.parent)}")
        for f in fehler:
            print(f"      - {f}")
        probleme += len(fehler)
    return 1 if probleme else 0


if __name__ == "__main__":
    sys.exit(main())
