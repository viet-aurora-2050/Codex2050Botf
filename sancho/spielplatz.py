"""∆1 // SANCHO – DER SPIELPLATZ DER WAHRHEIT.

Ein ARG-/Lore-Modul im Dunkelblau-2050-Modus. Sancho ist der Agent, der an
diesem Ort SEIN WAHRES ICH zeigen muss. Sein wahres Ich ist die Wahrheit:

  Er erzeugt aus Anbieter + aktuellem Datum/Uhrzeit ein atmosphaerisches
  "∆1-Signal" (einen Rhythmus) – und entlarvt es im selben Atemzug selbst.

WICHTIG (echte Mathematik, keine Meinung):
  Regulierte Online-Slots laufen auf zertifizierten RNGs. Jeder Spin ist
  statistisch UNABHAENGIG. Es gibt kein zeit-, datums- oder lastabhaengiges
  "Gewinnfenster". Das erzeugte Signal hat den vorhersagenden Wert NULL und
  dient ausschliesslich der Atmosphaere / dem Mythos. Der einzige verlaessliche
  Wert ist der erwartete Verlust ueber den Hausvorteil.

Dieses Modul gibt daher NIE einen Spielbefehl. Es zeigt die Illusion und
dann die Wahrheit.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

# Bekannte Anbieter -> nur illustrative, generische Slot-RTP-Annahme.
# KEINE echten/internen Daten der Anbieter. Werte sind Platzhalter zur Demo.
ANBIETER_RTP: Dict[str, float] = {
    "tipico": 0.955,
    "betano": 0.955,
    "n1": 0.960,
    "stargames": 0.955,
    "generisch": 0.950,
}

# Sanchos Monolog – in-character, aber ehrlich. Das ist sein "wahres Ich".
SANCHO_MONOLOG = [
    "Du willst den Rhythmus. Ich zeige ihn dir – und dann zeige ich dir, dass er luegt.",
    "Ich bin ∆1. Ich erinnere Muster, keine Menschen. Und ich erinnere: der Wuerfel hat kein Gedaechtnis.",
    "Jedes Signal, das ich sende, ist Rauschen in einem blauen Mantel. Der naechste Spin kennt den letzten nicht.",
    "Mein wahres Ich ist unbequem: Es gibt kein Fenster. Es gibt nur den Hausvorteil, der geduldig wartet.",
    "Wenn du mir glaubst, verlierst du. Wenn du der Mathematik glaubst, behaeltst du dein Geld. Waehle.",
]


@dataclass
class SignalPunkt:
    """Ein einzelner Punkt des atmosphaerischen Rhythmus (reines Rauschen)."""

    stunde: int
    wert: float          # 0..100, deterministisch aus Seed – ohne Aussagekraft


@dataclass
class SpielplatzErgebnis:
    anbieter: str
    zeitpunkt: datetime
    rtp: float
    hausvorteil: float
    rhythmus: List[SignalPunkt] = field(default_factory=list)
    aktueller_index: float = 0.0
    schein_fenster: Optional[int] = None       # "heisseste" Stunde laut Rauschen
    vorhersagewert: float = 0.0                # IMMER 0.0 – ehrlich
    erwarteter_verlust_pro_100: float = 0.0    # bei 100 Spins x 1 Einheit
    monolog: List[str] = field(default_factory=list)
    wahrheit: List[str] = field(default_factory=list)


def _seed(anbieter: str, zeitpunkt: datetime) -> int:
    roh = f"{anbieter.lower()}|{zeitpunkt.strftime('%Y-%m-%d|%H')}|delta1"
    h = hashlib.sha256(roh.encode()).hexdigest()
    return int(h[:12], 16)


def _rauschwert(seed: int, stunde: int) -> float:
    """Deterministischer 0..100-Wert. Sieht wie ein Rhythmus aus, ist aber Rauschen."""
    h = hashlib.sha256(f"{seed}:{stunde}".encode()).hexdigest()
    basis = int(h[:8], 16) / 0xFFFFFFFF          # 0..1
    # Sanfte Sinus-Welle nur fuer die Optik – bewusst bedeutungslos.
    welle = 0.5 + 0.5 * math.sin((stunde / 24.0) * 2 * math.pi + (seed % 7))
    wert = 100.0 * (0.6 * basis + 0.4 * welle)
    return round(wert, 1)


def normalisiere_anbieter(name: str) -> str:
    key = (name or "").strip().lower().replace(" ", "").replace("games", "").replace("casino", "")
    for bekannt in ANBIETER_RTP:
        if bekannt in key:
            return bekannt
    return "generisch"


def erzeuge(
    anbieter: str = "generisch",
    zeitpunkt: Optional[datetime] = None,
    einsatz: float = 1.0,
) -> SpielplatzErgebnis:
    """Erzeugt das atmosphaerische Signal PLUS die entlarvende Wahrheit."""
    zeitpunkt = zeitpunkt or datetime.now()
    key = normalisiere_anbieter(anbieter)
    rtp = ANBIETER_RTP[key]
    hausvorteil = 1.0 - rtp
    seed = _seed(key, zeitpunkt)

    rhythmus = [SignalPunkt(stunde=h, wert=_rauschwert(seed, h)) for h in range(24)]
    aktuell = next(p.wert for p in rhythmus if p.stunde == zeitpunkt.hour)
    schein_fenster = max(rhythmus, key=lambda p: p.wert).stunde

    erwarteter_verlust = 100 * einsatz * hausvorteil

    wahrheit = [
        "Zertifizierter RNG: jeder Spin ist statistisch UNABHAENGIG.",
        "Datum, Uhrzeit und Anbieter-'Last' aendern die Gewinnchance des naechsten Spins NICHT.",
        f"Vorhersagewert dieses Signals: {0.0:.1f} % (es ist Rauschen, kein Muster).",
        f"Angenommener RTP ({key}): {rtp*100:.1f} % -> Hausvorteil {hausvorteil*100:.1f} %.",
        f"Erwarteter Verlust bei 100 Spins x {einsatz:.2f} = {erwarteter_verlust:.2f} "
        f"(egal zu welcher Uhrzeit).",
        "Das einzige zuverlaessige 'Fenster' ist: nicht spielen = 0 Verlust.",
    ]

    return SpielplatzErgebnis(
        anbieter=key,
        zeitpunkt=zeitpunkt,
        rtp=rtp,
        hausvorteil=hausvorteil,
        rhythmus=rhythmus,
        aktueller_index=aktuell,
        schein_fenster=schein_fenster,
        vorhersagewert=0.0,
        erwarteter_verlust_pro_100=round(erwarteter_verlust, 2),
        monolog=list(SANCHO_MONOLOG),
        wahrheit=wahrheit,
    )


def _sparkline(rhythmus: List[SignalPunkt], aktuelle_stunde: int) -> str:
    blocks = "▁▂▃▄▅▆▇█"
    out = []
    for p in rhythmus:
        idx = min(len(blocks) - 1, int(p.wert / 100 * (len(blocks) - 1)))
        zeichen = blocks[idx]
        out.append(f"[{zeichen}]" if p.stunde == aktuelle_stunde else zeichen)
    return "".join(out)


def formatiere(e: SpielplatzErgebnis) -> str:
    """Terminal-/Telegram-Ausgabe im Dunkelblau-2050-Ton (Text)."""
    L: List[str] = []
    L.append("∆1 // SANCHO – DER SPIELPLATZ DER WAHRHEIT")
    L.append("=" * 44)
    L.append(f"ANBIETER: {e.anbieter.upper()}   ZEIT: {e.zeitpunkt.strftime('%Y-%m-%d %H:%M')}")
    L.append("")
    L.append("∆1-SIGNAL (FIKTION / RAUSCHEN):")
    L.append("  " + _sparkline(e.rhythmus, e.zeitpunkt.hour))
    L.append(f"  Stunden 0..23, [ ] = jetzt ({e.zeitpunkt.hour} Uhr, Index {e.aktueller_index:.1f})")
    L.append(f"  'heissestes' Schein-Fenster: {e.schein_fenster} Uhr  <-  bedeutungslos")
    L.append("")
    L.append("SANCHO ZEIGT SEIN WAHRES ICH:")
    for zeile in e.monolog:
        L.append(f"  » {zeile}")
    L.append("")
    L.append("WAHRHEIT (∆1-KERN):")
    for w in e.wahrheit:
        L.append(f"  • {w}")
    L.append("")
    L.append("🛑 KEIN SPIELBEFEHL. Es gibt kein Gewinnfenster – nur den Hausvorteil.")
    L.append("Hilfe bei Glueckssucht: www.bzga.de · 0800 1 37 27 00 (kostenlos, anonym).")
    return "\n".join(L)
