"""Automatischer Abgleich der Anbieter-Profile mit der offiziellen GGL-Whitelist.

Quelle: https://www.gluecksspiel-behoerde.de/de/whitelist (oeffentliche HTML-Seite
der Gemeinsamen Glücksspielbehörde der Länder). Die Seite ist laut robots.txt
abrufbar (nur PDFs und /component/ sind gesperrt). Es wird genau EINE Seite
abgerufen, mit identifizierbarem User-Agent, Timeout und Groessenlimit.

Aktualisiert wird NUR der Block `whitelist` je Anbieter in docs/anbieter.json.
Kuratierte Angaben (Limits, Studios, Quellen) bleiben unberuehrt.

Ehrlich:
  * Kein Eintrag = "keine deutsche Erlaubnis in der Whitelist gefunden" – keine
    juristische Bewertung, Stand = Abrufzeitpunkt.
  * Faellt der Abruf aus oder aendert sich das Seitenformat (zu wenige Eintraege),
    bleibt die bisherige Datei unveraendert; das Alter der Daten zeigt die App.

Aufruf:
    python -m datenbank.anbieter_whitelist              # docs/anbieter.json aktualisieren
    python -m datenbank.anbieter_whitelist --dry-run
    python -m datenbank.anbieter_whitelist --html-file whitelist.html   # offline
"""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

WHITELIST_URL = "https://www.gluecksspiel-behoerde.de/de/whitelist"
USER_AGENT = "Codex2050Games/3.0 (+https://github.com/viet-aurora-2050/Codex2050Botf)"
MAX_BYTES = 6_000_000
MIN_EINTRAEGE = 50          # Plausibilitaet: die echte Liste hat >150 Eintraege

# Welche Whitelist-Eintraege gehoeren zu welchem Anbieter-Profil?
# domains: Treffer, wenn der Eintrag diese Domain fuehrt. namen: Regex auf den Betreibernamen.
PROVIDERS: Dict[str, Dict] = {
    "jackpotpirat": {"name": "JackpotPiraten", "domains": ["jackpotpiraten.de"], "namen": []},
    "tipico": {"name": "Tipico Games", "domains": ["games.tipico.de", "casino.tipico.de"], "namen": []},
    "betano": {"name": "Betano", "domains": ["betano.de"], "namen": []},
    "n1": {"name": "N1 Casino", "domains": [], "namen": [r"\bN1\b"]},
    "stargames": {"name": "Stargames", "domains": ["stargames.de"], "namen": []},
}

_RTP_HINWEIS = ("Kein veroeffentlichter Betreiber-RTP in den verwendeten Quellen. RTP je Spiel in der "
                "Spielinfo bzw. im Tab SPIELE (Studio-Standardwerte) pruefen; kann abweichen.")

_DOMAIN = re.compile(r"(?<![\w.-])([a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.[a-z]{2,})(?![\w-])")
_DATUM = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b")


def _jetzt() -> datetime:
    return datetime.now(timezone.utc)


def abrufen(url: str = WHITELIST_URL, timeout: int = 30) -> str:
    """Laedt die Whitelist-Seite (Redirects werden gefolgt). Wirft bei Fehlern."""
    if not url.lower().startswith("https://"):
        raise ValueError("nur https-URLs erlaubt")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})  # noqa: S310
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - Schema oben geprueft
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "html" not in ctype:
            raise ValueError(f"unerwarteter Content-Type: {ctype or 'unbekannt'}")
        raw = resp.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Antwort groesser als erlaubt")
    return raw.decode("utf-8", errors="replace")


def parse_whitelist(seite: str) -> List[Dict]:
    """Zerlegt die Seite in Betreiber-Eintraege (Name, Erlaubnisarten, Domains, Daten)."""
    eintraege: List[Dict] = []
    for seg in re.split(r"(?=<li gglwhitelist-g-ids=)", seite)[1:]:
        body = seg[: seg.find("</li>")] if "</li>" in seg else seg
        m_name = re.search(r'<span class="ggl-wl-check-to-highlight">([^<]+)</span>', body)
        m_sw = re.search(r'gglwhitelist-search-words="([^"]*)"', body)
        if not m_name or not m_sw:
            continue
        name = html.unescape(m_name.group(1)).strip()
        suchwoerter = html.unescape(m_sw.group(1))
        arten = [html.unescape(a).strip() for a in re.findall(r"<h3[^>]*>([^<]+)</h3>", body)]
        domains = sorted({d for d in _DOMAIN.findall(suchwoerter.lower())})
        daten = sorted(set(_DATUM.findall(suchwoerter)), key=lambda x: tuple(reversed(x.split("."))))
        eintraege.append({"betreiber": name, "erlaubnisarten": arten, "domains": domains, "daten": daten})
    return eintraege


def _passt(eintrag: Dict, cfg: Dict) -> bool:
    doms = set(eintrag["domains"])
    for d in cfg.get("domains", []):
        if d.lower() in doms:
            return True
    return any(re.search(p, eintrag["betreiber"], re.I) for p in cfg.get("namen", []))


def abgleich(eintraege: List[Dict]) -> Dict[str, Dict]:
    """Pro Anbieter-Schluessel: gefunden ja/nein + die passenden Whitelist-Eintraege."""
    out: Dict[str, Dict] = {}
    for key, cfg in PROVIDERS.items():
        treffer = [e for e in eintraege if _passt(e, cfg)]
        out[key] = {"gefunden": bool(treffer), "eintraege": treffer}
    return out


def aktualisiere(daten: Dict, eintraege: List[Dict], jetzt: Optional[datetime] = None) -> Dict:
    """Schreibt den Block `whitelist` je Anbieter; legt fehlende Profile minimal an."""
    jetzt = jetzt or _jetzt()
    ts = jetzt.strftime("%Y-%m-%dT%H:%M:%SZ")
    daten = json.loads(json.dumps(daten))                       # tiefe Kopie
    daten.setdefault("schema_version", "1.0")
    daten.setdefault("anbieter", {})
    daten["abgerufen"] = jetzt.strftime("%Y-%m-%d")
    daten["whitelist_quelle"] = WHITELIST_URL
    for key, res in abgleich(eintraege).items():
        cfg = PROVIDERS[key]
        p = daten["anbieter"].setdefault(key, {"name": cfg["name"]})
        p.setdefault("rtp_hinweis", _RTP_HINWEIS)
        quellen = p.setdefault("quellen", [])
        if not any(q.get("url") == WHITELIST_URL for q in quellen):
            quellen.append({"titel": "GGL – Whitelist (Übersicht erlaubter Anbieter)",
                            "url": WHITELIST_URL, "art": "primaer"})
        p["whitelist"] = {
            "abgerufen": ts,
            "gefunden": res["gefunden"],
            "eintraege": res["eintraege"],
            "hinweis": ("Eintrag in der GGL-Whitelist gefunden." if res["gefunden"] else
                        "Kein Eintrag in der GGL-Whitelist gefunden (Stand Abruf) – keine deutsche "
                        "Erlaubnis bekannt. Keine juristische Bewertung; selbst pruefen."),
        }
    return daten


def _kern(d: Dict) -> str:
    """Vergleichsform ohne Zeitstempel: reine Abrufzeit-Aenderungen sind keine Aenderung."""
    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if k != "abgerufen"}
        if isinstance(x, list):
            return [strip(v) for v in x]
        return x
    return json.dumps(strip(d), ensure_ascii=False, sort_keys=True)


def schreibe(daten: Dict, pfad: Path) -> bool:
    """Atomar schreiben, nur bei inhaltlicher Aenderung. True = geschrieben."""
    if pfad.exists():
        try:
            if _kern(json.loads(pfad.read_text(encoding="utf-8"))) == _kern(daten):
                return False
        except (OSError, json.JSONDecodeError):
            pass
    pfad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pfad.with_suffix(pfad.suffix + ".tmp")
    tmp.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(pfad)
    return True


def _standard_pfad() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "anbieter.json"


def lauf(pfad: Path, seite: Optional[str] = None, dry_run: bool = False,
         min_eintraege: int = MIN_EINTRAEGE) -> int:
    """Kern des Jobs. Rueckgabe: 0 = ok (auch bei Ausfall: alte Daten bleiben)."""
    try:
        seite = seite if seite is not None else abrufen()
        eintraege = parse_whitelist(seite)
    except Exception as exc:  # noqa: BLE001 – Ausfall darf die vorhandene Datei nicht zerstoeren
        print(f"[warnung] Whitelist nicht abrufbar/parsebar: {type(exc).__name__}: {exc} – Datei bleibt unveraendert")
        return 0
    if len(eintraege) < min_eintraege:
        print(f"[warnung] Nur {len(eintraege)} Eintraege geparst (erwartet >= {min_eintraege}) – "
              "Seitenformat geaendert? Datei bleibt unveraendert")
        return 0
    alt = json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {}
    neu = aktualisiere(alt, eintraege)
    for key, p in neu["anbieter"].items():
        w = p.get("whitelist")
        if w:
            print(f"  {key:13} {'GEFUNDEN ' if w['gefunden'] else 'nicht gefunden'}"
                  f"{' – ' + ', '.join(e['betreiber'] for e in w['eintraege']) if w['gefunden'] else ''}")
    if dry_run:
        print(f"dry-run: {len(eintraege)} Whitelist-Eintraege geparst, nichts geschrieben")
        return 0
    print(("geschrieben: " if schreibe(neu, pfad) else "unveraendert (Kern gleich): ") + str(pfad))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Anbieter-Profile mit GGL-Whitelist abgleichen")
    ap.add_argument("--out", default=str(_standard_pfad()))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--html-file", help="lokale Kopie der Whitelist-Seite statt Abruf (Offline-Test)")
    a = ap.parse_args(argv)
    seite = Path(a.html_file).read_text(encoding="utf-8", errors="replace") if a.html_file else None
    return lauf(Path(a.out), seite=seite, dry_run=a.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
