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

# Strenge Barrierefreiheits-Pruefung (Labels, Live-Regionen) fuer diese Seiten. sancho.html ist
# bewusst NICHT enthalten: das Sancho-Modul bleibt auf Wunsch unveraendert.
A11Y_STRENG = {"index.html", "akt4-decoder.html"}


def pruefe_html(pfad: Path) -> list[str]:
    fehler: list[str] = []
    html = pfad.read_text(encoding="utf-8")
    if not re.search(r"<html[^>]*\blang=", html):
        fehler.append("fehlendes lang-Attribut auf <html>")
    if 'name="viewport"' not in html:
        fehler.append("fehlendes viewport-Meta")
    if not re.search(r"<title>[^<]+</title>", html):
        fehler.append("fehlender <title>")
    if pfad.name in A11Y_STRENG:
        fehler += pruefe_a11y(html)
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


def pruefe_a11y(html: str) -> list[str]:
    """Jedes Formularfeld braucht ein <label for=...> (oder aria-label); Ergebnisse brauchen aria-live."""
    fehler: list[str] = []
    ohne_for = re.findall(r"<label(?![^>]*\bfor=)[^>]*>\s*([^<]{3,60})", html)
    nackt = [m for m in ohne_for if not re.search(r"<label[^>]*>[^<]*" + re.escape(m[:10]) + r"[\s\S]{0,80}<input", html)]
    for text in nackt:
        fehler.append(f"label ohne for=: {text.strip()[:40]!r}")
    for tag, attrs in re.findall(r"<(input|select|textarea)\b([^>]*)>", html):
        m = re.search(r'\bid="([^"]+)"', attrs)
        if re.search(r'type="(hidden|checkbox)"', attrs) and not m:
            continue
        if not m:
            if "aria-label" not in attrs:
                fehler.append(f"<{tag}> ohne id/aria-label")
        elif f'for="{m.group(1)}"' not in html and "aria-label" not in attrs and 'onchange="Akt4' not in attrs:
            fehler.append(f"<{tag} id={m.group(1)}> ohne zugehöriges label")
    if "aria-live" not in html:
        fehler.append("keine aria-live-Region für Ergebnisse")
    if "Content-Security-Policy" not in html:
        fehler.append("fehlende Content-Security-Policy (meta)")
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
