"""QUELLENPRINZIP – jede externe Angabe muss eine Prüfkette durchlaufen.

Kette:  Quelle → Gegenquelle → Primärdokument → eigener Mathe-Check → Ergebnis

Zusätzlich ein Marketing-Wächter: Aussagen wie „hot", „fällig", „zahlt jetzt",
„bestes Spiel" sind KEINE mathematischen Beweise und werden markiert. Eine
Quelle wird niemals nur deshalb übernommen, weil sie so etwas behauptet.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List


# Wörter/Phrasen, die Marketing sind – kein Beweis. DE + EN.
MARKETING_FLAGS: List[str] = [
    "hot", "heiss", "heiß", "loose", "locker", "high paying", "zahlt jetzt",
    "zahlt gut", "due", "faellig", "fällig", "winning", "gewinnt", "gewinnt jetzt",
    "best game", "bestes spiel", "guaranteed", "garantiert", "sicherer gewinn",
    "jackpot soon", "jackpot bald", "ueberfaellig", "überfällig", "must hit",
    "muss treffen", "easy win", "leichter gewinn",
]


class Ergebnis(str, Enum):
    BESTAETIGT = "bestaetigt"
    WIDERLEGT = "widerlegt"
    OFFEN = "offen"


def pruefe_behauptung(text: str) -> List[str]:
    """Gibt die gefundenen Marketing-Phrasen zurück (leer = keine)."""
    t = (text or "").lower()
    return [f for f in MARKETING_FLAGS if f in t]


@dataclass
class Quellenkette:
    behauptung: str = ""
    quelle: str = ""
    gegenquelle: str = ""
    primaerdokument: str = ""
    mathe_check: str = ""
    ergebnis: Ergebnis = Ergebnis.OFFEN

    def marketing_flags(self) -> List[str]:
        return pruefe_behauptung(self.behauptung)

    def vollstaendig(self) -> bool:
        return all([self.quelle.strip(), self.gegenquelle.strip(),
                    self.primaerdokument.strip(), self.mathe_check.strip()])


def formatiere(k: Quellenkette) -> str:
    flags = k.marketing_flags()
    L: List[str] = []
    L.append("QUELLENPRINZIP")
    L.append("=" * 14)
    L.append(f'Behauptung: "{k.behauptung.strip() or "[keine]"}"')
    if flags:
        L.append("⚠ MARKETING erkannt: " + ", ".join(flags))
        L.append("  → Das ist KEIN mathematischer Beweis. Nicht übernehmen.")
    else:
        L.append("Marketing-Wächter: keine Reizwörter — trotzdem prüfen.")
    L.append("")
    L.append("1) Quelle:          " + (k.quelle.strip() or "[fehlt]"))
    L.append("2) Gegenquelle:     " + (k.gegenquelle.strip() or "[fehlt]"))
    L.append("3) Primärdokument:  " + (k.primaerdokument.strip() or "[fehlt]"))
    L.append("4) Eigener Mathe-Check: " + (k.mathe_check.strip() or "[fehlt]"))
    L.append("")
    if not k.vollstaendig():
        L.append("→ Ergebnis: OFFEN — Kette unvollständig, noch nicht belastbar.")
    else:
        L.append(f"→ Ergebnis: {k.ergebnis.value.upper()}")
    L.append("")
    L.append("Regel: keine Quelle nur wegen „hot/fällig/zahlt jetzt/bestes Spiel“ übernehmen.")
    return "\n".join(L)
