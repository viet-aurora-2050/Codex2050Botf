"""AGB-Datenbank: öffentliche Bonus-/AGB-Seiten täglich lesen, mit dem Scanner auswerten, Änderungen erkennen.

Schreibt docs/agb.json. Je Anbieter eine Liste öffentlicher Seiten (nur Seiten, die ohne Anmeldung und ohne
Umgehung von Schutzmaßnahmen lesbar sind):

  * rolle "bonus"       -> Abschnitt mit dem Willkommensbonus wird gescannt (Funde mit Beleg, Annahmen, Beispiele).
  * rolle "bedingungen" / "agb" -> einzelne Fundstellen (Faktor, Limits, Fristen) ohne Zusammenfassung zu EINEM Wert,
    weil allgemeine AGB mehrere Angebote und Zusammenhänge mischen.
  * rolle "start"       -> nur Erreichbarkeit und (falls lesbar) bis zu 3 Links zu AGB-/Bonusseiten.

Ehrlichkeit und Rücksicht:
  * Nur https, nur der konfigurierte Host (auch nach Weiterleitungen), robots.txt wird beachtet,
    identifizierbarer User-Agent, Größen- und Zeitlimit, 1 s Pause zwischen Abrufen.
  * 403/Geo-Sperre/JavaScript-Hülle werden als Status dokumentiert, NICHT umgangen.
  * Gespeichert werden Kennzahlen, kurze Textbelege (max. 150 Zeichen), Quelle, Abrufdatum und ein Hash – nicht der
    vollständige Text. Ändert sich der Hash des relevanten Texts, wird `geaendert` gesetzt (AGB-Änderungsmonitor).
  * Fällt ein Abruf aus, bleibt der letzte erfolgreiche Befund erhalten und der Status zeigt den Ausfall.
  * Keine Zahl wird erfunden; Annahmen stehen getrennt (siehe analyzer.scan).

Aufruf:  python -m datenbank.agb_sammler [--dry-run] [--out pfad.json]
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from analyzer.bonus import BonusSzenario, UmsatzBasis, analysiere, formatiere
from analyzer.scan import relevante_saetze, scanne

from .anbieter_whitelist import MAX_BYTES, USER_AGENT

SCHEMA_VERSION = "1.0"
HINWEIS = (
    "Aus oeffentlich lesbaren Bonus-/AGB-Seiten automatisch ausgelesen (Regex-Scanner, kein Rechtstext). "
    "Gespeichert werden Kennzahlen, kurze Belege, Quelle und Abrufdatum. Angebote und Bedingungen aendern sich - "
    "vor einer Entscheidung das Original lesen. Keine Anbieter-API, keine Vorhersage, keine Rechtsberatung."
)
ROBOTS_TOKEN = "Codex2050Games"  # noqa: S105 - robots.txt-Agentenname, kein Passwort
MIN_ZEICHEN = 600                # darunter: Sperrseite/JavaScript-Hülle, kein lesbarer Inhalt
PAUSE_SEKUNDEN = 1.0
MAX_FUNDSTELLEN = 30
FUNDSTELLEN_FELDER = {"Umsatzfaktor", "Maximaler Einsatz mit Bonus", "Maximaler Gewinn/Auszahlung", "Zeitlimit",
                      "Mindesteinzahlung", "Bonus-Deckel"}
BEISPIEL_EINZAHLUNGEN = (10, 50, 100)

JP = "https://www.jackpotpiraten.de"
KONFIG: Dict[str, Dict] = {
    "jackpotpirat": {
        "name": "JackpotPiraten",
        "host": "www.jackpotpiraten.de",
        "seiten": [
            {"id": "bonus", "titel": "Bonus-Übersicht (Willkommensbonus)", "url": f"{JP}/bonus", "rolle": "bonus",
             "abschnitt": r"Willkommensbonus\s+\d{4}\s+im\s+Detail", "abschnitt_laenge": 2500},
            {"id": "promotionsbedingungen", "titel": "Promotionsbedingungen", "url": f"{JP}/info/promotions-bedingungen",
             "rolle": "bedingungen"},
            {"id": "agb", "titel": "Allgemeine Geschäftsbedingungen", "url": f"{JP}/info/allgemeine-geschaeftsbedingungen",
             "rolle": "agb"},
        ],
    },
    # Betreiberseiten, die laut docs/anbieter.json (betreiberseiten_hinweis) nicht maschinell lesbar waren:
    # nur Erreichbarkeits-Status, ohne Umgehung. Wird eine Seite lesbar, werden AGB-/Bonus-Links entdeckt.
    "tipico": {"name": "Tipico Games", "host": "games.tipico.de",
               "seiten": [{"id": "start", "titel": "Startseite", "url": "https://games.tipico.de/", "rolle": "start"}]},
    "betano": {"name": "Betano", "host": "www.betano.de",
               "seiten": [{"id": "start", "titel": "Startseite", "url": "https://www.betano.de/", "rolle": "start"}]},
    "n1": {"name": "N1 Casino", "host": "n1casino.com",
           "seiten": [{"id": "start", "titel": "Startseite", "url": "https://n1casino.com/", "rolle": "start"}]},
    "stargames": {"name": "Stargames", "host": "www.stargames.de",
                  "seiten": [{"id": "start", "titel": "Startseite", "url": "https://www.stargames.de/", "rolle": "start"}]},
}

# Rückgabe von hole(): (HTTP-Status oder None, Text oder None, Fehlermeldung oder None)
HoleFn = Callable[[str], Tuple[Optional[int], Optional[str], Optional[str]]]


def _jetzt() -> datetime:
    return datetime.now(timezone.utc)


def hole(url: str, timeout: int = 20) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """Eine Seite laden. Erzwingt https; Weiterleitungen auf fremde Hosts werden verworfen."""
    teile = urllib.parse.urlsplit(url)
    if teile.scheme != "https" or not teile.hostname:
        return None, None, "nur https-URLs erlaubt"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain"})  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - Schema oben geprueft
            if urllib.parse.urlsplit(resp.geturl()).hostname != teile.hostname:
                return resp.status, None, "Weiterleitung auf anderen Host verworfen"
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "html" not in ctype and "text/plain" not in ctype:
                return resp.status, None, f"unerwarteter Content-Type: {ctype or 'unbekannt'}"
            raw = resp.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        return exc.code, None, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, None, f"nicht erreichbar ({type(exc).__name__})"
    if len(raw) > MAX_BYTES:
        return resp.status, None, "Antwort groesser als erlaubt"
    return resp.status, raw.decode("utf-8", errors="replace"), None


def robots_erlaubt(url: str, hole_fn: HoleFn, cache: Dict[str, Optional[urllib.robotparser.RobotFileParser]]) -> bool:
    """robots.txt des Hosts beachten. 4xx/fehlend = erlaubt (Standard), 5xx/Netzfehler = nicht lesen."""
    teile = urllib.parse.urlsplit(url)
    host = teile.netloc
    if host not in cache:
        status, text, _ = hole_fn(f"{teile.scheme}://{host}/robots.txt")
        if status is not None and 400 <= status < 500:
            cache[host] = None                              # keine robots.txt -> alles erlaubt
        elif text is None:
            cache[host] = urllib.robotparser.RobotFileParser()   # Netzfehler/5xx: vorsichtshalber nichts lesen
            cache[host].disallow_all = True
        else:
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(text.splitlines())
            rp.modified()
            cache[host] = rp
    rp = cache[host]
    return True if rp is None else rp.can_fetch(ROBOTS_TOKEN, url)


def seitentext(seite: str) -> str:
    seite = re.sub(r"(?is)<(script|style|noscript|nav|header|footer|svg)[^>]*>.*?</\1>", " ", seite)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seite))).strip()


def abschnitt(text: str, muster: str, laenge: int) -> Optional[str]:
    m = re.search(muster, text, re.I)
    return text[m.start(): m.start() + laenge] if m else None


def szenario_dict(s: BonusSzenario) -> Dict:
    """Schlüssel wie im JavaScript-Port (docs/index.html, agbRechne)."""
    return {
        "einzahlung": s.einzahlung, "bonus_betrag": s.bonus_betrag, "bonus_prozent": s.bonus_prozent,
        "bonus_deckel": s.bonus_deckel, "umsatzfaktor": s.umsatzfaktor, "basis": s.umsatz_basis.value,
        "freispiel_gewinn": s.freispiel_gewinn, "freispiel_faktor": s.freispiel_umsatzfaktor, "rtp": s.rtp,
        "max_gewinn": s.max_gewinn, "max_einsatz": s.max_einsatz_pro_spin, "zeitlimit": s.zeitlimit_tage,
        "einsatz": s.durchschnittseinsatz, "sph": s.spins_pro_stunde, "std_tag": s.spielstunden_pro_tag,
    }


def szenario_aus_dict(d: Dict) -> BonusSzenario:
    return BonusSzenario(
        einzahlung=d["einzahlung"], bonus_betrag=d["bonus_betrag"], bonus_prozent=d["bonus_prozent"],
        bonus_deckel=d["bonus_deckel"], umsatzfaktor=d["umsatzfaktor"], umsatz_basis=UmsatzBasis(d["basis"]),
        freispiel_gewinn=d["freispiel_gewinn"], freispiel_umsatzfaktor=d["freispiel_faktor"], rtp=d["rtp"],
        max_gewinn=d["max_gewinn"], max_einsatz_pro_spin=d["max_einsatz"], zeitlimit_tage=d["zeitlimit"],
        durchschnittseinsatz=d["einsatz"], spins_pro_stunde=d["sph"], spielstunden_pro_tag=d["std_tag"])


def _funde(scan) -> List[Dict]:
    return [{"feld": f.feld, "wert": str(f.wert), "beleg": f.beleg} for f in scan.funde]


def werte_bonus_aus(text: str, cfg: Dict) -> Dict:
    """Willkommensbonus-Abschnitt scannen (Fallback: ganze relevante Seite, mit Hinweis)."""
    teil = abschnitt(text, cfg["abschnitt"], cfg["abschnitt_laenge"]) if cfg.get("abschnitt") else None
    gefunden = teil is not None
    quelle = teil if gefunden else relevante_saetze(text)
    try:
        scan = scanne(quelle)
    except ValueError as exc:
        return {"abschnitt_gefunden": gefunden, "fehler": str(exc)}
    hinweise = list(scan.hinweise)
    if not gefunden:
        hinweise.insert(0, "Abschnitt „Willkommensbonus“ nicht gefunden (Seitenaufbau geändert?) – ganze Seite gelesen, "
                           "Werte können mehrere Angebote mischen.")
    beispiele = []
    if scan.szenario.bonus_prozent is not None or scan.szenario.bonus_betrag is not None:
        for ez in BEISPIEL_EINZAHLUNGEN:
            try:
                sc = scanne(quelle, einzahlung=ez)
                e = analysiere(sc.szenario)
            except ValueError:
                continue
            beispiele.append({"einzahlung": ez, "bonus": e.bonus, "mindestumsatz": e.mindestumsatz,
                              "erwarteter_verlust": e.erwarteter_verlust, "erwartungswert": e.erwartungswert,
                              "benoetigte_tage": e.benoetigte_tage, "empfehlung": e.empfehlung.value})
    return {"abschnitt_gefunden": gefunden, "funde": _funde(scan), "annahmen": scan.annahmen, "hinweise": hinweise,
            "szenario": szenario_dict(scan.szenario), "beispiele": beispiele,
            "mindesteinzahlung": scan.mindesteinzahlung, "freispiele_anzahl": scan.freispiele_anzahl}


def fundstellen(text: str) -> List[Dict]:
    """Einzelne Fundstellen aus allgemeinen AGB: jeder Satz für sich, keine Zusammenfassung zu einem Wert."""
    from analyzer.scan import _saetze   # interne Satzzerlegung wiederverwenden

    gesehen, out = set(), []
    for satz in _saetze(relevante_saetze(text)):
        try:
            sc = scanne(satz, strikt=False)
        except ValueError:
            continue
        for f in sc.funde:
            if f.feld in FUNDSTELLEN_FELDER and (f.feld, str(f.wert)) not in gesehen:
                gesehen.add((f.feld, str(f.wert)))
                out.append({"feld": f.feld, "wert": str(f.wert), "beleg": f.beleg})
                if len(out) >= MAX_FUNDSTELLEN:
                    return out
    return out


def entdecke_links(seite: str, url: str, host: str) -> List[Dict]:
    """Bis zu 3 AGB-/Bonus-Links desselben Hosts aus einer lesbaren Startseite."""
    gefunden: Dict[str, str] = {}
    for href in re.findall(r'href="([^"#]+)"', seite):
        voll = urllib.parse.urljoin(url, html.unescape(href))
        t = urllib.parse.urlsplit(voll)
        if t.scheme == "https" and t.hostname == host and re.search(r"agb|bonus|bedingung|promotion", t.path, re.I):
            gefunden.setdefault(f"https://{t.hostname}{t.path}", t.path)
    return [{"id": f"entdeckt-{i}", "titel": f"Entdeckt: {pfad}", "url": u, "rolle": "bedingungen", "entdeckt": True}
            for i, (u, pfad) in enumerate(sorted(gefunden.items())[:3], 1)]


def verarbeite_seite(cfg: Dict, host: str, alt: Optional[Dict], hole_fn: HoleFn, robots: Dict, jetzt: datetime,
                     schlaf: Callable[[float], None]) -> Tuple[Dict, Optional[str]]:
    """Eine Seite abrufen und auswerten. Rückgabe: (Eintrag, HTML für Link-Entdeckung)."""
    heute = jetzt.strftime("%Y-%m-%d")
    eintrag: Dict = {k: cfg[k] for k in ("id", "titel", "url", "rolle")}
    if cfg.get("entdeckt"):
        eintrag["entdeckt"] = True
    if not robots_erlaubt(cfg["url"], hole_fn, robots):
        eintrag.update(status="robots_gesperrt", abgerufen=heute)
        return _mit_altwerten(eintrag, alt), None
    schlaf(PAUSE_SEKUNDEN)
    status, seite, fehler = hole_fn(cfg["url"])
    eintrag["abgerufen"] = heute
    if seite is None:
        eintrag.update(status="nicht_lesbar", http=status, fehler=fehler or "kein Inhalt")
        return _mit_altwerten(eintrag, alt), None
    text = seitentext(seite)
    if len(text) < MIN_ZEICHEN:
        eintrag.update(status="nicht_lesbar", http=status,
                       fehler=f"kaum lesbarer Inhalt ({len(text)} Zeichen) – Sperrseite oder JavaScript-Hülle")
        return _mit_altwerten(eintrag, alt), None
    relevant = relevante_saetze(text, max_zeichen=10 ** 6)
    sha = hashlib.sha256(relevant.encode("utf-8")).hexdigest()
    eintrag.update(status="ok", http=status, sha256=sha, zeichen=len(text))
    m = re.search(r"Stand:\s*(\d{2}\.\d{2}\.\d{4})", text)
    if m:
        eintrag["stand_text"] = m.group(1)
    if alt and alt.get("sha256"):
        eintrag["erstmals_erfasst"] = alt.get("erstmals_erfasst", alt.get("abgerufen", heute))
        if alt["sha256"] == sha:
            if alt.get("geaendert"):
                eintrag["geaendert"] = alt["geaendert"]
        else:
            eintrag["geaendert"] = heute
            eintrag["vorheriger_sha256"] = alt["sha256"]
    else:
        eintrag["erstmals_erfasst"] = heute
    rolle = cfg["rolle"]
    if rolle == "bonus":
        eintrag["ergebnis"] = werte_bonus_aus(text, cfg)
    elif rolle in ("bedingungen", "agb"):
        eintrag["ergebnis"] = {"fundstellen": fundstellen(text),
                               "hinweis": "Einzelne Fundstellen aus allgemeinen AGB – Zusammenhang im Original prüfen."}
    return eintrag, seite


def _mit_altwerten(neu: Dict, alt: Optional[Dict]) -> Dict:
    """Bei Ausfall den letzten erfolgreichen Befund behalten (nur der Status ist neu)."""
    if alt:
        for k in ("sha256", "zeichen", "stand_text", "geaendert", "vorheriger_sha256", "erstmals_erfasst", "ergebnis"):
            if k in alt:
                neu[k] = alt[k]
        neu["letzter_erfolg"] = alt.get("letzter_erfolg") or (alt.get("abgerufen") if alt.get("status") == "ok" else None)
    return neu


def baue(alt: Optional[Dict] = None, hole_fn: HoleFn = hole, konfig: Optional[Dict[str, Dict]] = None,
         jetzt: Optional[datetime] = None, schlaf: Callable[[float], None] = time.sleep) -> Dict:
    konfig = KONFIG if konfig is None else konfig
    jetzt = jetzt or _jetzt()
    robots: Dict = {}
    anbieter: Dict[str, Dict] = {}
    for key, cfg in konfig.items():
        alt_seiten = {s["id"]: s for s in ((alt or {}).get("anbieter", {}).get(key, {}).get("seiten", []))}
        seiten: List[Dict] = []
        for scfg in cfg["seiten"]:
            eintrag, roh = verarbeite_seite(scfg, cfg["host"], alt_seiten.get(scfg["id"]), hole_fn, robots, jetzt, schlaf)
            seiten.append(eintrag)
            if scfg["rolle"] == "start" and roh:
                for neu in entdecke_links(roh, scfg["url"], cfg["host"]):
                    e2, _ = verarbeite_seite(neu, cfg["host"], alt_seiten.get(neu["id"]), hole_fn, robots, jetzt, schlaf)
                    seiten.append(e2)
        anbieter[key] = {"name": cfg["name"], "host": cfg["host"], "seiten": seiten}
    return {"schema_version": SCHEMA_VERSION, "_hinweis": HINWEIS, "abgerufen": jetzt.strftime("%Y-%m-%d"),
            "geprueft": jetzt.strftime("%Y-%m-%dT%H:%M:%SZ"), "anbieter": anbieter}


def _kern(d: Dict) -> str:
    """Vergleich ohne Abrufzeiten, damit ein reiner Tageswechsel keinen Inhalts-Update ausloest."""
    def sauber(x):
        if isinstance(x, dict):
            return {k: sauber(v) for k, v in x.items() if k not in ("abgerufen", "geprueft", "letzter_erfolg")}
        if isinstance(x, list):
            return [sauber(v) for v in x]
        return x
    return json.dumps(sauber(d), ensure_ascii=False, sort_keys=True)


def schreibe(daten: Dict, pfad: str) -> bool:
    """Schreibt bei Inhaltsaenderung (True). Sonst hoechstens `geprueft`/`abgerufen` einmal pro Tag erneuern (False)."""
    p = Path(pfad)
    if p.exists():
        try:
            alt = json.loads(p.read_text(encoding="utf-8"))
            if _kern(alt) == _kern(daten):
                if str(alt.get("geprueft", ""))[:10] != daten["geprueft"][:10]:
                    alt["geprueft"], alt["abgerufen"] = daten["geprueft"], daten["abgerufen"]
                    p.write_text(json.dumps(alt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                return False
        except (OSError, json.JSONDecodeError):
            pass
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)
    return True


def lade(pfad: Optional[str] = None) -> Dict:
    p = Path(pfad) if pfad else _standard_pfad()
    return json.loads(p.read_text(encoding="utf-8"))


def _standard_pfad() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "agb.json"


def rechne(eintrag_bonus: Dict, einzahlung: Optional[float] = None, rtp: Optional[float] = None,
           einsatz: Optional[float] = None) -> str:
    """Gespeicherten Bonus-Befund mit eigenen Werten durchrechnen (Engine unveraendert). Wirft ValueError."""
    erg = eintrag_bonus.get("ergebnis") or {}
    if "szenario" not in erg:
        raise ValueError(erg.get("fehler") or "Für diese Seite liegt kein berechenbarer Bonus vor.")
    s = szenario_aus_dict(erg["szenario"])
    if einzahlung is not None:
        s.einzahlung = float(einzahlung)
    if rtp is not None:
        s.rtp = rtp / 100.0 if rtp > 1.5 else rtp
    if einsatz is not None:
        s.durchschnittseinsatz = float(einsatz)
    return formatiere(analysiere(s), s)


_STATUS_TEXT = {"ok": "gelesen", "nicht_lesbar": "nicht lesbar", "robots_gesperrt": "robots.txt sperrt das Lesen"}


def uebersicht(daten: Dict) -> str:
    """Kurzliste aller Anbieter der AGB-Datenbank (Bot/API)."""
    L = [f"AGB-Datenbank (öffentliche Seiten, geprüft {str(daten.get('geprueft', ''))[:10]})", ""]
    for key, a in daten.get("anbieter", {}).items():
        ok = sum(1 for s in a["seiten"] if s["status"] == "ok")
        L.append(f"• {key} – {a['name']}: {ok} von {len(a['seiten'])} Seite(n) lesbar")
    L += ["", "Details: /agb <anbieter> [einzahlung=50 rtp=95 einsatz=1]"]
    return "\n".join(L)


def bericht(daten: Dict, key: str, einzahlung: Optional[float] = None, rtp: Optional[float] = None,
            einsatz: Optional[float] = None) -> str:
    """Befund eines Anbieters als Text; mit einzahlung/rtp/einsatz wird der Willkommensbonus durchgerechnet.
    Wirft KeyError bei unbekanntem Anbieter, ValueError bei nicht berechenbarem Bonus."""
    a = daten["anbieter"][key]
    L = [f"AGB-DATENBANK · {a['name']}", "=" * 30]
    bonus_seite = None
    for s in a["seiten"]:
        zeile = f"• {s['titel']} – {_STATUS_TEXT.get(s['status'], s['status'])}, abgerufen {s['abgerufen']}"
        if s.get("stand_text"):
            zeile += f", Text-Stand {s['stand_text']}"
        L.append(zeile)
        L.append(f"  {s['url']}")
        if s.get("fehler"):
            L.append(f"  Hinweis: {s['fehler']} (wird nicht umgangen)")
        if s.get("geaendert"):
            L.append(f"  ⚠ Relevanter Text hat sich am {s['geaendert']} geändert – Original neu lesen.")
        erg = s.get("ergebnis") or {}
        for f in erg.get("funde", []):
            L.append(f"    {f['feld']}: {f['wert']}")
        for f in erg.get("fundstellen", [])[:8]:
            L.append(f"    Fundstelle {f['feld']}: {f['wert']}  „{f['beleg']}“")
        if s["rolle"] == "bonus" and "szenario" in erg:
            bonus_seite = s
    mit_werten = any(v is not None for v in (einzahlung, rtp, einsatz))
    if mit_werten and bonus_seite is None:
        raise ValueError("Für diesen Anbieter liegt kein berechenbarer Bonus in der AGB-Datenbank vor "
                         "(Seite nicht lesbar oder kein Bonus erkannt).")
    if bonus_seite is not None and mit_werten:
        L += ["", rechne(bonus_seite, einzahlung, rtp, einsatz)]
    elif bonus_seite is not None:
        bsp = [b for b in bonus_seite["ergebnis"]["beispiele"] if b["einzahlung"] == 50]
        if bsp:
            b = bsp[0]
            L += ["", f"Beispiel bei 50 € Einzahlung: Bonus {b['bonus']:.2f} €, Mindestumsatz {b['mindestumsatz']:.2f} €, "
                      f"Erwartungswert {b['erwartungswert']:+.2f} € (RTP 96 % angenommen)."]
    L += ["", "Automatisch aus öffentlichen Seiten gelesen – Regex-Scanner, kein Rechtstext. Original prüfen. "
              "Keine Vorhersage, keine Rechtsberatung."]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AGB-Datenbank aktualisieren (docs/agb.json)")
    ap.add_argument("--out", default=str(_standard_pfad()))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    alt = None
    if Path(args.out).exists():
        try:
            alt = json.loads(Path(args.out).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            alt = None
    daten = baue(alt)
    for key, a in daten["anbieter"].items():
        stati = ", ".join(f"{s['id']}={s['status']}" for s in a["seiten"])
        print(f"{key}: {stati}")
    if args.dry_run:
        print(json.dumps(daten, ensure_ascii=False, indent=2)[:3000])
        return 0
    print(("geschrieben: " if schreibe(daten, args.out) else "unveraendert (Kern gleich): ") + args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
