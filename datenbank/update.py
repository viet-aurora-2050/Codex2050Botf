"""Erzeugt docs/games.json — generierter Snapshot des öffentlichen Katalogs (v3).

Aufruf:
    python -m datenbank                       # schreibt docs/games.json
    python -m datenbank --dry-run             # Vorschau, nichts schreiben
    python -m datenbank --out pfad.json       # anderes Ziel
    python -m datenbank --alternativen "Name" # ähnliche Spiele (Metadaten)

Der GitHub-Actions-Job ruft `python -m datenbank` täglich auf. Es wird nur
geschrieben, wenn sich der KERN-Inhalt tatsächlich ändert (Zeitstempel und
Source-Status allein lösen keinen Commit aus).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .alternativen import finde_nach_name
from .sources import BASIS_QUELLE, sammle

SCHEMA_VERSION = "3.0"
HINWEIS = (
    "Oeffentlicher Spiele-Katalog (generierter Snapshot). RTP ist eine langfristige "
    "theoretische Kennzahl und variiert je Operator/Jurisdiktion/Version. Quelle je "
    "Datensatz erhalten. Keine Anbieter-API, keine Vorhersage. `reported_recent_win` "
    "ist eine von der Quelle gemeldete Beobachtung – kein Beweis, keine Next-Spin-Aussage."
)


def _statistik(games: List[Dict]) -> Dict:
    rtps = [g["rtp"] for g in games if isinstance(g.get("rtp"), (int, float))]
    return {
        "anbieter": len({g.get("anbieter") for g in games if g.get("anbieter")}),
        "rtp_bekannt": len(rtps),
        "rtp_min": round(min(rtps), 4) if rtps else None,
        "rtp_max": round(max(rtps), 4) if rtps else None,
        "rtp_schnitt": round(sum(rtps) / len(rtps), 4) if rtps else None,
    }


def baue(urls=None) -> Dict:
    """Baut den Snapshot. `urls=[]` erzwingt reinen Basissatz (für Tests)."""
    spiele, states = sammle(urls)
    jetzt = datetime.now(timezone.utc)
    return {
        "schema_version": SCHEMA_VERSION,
        "_hinweis": HINWEIS,
        "stand": jetzt.strftime("%Y-%m-%d"),
        "generiert": jetzt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "quellen": sorted({g.get("quelle", BASIS_QUELLE) for g in spiele}),
        "source_status": states,
        "anzahl": len(spiele),
        "statistik": _statistik(spiele),
        "spiele": spiele,
    }


def _default_out() -> str:
    return str(Path(__file__).resolve().parents[1] / "docs" / "games.json")


def _kern(d: Dict) -> str:
    """Vergleichs-Kern OHNE volatile Felder (stand/generiert/source_status).

    So löst ein reiner Zeitstempel- oder Source-Health-Wechsel KEINEN Commit aus.
    """
    x = dict(d)
    for k in ("stand", "generiert", "source_status"):
        x.pop(k, None)
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def schreibe(data: Dict, pfad: str) -> bool:
    """Atomar schreiben, aber nur bei echter Kern-Änderung. True = geschrieben."""
    p = Path(pfad)
    if p.exists():
        try:
            if _kern(json.loads(p.read_text(encoding="utf-8"))) == _kern(data):
                return False
        except (OSError, json.JSONDecodeError):
            pass
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Erzeuge docs/games.json (v3-Katalog)")
    ap.add_argument("--out", default=_default_out())
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--alternativen", metavar="NAME", help="Ähnliche Spiele zu NAME zeigen")
    args = ap.parse_args(argv)

    daten = baue()

    if args.alternativen:
        res = finde_nach_name(args.alternativen, daten["spiele"])
        if not res:
            print(f"Kein Spiel gefunden: {args.alternativen}")
            return 1
        print(f"Ähnliche Spiele zu {res['spiel']['name']} ({res['spiel']['anbieter']}):")
        for a in res["alternativen"]:
            rtp = f"{a['rtp']*100:.2f}%" if isinstance(a["rtp"], (int, float)) else "—"
            print(f"  {a['name']} · {a['anbieter']} · RTP {rtp} · Vola {a['vola']} · Score {a['score']}")
        return 0

    online = sum(1 for s in daten["source_status"] if s.get("status") == "online")
    print(f"{daten['anzahl']} Spiele · {daten['statistik']['anbieter']} Anbieter · "
          f"{len(daten['source_status'])} externe Quelle(n) ({online} online)")
    if args.dry_run:
        print(json.dumps(daten, ensure_ascii=False, indent=2))
        return 0
    geaendert = schreibe(daten, args.out)
    print(("geschrieben: " if geaendert else "unveraendert (Kern gleich): ") + args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
