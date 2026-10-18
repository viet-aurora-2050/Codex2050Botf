"""PERSONAL-RISIKO-ANALYSE aus oeffentlichen Fakten (RTP/Volatilitaet) + eigenen Angaben.

Berechnet erwarteten Verlust, Chance im Plus zu enden, Risk of Ruin und
Bandbreite per Monte-Carlo. KEINE Spin-Vorhersage, kein Server-Zugriff.
"""

from .analyse import (
    RisikoErgebnis,
    RisikoSzenario,
    Volatilitaet,
    analysiere,
    formatiere,
)
from .profil import ProfilEingabe, berechne, eingabe_aus_text, formatiere_profil

__all__ = [
    "RisikoErgebnis",
    "RisikoSzenario",
    "Volatilitaet",
    "analysiere",
    "formatiere",
    "ProfilEingabe",
    "berechne",
    "eingabe_aus_text",
    "formatiere_profil",
]
