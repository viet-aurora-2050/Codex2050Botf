"""∆1 // GEWINNER – dokumentierte Faelle: mit Mathematik gewonnen, dann verbannt.

Reale, gut belegte Faelle von Menschen, die Gluecksspiele mit Intelligenz und
Mathematik legal geschlagen haben – und dafuer Hausverbot bekamen oder deren
Regel danach geaendert wurde.

Der rote Faden (und der ehrliche Kern): Diese Leute gewannen NUR dort, wo es
einen echten strukturellen Riss gab:
  - abhaengige Ziehungen (Blackjack – Karten ohne Zuruecklegen),
  - physikalische Unwucht (mechanisch fehlerhafte Roulette-Kessel),
  - fehlerhafter +EV-Auszahlungsmechanismus (Lotto-Rolldown / alle
    Kombinationen kaufen).
Zertifizierte RNG-Slots haben KEINEN dieser Risse (unabhaengige Ziehungen,
keine Unwucht, negativer EV per Design). Deshalb existiert kein „Slot-Thorp".
Und die Belohnung fuers Gewinnen war der Rauswurf.

Quellen sind als nachpruefbare Referenzen (Buch/Gericht/Presse) angegeben,
bewusst ohne erfundene Links.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Fall:
    name: str
    zeit: str
    spiel: str
    methode: str
    mathe: str          # warum es mathematisch funktionierte
    ergebnis: str       # Gewinn + Rauswurf/Regeländerung
    legal: str          # rechtlicher Ausgang
    quelle: str


FAELLE: List[Fall] = [
    Fall(
        name="Edward O. Thorp",
        zeit="ab 1962",
        spiel="Blackjack",
        methode="Kartenzaehlen (High-Low), mathematisch hergeleitet (MIT-Mathematiker)",
        mathe="Blackjack-Karten werden OHNE Zuruecklegen gezogen -> die Wahrscheinlichkeiten "
              "haengen vom Reststapel ab. Viele hohe Karten im Rest verschieben den "
              "Erwartungswert zum Spieler. Das ist der Riss: abhaengige Ziehungen.",
        ergebnis="Bewies Blackjack als schlagbar; Casinos fuehrten mehrere Decks, "
                 "Mischmaschinen und Hausverbote fuer Zaehler ein.",
        legal="Legal – Kartenzaehlen im Kopf ist kein Betrug; Casinos reagieren mit Hausrecht.",
        quelle="E. Thorp, „Beat the Dealer\" (1962).",
    ),
    Fall(
        name="MIT Blackjack Team",
        zeit="1980er–1990er",
        spiel="Blackjack",
        methode="Team-Kartenzaehlen, Rollenverteilung (Spotter/Big Player), Bankroll-Management",
        mathe="Dasselbe Prinzip wie Thorp, im Team skaliert: nur bei positiver Zaehlung "
              "hohe Einsaetze -> messbarer, wenn auch kleiner Spielervorteil ueber Volumen.",
        ergebnis="Gewinne in Millionenhoehe; von zahlreichen Casinos identifiziert und "
                 "mit Hausverbot belegt.",
        legal="Legal, aber ueber Hausrecht/Ueberwachung (z. B. Griffin) ausgeschlossen.",
        quelle="B. Mezrich, „Bringing Down the House\" (2002, dramatisiert); Film „21\".",
    ),
    Fall(
        name="Gonzalo Garcia-Pelayo",
        zeit="1990er",
        spiel="Roulette",
        methode="Tausende Kessel-Ergebnisse protokolliert, unwuchtige Kessel gefunden, "
                "auf haeufigere Zahlen gesetzt",
        mathe="Ein real existierender Kessel ist nie perfekt – kleine mechanische "
              "Unwuchten machen manche Zahlen minimal haeufiger. Das kippt den "
              "Erwartungswert. Reine Beobachtung, kein Geraet.",
        ergebnis="Gewann mit Familie eine hohe Summe; Casinos versuchten, ihn "
                 "auszuschliessen.",
        legal="Spanischer Oberster Gerichtshof entschied zu seinen Gunsten – er nutzte "
              "nur oeffentlich beobachtbare Daten, kein Hilfsmittel.",
        quelle="Urteil Tribunal Supremo (Spanien); breite Presseberichterstattung.",
    ),
    Fall(
        name="Richard Jarecki",
        zeit="1960er–1970er",
        spiel="Roulette",
        methode="Systematische Kessel-Analyse in europaeischen Casinos, Wetten auf "
                "bevorzugte Zahlen unwuchtiger Kessel",
        mathe="Gleicher Riss wie Garcia-Pelayo: physikalische Unwucht schlaegt den "
              "theoretischen Gleichverteilungs-Nachteil.",
        ergebnis="Gewann rund 1,2 Mio. US-Dollar; wurde von Casinos ausgeschlossen.",
        legal="Legal – Ausnutzung eines realen Materialfehlers; Casinos reagierten mit "
              "haeufigerem Kesseltausch und Hausverbot.",
        quelle="Nachrufe u. a. New York Times (2018), die die Kessel-Methode bestaetigten.",
    ),
    Fall(
        name="Stefan Mandel",
        zeit="1980er–1992",
        spiel="Lotterie",
        methode="Alle moeglichen Zahlenkombinationen aufkaufen, wenn der Jackpot groesser "
                "war als die Gesamtkosten aller Tickets (Investoren-Syndikat)",
        mathe="Wenn Jackpot + Nebengewinne > Kosten ALLER Kombinationen, ist der "
              "Erwartungswert POSITIV. Ein Rechen-/Regelfehler der Lotterie, kein Zufall.",
        ergebnis="Gewann 14 Lotterien, u. a. Virginia 1992 (~7,1 Mio. Kombinationen "
                 "gekauft). Danach aenderten viele Lotterien die Regeln.",
        legal="Damals legal; Gesetze wurden anschliessend angepasst, um Massenkauf zu "
              "verhindern.",
        quelle="Umfangreich dokumentiert (u. a. Virginia-Lottery-Fall 1992).",
    ),
    Fall(
        name="Gerald „Jerry\" Selbee (Cash WinFall)",
        zeit="2005–2011",
        spiel="Lotterie (Massachusetts „Cash WinFall\")",
        methode="Grosskauf genau in den „Rolldown\"-Wochen, in denen der Jackpot auf "
                "kleinere Gewinnstufen verteilt wurde",
        mathe="Beim Rolldown wurde der Erwartungswert der niedrigeren Stufen kurzfristig "
              "POSITIV – ein Konstruktionsfehler der Spielregel, mathematisch ausnutzbar.",
        ergebnis="Selbees Gruppe und eine MIT-Gruppe gewannen ueber Jahre Millionen, bis "
                 "der Staat das Spiel 2012 beendete.",
        legal="Legal; ein Untersuchungsbericht bestaetigte, dass keine Regel gebrochen wurde.",
        quelle="Bericht des Inspector General von Massachusetts (2012); Boston Globe; "
               "Film „Jerry & Marge Go Large\".",
    ),
    Fall(
        name="Phil Ivey (Gegenbeispiel)",
        zeit="2012",
        spiel="Punto Banco / Baccarat",
        methode="„Edge Sorting\": winzige Asymmetrien im Kartenrueckenmuster ausnutzen",
        mathe="Technisch ein Informationsvorteil – aber er verlangte aktive Manipulation "
              "des Ablaufs (Bitte, Karten zu drehen).",
        ergebnis="Gewann ~7,7 Mio. GBP (Crockfords) und ~10 Mio. USD (Borgata) – musste "
                 "beides zurueckgeben.",
        legal="Gerichte (u. a. UK Supreme Court 2017) werteten es als unzulaessiges "
              "Vorgehen. Zeigt: nicht jede Cleverness gilt als legal.",
        quelle="UK Supreme Court, Ivey v Genting (2017); Borgata-Verfahren (USA).",
    ),
]


LEHRE = [
    "Alle echten Gewinner nutzten einen REALEN strukturellen Riss:",
    "  • abhaengige Ziehungen (Blackjack),",
    "  • physikalische Unwucht (Roulette-Kessel),",
    "  • fehlerhafter +EV-Auszahlungsmechanismus (Lotto-Rolldown / alle Kombinationen).",
    "Ein zertifizierter Online-Slot hat KEINEN dieser Risse: unabhaengige Ziehungen, "
    "keine Unwucht, negativer Erwartungswert per Design. Darum gibt es keinen „Slot-Thorp\".",
    "Und die Belohnung fuers Gewinnen war fast immer: Hausverbot oder Regeländerung.",
    "Das Haus laesst sich nicht schlagen – und wo doch, aendert es die Regeln.",
]


def formatiere() -> str:
    L: List[str] = []
    L.append("∆1 // GEWINNER – mit Mathematik gewonnen, dann verbannt")
    L.append("=" * 52)
    for f in FAELLE:
        L.append("")
        L.append(f"▮ {f.name}  ({f.zeit}) — {f.spiel}")
        L.append(f"  Methode:  {f.methode}")
        L.append(f"  Mathe:    {f.mathe}")
        L.append(f"  Ergebnis: {f.ergebnis}")
        L.append(f"  Recht:    {f.legal}")
        L.append(f"  Quelle:   {f.quelle}")
    L.append("")
    L.append("— LEHRE —")
    for z in LEHRE:
        L.append("  " + z)
    L.append("")
    L.append("Kein Rat zum Gluecksspiel. Hilfe anonym: 0800 1 37 27 00 · www.check-dein-spiel.de")
    return "\n".join(L)
