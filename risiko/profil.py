"""PERSÖNLICHES RISIKOPROFIL – psychologisch und mathematisch, ruhig im Ton.

Ergänzt die Risiko-Engine (`risiko.analyse`, unverändert) um zwei Dinge:

  1. Mathematik aus DEINEN Angaben: erwarteter Verlust pro Stunde/Woche/Monat, Puffer in Einsätzen,
     erwartete Budget-Lebensdauer und – über die vorhandene Monte-Carlo-Engine – Risk of Ruin einer Session.
  2. Selbst-Check (6 Fragen, 0-3): beschreibt riskante Verhaltensmuster (Verlustjagd, Kontrollverlust,
     Fehlschluss „Gewinn ist fällig“). Der Wert passt die EMPFOHLENEN Grenzen an (kleinerer Einsatzanteil,
     kürzere Sitzung) – er verändert nie die Wahrscheinlichkeiten des Spiels.

Grenzen: Der Selbst-Check ist KEIN klinisches Screening und keine Diagnose. Die Grenzwerte sind Faustregeln
zur Selbstkontrolle, keine gemessenen Naturkonstanten. Keine Spin-Vorhersage; der RNG bleibt unabhängig.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from .analyse import RisikoErgebnis, RisikoSzenario, Volatilitaet, analysiere

WOCHEN_PRO_MONAT = 52 / 12

FRAGEN: Tuple[str, ...] = (
    "Ich spiele länger oder mit mehr Geld, als ich mir vorgenommen hatte.",
    "Nach Verlusten erhöhe ich den Einsatz oder spiele weiter, um das Verlorene zurückzuholen.",
    "Ich spiele mit Geld, das ich eigentlich für anderes brauche.",
    "Ich glaube, nach vielen Verlusten in Folge ist ein Gewinn „fällig“.",
    "Ich spiele, um Stress, Langeweile oder schlechte Stimmung zu verdrängen.",
    "Ich verschweige anderen, wie viel oder wie oft ich spiele.",
)
SKALA = ("nie", "selten", "oft", "fast immer")      # Antwort 0..3

# (Obergrenze des Scores, Stufe, max. Einsatz-Anteil am Budget, empfohlene Sitzungslänge in Minuten)
_STUFEN: Tuple[Tuple[int, str, float, int], ...] = (
    (3, "niedrig", 0.010, 60),
    (8, "erhöht", 0.005, 30),
    (18, "hoch", 0.0025, 15),
)


@dataclass
class ProfilEingabe:
    budget: float = 100.0              # Geld, dessen Verlust du verkraftest
    einsatz: float = 1.0
    rtp: float = 0.96
    volatilitaet: Volatilitaet = Volatilitaet.MITTEL
    spins_pro_stunde: float = 500.0
    stunden_pro_woche: float = 2.0
    sitzungs_minuten: float = 60.0
    antworten: Optional[Sequence[int]] = None      # 6 Werte 0..3, None = Selbst-Check nicht beantwortet


@dataclass
class Profil:
    hausvorteil: float
    verlust_pro_stunde: float
    verlust_pro_woche: float
    verlust_pro_monat: float
    puffer_einsaetze: float            # Budget / Einsatz
    lebensdauer_stunden: float         # Budget / Verlust pro Stunde (Erwartung, ohne Streuung)
    sitzung: Optional[RisikoErgebnis]
    sitzung_spins: int
    score: Optional[int]
    stufe: Optional[str]
    empf_max_einsatz: float
    empf_sitzung_minuten: int
    hinweise: List[str] = field(default_factory=list)


def pruefe(e: ProfilEingabe) -> None:
    def endlich(x):
        return isinstance(x, (int, float)) and math.isfinite(x)

    if not (endlich(e.spins_pro_stunde) and 10 <= e.spins_pro_stunde <= 5000):
        raise ValueError("Spins pro Stunde muss zwischen 10 und 5000 liegen.")
    if not (endlich(e.stunden_pro_woche) and 0 <= e.stunden_pro_woche <= 168):
        raise ValueError("Stunden pro Woche muss zwischen 0 und 168 liegen.")
    if not (endlich(e.sitzungs_minuten) and 1 <= e.sitzungs_minuten <= 600):
        raise ValueError("Sitzungsdauer muss zwischen 1 und 600 Minuten liegen.")
    if e.antworten is not None:
        if len(e.antworten) != len(FRAGEN) or any(
                not isinstance(a, int) or isinstance(a, bool) or not 0 <= a <= 3 for a in e.antworten):
            raise ValueError(f"Selbst-Check: genau {len(FRAGEN)} Antworten, je 0 bis 3.")


def stufe_fuer(score: int) -> Tuple[str, float, int]:
    for obergrenze, name, anteil, minuten in _STUFEN:
        if score <= obergrenze:
            return name, anteil, minuten
    return _STUFEN[-1][1:]


def berechne(e: ProfilEingabe, runs: int = 4000) -> Profil:
    """Rechnet das Profil. Wirft ValueError bei unsinnigen Eingaben (auch aus der Risiko-Engine)."""
    pruefe(e)
    spins = max(1, int(round(e.spins_pro_stunde * e.sitzungs_minuten / 60.0)))
    szenario = RisikoSzenario(budget=e.budget, einsatz=e.einsatz, spins=spins, rtp=e.rtp,
                              volatilitaet=e.volatilitaet)
    sitzung = analysiere(szenario, runs=runs)           # prüft Budget/Einsatz/RTP/Spins mit

    hv = 1.0 - e.rtp
    pro_stunde = e.einsatz * hv * e.spins_pro_stunde
    pro_woche = pro_stunde * e.stunden_pro_woche
    lebensdauer = e.budget / pro_stunde if pro_stunde > 0 else math.inf

    score = stufe = None
    anteil, minuten = _STUFEN[0][2], _STUFEN[0][3]
    if e.antworten is not None:
        score = sum(e.antworten)
        stufe, anteil, minuten = stufe_fuer(score)
    empf_einsatz = round(e.budget * anteil, 2)

    h: List[str] = []
    puffer = e.budget / e.einsatz
    if puffer < 100:
        h.append(f"Puffer: nur {puffer:.0f} Einsätze im Budget – kurze Pechsträhnen reichen dann schon für die Pleite.")
    if e.einsatz > empf_einsatz:
        h.append(f"Dein Einsatz ({e.einsatz:.2f}) liegt über der Faustregel für deine Stufe "
                 f"({empf_einsatz:.2f} = {anteil*100:.2f} % des Budgets).")
    if e.sitzungs_minuten > minuten:
        h.append(f"Deine Sitzung ({e.sitzungs_minuten:.0f} min) ist länger als die Faustregel ({minuten} min). "
                 "Geplante Pausen halten die Entscheidung bei dir statt beim Spielverlauf.")
    if e.antworten is not None:
        if e.antworten[3] >= 2:
            h.append("„Gewinn ist fällig“ gibt es nicht: Jeder Spin ist unabhängig. Nach 10 Nieten bei Trefferquote "
                     f"{_h(e.volatilitaet)*100:.0f} % ist die Chance beim nächsten Spin unverändert "
                     f"{_h(e.volatilitaet)*100:.0f} %.")
        if e.antworten[1] >= 2:
            h.append("Verlustjagd: Mehr Einsatz nach Verlusten erhöht den erwarteten Verlust pro Minute, nie die Chance. "
                     "Feste Regel vorher festlegen: Einsatz bleibt gleich, Verlustlimit gilt.")
        if e.antworten[2] >= 2:
            h.append("Spiele nur mit Geld, dessen Verlust dein Leben nicht verändert. Das Budget oben sollte genau das sein.")
    if stufe == "hoch":
        h.append("Dein Selbst-Check zeigt viele Warnzeichen. Das ist keine Diagnose, aber ein guter Anlass für Pause, "
                 "Sperre (OASIS) oder ein anonymes Beratungsgespräch: check-dein-spiel.de")

    return Profil(hausvorteil=round(hv, 4), verlust_pro_stunde=round(pro_stunde, 2),
                  verlust_pro_woche=round(pro_woche, 2), verlust_pro_monat=round(pro_woche * WOCHEN_PRO_MONAT, 2),
                  puffer_einsaetze=round(puffer, 1), lebensdauer_stunden=lebensdauer,
                  sitzung=sitzung, sitzung_spins=spins, score=score, stufe=stufe,
                  empf_max_einsatz=empf_einsatz, empf_sitzung_minuten=minuten, hinweise=h)


def _h(v: Volatilitaet) -> float:
    from .analyse import TREFFERQUOTE
    return TREFFERQUOTE[v]


def formatiere_profil(p: Profil, e: ProfilEingabe) -> str:
    """Ruhiger, sachlicher Text ohne Dekor."""
    w = "EUR"
    L = ["Dein Risikoprofil", ""]
    L.append(f"Mathematik (Hausvorteil {p.hausvorteil*100:.2f} %):")
    L.append(f"  Erwarteter Verlust: {p.verlust_pro_stunde:.2f} {w} pro Stunde · {p.verlust_pro_woche:.2f} pro Woche · "
             f"{p.verlust_pro_monat:.2f} pro Monat")
    leben = "unbegrenzt" if math.isinf(p.lebensdauer_stunden) else f"{p.lebensdauer_stunden:.1f} Stunden"
    L.append(f"  Puffer: {p.puffer_einsaetze:g} Einsätze · erwartete Budget-Lebensdauer: {leben} "
             "(Mittelwert, die Streuung ist groß)")
    s = p.sitzung
    if s:
        L.append(f"  Eine Sitzung von {e.sitzungs_minuten:.0f} min (~{p.sitzung_spins} Spins): "
                 f"Risk of Ruin {s.risk_of_ruin*100:.1f} % "
                 f"(95%-KI {s.ki_risk_of_ruin[0]*100:.1f}..{s.ki_risk_of_ruin[1]*100:.1f} %), "
                 f"im Plus {s.p_im_plus*100:.1f} %")
    L.append("")
    if p.score is None:
        L.append("Selbst-Check: nicht beantwortet (6 Fragen, 0-3). Ohne ihn gilt die mildeste Faustregel.")
    else:
        L.append(f"Selbst-Check: {p.score} von 18 Punkten · Stufe {p.stufe}")
    L.append(f"Faustregel für dich: Einsatz höchstens {p.empf_max_einsatz:.2f} {w} · Sitzung höchstens "
             f"{p.empf_sitzung_minuten} min")
    for hin in p.hinweise:
        L.append(f"  · {hin}")
    L += ["", "Das ist deine Erwartungswert-Mathematik und eine Selbstbeobachtung – keine Spin-Vorhersage und keine Diagnose.",
          "Der Erwartungswert bleibt negativ."]
    return "\n".join(L)


_VOLA = {"niedrig": Volatilitaet.NIEDRIG, "low": Volatilitaet.NIEDRIG,
         "mittel": Volatilitaet.MITTEL, "mid": Volatilitaet.MITTEL,
         "hoch": Volatilitaet.HOCH, "high": Volatilitaet.HOCH}


def eingabe_aus_text(text: str) -> ProfilEingabe:
    """`budget=100 einsatz=1 rtp=96 vola=mittel spins_h=500 std_woche=2 minuten=60 check=1,0,2,0,1,0`."""
    import re

    e = ProfilEingabe()
    gefunden = False
    for k, v in re.findall(r"([a-zA-Z_]+)\s*[=:]\s*([\w.,\-]+)", text or ""):
        k = k.lower()
        try:
            if k in ("budget", "guthaben"):
                e.budget = float(v.replace(",", "."))
            elif k in ("einsatz", "bet"):
                e.einsatz = float(v.replace(",", "."))
            elif k == "rtp":
                r = float(v.replace(",", "."))
                e.rtp = r / 100 if r > 1.5 else r
            elif k in ("vola", "volatilitaet"):
                e.volatilitaet = _VOLA[v.lower()]
            elif k in ("spins_h", "spins_pro_stunde"):
                e.spins_pro_stunde = float(v.replace(",", "."))
            elif k in ("std_woche", "stunden_woche"):
                e.stunden_pro_woche = float(v.replace(",", "."))
            elif k in ("minuten", "sitzung"):
                e.sitzungs_minuten = float(v.replace(",", "."))
            elif k in ("check", "antworten"):
                e.antworten = [int(x) for x in v.split(",")]
            else:
                continue
            gefunden = True
        except (ValueError, KeyError):
            raise ValueError(f"Wert für „{k}“ nicht lesbar.") from None
    if not gefunden:
        raise ValueError("Keine Angaben erkannt.")
    return e
