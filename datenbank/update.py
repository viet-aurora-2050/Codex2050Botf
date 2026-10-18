"""Erzeugt docs/games.json aus dem Basissatz + konfigurierten öffentlichen Feeds.

Aufruf:
    python -m datenbank                 # schreibt docs/games.json
    python -m datenbank --dry-run       # nur Vorschau, nichts schreiben
    python -m datenbank --out pfad.json # anderes Ziel

Der GitHub-Actions-Job ruft dies täglich auf. `stand`/`generiert` bleiben beim
Datum der letzten inhaltlichen Änderung; `geprueft` wird bei jedem Lauf (höchstens
einmal pro Tag) aktualisiert. So zeigt die App „Daten unverändert, aber heute geprüft“
statt fälschlich „veraltet“.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Dict, List

from .sources import BASIS_QUELLE, sammle

HINWEIS = (
    "Automatisch taeglich erzeugt aus dem oeffentlichen Basissatz + optionalen "
    "oeffentlichen JSON-Feeds (GAMES_SOURCES). Oeffentlich veroeffentlichte "
    "Standard-RTPs - variieren je Version/Betreiber, immer gegen die offizielle "
    "Spielinfo pruefen. Keine Anbieter-API, keine Vorhersage."
)


def baue(urls=None) -> Dict:
    spiele: List[Dict] = sammle(urls)
    quellen = sorted({g.get("quelle", BASIS_QUELLE) for g in spiele})
    jetzt = datetime.now(timezone.utc)
    return {
        "_hinweis": HINWEIS,
        "stand": jetzt.strftime("%Y-%m-%d"),
        "generiert": jetzt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "geprueft": jetzt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "quellen": quellen,
        "anzahl": len(spiele),
        "spiele": spiele,
    }


def _default_out() -> str:
    hier = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(hier), "docs", "games.json")


def schreibe(daten: Dict, pfad: str) -> bool:
    """Schreibt die Daten, wenn sich die Spiele inhaltlich geaendert haben.

    Vergleich ignoriert die Zeitstempel. Bleibt der Kern gleich, behaelt die Datei
    `stand`/`generiert`; nur `geprueft` wird (hoechstens einmal pro Tag) erneuert.
    Rueckgabe: True = Inhalt geaendert und geschrieben.
    """
    neu_kern = json.dumps(daten["spiele"], ensure_ascii=False, sort_keys=True)
    if os.path.exists(pfad):
        try:
            with open(pfad, encoding="utf-8") as f:
                alt = json.load(f)
            if json.dumps(alt.get("spiele", []), ensure_ascii=False, sort_keys=True) == neu_kern:
                if str(alt.get("geprueft", ""))[:10] != daten["geprueft"][:10]:
                    alt["geprueft"] = daten["geprueft"]
                    with open(pfad, "w", encoding="utf-8") as f:
                        json.dump(alt, f, ensure_ascii=False, indent=2)
                        f.write("\n")
                return False
        except (json.JSONDecodeError, OSError):
            pass
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Erzeuge docs/games.json")
    ap.add_argument("--out", default=_default_out())
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    daten = baue()
    print(f"{daten['anzahl']} Spiele aus {len(daten['quellen'])} Quelle(n): "
          f"{', '.join(daten['quellen'])}")
    if args.dry_run:
        print(json.dumps(daten, ensure_ascii=False, indent=2))
        return 0
    geaendert = schreibe(daten, args.out)
    print(("geschrieben: " if geaendert else "unveraendert (Kerninhalt gleich): ") + args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
