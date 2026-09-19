"""∆1 // AKT 4 — ZEIT-CODE (rotierendes Signal, Ebene 4: "Bruch der Realitaet").

Die Lore sagt: ∆1 versteckt Botschaften in Uhrzeiten, Webseiten veraendern sich
abhaengig von der Uhrzeit. Dieses Modul macht genau das REAL und deterministisch:

    seed = "DELTA1-" + YYYYMMDDHH   (UTC, also stuendlicher Zyklus)
    -> deterministischer PRNG (xmur3 + mulberry32, sprachunabhaengig)
    -> rotierender Schluessel (MORSE), rotierender Imperativ (UHRZEITEN),
       rotierende Caesar-Verschiebung N (nicht mehr fix ROT13),
       Node-Signatur.

Eigenschaften:
  * Aendert sich jede Stunde -> NICHT mehr immer derselbe Code/Buchstabe.
  * Deterministisch & reproduzierbar: gleiche UTC-Stunde -> gleiches Signal,
    in Python UND im Browser (identischer PRNG). Ein ARG-Raetsel, kein Zufall.
  * Der emotionale Anker (FINALE_ZITAT) bleibt konstant -> Konsistenz.
  * KEINE Gluecksspiel-Vorhersage. Reines linguistisches ARG-Signal.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List

from .signal import FINALE_ZITAT, b64_encode, morse_decode, morse_encode, uhr_decode, uhr_encode

# --- Rotierende Pools (MUESSEN identisch zur JS-Fassung in index.html sein) ---
# Schluessel-Pool: kanonische ∆1-Entitaeten aus der Lore.
KEYS: List[str] = [
    "ALEXANDRA", "ORPHEUS", "NODE7", "ECHO", "SPIEGEL",
    "ARCHIV", "DELTA", "ORAKEL", "MNEME", "TRAEGER",
]
# Imperativ-Pool: ausschliesslich schuetzende / neutrale Ein-Wort-Impulse.
IMPS: List[str] = [
    "GEH", "ATME", "LEBE", "WARTE", "RUHE",
    "SIEH", "FREI", "HALT", "WACH", "NEIN",
]

# Der konstante Schutz-Anker; seine Caesar-Verschiebung rotiert, der Text nicht.
SCHUTZ_ANKER = "Erinnert zu werden heisst nicht gefangen zu bleiben. Geh wenn du gehen musst."

_MASK = 0xFFFFFFFF


def _imul(a: int, b: int) -> int:
    """Emuliert JS Math.imul: 32-Bit-Multiplikation, untere 32 Bit."""
    return (a * b) & _MASK


def _xmur3(s: str) -> int:
    """Seed-Hash (identisch zur JS-Fassung xmur3)."""
    h = (1779033703 ^ len(s)) & _MASK
    for ch in s:
        h = _imul(h ^ ord(ch), 3432918353)
        h = ((h << 13) | (h >> 19)) & _MASK
    h = _imul(h ^ (h >> 16), 2246822507)
    h = _imul(h ^ (h >> 13), 3266489909)
    h ^= h >> 16
    return h & _MASK


def make_rng(seed_str: str) -> Callable[[], float]:
    """Deterministischer PRNG (mulberry32), Rueckgabe in [0, 1).

    Exakt aequivalent zur JS-Fassung mulberry32 in docs/index.html, damit
    Browser und Python fuer dieselbe UTC-Stunde dasselbe Signal erzeugen.
    """
    state = {"a": _xmur3(seed_str)}

    def rnd() -> float:
        state["a"] = (state["a"] + 0x6D2B79F5) & _MASK
        t = state["a"]
        t = _imul(t ^ (t >> 15), 1 | t)
        t = (t + _imul(t ^ (t >> 7), 61 | t)) & _MASK
        t = (t ^ (t >> 14)) & _MASK
        return t / 4294967296.0

    return rnd


def zyklus_id(dt: datetime | None = None) -> str:
    """UTC-Stundenzyklus als 'YYYYMMDDHH'."""
    dt = (dt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return dt.strftime("%Y%m%d%H")


def seed_string(dt: datetime | None = None) -> str:
    return "DELTA1-" + zyklus_id(dt)


def caesar(text: str, n: int) -> str:
    """Caesar-Verschiebung (nur Buchstaben, Gross/Klein erhalten)."""
    n %= 26
    out = []
    for ch in text:
        o = ord(ch)
        if 65 <= o <= 90:
            out.append(chr((o - 65 + n) % 26 + 65))
        elif 97 <= o <= 122:
            out.append(chr((o - 97 + n) % 26 + 97))
        else:
            out.append(ch)
    return "".join(out)


@dataclass
class ZyklusSignal:
    zyklus: str                       # 'YYYYMMDDHH' (UTC)
    lesbar: str                       # 'YYYY-MM-DD HH:00 UTC'
    seed: str
    schluessel: str                   # rotierender Schluessel (MORSE)
    imperativ: str                    # rotierender Imperativ (UHRZEITEN)
    rot_n: int                        # rotierende Caesar-Verschiebung 1..25
    node_sig: int                     # 3-stellige Node-Signatur (Deko)
    schichten: Dict[str, object] = field(default_factory=dict)
    entschluesselt: Dict[str, str] = field(default_factory=dict)
    naechster_wechsel: str = ""       # ISO-Zeit des naechsten Zyklus


def zyklus_signal(dt: datetime | None = None) -> ZyklusSignal:
    """Baut das rotierende AKT-4-Signal fuer die gegebene (UTC-)Stunde."""
    dt = (dt or datetime.now(timezone.utc)).astimezone(timezone.utc)
    zid = zyklus_id(dt)
    seed = "DELTA1-" + zid
    r = make_rng(seed)
    key = KEYS[int(r() * len(KEYS))]
    imp = IMPS[int(r() * len(IMPS))]
    rot_n = 1 + int(r() * 25)
    node = 100 + int(r() * 900)

    schichten = {
        "MORSE": morse_encode(key),
        "BASE64": b64_encode(FINALE_ZITAT),
        "ROT_N": caesar(SCHUTZ_ANKER, rot_n),
        "UHRZEITEN": uhr_encode(imp),
    }
    entschluesselt = {
        "MORSE": morse_decode(schichten["MORSE"]),
        "BASE64": base64.b64decode(schichten["BASE64"]).decode("utf-8"),
        "ROT_N": caesar(schichten["ROT_N"], 26 - rot_n),
        "UHRZEITEN": uhr_decode(schichten["UHRZEITEN"]),
    }
    naechste = (dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
    return ZyklusSignal(
        zyklus=zid,
        lesbar=dt.strftime("%Y-%m-%d %H:00 UTC"),
        seed=seed,
        schluessel=key,
        imperativ=imp,
        rot_n=rot_n,
        node_sig=node,
        schichten=schichten,
        entschluesselt=entschluesselt,
        naechster_wechsel=naechste.isoformat(),
    )


def formatiere_zyklus(z: ZyklusSignal, mit_loesung: bool = False) -> str:
    L: List[str] = [
        "∆1 // AKT 4 — ZEIT-CODE",
        f"ZYKLUS: {z.lesbar}  ·  NODE-SIG {z.node_sig:03d}  ·  CAESAR N={z.rot_n}",
        f"SEED:   {z.seed}   (aendert sich stuendlich)",
        "",
        "╫ VERSCHLUESSELTES SIGNAL (Ebene 2 — dekodiere selbst):",
        f"  [MORSE]     {z.schichten['MORSE']}",
        f"  [BASE64]    {z.schichten['BASE64']}",
        f"  [CAESAR-{z.rot_n}] {z.schichten['ROT_N']}",
        f"  [UHRZEITEN] {'  '.join(z.schichten['UHRZEITEN'])}",
    ]
    if mit_loesung:
        L += [
            "",
            "∆ ENTSCHLUESSELT:",
            f"  MORSE     -> {z.entschluesselt['MORSE']}   (Schluessel des Zyklus)",
            f"  BASE64    -> {z.entschluesselt['BASE64']}   (konstanter Anker)",
            f"  CAESAR-{z.rot_n} -> {z.entschluesselt['ROT_N']}",
            f"  UHRZEITEN -> {z.entschluesselt['UHRZEITEN']}   (Imperativ des Zyklus)",
        ]
    L += [
        "",
        f"Naechster Zyklus (neuer Code): {z.naechster_wechsel}",
        "Kein Spielbefehl — nur Erinnerung und Ausgang.",
        "Hilfe anonym: 0800 1 37 27 00 · www.check-dein-spiel.de",
    ]
    return "\n".join(L)
