"""Casino-Bonus- und Umsatz-Analytiker.

Transparente Rechen-Engine + Parser fuer Online-Casino-Bonusbedingungen.
"""

from .bonus import (
    BonusSzenario,
    Empfehlung,
    Ergebnis,
    UmsatzBasis,
    analysiere,
    formatiere,
)
from .parser import parse
from .prompts import SYSTEM_PROMPT

__all__ = [
    "BonusSzenario",
    "Empfehlung",
    "Ergebnis",
    "UmsatzBasis",
    "analysiere",
    "formatiere",
    "parse",
    "SYSTEM_PROMPT",
]

__version__ = "1.0.0"
