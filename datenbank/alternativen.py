"""Transparente Metadaten-Suche nach ähnlichen Spielen (Phase 11).

Findet technisch ähnliche Spiele über öffentliche Metadaten (Provider, RTP-Bereich,
Volatilität, Einsatz-/Max-Win-Bereich). Bewusst als On-Demand-Abfrage ausgelegt –
NICHT als vorberechneter N×N-Block im Snapshot, damit der Katalog auf tausende
Spiele skaliert.

WICHTIG: Dies ist reine Ähnlichkeit über Metadaten. Es sagt NICHT aus, welches
Spiel gewinnt oder beim nächsten Spin höhere Chancen hätte. Keine Vorhersage.
"""

from __future__ import annotations

from typing import Dict, List, Optional


def _num(v):
    return v if isinstance(v, (int, float)) else None


def aehnlichkeit(a: Dict, b: Dict) -> float:
    """Punktzahl (höher = ähnlicher) aus öffentlichen Metadaten."""
    score = 0.0
    if a.get("anbieter") and a.get("anbieter") == b.get("anbieter"):
        score += 2.0
    if a.get("vola") and a.get("vola") == b.get("vola"):
        score += 3.0
    ra, rb = _num(a.get("rtp")), _num(b.get("rtp"))
    if ra is not None and rb is not None:
        score += max(0.0, 2.0 - abs(ra - rb) * 100.0)   # ~2 Punkte bei gleichem RTP
    for feld, gew in (("minb", 1.0), ("maxb", 1.0), ("max", 1.0)):
        va, vb = _num(a.get(feld)), _num(b.get(feld))
        if va is not None and vb is not None:
            hi = max(abs(va), abs(vb), 1.0)
            score += gew * max(0.0, 1.0 - abs(va - vb) / hi)
    return round(score, 4)


def finde_alternativen(ziel: Dict, katalog: List[Dict], limit: int = 5) -> List[Dict]:
    """Die `limit` ähnlichsten Spiele zu `ziel` (ohne das Ziel selbst)."""
    kandidaten = []
    for g in katalog:
        if g is ziel or (g.get("name") == ziel.get("name")
                         and g.get("anbieter") == ziel.get("anbieter")):
            continue
        kandidaten.append((aehnlichkeit(ziel, g), g))
    kandidaten.sort(key=lambda z: (-z[0], z[1].get("name", "")))
    return [
        {"name": g.get("name"), "anbieter": g.get("anbieter"), "rtp": g.get("rtp"),
         "vola": g.get("vola"), "score": s}
        for s, g in kandidaten[:limit]
    ]


def finde_nach_name(name: str, katalog: List[Dict], limit: int = 5) -> Optional[Dict]:
    """Sucht ein Spiel per Name (case-insensitiv) und liefert seine Alternativen."""
    name_cf = (name or "").casefold()
    ziel = next((g for g in katalog if str(g.get("name", "")).casefold() == name_cf), None)
    if ziel is None:
        return None
    return {"spiel": ziel, "alternativen": finde_alternativen(ziel, katalog, limit)}
