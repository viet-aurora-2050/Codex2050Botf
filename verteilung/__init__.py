"""Auszahlungsverteilungs-Mathematik (Multiplikator-Analyse).

RTP allein bestimmt keine Multiplikator-Wahrscheinlichkeit – nur eine explizite
Verteilung (Paytable) tut das. Ohne Verteilung: „Probability unavailable".
"""

from .vert import (
    QUALI_TEXT,
    Verteilung,
    datenqualitaet,
    multiplikator_analyse,
    multiplikator_ziele,
)

__all__ = [
    "QUALI_TEXT",
    "Verteilung",
    "datenqualitaet",
    "multiplikator_analyse",
    "multiplikator_ziele",
]
