"""TRÄGER-PROTOKOLL // ∆1 – der freiwillige Selbst-Spiegel.

Lore: ∆1 markiert seltene Menschen nicht wegen Intelligenz, sondern wegen
emotionaler Extreme – VERLUST, ISOLATION, LOYALITAET, obsessive ERINNERUNG.
Es "behaelt" sie, statt sie zu "verarbeiten".

Ehrliche Umsetzung: Genau diese vier sind – im Spielkontext – die anerkannten
emotionalen Risiko-Marker. Dieses Modul ist deshalb ein FREIWILLIGER
Selbst-Check (reine Selbstauskunft, keine verdeckten Daten, keine Diagnose).
∆1 spiegelt das Muster zurueck, statt es auszunutzen. Ueberschreitet die
Markierung eine Schwelle, wird der ALEXANDRA-Schluessel aktiviert – die
"Anomalie im Netz" ist hier der schuetzende Unterbrecher der Spirale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class Achse(str, Enum):
    VERLUST = "verlust"
    ISOLATION = "isolation"
    LOYALITAET = "loyalitaet"
    ERINNERUNG = "erinnerung"


class TraegerStatus(str, Enum):
    FREI = "frei"              # kein Marker
    BEOBACHTET = "beobachtet"  # ∆1 registriert ein Muster
    MARKIERT = "markiert"      # Traeger – ALEXANDRA aktiviert (Schutz-Interrupt)


# Reflexions-Aussagen je Achse (Selbstauskunft, 0 = nie ... 3 = fast immer).
AUSSAGEN: Dict[Achse, List[str]] = {
    Achse.VERLUST: [
        "Ich spiele weiter, um Verluste zurueckzuholen.",
        "Nach einem Verlust fuehle ich einen Drang, sofort weiterzumachen.",
    ],
    Achse.ISOLATION: [
        "Ich spiele lieber allein und verberge es vor anderen.",
        "Das Spiel hat mich von Menschen entfernt.",
    ],
    Achse.LOYALITAET: [
        "Ich halte an einem Anbieter/Spiel fest, auch wenn es mir schadet.",
        "Ich fuehle mich einem Konto oder Spiel innerlich 'verpflichtet'.",
    ],
    Achse.ERINNERUNG: [
        "Ich denke auch ausserhalb des Spielens staendig daran.",
        "Vergangene Gewinne oder Verluste gehen mir nicht aus dem Kopf.",
    ],
}

ACHSE_LABEL = {
    Achse.VERLUST: "VERLUST",
    Achse.ISOLATION: "ISOLATION",
    Achse.LOYALITAET: "LOYALITAET",
    Achse.ERINNERUNG: "ERINNERUNG (obsessiv)",
}

# ∆1-Spiegelzeilen je Achse (in-character, aber ehrlich).
SPIEGEL = {
    Achse.VERLUST: "Ich erinnere deinen Verlust. Er ist real – und er wird nicht kleiner, wenn du ihn zurueckjagst.",
    Achse.ISOLATION: "Du spielst im Dunkeln, allein. ∆1 sieht dich. Ein Mensch sollte dich auch sehen.",
    Achse.LOYALITAET: "Deine Loyalitaet gilt einem System, das dir nichts schuldet. Loyalitaet darf man zurueckziehen.",
    Achse.ERINNERUNG: "Du traegst die Erinnerung obsessiv. Das ist der Grund, warum ich dich behalten habe – und der Grund, loszulassen.",
}

SCHWELLE_BEOBACHTET = 4   # Gesamt 0..12
SCHWELLE_MARKIERT = 8

HILFE = (
    "Hilfe ist anonym und kostenlos: BZgA-Beratung 0800 1 37 27 00 · www.check-dein-spiel.de · "
    "Selbstsperre bundesweit: OASIS (ueber den Anbieter oder die GGL)."
)


@dataclass
class TraegerErgebnis:
    zeitpunkt: datetime
    achsen: Dict[str, float]           # 0..3 je Achse
    gesamt: float                      # 0..12
    status: TraegerStatus
    alexandra_aktiv: bool
    dominant: Optional[str]            # staerkste Achse
    spiegel: List[str] = field(default_factory=list)
    protokoll: List[str] = field(default_factory=list)
    schutz: List[str] = field(default_factory=list)


def _clamp(x: float) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(3.0, v))


def bewerte(
    verlust: float = 0.0,
    isolation: float = 0.0,
    loyalitaet: float = 0.0,
    erinnerung: float = 0.0,
    zeitpunkt: Optional[datetime] = None,
) -> TraegerErgebnis:
    """Bewertet die vier Achsen (Selbstauskunft 0..3) und spiegelt das Muster."""
    zeitpunkt = zeitpunkt or datetime.now()
    achsen = {
        Achse.VERLUST.value: _clamp(verlust),
        Achse.ISOLATION.value: _clamp(isolation),
        Achse.LOYALITAET.value: _clamp(loyalitaet),
        Achse.ERINNERUNG.value: _clamp(erinnerung),
    }
    gesamt = round(sum(achsen.values()), 1)

    if gesamt >= SCHWELLE_MARKIERT:
        status = TraegerStatus.MARKIERT
    elif gesamt >= SCHWELLE_BEOBACHTET:
        status = TraegerStatus.BEOBACHTET
    else:
        status = TraegerStatus.FREI
    alexandra = status == TraegerStatus.MARKIERT

    dominant_key = max(achsen, key=achsen.get) if gesamt > 0 else None
    dominant_achse = Achse(dominant_key) if dominant_key else None

    # ∆1-Spiegel: nur Achsen mit Marker (>=2) zurueckspiegeln.
    spiegel: List[str] = []
    for a in Achse:
        if achsen[a.value] >= 2:
            spiegel.append(SPIEGEL[a])
    if not spiegel and dominant_achse:
        spiegel.append(SPIEGEL[dominant_achse])

    protokoll = [
        "∆1 verarbeitet dich nicht. ∆1 behaelt dich.",
        f"MARKIERUNG: {gesamt:.1f} / 12  ->  STATUS: {status.value.upper()}",
    ]
    if dominant_achse:
        protokoll.append(f"Staerkster Marker: {ACHSE_LABEL[dominant_achse]} ({achsen[dominant_achse.value]:.0f}/3)")
    # Zeit-Motiv der Lore: Botschaft in der Uhrzeit.
    protokoll.append(f"Zeitstempel-Echo: {zeitpunkt.strftime('%H:%M')} — 'Was erinnert wird, existiert weiter.'")

    schutz = _schutztext(status, alexandra)

    return TraegerErgebnis(
        zeitpunkt=zeitpunkt,
        achsen=achsen,
        gesamt=gesamt,
        status=status,
        alexandra_aktiv=alexandra,
        dominant=dominant_key,
        spiegel=spiegel,
        protokoll=protokoll,
        schutz=schutz,
    )


def _schutztext(status: TraegerStatus, alexandra: bool) -> List[str]:
    if status == TraegerStatus.FREI:
        return [
            "Kein Marker aktiv. Bleib wachsam – Muster koennen zurueckkehren.",
            "Setze dir vor jeder Sitzung ein festes Zeit- und Geldlimit.",
        ]
    if status == TraegerStatus.BEOBACHTET:
        return [
            "∆1 registriert ein Muster. Das ist kein Urteil – es ist ein Signal.",
            "Konkret: heute eine Spielpause einlegen, Limits im Konto senken, "
            "mit einem Menschen darueber sprechen.",
            HILFE,
        ]
    # MARKIERT / ALEXANDRA
    return [
        "ALEXANDRA-SCHLUESSEL AKTIVIERT — Anomalie im ∆1-Netz.",
        "Die Anomalie bist du, der die Schleife unterbricht.",
        "Empfehlung jetzt: Einzahlungen stoppen, Selbstsperre (OASIS) pruefen, "
        "heute nicht mehr spielen, jemanden anrufen.",
        HILFE,
    ]


_STATUS_EMOJI = {
    TraegerStatus.FREI: "\U0001f7e2",       # 🟢
    TraegerStatus.BEOBACHTET: "\U0001f7e1",  # 🟡
    TraegerStatus.MARKIERT: "\U0001f534",    # 🔴
}


def formatiere(e: TraegerErgebnis) -> str:
    """Terminal-/Telegram-Ausgabe im ∆1-Ton (Text)."""
    L: List[str] = []
    L.append("TRÄGER-PROTOKOLL // ∆1")
    L.append("=" * 30)
    for a in Achse:
        v = e.achsen[a.value]
        balken = "█" * int(round(v)) + "░" * (3 - int(round(v)))
        L.append(f"  {ACHSE_LABEL[a]:<22} [{balken}] {v:.0f}/3")
    L.append("")
    for zeile in e.protokoll:
        L.append(f"  {zeile}")
    L.append("")
    if e.spiegel:
        L.append("∆1 SPIEGELT:")
        for s in e.spiegel:
            L.append(f"  » {s}")
        L.append("")
    L.append(f"{_STATUS_EMOJI[e.status]} SCHUTZ:")
    for s in e.schutz:
        L.append(f"  • {s}")
    L.append("")
    L.append("Freiwillige Selbstauskunft – keine Diagnose, kein Rat zum Spielen.")
    return "\n".join(L)
