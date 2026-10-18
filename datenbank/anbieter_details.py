"""Automatische Details für Anbieter-Profile: gesetzlicher Rahmen + Jackpotpiraten-Studios.

Zwei lesbare, öffentliche Quellen (je eine Seite, identifizierbarer User-Agent, Timeout):

1. GGL-Spielerschutzseiten (amtlich) -> `regulatorischer_rahmen`: Höchsteinsatz, Stufen,
   Mindestdauer pro Spiel, Autoplay-Verbot, Cool-Down, anbieterübergreifendes Einzahlungslimit.
   Gilt für ALLE Inhaber einer deutschen Erlaubnis für virtuelle Automatenspiele – es ist
   KEINE anbieterspezifische Angabe.
2. Betreiberseite jackpotpiraten.de (robots.txt: Allow /) -> Studio-Tabelle (Studio, Anzahl
   Slots, beliebtester Titel), Gesamtzahl und Limit-Sätze.

Ehrlich:
  * Jede Zahl wird per Regex aus dem Originaltext gelesen. Findet sich ein Muster nicht,
    bleibt der bisherige Wert stehen und das Feld wird als `fehlend` gemeldet.
  * Für Tipico, Betano, N1 und Stargames sind die Betreiberseiten maschinell nicht lesbar
    (Geo-/Bot-Schutz bzw. reine JavaScript-Seite). Das wird dokumentiert, nicht umgangen.
  * Kein RTP wird erfunden.

Aufruf:  python -m datenbank.anbieter_details [--dry-run]
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .anbieter_whitelist import _standard_pfad, abrufen, schreibe

GGL_SPIELERSCHUTZ = ("https://www.gluecksspiel-behoerde.de/de/fuer-spielende/"
                     "die-spielerschutzmassnahmen-des-gluestv21-im-ueberblick/"
                     "konkrete-spielerschutzmassnahmen-fuer-verschiedene-gluecksspielarten")
GGL_LIMITS = ("https://www.gluecksspiel-behoerde.de/de/fuer-spielende/"
              "informationen-fuer-spielende-faqs/faq-einzahlungslimit-und-hoechsteinsatz")
JP_HOME = "https://www.jackpotpiraten.de/"

# Dokumentierte Erreichbarkeit der übrigen Betreiberseiten (manuelle Prüfung, kein täglicher Abruf).
BETREIBERSEITE_HINWEIS = {
    "geprueft": "2026-10-07",
    "tipico": "games.tipico.de lieferte eine „No Service\"-Seite (Geo-Sperre) – keine lesbaren Inhalte.",
    "betano": "betano.de antwortete mit HTTP 403 (Schutzseite) – nicht lesbar.",
    "n1": "n1casino.com antwortete mit HTTP 403 (Bot-Schutz) – nicht lesbar.",
    "stargames": "stargames.de liefert nur eine JavaScript-Hülle ohne lesbare Inhalte; "
                 "private Schnittstellen werden nicht erraten.",
    "folge": "Limits/Studios aus der Betreiberseite für diese Anbieter nicht übernommen.",
}


def _jetzt() -> datetime:
    return datetime.now(timezone.utc)


def _text(seite: str) -> str:
    seite = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", seite)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seite)))


def _zahl(s: str) -> int:
    return int(s.replace(".", ""))


def parse_rahmen(text_schutz: str, text_limits: str) -> Tuple[Dict, List[str]]:
    """Liest den gesetzlichen Rahmen aus den Originaltexten. Rückgabe: (Werte, fehlende Felder)."""
    regeln = [
        # (Feld, Text, Regex, Umwandlung)
        ("einsatz_regel_eur", text_limits, r"Höchsteinsatz von (\d+) Euro als Regelfall", int),
        ("einsatz_stufe1_eur", text_limits, r"ersten Stufe kann der Höchsteinsatz auf bis zu (\d+) Euro", int),
        ("einsatz_stufe2_eur", text_limits, r"zweiten Stufe ist eine weitere Erhöhung auf bis zu (\d+) Euro", int),
        ("einsatz_erhoeht_ab_alter", text_limits, r"Altersgrenze von (\d+) Jahren", int),
        ("einsatz_erhoeht_seit", text_limits, r"seit dem (\d{1,2}\. [A-Za-zäöüÄÖÜ]+ \d{4})", str),
        ("einzahlung_monat_eur", text_limits, r"nicht mehr als ([\d.]+) Euro anbieterübergreifend", _zahl),
        ("min_sekunden_pro_spiel", text_schutz, r"Mindestdauer von (\d+) Sekunden", int),
        ("cooldown_nach_min", text_schutz, r"ununterbrochenen Spieldauer von (\d+) Minuten", int),
        ("cooldown_pause_min", text_schutz, r"erst nach (\d+) Minuten nach Bestätigung", int),
    ]
    werte: Dict = {}
    fehlend: List[str] = []
    for feld, text, muster, conv in regeln:
        m = re.search(muster, text)
        if m:
            werte[feld] = conv(m.group(1))
        else:
            fehlend.append(feld)
    if re.search(r"automatische[rn]? Start[^.]{0,200}verboten", text_schutz):
        werte["autoplay_verboten"] = True
    else:
        fehlend.append("autoplay_verboten")
    return werte, fehlend


def parse_jackpotpirat(seite: str) -> Optional[Dict]:
    """Studio-Tabelle + Gesamtzahl + Limit-Sätze der Betreiberseite. None, wenn Tabelle fehlt."""
    zeilen = re.findall(r"<tr><td>([^<]+)</td><td>(\d+)</td><td>([^<]*)</td></tr>", seite)
    if len(zeilen) < 5:
        return None
    studios: Dict[str, int] = {}
    top: Dict[str, str] = {}
    for name, n, titel in zeilen:
        key = html.unescape(name).replace("’", "'").strip()
        studios[key] = int(n)
        top[key] = html.unescape(titel).replace("’", "'").strip()
    t = _text(seite)
    out: Dict = {"studios": studios, "studios_beliebtester_titel": top, "summe_studios": sum(studios.values())}
    m = re.search(r"(\d+) Spielautomaten zur Verfügung", t)
    if m:
        out["spielautomaten_angabe"] = int(m.group(1))
    m = re.search(r"Einsatzlimit von (\d+) € pro Spielrunde", t)
    if m:
        out["einsatz_pro_spin_eur"] = int(m.group(1))
    m = re.search(r"bis zu (\d+) € beziehungsweise (\d+) € pro Spin", t)
    if m:
        out["einsatz_erhoeht_eur"] = [int(m.group(1)), int(m.group(2))]
    m = re.search(r"Einzahlungslimit \( ?LUGAS Limit ?\) in Höhe von ([\d.]+) €", t)
    if m:
        out["einzahlung_monat_eur"] = _zahl(m.group(1))
    return out


def aktualisiere(daten: Dict, rahmen: Optional[Tuple[Dict, List[str]]], jp: Optional[Dict],
                 jetzt: Optional[datetime] = None) -> Dict:
    """Schreibt `regulatorischer_rahmen` und die Jackpotpiraten-Details; alles andere bleibt."""
    jetzt = jetzt or _jetzt()
    ts = jetzt.strftime("%Y-%m-%dT%H:%M:%SZ")
    daten = json.loads(json.dumps(daten))
    daten.setdefault("schema_version", "1.0")
    daten.setdefault("anbieter", {})
    daten["betreiberseiten_hinweis"] = BETREIBERSEITE_HINWEIS

    if rahmen is not None:
        werte, fehlend = rahmen
        alt = daten.get("regulatorischer_rahmen", {})
        neu = dict(alt)
        neu.update(werte)                                  # fehlende Felder behalten den alten Wert
        neu.update({
            "abgerufen": ts,
            "gilt_fuer": "Inhaber einer deutschen Erlaubnis für virtuelle Automatenspiele "
                         "(GlüStV 2021, GGL) – gesetzlicher Rahmen, nicht anbieterspezifisch",
            "fehlend": fehlend,
            "quellen": [
                {"titel": "GGL – Konkrete Spielerschutzmaßnahmen", "url": GGL_SPIELERSCHUTZ, "art": "primaer"},
                {"titel": "GGL – FAQ Einzahlungslimit und Höchsteinsatz", "url": GGL_LIMITS, "art": "primaer"},
            ],
        })
        daten["regulatorischer_rahmen"] = neu

    if jp is not None:
        p = daten["anbieter"].setdefault("jackpotpirat", {"name": "JackpotPiraten"})
        p["studios"] = jp["studios"]
        p["studios_beliebtester_titel"] = jp["studios_beliebtester_titel"]
        summe = jp["summe_studios"]
        ang = jp.get("spielautomaten_angabe")
        p["titel_gesamt_angabe"] = (f"{ang} Spielautomaten (Betreiberseite)"
                                    + (f"; die Studio-Zahlen summieren sich auf {summe}" if ang and ang != summe else ""))
        lim = p.setdefault("limits", {})
        for k in ("einsatz_pro_spin_eur", "einsatz_erhoeht_eur", "einzahlung_monat_eur"):
            if k in jp:
                lim[k] = jp[k]
        genannt = list(p.get("spiele_genannt", []))
        for titel in jp["studios_beliebtester_titel"].values():
            if titel and titel not in genannt:
                genannt.append(titel)
        p["spiele_genannt"] = genannt
        p["betreiberseite"] = {"abgerufen": ts, "url": JP_HOME, "gelesen": ["studios", "limits"]}
        quellen = p.setdefault("quellen", [])
        if not any(q.get("url") == JP_HOME for q in quellen):
            quellen.append({"titel": "JackpotPiraten – Startseite", "url": JP_HOME, "art": "betreiber"})
    daten["abgerufen"] = jetzt.strftime("%Y-%m-%d")
    return daten


def lauf(pfad: Path, seiten: Optional[Dict[str, str]] = None, dry_run: bool = False) -> int:
    """Jeder Teil läuft unabhängig; ein Ausfall lässt die jeweiligen alten Werte stehen."""
    seiten = seiten or {}

    def hole(schluessel: str, url: str) -> Optional[str]:
        if schluessel in seiten:
            return seiten[schluessel]
        try:
            return abrufen(url)
        except Exception as exc:  # noqa: BLE001
            print(f"[warnung] {schluessel} nicht abrufbar: {type(exc).__name__}: {exc} – alter Stand bleibt")
            return None

    schutz, limits, jp_html = (hole("schutz", GGL_SPIELERSCHUTZ), hole("limits", GGL_LIMITS),
                               hole("jp", JP_HOME))
    rahmen = None
    if schutz and limits:
        werte, fehlend = parse_rahmen(_text(schutz), _text(limits))
        if len(werte) >= 5:
            rahmen = (werte, fehlend)
            if fehlend:
                print(f"[warnung] Rahmen unvollständig, alte Werte bleiben für: {', '.join(fehlend)}")
        else:
            print("[warnung] Rahmen: zu wenige Werte gelesen (Seitenformat geändert?) – alter Stand bleibt")
    jp = parse_jackpotpirat(jp_html) if jp_html else None
    if jp_html and jp is None:
        print("[warnung] Jackpotpiraten: Studio-Tabelle nicht gefunden – alter Stand bleibt")

    alt = json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {}
    neu = aktualisiere(alt, rahmen, jp)
    r = neu.get("regulatorischer_rahmen", {})
    print(f"  Rahmen: Einsatz {r.get('einsatz_regel_eur')} € (Stufen {r.get('einsatz_stufe1_eur')}/{r.get('einsatz_stufe2_eur')} € "
          f"ab {r.get('einsatz_erhoeht_ab_alter')}), {r.get('min_sekunden_pro_spiel')} s/Spiel, "
          f"Einzahlung {r.get('einzahlung_monat_eur')} €/Monat, Autoplay verboten: {r.get('autoplay_verboten')}")
    if jp:
        print(f"  Jackpotpiraten: {len(jp['studios'])} Studios, Summe {jp['summe_studios']}")
    if dry_run:
        print("dry-run: nichts geschrieben")
        return 0
    print(("geschrieben: " if schreibe(neu, pfad) else "unveraendert (Kern gleich): ") + str(pfad))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Gesetzlichen Rahmen + Jackpotpiraten-Details aktualisieren")
    ap.add_argument("--out", default=str(_standard_pfad()))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    return lauf(Path(a.out), dry_run=a.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
