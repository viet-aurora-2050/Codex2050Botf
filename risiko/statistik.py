"""Kleine, geprüfte Statistik-Bausteine für die Risiko-Simulation.

Warum: Eine Monte-Carlo-Zahl ohne Unsicherheitsangabe suggeriert eine Genauigkeit, die sie nicht hat.
Bei 3.000 simulierten Sessions beträgt der Stichprobenfehler einer Wahrscheinlichkeit um 50 % rund
±1,8 Prozentpunkte. Wir geben deshalb Konfidenzintervalle an.
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple

Z95 = 1.959963984540054   # 97,5-%-Quantil der Standardnormalverteilung


def wilson_intervall(erfolge: int, n: int, z: float = Z95) -> Tuple[float, float]:
    """Wilson-Score-Intervall für einen Anteil (robuster als Wald, auch bei p nahe 0 oder 1).

    Quelle: E. B. Wilson (1927), J. Am. Stat. Assoc. 22; Standardempfehlung u. a. bei
    Brown/Cai/DasGupta (2001), Statistical Science 16(2).
    """
    if n <= 0:
        return (0.0, 1.0)
    if not 0 <= erfolge <= n:
        raise ValueError("erfolge muss zwischen 0 und n liegen")
    p = erfolge / n
    z2 = z * z
    nenner = 1.0 + z2 / n
    mitte = (p + z2 / (2 * n)) / nenner
    halb = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / nenner
    return (max(0.0, mitte - halb), min(1.0, mitte + halb))


def mittelwert_intervall(werte: Sequence[float], z: float = Z95) -> Tuple[float, float, float]:
    """(Mittelwert, untere, obere Grenze) des Mittelwerts per Normalnäherung (Zentraler Grenzwertsatz)."""
    n = len(werte)
    if n == 0:
        return (0.0, 0.0, 0.0)
    m = math.fsum(werte) / n
    if n == 1:
        return (m, m, m)
    var = math.fsum((x - m) ** 2 for x in werte) / (n - 1)
    se = math.sqrt(var / n)
    return (m, m - z * se, m + z * se)
