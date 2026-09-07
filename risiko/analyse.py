"""PERSONAL-RISIKO-ANALYSE aus OEFFENTLICHEN Fakten.

Diese Engine nutzt ausschliesslich oeffentlich verfuegbare Parameter
(veroeffentlichter RTP, Volatilitaetsklasse) plus DEINE eigenen Angaben
(Budget, Einsatz, Anzahl Spins) und berechnet daraus eine persoenliche,
mathematische Auswertung:

  - erwarteter Verlust (Hausvorteil)
  - Streuung / Konfidenzband (Volatilitaet)
  - Wahrscheinlichkeit, am Ende im Plus zu sein
  - Risk of Ruin (Wahrscheinlichkeit, das Budget zu verlieren)
  - Median-Endkapital, P5/P95

WICHTIG: Das sagt KEINEN einzelnen Spin voraus (RNG-Unabhaengigkeit bleibt).
Es analysiert DEIN Risiko und deinen Erwartungswert - nicht die Zukunft des
Automaten. Kein Server-Zugriff, keine Fremddaten.

Modell (transparent): pro Spin faellt mit Trefferquote h ein Gewinn; die
Auszahlung ist exponentialverteilt mit Mittel RTP/h. Damit ist der
Erwartungswert pro Spin exakt = Einsatz * (RTP - 1) = -Einsatz * Hausvorteil.
Niedrige Trefferquote = hohe Volatilitaet (seltene, grosse Gewinne).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class Volatilitaet(str, Enum):
    NIEDRIG = "niedrig"
    MITTEL = "mittel"
    HOCH = "hoch"


# Oeffentlich bekannte Groessenordnungen: niedrige Volatilitaet = haeufige
# kleine Treffer; hohe Volatilitaet = seltene grosse Treffer.
TREFFERQUOTE: Dict[Volatilitaet, float] = {
    Volatilitaet.NIEDRIG: 0.32,
    Volatilitaet.MITTEL: 0.18,
    Volatilitaet.HOCH: 0.09,
}


@dataclass
class RisikoSzenario:
    budget: float = 100.0        # dein Guthaben
    einsatz: float = 1.0         # Einsatz pro Spin
    spins: int = 500             # geplante Anzahl Spins
    rtp: float = 0.96            # veroeffentlichter RTP (0..1)
    volatilitaet: Volatilitaet = Volatilitaet.MITTEL
    waehrung: str = "EUR"


@dataclass
class RisikoErgebnis:
    hausvorteil: float
    erwarteter_verlust: float          # ueber die Session (Betrag, positiv = Verlust)
    erwartetes_endkapital: float
    median_endkapital: float
    p_im_plus: float                   # Wahrscheinlichkeit final > budget
    risk_of_ruin: float                # Wahrscheinlichkeit, pleite zu gehen
    p05: float
    p95: float
    runs: int
    schritte: List[str] = field(default_factory=list)


def _spin_return(rng: random.Random, einsatz: float, rtp: float, h: float) -> float:
    """Netto-Ergebnis EINES Spins (kann negativ = Einsatz verloren)."""
    if rng.random() < h:
        mittel_multiplikator = rtp / h              # so, dass E[Auszahlung]=RTP*Einsatz
        multiplikator = rng.expovariate(1.0 / mittel_multiplikator)
        auszahlung = einsatz * multiplikator
    else:
        auszahlung = 0.0
    return auszahlung - einsatz


def analysiere(s: RisikoSzenario, runs: int = 20000, seed: int = 20500) -> RisikoErgebnis:
    """Monte-Carlo-Auswertung ueber viele simulierte Sessions."""
    h = TREFFERQUOTE[s.volatilitaet]
    hausvorteil = 1.0 - s.rtp
    erwarteter_verlust = s.spins * s.einsatz * hausvorteil
    erwartetes_endkapital = s.budget - erwarteter_verlust

    rng = random.Random(seed)
    endkapital: List[float] = []
    ruin = 0
    for _ in range(runs):
        kapital = s.budget
        pleite = False
        for _ in range(s.spins):
            if kapital < s.einsatz:               # kann nicht mehr setzen -> pleite
                pleite = True
                break
            kapital += _spin_return(rng, s.einsatz, s.rtp, h)
        if pleite or kapital < s.einsatz:
            ruin += 1
        endkapital.append(max(0.0, kapital))

    endkapital.sort()
    n = len(endkapital)

    def perc(p: float) -> float:
        return endkapital[min(n - 1, max(0, int(p * n)))]

    median = perc(0.50)
    im_plus = sum(1 for x in endkapital if x > s.budget) / n

    schritte = [
        f"Hausvorteil = 1 - RTP = 1 - {s.rtp:.4f} = {hausvorteil*100:.2f}%",
        f"Erwarteter Verlust = Spins x Einsatz x Hausvorteil = "
        f"{s.spins} x {s.einsatz:.2f} x {hausvorteil*100:.2f}% = {erwarteter_verlust:.2f} {s.waehrung}",
        f"Erwartetes Endkapital = Budget - erwarteter Verlust = "
        f"{s.budget:.2f} - {erwarteter_verlust:.2f} = {erwartetes_endkapital:.2f} {s.waehrung}",
        f"Volatilitaet '{s.volatilitaet.value}' -> Trefferquote {h*100:.0f}% "
        f"(niedrige Quote = groessere Schwankung)",
        f"Monte-Carlo ueber {runs} simulierte Sessions (oeffentliche Parameter, kein Server).",
    ]

    return RisikoErgebnis(
        hausvorteil=round(hausvorteil, 4),
        erwarteter_verlust=round(erwarteter_verlust, 2),
        erwartetes_endkapital=round(erwartetes_endkapital, 2),
        median_endkapital=round(median, 2),
        p_im_plus=round(im_plus, 4),
        risk_of_ruin=round(ruin / runs, 4),
        p05=round(perc(0.05), 2),
        p95=round(perc(0.95), 2),
        runs=runs,
        schritte=schritte,
    )


def formatiere(e: RisikoErgebnis, s: RisikoSzenario) -> str:
    w = s.waehrung
    L: List[str] = []
    L.append("📈 PERSONAL-RISIKO-ANALYSE")
    L.append("=" * 30)
    L.append("Aus oeffentlichen Fakten (RTP/Volatilitaet) + deinen Angaben:")
    L.append("")
    for i, schritt in enumerate(e.schritte, 1):
        L.append(f"  {i}. {schritt}")
    L.append("")
    L.append("Deine persoenliche Auswertung:")
    L.append(f"  • Erwartetes Endkapital: {e.erwartetes_endkapital:.2f} {w}  (Start {s.budget:.2f})")
    L.append(f"  • Median-Endkapital:     {e.median_endkapital:.2f} {w}")
    L.append(f"  • Chance, im Plus zu enden: {e.p_im_plus*100:.1f}%")
    L.append(f"  • Risk of Ruin (pleite):    {e.risk_of_ruin*100:.1f}%")
    L.append(f"  • Bandbreite (P5..P95):  {e.p05:.2f} .. {e.p95:.2f} {w}")
    L.append("")
    L.append("Merke: Das ist DEINE Risiko-/Erwartungswert-Mathematik – KEINE Spin-Vorhersage.")
    L.append("Der RNG bleibt unabhaengig. Erwartungswert ist und bleibt negativ.")
    L.append("Hilfe anonym: 0800 1 37 27 00 · www.check-dein-spiel.de")
    return "\n".join(L)
