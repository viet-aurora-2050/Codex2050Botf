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
from typing import Dict, List, Tuple

from .statistik import mittelwert_intervall, wilson_intervall


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


# Schutz vor Überlast (z. B. durch Nutzereingaben im öffentlichen Bot): die Rechenzeit wächst mit
# Sessions x Spins. Die Sessions werden bei großen Spin-Zahlen verringert, nie unter MIN_SESSIONS.
MAX_SPINS = 100_000
MAX_ARBEIT = 10_000_000          # simulierte Spins insgesamt (ca. 4-5 s Rechenzeit)
MIN_SESSIONS = 500


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
    # Unsicherheit (95-%-Konfidenzintervalle) und Modell-Check – mit Defaults, damit älterer Code weiterläuft.
    ki_p_im_plus: Tuple[float, float] = (0.0, 1.0)
    ki_risk_of_ruin: Tuple[float, float] = (0.0, 1.0)
    mittel_endkapital_sim: float = 0.0            # simulierter Mittelwert (mit Pleite-Abbruch)
    mittel_endkapital_ki: Tuple[float, float] = (0.0, 0.0)
    mittel_gespielte_spins: float = 0.0
    runs_angefragt: int = 0


def pruefe(s: RisikoSzenario) -> None:
    """Wirft ValueError mit verständlicher Meldung bei unsinnigen oder gefährlich großen Eingaben."""
    def endlich(x):
        return isinstance(x, (int, float)) and math.isfinite(x)

    if not (endlich(s.budget) and 0 < s.budget <= 1e9):
        raise ValueError("Budget muss eine positive Zahl (max. 1.000.000.000) sein.")
    if not (endlich(s.einsatz) and 0 < s.einsatz <= 1e7):
        raise ValueError("Einsatz muss eine positive Zahl sein.")
    if not (isinstance(s.spins, int) and 1 <= s.spins <= MAX_SPINS):
        raise ValueError(f"Spins muss eine ganze Zahl zwischen 1 und {MAX_SPINS:,} sein.".replace(",", "."))
    if not (endlich(s.rtp) and 0.5 <= s.rtp <= 1.0):
        raise ValueError("RTP muss zwischen 0,50 und 1,00 liegen (z. B. 0.96 oder 96).")


def _spin_return(rng: random.Random, einsatz: float, rtp: float, h: float) -> float:
    """Netto-Ergebnis EINES Spins (kann negativ = Einsatz verloren)."""
    if rng.random() < h:
        mittel_multiplikator = rtp / h              # so, dass E[Auszahlung]=RTP*Einsatz
        multiplikator = rng.expovariate(1.0 / mittel_multiplikator)
        auszahlung = einsatz * multiplikator
    else:
        auszahlung = 0.0
    return auszahlung - einsatz


def simuliere_sessions(s: RisikoSzenario, runs: int, seed: int = 20500) -> Tuple[List[float], List[int], int]:
    """Simuliert `runs` Sessions. Rueckgabe: (Endkapital je Session, gespielte Spins je Session, Pleiten).

    Eine Session endet, sobald das Kapital unter den Einsatz faellt (man kann nicht mehr setzen).
    Deterministisch fuer gleiche Eingaben und Seed (reproduzierbar).
    """
    h = TREFFERQUOTE[s.volatilitaet]
    rng = random.Random(seed)
    endkapital: List[float] = []
    gespielt: List[int] = []
    ruin = 0
    for _ in range(runs):
        kapital = s.budget
        pleite = False
        n_gespielt = 0
        for _ in range(s.spins):
            if kapital < s.einsatz:               # kann nicht mehr setzen -> pleite
                pleite = True
                break
            kapital += _spin_return(rng, s.einsatz, s.rtp, h)
            n_gespielt += 1
        if pleite or kapital < s.einsatz:
            ruin += 1
        endkapital.append(max(0.0, kapital))
        gespielt.append(n_gespielt)
    return endkapital, gespielt, ruin


def analysiere(s: RisikoSzenario, runs: int = 20000, seed: int = 20500) -> RisikoErgebnis:
    """Monte-Carlo-Auswertung ueber viele simulierte Sessions."""
    pruefe(s)
    runs_angefragt = runs
    runs = max(MIN_SESSIONS, min(runs, MAX_ARBEIT // s.spins))
    h = TREFFERQUOTE[s.volatilitaet]
    hausvorteil = 1.0 - s.rtp
    erwarteter_verlust = s.spins * s.einsatz * hausvorteil
    erwartetes_endkapital = s.budget - erwarteter_verlust

    endkapital, gespielt, ruin = simuliere_sessions(s, runs, seed)

    endkapital.sort()
    n = len(endkapital)

    def perc(p: float) -> float:
        return endkapital[min(n - 1, max(0, int(p * n)))]

    median = perc(0.50)
    plus_n = sum(1 for x in endkapital if x > s.budget)
    im_plus = plus_n / n
    mw, mw_lo, mw_hi = mittelwert_intervall(endkapital)

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
    if runs < runs_angefragt:
        schritte.append(f"Hinweis: Sessions von {runs_angefragt} auf {runs} reduziert (Rechenlimit bei vielen Spins).")

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
        ki_p_im_plus=wilson_intervall(plus_n, n),
        ki_risk_of_ruin=wilson_intervall(ruin, n),
        mittel_endkapital_sim=round(mw, 2),
        mittel_endkapital_ki=(round(mw_lo, 2), round(mw_hi, 2)),
        mittel_gespielte_spins=round(sum(gespielt) / n, 1),
        runs_angefragt=runs_angefragt,
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
    L.append(f"  • Erwartetes Endkapital: {e.erwartetes_endkapital:.2f} {w}  (Start {s.budget:.2f}; "
             f"theoretisch, wenn alle {s.spins} Spins gespielt werden)")
    L.append(f"  • Simuliertes Ø-Endkapital: {e.mittel_endkapital_sim:.2f} {w}  "
             f"(95%-KI {e.mittel_endkapital_ki[0]:.2f}..{e.mittel_endkapital_ki[1]:.2f}; "
             f"Ø {e.mittel_gespielte_spins:.0f} Spins gespielt – bei Pleite endet die Session frueher)")
    L.append(f"  • Median-Endkapital:     {e.median_endkapital:.2f} {w}")
    L.append(f"  • Chance, im Plus zu enden: {e.p_im_plus*100:.1f}%  "
             f"(95%-KI {e.ki_p_im_plus[0]*100:.1f}..{e.ki_p_im_plus[1]*100:.1f}%)")
    L.append(f"  • Risk of Ruin (pleite):    {e.risk_of_ruin*100:.1f}%  "
             f"(95%-KI {e.ki_risk_of_ruin[0]*100:.1f}..{e.ki_risk_of_ruin[1]*100:.1f}%)")
    L.append(f"  • Bandbreite (P5..P95):  {e.p05:.2f} .. {e.p95:.2f} {w}")
    L.append("")
    L.append("Modell & Grenzen: vereinfacht (Trefferquote je Volatilitaetsstufe angenommen, Gewinnhoehe")
    L.append("exponentialverteilt, kein Max-Win-Limit). Echte Spiele koennen staerker schwanken; die")
    L.append("Volatilitaetsstufe ist eine Annahme, kein veroeffentlichter Wert.")
    L.append("")
    L.append("Merke: Das ist DEINE Risiko-/Erwartungswert-Mathematik – KEINE Spin-Vorhersage.")
    L.append("Der RNG bleibt unabhaengig. Erwartungswert ist und bleibt negativ.")
    L.append("Hilfe anonym: 0800 1 37 27 00 · www.check-dein-spiel.de")
    return "\n".join(L)
