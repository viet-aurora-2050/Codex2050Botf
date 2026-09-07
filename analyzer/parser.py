"""Parst kompakte Nutzereingaben (Telegram/CLI) in ein BonusSzenario.

Beispiel:
    einzahlung=100 bonus=100% faktor=30 basis=b rtp=0.96 zeit=3 einsatz=1
    fs_gewinn=50 maxgewinn=500 maxeinsatz=5

Akzeptiert Komma oder Punkt als Dezimaltrennzeichen und mehrere
Alias-Schluessel pro Feld.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .bonus import BonusSzenario, UmsatzBasis

# Alias -> kanonisches Feld
_ALIASE: Dict[str, str] = {
    "einzahlung": "einzahlung", "deposit": "einzahlung", "d": "einzahlung", "einz": "einzahlung",
    "bonus": "bonus", "b": "bonus",
    "faktor": "faktor", "umsatzfaktor": "faktor", "wager": "faktor", "x": "faktor", "wr": "faktor",
    "basis": "basis", "umsatzbasis": "basis",
    "rtp": "rtp", "auszahlungsquote": "rtp",
    "zeit": "zeit", "tage": "zeit", "zeitlimit": "zeit", "days": "zeit",
    "einsatz": "einsatz", "bet": "einsatz", "durchschnittseinsatz": "einsatz",
    "fs_gewinn": "fs_gewinn", "freispielgewinn": "fs_gewinn", "fsgewinn": "fs_gewinn", "fs": "fs_gewinn",
    "fs_faktor": "fs_faktor", "freispielfaktor": "fs_faktor",
    "maxgewinn": "maxgewinn", "max_gewinn": "maxgewinn", "cap": "maxgewinn", "maxwin": "maxgewinn",
    "maxeinsatz": "maxeinsatz", "max_einsatz": "maxeinsatz", "maxbet": "maxeinsatz",
    "deckel": "deckel", "bonusdeckel": "deckel", "bonuscap": "deckel",
    "spins": "spins", "spins_h": "spins", "spinsprostunde": "spins",
    "stunden": "stunden", "spielstunden": "stunden", "h": "stunden",
    "waehrung": "waehrung", "currency": "waehrung", "cur": "waehrung",
}

_BASIS_MAP = {
    "b": UmsatzBasis.BONUS, "bonus": UmsatzBasis.BONUS,
    "db": UmsatzBasis.EINZAHLUNG_PLUS_BONUS,
    "d+b": UmsatzBasis.EINZAHLUNG_PLUS_BONUS,
    "einzahlung_plus_bonus": UmsatzBasis.EINZAHLUNG_PLUS_BONUS,
    "deposit_bonus": UmsatzBasis.EINZAHLUNG_PLUS_BONUS,
    "d": UmsatzBasis.EINZAHLUNG, "einzahlung": UmsatzBasis.EINZAHLUNG,
}

_PAAR = re.compile(r"([a-zA-Z_]+)\s*[=:]\s*([^\s]+)")


def _zahl(text: str) -> float:
    """'1.234,50', '100%', '30x' -> float. Prozent/x werden als Zahl behandelt."""
    t = text.strip().lower().replace("%", "").replace("x", "").replace("€", "").replace("eur", "")
    t = t.strip()
    # 1.234,50 -> 1234.50 ; 1,5 -> 1.5
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    return float(t)


def parse(text: str) -> Tuple[BonusSzenario, List[str]]:
    """Gibt (Szenario, Hinweise) zurueck. Wirft ValueError bei leerer Eingabe."""
    paare = _PAAR.findall(text or "")
    if not paare:
        raise ValueError("Keine gueltigen Parameter gefunden (Format: schluessel=wert).")

    s = BonusSzenario()
    hinweise: List[str] = []
    bonus_ist_prozent = False

    for roh_key, roh_val in paare:
        key = _ALIASE.get(roh_key.lower())
        if key is None:
            hinweise.append(f"Unbekannter Parameter ignoriert: {roh_key}")
            continue
        try:
            if key == "basis":
                b = _BASIS_MAP.get(roh_val.lower())
                if b is None:
                    hinweise.append(f"Unbekannte Umsatzbasis '{roh_val}', nutze 'bonus'.")
                else:
                    s.umsatz_basis = b
                continue
            if key == "waehrung":
                s.waehrung = roh_val.upper()
                continue

            if key == "bonus":
                if "%" in roh_val:
                    s.bonus_prozent = _zahl(roh_val)
                    bonus_ist_prozent = True
                else:
                    s.bonus_betrag = _zahl(roh_val)
                continue

            val = _zahl(roh_val)
            if key == "einzahlung":
                s.einzahlung = val
            elif key == "faktor":
                s.umsatzfaktor = val
            elif key == "rtp":
                s.rtp = val / 100.0 if val > 1.5 else val  # 96 -> 0.96
            elif key == "zeit":
                s.zeitlimit_tage = val
            elif key == "einsatz":
                s.durchschnittseinsatz = val
            elif key == "fs_gewinn":
                s.freispiel_gewinn = val
            elif key == "fs_faktor":
                s.freispiel_umsatzfaktor = val
            elif key == "maxgewinn":
                s.max_gewinn = val
            elif key == "maxeinsatz":
                s.max_einsatz_pro_spin = val
            elif key == "deckel":
                s.bonus_deckel = val
            elif key == "spins":
                s.spins_pro_stunde = val
            elif key == "stunden":
                s.spielstunden_pro_tag = val
        except ValueError:
            hinweise.append(f"Wert fuer '{roh_key}' nicht lesbar: {roh_val}")

    if bonus_ist_prozent and s.einzahlung <= 0:
        hinweise.append("Bonus in % angegeben, aber keine Einzahlung – Bonus = 0.")

    return s, hinweise
