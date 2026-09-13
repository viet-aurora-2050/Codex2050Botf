"""Akt4GameRiddleDecoder – isolierte, zusätzliche Rätsel-Ebene für AKT 4.

Reproduzierbarer Decoder: Morse → Base64 → ROT13 → Uhrzeit → Alphabet →
Game-Titel → Buchstaben → Wort. Keine Glücksspiel-Vorhersage; Game-Titel sind
reine Wortschlüssel. Verändert nichts am bestehenden CODEX2050.
"""

from .data import FALLBACK_GAMES, QUELLE
from .riddle import (
    Game,
    Kandidat,
    clock_letters,
    clock_to_letter,
    decode_base64,
    decode_morse,
    decode_rot13,
    find_game_matches,
    match_chain,
    riddle_validation,
    sancho_check,
)

__all__ = [
    "FALLBACK_GAMES",
    "QUELLE",
    "Game",
    "Kandidat",
    "clock_letters",
    "clock_to_letter",
    "decode_base64",
    "decode_morse",
    "decode_rot13",
    "find_game_matches",
    "match_chain",
    "riddle_validation",
    "sancho_check",
]
