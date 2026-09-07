"""∆1 // MELDE-ASSISTENT – Mathematik + faktische Beschwerde/Anzeige an die GGL.

Erzeugt aus dem mathematischen Prinzip (Hausvorteil, struktureller Verlust,
Risk of Ruin) eine sachliche Meldung an die Aufsichtsbehoerde – fuer jeden
Online-Anbieter. Nur wahrheitsgemaesse Angaben; alles als Verdacht/Bitte um
Pruefung, keine Rechtsberatung.
"""

from .anzeige import (
    Lizenz,
    MeldeErgebnis,
    MeldeSzenario,
    erstelle,
    formatiere,
)

__all__ = [
    "Lizenz",
    "MeldeErgebnis",
    "MeldeSzenario",
    "erstelle",
    "formatiere",
]
