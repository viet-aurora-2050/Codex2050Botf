"""Auszahlungsverteilungs-Mathematik – für die Multiplikator-Analyse.

KERNPRINZIP (ehrlich): Der RTP allein bestimmt NICHT die Wahrscheinlichkeit
eines 2x-, 3x- oder 10x-Ergebnisses. Dafuer braucht es die vollstaendige
Gewinnverteilung (Paytable). Ohne Verteilung -> „Probability unavailable".

Dieses Modul rechnet ausschliesslich auf einer EXPLIZIT angegebenen,
oeffentlichen/eigenen Verteilung. Es sagt keinen einzelnen Spin voraus –
es beschreibt die Verteilung eines Einsatzes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Verteilung:
    """Diskrete Auszahlungsverteilung: (Multiplikator, Wahrscheinlichkeit)."""

    paare: List[Tuple[float, float]] = field(default_factory=list)

    def summe_p(self) -> float:
        return sum(p for _, p in self.paare)

    def ist_gueltig(self, tol: float = 1e-6) -> bool:
        if not self.paare:
            return False
        if any(p < 0 for _, p in self.paare):
            return False
        return abs(self.summe_p() - 1.0) <= 1e-3 or self.summe_p() <= 1.0 + tol

    def ev(self) -> float:
        """Erwarteter Rueckfluss je Einsatz-Einheit (RTP der Verteilung)."""
        return sum(m * p for m, p in self.paare)

    def hausvorteil(self) -> float:
        return 1.0 - self.ev()

    def varianz(self) -> float:
        mu = self.ev()
        return sum(p * (m - mu) ** 2 for m, p in self.paare)

    def std(self) -> float:
        return self.varianz() ** 0.5

    def p_ge(self, k: float) -> float:
        """P(Rueckfluss-Multiplikator >= k)."""
        return sum(p for m, p in self.paare if m >= k)


def multiplikator_ziele(einsatz: float, ziele: Optional[List[float]] = None) -> Dict[float, float]:
    """Zielbetraege je Multiplikator: einsatz * k. Reine Umrechnung, keine W-keit."""
    ziele = ziele or [1, 2, 3, 4, 5, 10, 20, 50, 100]
    return {float(k): round(einsatz * k, 2) for k in ziele}


def datenqualitaet(has_paytable: bool, has_public_stats: bool,
                   has_rtp: bool, has_vola: bool) -> str:
    """A..F – wie belastbar ist die Datengrundlage?"""
    if has_paytable:
        return "A"
    if has_public_stats:
        return "B"
    if has_rtp and has_vola:
        return "C"
    if has_rtp or has_vola:
        return "D"
    return "F"


QUALI_TEXT = {
    "A": "vollstaendige Primaerdaten / Paytable",
    "B": "belastbare oeffentliche Statistik",
    "C": "RTP + Volatilitaet vorhanden",
    "D": "unvollstaendige Daten",
    "F": "keine ausreichende mathematische Grundlage",
}


def multiplikator_analyse(v: Optional[Verteilung], einsatz: float,
                          ziele: Optional[List[float]] = None) -> dict:
    """Gibt Zielbetraege und – NUR bei vorhandener Verteilung – P(>=k) zurueck."""
    ziele = ziele or [1, 2, 3, 4, 5, 10, 20, 50, 100]
    betraege = multiplikator_ziele(einsatz, ziele)
    if v is None or not v.paare:
        return {
            "betraege": betraege,
            "wahrscheinlichkeiten": None,
            "grund": "RTP allein bestimmt die Auszahlungsverteilung nicht. "
                     "Probability unavailable.",
        }
    wahrsch = {float(k): round(v.p_ge(k), 6) for k in ziele}
    return {
        "betraege": betraege,
        "wahrscheinlichkeiten": wahrsch,
        "ev": round(v.ev(), 6),
        "hausvorteil": round(v.hausvorteil(), 6),
        "std": round(v.std(), 6),
    }
