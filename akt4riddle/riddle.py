"""Akt4GameRiddleDecoder – reproduzierbarer Decoder für die AKT-4-Rätselkette.

Kette (keine Blackbox):
    Morse → Base64 → ROT13 → Uhrzeit → Alphabet → Game-Titel → Buchstaben → Wort

Wichtig:
  - KEINE Glücksspiel-Vorhersage. Game-Titel sind reine Buchstaben-/Wortschlüssel.
  - Game-Namen werden NICHT erfunden. Ohne verifizierbaren Treffer: NO VERIFIED MATCH.
  - Anti-Zufall: das Ergebnis gilt nicht als „gelöst", nur weil eine Kombination
    ein sinnvolles Wort ergibt – die Kette wird explizit validiert.

Dieses Modul verändert NICHTS am bestehenden CODEX2050. Es ist eine zusätzliche
Schicht mit eigenem Namespace.
"""

from __future__ import annotations

import base64
import codecs
from dataclasses import dataclass, field
from typing import Dict, List, Optional

MORSE_INV: Dict[str, str] = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
    "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
    "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z",
}


# ---------------------------------------------------------------- Decoder-Ebenen
def decode_morse(code: str) -> str:
    out = []
    for tok in (code or "").split(" "):
        if tok == "/":
            out.append(" ")
        elif tok in MORSE_INV:
            out.append(MORSE_INV[tok])
    return "".join(out)


def decode_base64(text: str) -> str:
    try:
        return base64.b64decode((text or "").encode("ascii")).decode("utf-8")
    except Exception:
        return ""


def decode_rot13(text: str) -> str:
    return codecs.encode(text or "", "rot_13")


def clock_to_letter(hhmm: str) -> Optional[str]:
    """'07:07' -> Stunde 7 -> 'G'. Nur 1..26 zulässig, sonst None (eindeutig?)."""
    try:
        stunde = int((hhmm or "").split(":")[0])
    except (ValueError, IndexError):
        return None
    if 1 <= stunde <= 26:
        return chr(ord("A") + stunde - 1)
    return None


def clock_letters(times: List[str]) -> List[dict]:
    res = []
    for t in times:
        st = None
        try:
            st = int(t.split(":")[0])
        except (ValueError, IndexError):
            st = None
        res.append({"time": t, "hour": st, "letter": clock_to_letter(t)})
    return res


# ---------------------------------------------------------------- Game-Matching
@dataclass
class Game:
    title: str
    provider: str = ""
    source: str = ""
    verified: bool = False


def _norm(s: str) -> str:
    return (s or "").strip().lstrip("„\"'").strip()


def find_game_matches(letter: str, games: List[Game]) -> List[Game]:
    """Alle Games, deren Titel mit `letter` beginnt. Erfindet nichts."""
    if not letter:
        return []
    L = letter.upper()
    return [g for g in games if _norm(g.title)[:1].upper() == L]


@dataclass
class Kandidat:
    letter: str
    time: str
    matches: List[Game] = field(default_factory=list)

    @property
    def status(self) -> str:
        if not self.letter:
            return "CLOCK INVALID"
        if not self.matches:
            return "NO VERIFIED MATCH"
        if not any(g.verified for g in self.matches):
            return "NO VERIFIED MATCH"
        if len(self.matches) == 1:
            return "VERIFIED"
        return "MULTIPLE CANDIDATES"

    @property
    def confidence(self) -> str:
        st = self.status
        if st == "VERIFIED":
            # Primärquelle -> HIGH, Fallback -> MEDIUM
            src = (self.matches[0].source or "").lower()
            return "HIGH" if ("primaer" in src or "primär" in src or "extern" in src) else "MEDIUM"
        if st == "MULTIPLE CANDIDATES":
            return "LOW"
        return "UNKNOWN"


def match_chain(times: List[str], games: List[Game]) -> List[Kandidat]:
    out = []
    for cl in clock_letters(times):
        L = cl["letter"]
        out.append(Kandidat(letter=L or "", time=cl["time"],
                            matches=find_game_matches(L, games) if L else []))
    return out


# ---------------------------------------------------------------- Validierung
def riddle_validation(times: List[str], games: List[Game]) -> Dict[str, object]:
    """7 Prüfungen gegen Zufallstreffer und erfundene Zuordnungen."""
    ketten = match_chain(times, games)
    wort = "".join(k.letter for k in ketten)
    checks = {
        "1_buchstabe_eindeutig": all(k.letter for k in ketten),
        "2_game_existiert": all(k.matches for k in ketten),
        "3_titel_verifiziert": all(any(g.verified for g in k.matches) for k in ketten) if all(k.matches for k in ketten) else False,
        "4_mehrere_treffer": any(len(k.matches) > 1 for k in ketten),
        "5_unabhaengige_bestaetigung": all(
            len({g.source for g in k.matches if g.verified}) >= 2 for k in ketten
        ) if all(k.matches for k in ketten) else False,
        "6_ergibt_sinnvolles_wort": wort.isalpha() and len(wort) >= 2,
        "7_moeglicherweise_zufall": (not all(k.status == "VERIFIED" for k in ketten)),
    }
    return {"wort": wort, "ketten": ketten, "checks": checks}


def sancho_check(times: List[str], games: List[Game], rot13_ok: bool = True) -> Dict[str, str]:
    v = riddle_validation(times, games)
    ketten: List[Kandidat] = v["ketten"]
    if all(k.status == "VERIFIED" and k.confidence == "HIGH" for k in ketten):
        title_status, conf = "OK", "HIGH"
    elif all(k.matches and any(g.verified for g in k.matches) for k in ketten):
        title_status, conf = "PARTIAL", "MEDIUM"
    elif any(k.matches for k in ketten):
        title_status, conf = "PARTIAL", "LOW"
    else:
        title_status, conf = "FAILED", "LOW"
    unabh = "OK" if v["checks"]["5_unabhaengige_bestaetigung"] else "NOT AVAILABLE"
    return {
        "decoded_text": "OK" if rot13_ok else "UNKNOWN",
        "clock_conversion": "OK" if all(k.letter for k in ketten) else "UNKNOWN",
        "game_title_verification": title_status,
        "independent_confirmation": unabh,
        "final_interpretation": v["wort"] or "UNKNOWN",
        "confidence": conf,
    }
