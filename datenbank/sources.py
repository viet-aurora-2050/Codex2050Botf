"""Quellen-Adapter für den öffentlichen Spiele-Katalog (v3).

Pipeline:
    öffentliche Quellen → Source-Adapter → Validation → Normalization
    → Deduplication → Katalog (+ Source-Health)

Prinzip (ehrlich, unverändert):
  * KEINE Anbieter-API, kein Live-Casino-Feed, keine Vorhersage.
  * Der garantierte Basissatz sind öffentlich veröffentlichte Studio-RTPs.
  * Zusätzliche öffentliche JSON-Feeds werden ausdrücklich über die
    Umgebungsvariable GAMES_SOURCES (kommagetrennte URLs) konfiguriert.
    Der Tages-Job läuft serverseitig (GitHub Actions) → keine CORS-Schranke.
  * Jeder Datensatz behält seine Herkunft (Provenance). RTP ist eine
    langfristige theoretische Kennzahl und variiert je Version/Betreiber.
  * Der Ausfall einer Quelle zerstört den Katalog NICHT (Fallback bleibt).
  * `reported_recent_win` ist eine von der Quelle gemeldete Beobachtung –
    ausdrücklich KEIN Beweis und KEINE Next-Spin-Vorhersage.
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

BASIS_QUELLE = "kuratierter oeffentlicher Basissatz (veroeffentlichte Studio-RTPs)"
VOLA_OK = {"niedrig", "mittel", "hoch"}
_VOLA_ALIAS = {"low": "niedrig", "medium": "mittel", "mid": "mittel", "high": "hoch"}

# --- Basissatz (garantierter Fallback) · öffentlich veröffentlichte Studio-RTPs ---
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
    {"name": n, "anbieter": a, "rtp": r, "vola": v, "max": mx, "minb": mnb, "maxb": mxb,
     "quelle": BASIS_QUELLE, "source_type": "seed", "status": "verified-seed"}
    for (n, a, r, v, mx, mnb, mxb) in _ROH
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pick(item: Dict, *keys):
    """Erstes nicht-leeres Feld aus einer Reihe von Alias-Namen."""
    for k in keys:
        if item.get(k) not in (None, ""):
            return item[k]
    return None


def _to_float(val) -> Optional[float]:
    try:
        return float(str(val).replace("%", "").replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def _to_rtp(val) -> Optional[float]:
    """Akzeptiert 0.965, 96.5 oder '96.5%' -> Bruch. Unplausibel -> None."""
    f = _to_float(val)
    if f is None:
        return None
    if f > 1.5:
        f /= 100.0
    return round(f, 4) if 0.80 <= f <= 1.00 else None


def normalisiere(item: Dict, quelle: str) -> Optional[Dict]:
    """Rohdatensatz einer öffentlichen Quelle auf das interne Schema bringen.

    Pflichtfelder: name + anbieter. RTP darf fehlen (None) – es wird NICHTS
    erfunden. Herkunft (Provenance) bleibt erhalten.
    """
    name = str(_pick(item, "name", "title", "game_name") or "").strip()
    anb = str(_pick(item, "anbieter", "provider", "studio", "vendor") or "").strip()
    if not name or not anb:
        return None

    vola = str(_pick(item, "vola", "volatility", "variance") or "mittel").lower().strip()
    vola = _VOLA_ALIAS.get(vola, vola)
    if vola not in VOLA_OK:
        vola = "mittel"

    out: Dict = {
        "name": name,
        "anbieter": anb,
        "rtp": _to_rtp(_pick(item, "rtp", "return", "return_to_player")),
        "vola": vola,
        "quelle": quelle,
        "source_type": "public-feed",
        "status": "online",
        "last_seen": _now(),
    }
    # Numerische Zusatzfelder (nur wenn vorhanden).
    for dst, aliases in (
        ("max", ("max", "maxwin", "max_win", "max_multiplier")),
        ("minb", ("minb", "min_bet", "minimum_bet")),
        ("maxb", ("maxb", "max_bet", "maximum_bet")),
    ):
        f = _to_float(_pick(item, *aliases))
        if f is not None:
            out[dst] = round(f, 4)
    # Provenance / Varianten (nur wenn die Quelle sie liefert).
    for dst, aliases in (
        ("game_id", ("game_id", "id", "slug")),
        ("variant", ("variant", "rtp_version", "version")),
        ("source_url", ("source_url", "url", "link")),
    ):
        v = _pick(item, *aliases)
        if v not in (None, ""):
            out[dst] = str(v).strip()
    # Öffentlich gemeldeter Recent-Win (Beobachtung, KEINE Vorhersage).
    rw = _pick(item, "reported_recent_win", "recent_win", "last_win")
    if rw not in (None, ""):
        out["reported_recent_win"] = rw
        out["reported_recent_win_note"] = (
            "von der Quelle gemeldete Beobachtung – kein Beweis, keine Vorhersage"
        )
        ts = _pick(item, "recent_win_at", "win_timestamp", "timestamp")
        if ts not in (None, ""):
            out["reported_recent_win_at"] = str(ts).strip()
    return out


def _items(raw) -> List[Dict]:
    """Extrahiert die Datensatz-Liste aus verschiedenen Container-Formaten."""
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, dict):
        for key in ("spiele", "games", "items", "results", "data"):
            if isinstance(raw.get(key), list):
                return [x for x in raw[key] if isinstance(x, dict)]
    return []


def http_json_source(url: str, timeout: int = 15, max_items: int = 10000) -> Tuple[List[Dict], Dict]:
    """Lädt einen öffentlichen JSON-Feed. Rückgabe: (Spiele, Health-Meta).

    Robust: Timeout, Datensatz-Deckel, Content-Type-Prüfung, saubere
    Exception-Behandlung. Ein Fehler liefert ([], meta{status:offline}).
    """
    meta: Dict = {"url": url, "status": "offline", "fetched_at": _now(), "records_received": 0}
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Codex2050Games/3.0", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "json" not in ctype:
                raise ValueError(f"unerwarteter Content-Type: {ctype or 'unbekannt'}")
            raw = json.loads(resp.read().decode("utf-8"))
        games = []
        for it in _items(raw)[:max_items]:
            g = normalisiere(it, quelle=url)
            if g:
                games.append(g)
        meta.update(status="online", records_received=len(games))
        return games, meta
    except Exception as exc:  # noqa: BLE001 – Quelle darf ausfallen, Katalog bleibt
        meta["error"] = f"{type(exc).__name__}: {exc}"
        print(f"[warnung] Quelle offline: {url} ({meta['error']})")
        return [], meta


def _dedupe_key(g: Dict) -> Tuple:
    """Logischer Schlüssel: game_id falls vorhanden, sonst Provider+Name+Variante.

    Unterschiedliche RTP-Versionen (variant) werden NICHT fälschlich vereint.
    """
    gid = g.get("game_id")
    if gid:
        return ("id", str(gid).casefold())
    return ("nm", g["anbieter"].casefold(), g["name"].casefold(), str(g.get("variant", "")).casefold())


def sammle(urls: Optional[List[str]] = None,
           timeout: Optional[int] = None,
           max_items: Optional[int] = None) -> Tuple[List[Dict], List[Dict]]:
    """Basissatz + konfigurierte öffentliche Feeds → (Katalog, Source-Status).

    Feeds überschreiben den Basissatz beim selben logischen Schlüssel (frischer).
    Ein Quellen-Ausfall wird dokumentiert; der Basissatz bleibt erhalten.
    """
    if urls is None:
        env = os.getenv("GAMES_SOURCES", "").strip()
        urls = [u.strip() for u in env.split(",") if u.strip()]
    if timeout is None:
        timeout = int(os.getenv("GAMES_TIMEOUT", "15"))
    if max_items is None:
        max_items = int(os.getenv("GAMES_MAX_ITEMS", "10000"))

    merged: Dict[Tuple, Dict] = {_dedupe_key(g): dict(g) for g in SEED_GAMES}
    states: List[Dict] = []
    for url in urls:
        games, meta = http_json_source(url, timeout=timeout, max_items=max_items)
        states.append(meta)
        for g in games:
            merged[_dedupe_key(g)] = g

    katalog = sorted(merged.values(), key=lambda g: (g["anbieter"].casefold(), g["name"].casefold()))
    return katalog, states
