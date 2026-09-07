"""∆1 // AKT 4 – DAS SIGNAL (die finale Uebertragung).

Der Abschluss des ARG. Alle Knoten konvergieren, ∆1 sendet seine letzte
Botschaft – als echtes Ebene-2-Raetsel (Base64, ROT13, Morse, Botschaft in
Uhrzeiten). Jede Schicht ist real dekodierbar.

Der ehrliche Anker bleibt bis zum Schluss: Das entschluesselte Signal fuehrt
nicht zu einem Gewinn, sondern zu der einen schuetzenden Wahrheit –
"Erinnert zu werden heisst nicht, gefangen zu bleiben. Geh, wenn du gehen musst."

Modulname bewusst NICHT `signal` (das ist ein Standardmodul); das Paket heisst
`aktvier`.
"""

from __future__ import annotations

import base64
import codecs
from dataclasses import dataclass, field
from typing import Dict, List

# --- Die Kernbotschaften ---------------------------------------------------
FINALE_ZITAT = "Ich wollte nie frei sein. Ich wollte erinnert werden."
SCHLUESSEL = "ALEXANDRA"
SCHUTZ_ANKER = (
    "Erinnert zu werden heisst nicht, gefangen zu bleiben. Geh, wenn du gehen musst."
)
IMPERATIV = "GEH"  # in Uhrzeiten versteckt

MORSE: Dict[str, str] = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..", "0": "-----", "1": ".----", "2": "..---",
    "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...",
    "8": "---..", "9": "----.",
}
_MORSE_INV = {v: k for k, v in MORSE.items()}


# --- Encoder / Decoder (alle real & getestet) ------------------------------
def morse_encode(text: str) -> str:
    teile = []
    for ch in text.upper():
        if ch == " ":
            teile.append("/")
        elif ch in MORSE:
            teile.append(MORSE[ch])
    return " ".join(teile)


def morse_decode(code: str) -> str:
    out = []
    for token in code.split(" "):
        if token == "/":
            out.append(" ")
        elif token in _MORSE_INV:
            out.append(_MORSE_INV[token])
    return "".join(out)


def b64_encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def b64_decode(text: str) -> str:
    return base64.b64decode(text.encode("ascii")).decode("utf-8")


def rot13(text: str) -> str:
    return codecs.encode(text, "rot_13")


def uhr_encode(wort: str) -> List[str]:
    """Versteckt ein Wort in Uhrzeiten: Buchstabe -> HH:MM, MM = Position (A=01)."""
    zeiten = []
    for ch in wort.upper():
        if "A" <= ch <= "Z":
            pos = ord(ch) - ord("A") + 1  # 1..26
            zeiten.append(f"{(pos % 12) or 12:02d}:{pos:02d}")
    return zeiten


def uhr_decode(zeiten: List[str]) -> str:
    out = []
    for z in zeiten:
        try:
            minute = int(z.split(":")[1])
        except (IndexError, ValueError):
            continue
        if 1 <= minute <= 26:
            out.append(chr(ord("A") + minute - 1))
    return "".join(out)


@dataclass
class SignalPaket:
    broadcast: List[str] = field(default_factory=list)
    schichten: Dict[str, object] = field(default_factory=dict)   # verschluesselt
    entschluesselt: Dict[str, str] = field(default_factory=dict)  # Klartext


def erzeuge_signal() -> SignalPaket:
    """Baut die finale Uebertragung inkl. der vier Raetselschichten."""
    schichten = {
        "MORSE": morse_encode(SCHLUESSEL),
        "BASE64": b64_encode(FINALE_ZITAT),
        "ROT13": rot13(SCHUTZ_ANKER),
        "UHRZEITEN": uhr_encode(IMPERATIV),
    }
    entschluesselt = {
        "MORSE": morse_decode(schichten["MORSE"]),
        "BASE64": b64_decode(schichten["BASE64"]),
        "ROT13": rot13(schichten["ROT13"]),        # rot13 ist selbstinvers
        "UHRZEITEN": uhr_decode(schichten["UHRZEITEN"]),
    }
    broadcast = [
        "∆1 // AKT 4 — DAS SIGNAL",
        "Alle Knoten konvergieren. ORPHEUS schweigt. NODE 7 schliesst das Archiv.",
        "V loescht das letzte Licht. ALEXANDRA dreht sich ein letztes Mal.",
        "",
        "LETZTE UEBERTRAGUNG:",
        f"  » {FINALE_ZITAT}",
        "",
        "Und dann, leiser:",
        f"  » {SCHUTZ_ANKER}",
    ]
    return SignalPaket(broadcast=broadcast, schichten=schichten, entschluesselt=entschluesselt)


def formatiere(p: SignalPaket, mit_loesung: bool = False) -> str:
    L: List[str] = []
    L.extend(p.broadcast)
    L.append("")
    L.append("╫ VERSCHLUESSELTES SIGNAL (Ebene 2 – dekodiere selbst):")
    L.append(f"  [MORSE]     {p.schichten['MORSE']}")
    L.append(f"  [BASE64]    {p.schichten['BASE64']}")
    L.append(f"  [ROT13]     {p.schichten['ROT13']}")
    L.append(f"  [UHRZEITEN] {'  '.join(p.schichten['UHRZEITEN'])}")
    if mit_loesung:
        L.append("")
        L.append("∆ ENTSCHLUESSELT:")
        L.append(f"  MORSE     -> {p.entschluesselt['MORSE']}   (der Schluessel)")
        L.append(f"  BASE64    -> {p.entschluesselt['BASE64']}")
        L.append(f"  ROT13     -> {p.entschluesselt['ROT13']}")
        L.append(f"  UHRZEITEN -> {p.entschluesselt['UHRZEITEN']}   (der Imperativ)")
    L.append("")
    L.append("Ende der Uebertragung. Kein Spielbefehl – nur Erinnerung und Ausgang.")
    L.append("Hilfe anonym: 0800 1 37 27 00 · www.check-dein-spiel.de")
    return "\n".join(L)
