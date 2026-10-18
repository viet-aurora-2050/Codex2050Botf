"""AGB-Scanner: liest FREIEN Bonus-Text und füttert damit die unveränderte Rechen-Engine.

    python -m analyzer.scan "100 % bis zu 200 € ... Umsatz 35-fach ... max. Einsatz 5 €" einzahlung=50

Was er tut
  * zerlegt den Text in Sätze und liest je Satz nur, was dort zum Thema passt
    (Umsatzfaktor, Bonus-%, Deckel, Zeitlimit, Max-Einsatz, Gewinn-Cap, Mindesteinzahlung, Freispiele),
  * nennt zu JEDEM Fund den Textbeleg, damit man ihn prüfen kann,
  * rechnet danach mit `analyzer.bonus.analysiere` – diese Engine bleibt unverändert.

Was er bewusst NICHT tut
  * nichts erfinden: Was nicht im Text steht, steht unter ANNAHMEN (mit Wert) – nie als Fund,
  * bei widersprüchlichen Zahlen konservativ wählen (höchster Umsatz, kürzeste Frist, niedrigstes Limit)
    und den Konflikt melden,
  * keine Rechtsberatung, keine Vorhersage. Ein Regex kann Formulierungen missverstehen – die Belege
    zeigen, woher jede Zahl kommt; im Zweifel den Originaltext lesen.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .bonus import BonusSzenario, Ergebnis, UmsatzBasis, analysiere, formatiere

MAX_ZEICHEN = 20_000          # Schutz vor Missbrauch/Speicherdruck (öffentlicher Bot, Web-API)
BELEG_LAENGE = 150

_ABK = re.compile(r"\b(max|min|ca|inkl|bzw|ggf|etc|mind)\.", re.I)
_SATZ = re.compile(r"(?<=[.!?;])\s+(?=[A-ZÄÖÜ0-9„\"(])|\n+")
# Zahlen sind auf 9 Stellen begrenzt und dürfen nicht mitten in einer Ziffernfolge starten: sonst würde
# eine 20.000-stellige Ziffernfolge die Suche quadratisch machen (ReDoS bei öffentlichem Bot/Web-API).
_GELD = re.compile(r"(?<![\d.,])(\d{1,3}(?:\.\d{3}){1,3}|\d{1,9})(?:[,.](\d{1,2})(?!\d))?\s*(?:€|eur(?:o)?\b)", re.I)
_FAKTOR = re.compile(r"(?<![\d.,])(\d{1,9}(?:[.,]\d{1,3})?)\s*(?:x\b|[- ]?fach(?:e[rsmn]?)?\b|\s?mal\b)", re.I)
_PROZENT = re.compile(r"(?<![\d.,])(\d{1,9}(?:[.,]\d{1,3})?)\s*(?:%|prozent\b)", re.I)
_ZEIT = re.compile(r"(?<!\d)(\d{1,9})\s*(tage?n?|stunden?|std\b|wochen?)", re.I)
_ANZAHL_FS = re.compile(r"(?<!\d)(\d{1,9})\s*(?:gratis[- ]?)?freispiele?", re.I)


@dataclass
class Fund:
    feld: str
    wert: object
    beleg: str


@dataclass
class ScanErgebnis:
    szenario: BonusSzenario
    funde: List[Fund] = field(default_factory=list)
    annahmen: List[str] = field(default_factory=list)
    hinweise: List[str] = field(default_factory=list)
    mindesteinzahlung: Optional[float] = None
    freispiele_anzahl: Optional[int] = None


def _geld(m: "re.Match[str]") -> float:
    ganz = m.group(1).replace(".", "")
    return float(f"{ganz}.{m.group(2)}") if m.group(2) else float(ganz)


def _zahl(s: str) -> float:
    return float(s.replace(",", "."))


def _saetze(text: str) -> List[str]:
    text = _ABK.sub(lambda m: m.group(1), text)
    return [s.strip() for s in _SATZ.split(text) if s.strip()]


def _beleg(satz: str) -> str:
    satz = re.sub(r"\s+", " ", satz)
    return satz if len(satz) <= BELEG_LAENGE else satz[: BELEG_LAENGE - 1] + "…"


def _erstes_geld(satz: str) -> Optional[float]:
    m = _GELD.search(satz)
    return _geld(m) if m else None


def _geld_nach(satz: str, stichwort: str) -> Optional[float]:
    """Erster Geldbetrag NACH dem Stichwort (nicht der erste im Satz: „Bonus bis 100 €, Mindesteinzahlung 10 €“)."""
    k = re.search(stichwort, satz, re.I)
    if not k:
        return None
    m = _GELD.search(satz, k.end())
    return _geld(m) if m else None


def _zeit_in_tagen(satz: str) -> Optional[float]:
    m = _ZEIT.search(satz)
    if not m:
        return None
    n, einheit = int(m.group(1)), m.group(2).lower()
    if einheit.startswith(("stunde", "std")):
        return round(n / 24.0, 2)
    if einheit.startswith("woche"):
        return float(n * 7)
    return float(n)


def _waehle(kandidaten: List[Tuple[float, str]], konservativ: str, feld: str, hinweise: List[str],
            einheit: str = "") -> Optional[Tuple[float, str]]:
    """Mehrere Fundstellen -> konservativ wählen ('max' oder 'min') und Konflikt melden."""
    if not kandidaten:
        return None
    wahl = max(kandidaten, key=lambda k: k[0]) if konservativ == "max" else min(kandidaten, key=lambda k: k[0])
    werte = sorted({k[0] for k in kandidaten})
    if len(werte) > 1:
        wort = "höchster" if konservativ == "max" else "niedrigster"
        hinweise.append(f"{feld}: mehrere Werte im Text ({', '.join(f'{w:g}{einheit}' for w in werte)}) – "
                        f"{wort} Wert ({wahl[0]:g}{einheit}) für die Rechnung gewählt. Original prüfen.")
    return wahl


def scanne(text: str, einzahlung: Optional[float] = None, rtp: Optional[float] = None,
           einsatz: Optional[float] = None) -> ScanErgebnis:
    """Liest `text` in ein BonusSzenario. Wirft ValueError, wenn keine Rechnung möglich ist."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Kein Text übergeben.")
    if len(text) > MAX_ZEICHEN:
        raise ValueError(f"Text zu lang (max. {MAX_ZEICHEN} Zeichen).")

    saetze = _saetze(text)
    s = BonusSzenario()
    erg = ScanErgebnis(szenario=s)
    hinweise = erg.hinweise

    faktor_k: List[Tuple[float, str]] = []
    fs_faktor_k: List[Tuple[float, str]] = []
    zeit_k: List[Tuple[float, str]] = []
    maxeins_k: List[Tuple[float, str]] = []
    cap_k: List[Tuple[float, str]] = []
    mineinz_k: List[Tuple[float, str]] = []
    deckel_k: List[Tuple[float, str]] = []
    prozent_k: List[Tuple[float, str]] = []
    rtp_k: List[Tuple[float, str]] = []
    bonus_fix_k: List[Tuple[float, str]] = []
    basis_hinweise: List[Tuple[UmsatzBasis, str]] = []
    ohne_einzahlung = False

    for satz in saetze:
        low = satz.lower()
        b = _beleg(satz)
        ist_fs = "freispiel" in low

        if ist_fs:
            m = _ANZAHL_FS.search(satz)
            if m and erg.freispiele_anzahl is None:
                erg.freispiele_anzahl = int(m.group(1))
        if re.search(r"ohne\s+einzahlung|no[- ]deposit|ohne\s+eigene\s+einzahlung", low):
            ohne_einzahlung = True

        # Umsatzfaktor: nur in Sätzen, die vom Umsetzen handeln
        if re.search(r"umsatz|umsetz|wager|durchspiel|umgesetzt|durchgespielt", low):
            m = _FAKTOR.search(satz)
            if m:
                (fs_faktor_k if ist_fs else faktor_k).append((_zahl(m.group(1)), b))
            # Umsatzbasis
            if re.search(r"(bonus\w{0,10}\W{0,4}(und|\+|&|plus)\W{0,4}einzahlung"
                         r"|einzahlung\w{0,10}\W{0,4}(und|\+|&|plus)\W{0,4}bonus)", low):
                basis_hinweise.append((UmsatzBasis.EINZAHLUNG_PLUS_BONUS, b))
            elif re.search(r"(bonusbetrag|bonusgeld|bonus\s*(betrag|summe))", low) and "einzahlung" not in low:
                basis_hinweise.append((UmsatzBasis.BONUS, b))
            elif re.search(r"einzahlungsbetrag|einzahlung\b", low) and "bonus" not in low:
                basis_hinweise.append((UmsatzBasis.EINZAHLUNG, b))

        # Bonus-Prozent und Deckel
        if re.search(r"bonus", low) and not re.search(r"zähl|zaehl|beitrag|gewichtung|rtp|auszahlungsquote", low):
            m = _PROZENT.search(satz)
            if m:
                prozent_k.append((_zahl(m.group(1)), b))
                m2 = re.search(r"bis\s+(?:zu\s+)?(?:einem\s+betrag\s+von\s+)?" + _GELD.pattern, satz, re.I)
                if m2:
                    deckel_k.append((_geld(_GELD.search(satz[m2.start():])), b))
        # Fester Bonusbetrag ("10 € Bonus", "Bonus: 25 €")
        m = re.search(r"(?:^|\W)" + _GELD.pattern + r"\s*(?:gratis[- ]?)?(?:bonus|startguthaben|bonusguthaben)", satz, re.I)
        if m and "%" not in satz:
            bonus_fix_k.append((_geld(_GELD.search(satz[m.start():])), b))

        # Höchsteinsatz
        if re.search(r"einsatz|wetteinsatz|bet\b", low) and re.search(r"max|höchst|hoechst|obergrenze|nicht\s+(mehr|über|ueber)", low):
            g = _geld_nach(satz, r"einsatz|bet\b")
            if g is not None:
                maxeins_k.append((g, b))
        # Gewinn-/Auszahlungs-Cap
        if re.search(r"gewinn|auszahlung", low) and re.search(r"begrenz|limit|gedeckelt|höchstens|hoechstens|max|deckel", low) \
                and not re.search(r"einsatz", low):
            g = _geld_nach(satz, r"gewinn\w*|auszahlung\w*")
            if g is not None:
                cap_k.append((g, b))
        # Mindesteinzahlung
        if re.search(r"mindest\w*\s*einzahlung|einzahlung\w*\s*(ab|von\s+mindestens)|mindestens\s+[\d.,]+\s*(€|eur)\b[^.]{0,40}einzahl", low):
            g = _geld_nach(satz, r"mindest\w*\s*einzahlung|einzahlung\w*\s*(?:ab|von\s+mindestens)|mindestens")
            if g is not None:
                mineinz_k.append((g, b))
        # Zeitlimit
        if re.search(r"gültig|gueltig|innerhalb|verfäll|verfaell|frist|laufzeit|umsetz|umsatz|erfüll|erfuell|ablauf", low):
            t = _zeit_in_tagen(satz)
            if t is not None and t > 0 and not re.search(r"auszahlung\w*\s+(dauer|innerhalb)|bearbeit", low):
                zeit_k.append((t, b))
        # RTP, falls im Text genannt
        if re.search(r"\brtp\b|auszahlungsquote|return to player", low):
            m = _PROZENT.search(satz)
            if m:
                rtp_k.append((_zahl(m.group(1)), b))
        # Zählweise (nur Hinweis)
        m = re.search(r"(\w+)\s+zählen?\s+(?:nur\s+)?(?:zu\s+)?(\d+)\s*%", satz, re.I)
        if m and int(m.group(2)) < 100:
            hinweise.append(f"Umsatzbeitrag: „{_beleg(satz)}“ – diese Spiele bringen weniger Umsatz; die Rechnung "
                            f"nimmt 100 % Beitrag an (Slots).")

    # ---- Felder setzen ----------------------------------------------------------------
    def setze(feld: str, wert, beleg: str):
        erg.funde.append(Fund(feld, wert, beleg))

    w = _waehle(faktor_k, "max", "Umsatzfaktor", hinweise, "x")
    if w:
        s.umsatzfaktor = w[0]; setze("Umsatzfaktor", f"{w[0]:g}x", w[1])
    else:
        erg.annahmen.append(f"Umsatzfaktor nicht im Text gefunden – Annahme {s.umsatzfaktor:g}x (Engine-Standard).")
    w = _waehle(fs_faktor_k, "max", "Umsatzfaktor Freispiele", hinweise, "x")
    if w:
        s.freispiel_umsatzfaktor = w[0]; setze("Umsatzfaktor Freispiele", f"{w[0]:g}x", w[1])

    w = _waehle(prozent_k, "min", "Bonus-Prozentsatz", hinweise, " %")
    if w:
        s.bonus_prozent = w[0]; setze("Bonus", f"{w[0]:g} %", w[1])
    w = _waehle(deckel_k, "min", "Bonus-Deckel", hinweise, " €")
    if w:
        s.bonus_deckel = w[0]; setze("Bonus-Deckel", f"{w[0]:g} €", w[1])
    if s.bonus_prozent is None:
        w = _waehle(bonus_fix_k, "min", "Bonusbetrag", hinweise, " €")
        if w:
            s.bonus_betrag = w[0]; setze("Bonusbetrag", f"{w[0]:g} €", w[1])

    w = _waehle(zeit_k, "min", "Zeitlimit", hinweise, " Tage")
    if w:
        s.zeitlimit_tage = w[0]; setze("Zeitlimit", f"{w[0]:g} Tage", w[1])
    else:
        erg.annahmen.append("Kein Zeitlimit im Text gefunden – Machbarkeit wird nicht gegen eine Frist geprüft.")
    w = _waehle(maxeins_k, "min", "Maximaler Einsatz", hinweise, " €")
    if w:
        s.max_einsatz_pro_spin = w[0]; setze("Maximaler Einsatz mit Bonus", f"{w[0]:g} €", w[1])
    w = _waehle(cap_k, "min", "Gewinn-Cap", hinweise, " €")
    if w:
        s.max_gewinn = w[0]; setze("Maximaler Gewinn/Auszahlung", f"{w[0]:g} €", w[1])
    w = _waehle(mineinz_k, "max", "Mindesteinzahlung", hinweise, " €")
    if w:
        erg.mindesteinzahlung = w[0]; setze("Mindesteinzahlung", f"{w[0]:g} €", w[1])
    w = _waehle(rtp_k, "min", "RTP", hinweise, " %")
    if w:
        s.rtp = w[0] / 100.0 if w[0] > 1.5 else w[0]; setze("RTP", f"{w[0]:g} %", w[1])

    # Umsatzbasis: eindeutig -> setzen; unklar/widersprüchlich -> teuerste Variante (konservativ)
    arten = {a for a, _ in basis_hinweise}
    if len(arten) == 1:
        s.umsatz_basis = basis_hinweise[0][0]; setze("Umsatzbasis", s.umsatz_basis.value, basis_hinweise[0][1])
    elif len(arten) > 1:
        s.umsatz_basis = UmsatzBasis.EINZAHLUNG_PLUS_BONUS
        hinweise.append("Umsatzbasis: widersprüchliche Angaben im Text – es wird die TEUERSTE Variante "
                        "(Einzahlung + Bonus) gerechnet. Original prüfen.")
    else:
        s.umsatz_basis = UmsatzBasis.EINZAHLUNG_PLUS_BONUS
        erg.annahmen.append("Umsatzbasis nicht erkennbar – es wird die TEUERSTE Variante (Einzahlung + Bonus) gerechnet.")

    if s.bonus_prozent is None and s.bonus_betrag is None:
        raise ValueError("Weder Bonus-Prozentsatz noch fester Bonusbetrag im Text erkannt – "
                         "ohne Bonus gibt es nichts zu berechnen.")

    # ---- Einzahlung (Nutzerangabe > Text > Annahme) -------------------------------------
    if einzahlung is not None:
        s.einzahlung = float(einzahlung)
        erg.funde.append(Fund("Einzahlung", f"{einzahlung:g} €", "von dir angegeben"))
    elif s.bonus_prozent is not None:
        if erg.mindesteinzahlung:
            s.einzahlung = erg.mindesteinzahlung
            erg.annahmen.append(f"Einzahlung nicht angegeben – Annahme: die Mindesteinzahlung ({s.einzahlung:g} €). "
                                f"Mit einzahlung=… genauer rechnen.")
        else:
            raise ValueError("Bonus in % erkannt, aber weder Einzahlung noch Mindesteinzahlung bekannt – "
                             "bitte angeben, z. B. einzahlung=50.")
    elif ohne_einzahlung:
        s.einzahlung = 0.0
        erg.annahmen.append("Bonus „ohne Einzahlung“ erkannt – Einzahlung = 0 €.")
    else:
        s.einzahlung = erg.mindesteinzahlung or 0.0

    # ---- Nutzerangaben/Annahmen für den Rest ---------------------------------------------
    if rtp is not None:
        s.rtp = rtp / 100.0 if rtp > 1.5 else rtp
        erg.funde.append(Fund("RTP", f"{s.rtp * 100:g} %", "von dir angegeben"))
    elif not rtp_k:
        erg.annahmen.append(f"RTP steht nie in AGB – Annahme {s.rtp * 100:g} % (Engine-Standard); "
                            f"für das gespielte Slot-Spiel den veröffentlichten RTP einsetzen (rtp=…).")
    if einsatz is not None:
        s.durchschnittseinsatz = float(einsatz)
    elif s.max_einsatz_pro_spin is not None and s.durchschnittseinsatz > s.max_einsatz_pro_spin:
        s.durchschnittseinsatz = s.max_einsatz_pro_spin
        erg.annahmen.append(f"Durchschnittseinsatz auf das Einsatzlimit {s.max_einsatz_pro_spin:g} € gesetzt (Standard 1 € wäre darüber).")
    else:
        erg.annahmen.append(f"Durchschnittseinsatz {s.durchschnittseinsatz:g} € pro Spin angenommen (einsatz=… ändert das).")
    if erg.freispiele_anzahl:
        erg.annahmen.append(f"{erg.freispiele_anzahl} Freispiele erkannt – ihr Gewinn ist unbekannt und wird mit 0 € angesetzt "
                            f"(fs_gewinn=… in der Engine, falls bekannt).")

    # ---- Rote Flaggen (nur Hinweise, keine Wertung) ---------------------------------------
    gesamt = text.lower()
    if re.search(r"bonus\w*\s+(verfällt|verfaellt|wird\s+(gestrichen|entfernt|annulliert))", gesamt) and s.max_einsatz_pro_spin:
        hinweise.append("Ein Verstoß gegen das Einsatzlimit kann den Bonus (und Gewinne) kosten – Limit strikt einhalten.")
    if s.umsatzfaktor >= 40 and faktor_k:
        hinweise.append(f"Umsatzfaktor {s.umsatzfaktor:g}x ist hoch – bei Hausvorteil frisst der Umsatz den Bonus meist auf.")
    return erg


_OPT = re.compile(r"\b(einzahlung|rtp|einsatz)\s*=\s*([\d.,]+)", re.I)


def optionen_aus_text(text: str) -> Tuple[str, Dict[str, float]]:
    """Trennt `einzahlung=50 rtp=0.96 einsatz=1` vom AGB-Text. Rückgabe: (Text ohne Optionen, Optionen)."""
    opt: Dict[str, float] = {}
    for m in _OPT.finditer(text or ""):
        try:
            opt[m.group(1).lower()] = _zahl(m.group(2))
        except ValueError:
            pass
    return _OPT.sub(" ", text or "").strip(), opt


def sieht_nach_agb_aus(text: str) -> bool:
    """Grobe Erkennung für eingefügte Bonusbedingungen (Bot-Freitext): Bonus + Umsatzbezug, nicht winzig."""
    low = (text or "").lower()
    return (len(low) >= 40 and "bonus" in low
            and bool(re.search(r"umsatz|umsetz|durchspiel|wager|\d\s*x\b|-fach", low)))


def analysiere_text(text: str, **kwargs) -> Tuple[ScanErgebnis, Ergebnis]:
    """Scannen und mit der unveränderten Engine rechnen."""
    scan = scanne(text, **kwargs)
    return scan, analysiere(scan.szenario)


def formatiere_scan(scan: ScanErgebnis, ergebnis: Ergebnis) -> str:
    L: List[str] = ["📄 AGB-SCAN (offline, ohne KI)", "=" * 30, "", "GEFUNDEN (mit Textbeleg):"]
    if scan.funde:
        for f in scan.funde:
            L.append(f"  • {f.feld}: {f.wert}")
            if f.beleg and f.beleg != "von dir angegeben":
                L.append(f"      „{f.beleg}“")
    else:
        L.append("  (nichts Verwertbares gefunden)")
    if scan.annahmen:
        L += ["", "ANNAHMEN (stehen NICHT im Text):"] + [f"  • {a}" for a in scan.annahmen]
    if scan.hinweise:
        L += ["", "ACHTUNG:"] + [f"  ⚠ {h}" for h in scan.hinweise]
    L += ["", formatiere(ergebnis, scan.szenario), "",
          "Hinweis: Ein Text-Scanner kann Formulierungen missverstehen – prüfe die Belege am Original. Keine Rechtsberatung."]
    return "\n".join(L)


def _cli(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    text, opt = optionen_aus_text(" ".join(argv).strip())
    if text in ("-", ""):
        text = sys.stdin.read() if text == "-" or not sys.stdin.isatty() else ""
    if not text:
        print('Nutzung: python -m analyzer.scan "<AGB-Text>" [einzahlung=50] [rtp=0.96] [einsatz=1]\n'
              '         python -m analyzer.scan - < agb.txt')
        return 0
    try:
        scan, ergebnis = analysiere_text(text, **opt)
    except ValueError as exc:
        print(f"Fehler: {exc}")
        return 1
    print(formatiere_scan(scan, ergebnis))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
