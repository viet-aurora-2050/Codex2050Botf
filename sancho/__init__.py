"""∆1 // SANCHO – Spielplatz der Wahrheit (ARG-/Lore-Modul, Dunkelblau 2050).

Erzeugt ein atmosphaerisches Anbieter-'Signal' und entlarvt es sofort:
Slots laufen auf zertifiziertem RNG, jeder Spin ist unabhaengig, das Signal
hat Vorhersagewert 0. Kein Spielbefehl – nur Wahrheit und Spielerschutz.
"""

from .spielplatz import (
    ANBIETER_RTP,
    SignalPunkt,
    SpielplatzErgebnis,
    erzeuge,
    formatiere,
    normalisiere_anbieter,
)

__all__ = [
    "ANBIETER_RTP",
    "SignalPunkt",
    "SpielplatzErgebnis",
    "erzeuge",
    "formatiere",
    "normalisiere_anbieter",
]
