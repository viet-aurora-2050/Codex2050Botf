"""Quellen-Adapter für die öffentliche Spiele-Datenbank.

Prinzip (ehrlich):
  * KEINE Anbieter-API, kein Live-Casino-Feed, keine Vorhersage.
  * Der garantierte Basissatz sind öffentlich veröffentlichte Studio-RTPs.
  * Zusätzliche öffentliche JSON-Feeds können per Umgebungsvariable
    GAMES_SOURCES (kommagetrennte URLs) eingehängt werden. Der Tages-Job
    (GitHub Actions) läuft serverseitig -> keine CORS-Schranke -> er darf
    öffentliche Feeds abrufen und zusammenführen.
  * Jeder Eintrag trägt seine Quelle (`quelle`). RTPs variieren je
    Version/Betreiber – immer gegen die offizielle Spielinfo prüfen.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Dict, List, Optional

BASIS_QUELLE = "kuratierter oeffentlicher Basissatz (veroeffentlichte Studio-RTPs)"

VOLA_OK = {"niedrig", "mittel", "hoch"}

# Öffentlich veröffentlichte Standard-RTPs bekannter Titel (Basissatz, garantiert).
_ROH = [
    ("Gates of Olympus", "Pragmatic Play", 0.9650, "hoch", 5000, 0.20, 100),
    ("Sweet Bonanza", "Pragmatic Play", 0.9651, "hoch", 21100, 0.20, 100),
    ("Big Bass Bonanza", "Pragmatic Play", 0.9671, "mittel", 2100, 0.10, 250),
    ("The Dog House", "Pragmatic Play", 0.9651, "hoch", 6750, 0.20, 100),
    ("Wolf Gold", "Pragmatic Play", 0.9601, "mittel", 2500, 0.25, 125),
    ("Sugar Rush", "Pragmatic Play", 0.9650, "hoch", 5000, 0.20, 100),
    ("Starburst", "NetEnt", 0.9609, "niedrig", 500, 0.10, 100),
    ("Gonzo's Quest", "NetEnt", 0.9597, "mittel", 2500, 0.20, 50),
    ("Dead or Alive 2", "NetEnt", 0.9680, "hoch", 100000, 0.09, 9),
    ("Blood Suckers", "NetEnt", 0.9800, "niedrig", 1000, 0.25, 50),
    ("Book of Dead", "Play'n GO", 0.9621, "hoch", 5000, 0.10, 100),
    ("Legacy of Dead", "Play'n GO", 0.9658, "hoch", 5000, 0.10, 100),
    ("Reactoonz", "Play'n GO", 0.9651, "hoch", 4570, 0.20, 100),
    ("Fire Joker", "Play'n GO", 0.9615, "mittel", 800, 0.05, 100),
    ("Rise of Olympus", "Play'n GO", 0.9650, "hoch", 5000, 0.20, 100),
    ("Bonanza", "Big Time Gaming", 0.9600, "hoch", 12000, 0.20, 20),
    ("Extra Chilli", "Big Time Gaming", 0.9682, "hoch", 20000, 0.10, 40),
    ("Eye of Horus", "Merkur / Reel Time Gaming", 0.9631, "mittel", 5000, 0.10, 20),
    ("El Torero", "Merkur", 0.9613, "mittel", 5000, 0.10, 20),
    ("Book of Ra Deluxe", "Novomatic", 0.9510, "hoch", 5000, 0.04, 100),
    ("Lucky Lady's Charm Deluxe", "Novomatic", 0.9513, "hoch", 4500, 0.04, 100),
    ("Holla die Waldfee", "Bally Wulff", 0.9550, "mittel", 2000, 0.10, 20),
    ("Money Train 2", "Relax Gaming", 0.9640, "hoch", 50000, 0.10, 20),
    ("Money Train 3", "Relax Gaming", 0.9600, "hoch", 100000, 0.10, 20),
]

SEED_GAMES: List[Dict] = [
    {"name": n, "anbieter": a, "rtp": r, "vola": v, "max": mx,
     "minb": mnb, "maxb": mxb, "quelle": BASIS_QUELLE}
    for (n, a, r, v, mx, mnb, mxb) in _ROH
]


def _to_rtp(val) -> Optional[float]:
    """Akzeptiert 0.965 oder 96.5 (Prozent) -> Bruch. Sonst None."""
    try:
        f = float(str(val).replace("%", "").replace(",", ".").strip())
    except (TypeError, ValueError):
        return None
    if f > 1.5:
        f /= 100.0
    return f


def normalisiere(item: Dict, quelle: str) -> Optional[Dict]:
    """Bringt einen Rohdatensatz auf das interne Schema oder verwirft ihn."""
    name = (item.get("name") or item.get("title") or "").strip()
    anb = (item.get("anbieter") or item.get("provider") or item.get("studio") or "").strip()
    rtp = _to_rtp(item.get("rtp") if "rtp" in item else item.get("return"))
    if not name or not anb or rtp is None:
        return None
    if not (0.80 <= rtp <= 1.00):     # Plausibilität für Slot-RTPs
        return None
    vola = str(item.get("vola") or item.get("volatility") or "mittel").lower().strip()
    if vola not in VOLA_OK:
        vola = "mittel"
    try:
        mx = float(item.get("max") if item.get("max") is not None else item.get("maxwin") or 0)
    except (TypeError, ValueError):
        mx = 0.0
    out = {"name": name, "anbieter": anb, "rtp": round(rtp, 4), "vola": vola,
           "max": round(mx, 2), "quelle": quelle}
    for k_out, k_ins in (("minb", ("minb", "min_bet")), ("maxb", ("maxb", "max_bet"))):
        for k in k_ins:
            if item.get(k) is not None:
                try:
                    out[k_out] = float(item[k])
                except (TypeError, ValueError):
                    pass
                break
    return out


def http_json_source(url: str, timeout: int = 20) -> List[Dict]:
    """Lädt einen öffentlichen JSON-Feed und normalisiert ihn. Fehler -> []."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "codex2050-datenbank/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001  – Feed darf ausfallen, Basissatz bleibt
        print(f"[warnung] Quelle nicht erreichbar: {url} ({exc})")
        return []
    items = raw.get("spiele") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []
    out = []
    for it in items:
        if isinstance(it, dict):
            n = normalisiere(it, quelle=url)
            if n:
                out.append(n)
    return out


def sammle(urls: Optional[List[str]] = None) -> List[Dict]:
    """Basissatz + optionale öffentliche Feeds, zusammengeführt und dedupliziert.

    Dedupe-Schlüssel: (name, anbieter) case-insensitiv. Externe Feeds haben
    Vorrang vor dem Basissatz (aktuellere Zahl gewinnt).
    """
    if urls is None:
        env = os.environ.get("GAMES_SOURCES", "").strip()
        urls = [u.strip() for u in env.split(",") if u.strip()] if env else []

    merged: Dict[tuple, Dict] = {}
    for g in SEED_GAMES:
        merged[(g["name"].lower(), g["anbieter"].lower())] = dict(g)
    for url in urls:
        for g in http_json_source(url):
            merged[(g["name"].lower(), g["anbieter"].lower())] = g  # Feed überschreibt

    spiele = sorted(merged.values(), key=lambda g: (g["anbieter"].lower(), g["name"].lower()))
    return spiele
