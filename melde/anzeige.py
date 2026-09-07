"""∆1 // MELDE-ASSISTENT – Mathematik + Beschwerde/Anzeige an die Behörde.

Verbindet das mathematische Prinzip (Hausvorteil, struktureller Verlust,
Risk of Ruin) mit einer FAKTISCHEN Beschwerde/Anzeige an die zustaendige
Aufsicht (in Deutschland: GGL – Gemeinsame Gluecksspielbehoerde der Laender).

Nutzbar fuer JEDEN Online-Anbieter.

WICHTIGE SCHUTZREGELN (fest eingebaut):
  - Nur WAHRHEITSGEMAESSE Angaben. Eine wissentlich falsche Anzeige/
    Verdaechtigung ist selbst strafbar (§ 164, § 145d StGB).
  - Zuerst den Lizenzstatus pruefen (offizielle GGL-Whitelist). Ohne
    gesicherten Befund wird alles als VERDACHT / Bitte um Pruefung formuliert,
    nie als feststehende Behauptung.
  - Das ist keine Rechtsberatung und kein garantierter Erfolg.

Das Melden eines Verdachts an die Aufsicht ist legal und genau ihr Zweck.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional


class Lizenz(str, Enum):
    UNBEKANNT = "unbekannt"   # noch nicht geprueft -> als Verdacht formulieren
    KEINE = "keine"           # keine gueltige deutsche Lizenz gefunden
    GUELTIG = "gueltig"       # in der GGL-Whitelist gefunden


@dataclass
class MeldeSzenario:
    anbieter: str = ""
    lizenz: Lizenz = Lizenz.UNBEKANNT
    einzahlung_gesamt: float = 0.0
    verlust: float = 0.0            # 0 -> es wird die Einzahlung als Bezug genutzt
    zeitraum_von: str = ""
    zeitraum_bis: str = ""
    rtp: float = 0.96
    # optionale Absenderdaten (nur du entscheidest, ob du sie einträgst)
    name: str = ""
    ort: str = ""
    # optionale Spielparameter fuer die Risiko-Kennzahl
    einsatz: float = 1.0
    spins: int = 500
    waehrung: str = "EUR"


@dataclass
class MeldeErgebnis:
    hausvorteil: float
    erwarteter_verlust_struktur: float
    risk_of_ruin: Optional[float]
    text: str
    warnungen: List[str] = field(default_factory=list)


GGL_WHITELIST_HINWEIS = (
    "Pruefe den Anbieter zuerst in der offiziellen Whitelist der GGL "
    "(Gemeinsame Gluecksspielbehoerde der Laender, www.ggl.de). Nur dort "
    "gelistete Anbieter haben eine gueltige deutsche Erlaubnis."
)


def _mathblock(s: MeldeSzenario) -> tuple:
    hausvorteil = 1.0 - s.rtp
    bezug = s.verlust if s.verlust > 0 else s.einzahlung_gesamt
    # struktureller Erwartungsverlust ueber den getaetigten Umsatz-Bezug:
    strukt = bezug * hausvorteil
    risk = None
    try:
        from risiko import RisikoSzenario, analysiere
        if s.einzahlung_gesamt > 0 and s.einsatz > 0:
            e = analysiere(
                RisikoSzenario(budget=s.einzahlung_gesamt, einsatz=s.einsatz,
                               spins=s.spins, rtp=s.rtp),
                runs=4000,
            )
            risk = e.risk_of_ruin
    except Exception:
        risk = None
    return round(hausvorteil, 4), round(strukt, 2), risk


def erstelle(s: MeldeSzenario) -> MeldeErgebnis:
    hausvorteil, strukt, risk = _mathblock(s)
    heute = date.today().isoformat()
    w = s.waehrung
    anbieter = s.anbieter.strip() or "[Anbieter eintragen]"
    von = s.zeitraum_von or "[Datum]"
    bis = s.zeitraum_bis or "[Datum]"

    warnungen = [
        "Nur wahrheitsgemaesse Angaben einreichen – eine wissentlich falsche "
        "Anzeige ist selbst strafbar (§ 164 StGB).",
        GGL_WHITELIST_HINWEIS,
        "Keine Rechtsberatung, kein garantierter Erfolg. Fuer den Einzelfall: "
        "Verbraucherzentrale oder Fachanwalt fuer Gluecksspielrecht.",
    ]

    # Rechtliche Einordnung je nach Lizenzstatus – konservativ, als Verdacht.
    if s.lizenz == Lizenz.GUELTIG:
        einordnung = (
            "Der Anbieter ist offenbar in der GGL-Whitelist gelistet (gueltige "
            "Erlaubnis). Eine Anzeige wegen Angebots ohne Erlaubnis kommt dann "
            "nicht in Betracht. Eine Beschwerde ist dennoch moeglich, wenn "
            "konkrete Pflichtverstoesse vorliegen (z. B. Missachtung von Limits, "
            "Verweigerung fristgerechter Auszahlung, Verstoss gegen "
            "Spielerschutzauflagen). Bitte in diesem Fall den konkreten "
            "Pflichtverstoss schildern."
        )
        antrag = (
            "Ich bitte um Pruefung des geschilderten Verhaltens auf Verstoesse "
            "gegen die Erlaubnisauflagen und den Spielerschutz."
        )
    else:
        verdacht = ("nicht in der Whitelist auffindbar" if s.lizenz == Lizenz.KEINE
                    else "durch mich noch nicht gesichert geprueft")
        einordnung = (
            f"Nach meinem Kenntnisstand ist der Anbieter {verdacht}. Sollte keine "
            f"gueltige deutsche Erlaubnis vorliegen, besteht der Verdacht eines "
            f"unerlaubten Gluecksspielangebots gegenueber Spielern in Deutschland "
            f"(§ 4 Gluecksspielstaatsvertrag 2021). In diesem Fall koennen "
            f"abgeschlossene Spielvertraege nichtig sein (§ 134 BGB), sodass "
            f"geleistete Einzahlungen ggf. zurueckgefordert werden koennen "
            f"(§ 812 BGB). Dies ist ausdruecklich als Verdacht und Bitte um "
            f"Pruefung formuliert, nicht als feststehende Behauptung."
        )
        antrag = (
            "Ich bitte um Pruefung, ob der Anbieter ueber eine gueltige deutsche "
            "Erlaubnis verfuegt, und – falls nicht – um Einleitung der "
            "erforderlichen aufsichtsrechtlichen Schritte."
        )

    L: List[str] = []
    L.append("An: Gemeinsame Gluecksspielbehoerde der Laender (GGL)")
    L.append("Betreff: Beschwerde / Hinweis auf moeglichen Verstoss – "
             f"Online-Anbieter „{anbieter}\"")
    L.append(f"Datum: {heute}")
    if s.name or s.ort:
        L.append(f"Absender: {s.name or '[Name]'}, {s.ort or '[Ort]'}")
    L.append("")
    L.append("Sehr geehrte Damen und Herren,")
    L.append("")
    L.append("1) SACHVERHALT")
    L.append(f"   Anbieter: {anbieter}")
    L.append(f"   Zeitraum meiner Nutzung: {von} bis {bis}")
    L.append(f"   Getaetigte Einzahlungen gesamt: {s.einzahlung_gesamt:.2f} {w}")
    if s.verlust > 0:
        L.append(f"   Davon Verlust: {s.verlust:.2f} {w}")
    L.append(f"   Lizenzstatus (mein Kenntnisstand): {s.lizenz.value}")
    L.append("")
    L.append("2) MATHEMATISCHE EINORDNUNG (neutral, zur Dokumentation)")
    L.append(f"   Angegebener RTP: {s.rtp*100:.2f} % -> struktureller Hausvorteil "
             f"{hausvorteil*100:.2f} %.")
    L.append(f"   Erwarteter struktureller Verlust ueber den Bezugsbetrag: "
             f"{strukt:.2f} {w}.")
    if risk is not None:
        L.append(f"   Rechnerisches Ruin-Risiko bei den angegebenen Parametern: "
                 f"{risk*100:.1f} % (Monte-Carlo, oeffentliche Parameter).")
    L.append("   Diese Zahlen belegen den systematischen Nachteil des Spielers; "
             "sie sind kein Vorwurf fuer sich, sondern Kontext.")
    L.append("")
    L.append("3) RECHTLICHE EINORDNUNG")
    L.append("   " + einordnung)
    L.append("")
    L.append("4) ANTRAG")
    L.append("   " + antrag)
    L.append("   Um Zwischennachricht und Aktenzeichen wird gebeten.")
    L.append("")
    L.append("Ich versichere, dass die obigen Angaben nach bestem Wissen "
             "wahrheitsgemaess sind.")
    L.append("")
    L.append("Mit freundlichen Gruessen")
    L.append(s.name or "[Name]")
    L.append("")
    L.append("— — —")
    L.append("HINWEISE:")
    for wn in warnungen:
        L.append(f"• {wn}")

    return MeldeErgebnis(
        hausvorteil=hausvorteil,
        erwarteter_verlust_struktur=strukt,
        risk_of_ruin=risk,
        text="\n".join(L),
        warnungen=warnungen,
    )


def formatiere(e: MeldeErgebnis) -> str:
    return e.text
