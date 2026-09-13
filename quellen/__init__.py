"""QUELLENPRINZIP – Prüfkette für externe Angaben + Marketing-Wächter.

Quelle → Gegenquelle → Primärdokument → eigener Mathe-Check → Ergebnis.
Reizwörter wie „hot/fällig/zahlt jetzt/bestes Spiel" sind kein Beweis.
"""

from .prinzip import (
    MARKETING_FLAGS,
    Ergebnis,
    Quellenkette,
    formatiere,
    pruefe_behauptung,
)

__all__ = [
    "MARKETING_FLAGS",
    "Ergebnis",
    "Quellenkette",
    "formatiere",
    "pruefe_behauptung",
]
