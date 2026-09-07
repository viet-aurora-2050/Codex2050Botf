"""Casino-Bonus- und Umsatz-Analytiker – transparente Rechen-Engine.

Reines Python, keine externen Abhaengigkeiten. Jeder Rechenschritt ist
nachvollziehbar und wird im Ergebnis mitgeliefert, damit die Ausgabe
mathematisch pruefbar bleibt.

Alle Betraege in Euro (oder der jeweiligen Waehrung), Faktoren als Zahl
(30x = 30), RTP als Anteil (0.96 = 96 %).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class UmsatzBasis(str, Enum):
    """Worauf sich der Umsatzfaktor bezieht (in den AGB oft entscheidend)."""

    BONUS = "bonus"                          # nur Bonusbetrag  (B x Faktor)
    EINZAHLUNG_PLUS_BONUS = "einzahlung_plus_bonus"  # (D + B) x Faktor  -> teuerste Variante
    EINZAHLUNG = "einzahlung"                # nur Einzahlung   (D x Faktor)


class Empfehlung(str, Enum):
    SPIELEN = "spielen"          # Bedingungen realistisch, Erwartungswert vertretbar
    RISIKO = "risiko"            # grenzwertig – nur mit klarem Bewusstsein fuer den Verlust
    STORNIEREN = "stornieren"    # Bonus loeschen / stornieren und Echtgeld sichern


@dataclass
class BonusSzenario:
    """Eingabeparameter eines Bonus-Angebots."""

    einzahlung: float = 0.0
    # Bonus entweder direkt als Betrag ODER ueber Prozentsatz + Deckel.
    bonus_betrag: Optional[float] = None
    bonus_prozent: Optional[float] = None          # z. B. 100 (= 100 %)
    bonus_deckel: Optional[float] = None           # Maximaler Bonusbetrag

    umsatzfaktor: float = 30.0
    umsatz_basis: UmsatzBasis = UmsatzBasis.BONUS

    # Freispiele
    freispiel_gewinn: float = 0.0
    freispiel_umsatzfaktor: Optional[float] = None  # None -> gleich wie umsatzfaktor

    # Spiel-/Risikoparameter
    rtp: float = 0.96                    # Return to Player (Automat)
    max_gewinn: Optional[float] = None   # Maximale Auszahlung aus dem Bonus (Cap)
    max_einsatz_pro_spin: Optional[float] = None  # Erlaubter Maximaleinsatz im Bonus

    # Machbarkeit / Zeit
    zeitlimit_tage: Optional[float] = None
    durchschnittseinsatz: float = 1.0    # Einsatz pro Spin/Runde
    spins_pro_stunde: float = 500.0      # Realistisch fuer Slots: 400-800
    spielstunden_pro_tag: float = 3.0

    waehrung: str = "EUR"

    def bonus(self) -> float:
        """Effektiver Bonusbetrag inkl. prozentualer Berechnung und Deckel."""
        if self.bonus_betrag is not None:
            betrag = self.bonus_betrag
        elif self.bonus_prozent is not None:
            betrag = self.einzahlung * self.bonus_prozent / 100.0
        else:
            betrag = 0.0
        if self.bonus_deckel is not None:
            betrag = min(betrag, self.bonus_deckel)
        return round(betrag, 2)


@dataclass
class Ergebnis:
    """Vollstaendiges Analyseergebnis mit nachvollziehbaren Schritten."""

    bonus: float
    umsatzbasis_betrag: float
    mindestumsatz: float
    hausvorteil: float
    erwarteter_verlust: float
    brutto_bonuswert: float
    erwartungswert: float               # EV inkl. Cap-Deckelung
    benoetigte_spins: float
    benoetigte_tage: float
    zeit_machbar: Optional[bool]
    empfehlung: Empfehlung
    schritte: List[str] = field(default_factory=list)
    warnungen: List[str] = field(default_factory=list)


def _round(x: float, n: int = 2) -> float:
    return round(x + 0.0, n)


def analysiere(s: BonusSzenario) -> Ergebnis:
    """Fuehrt die komplette Bonus-/Umsatzanalyse transparent durch."""

    schritte: List[str] = []
    warnungen: List[str] = []

    # --- 1) Bonusbetrag -------------------------------------------------
    bonus = s.bonus()
    if s.bonus_prozent is not None and s.bonus_betrag is None:
        roh = s.einzahlung * s.bonus_prozent / 100.0
        schritte.append(
            f"Bonus = Einzahlung {s.einzahlung:.2f} {s.waehrung} x {s.bonus_prozent:.0f}% "
            f"= {roh:.2f} {s.waehrung}"
            + (f", gedeckelt auf {s.bonus_deckel:.2f} {s.waehrung}"
               if s.bonus_deckel is not None and roh > s.bonus_deckel else "")
        )
    else:
        schritte.append(f"Bonusbetrag = {bonus:.2f} {s.waehrung}")

    # --- 2) Umsatzbasis -------------------------------------------------
    if s.umsatz_basis == UmsatzBasis.BONUS:
        basis = bonus
        schritte.append(f"Umsatzbasis = nur Bonus = {basis:.2f} {s.waehrung}")
    elif s.umsatz_basis == UmsatzBasis.EINZAHLUNG_PLUS_BONUS:
        basis = s.einzahlung + bonus
        schritte.append(
            f"Umsatzbasis = Einzahlung + Bonus = {s.einzahlung:.2f} + {bonus:.2f} "
            f"= {basis:.2f} {s.waehrung}  (teuerste Variante!)"
        )
        warnungen.append(
            "Umsatz auf 'Einzahlung + Bonus' (D+B) verdoppelt faktisch die "
            "Durchspielsumme gegenueber 'nur Bonus'. Genau pruefen."
        )
    else:  # EINZAHLUNG
        basis = s.einzahlung
        schritte.append(f"Umsatzbasis = nur Einzahlung = {basis:.2f} {s.waehrung}")

    # --- 3) Mindestumsatz ----------------------------------------------
    umsatz_haupt = basis * s.umsatzfaktor
    schritte.append(
        f"Umsatz (Haupt) = {basis:.2f} x {s.umsatzfaktor:.0f} = {umsatz_haupt:.2f} {s.waehrung}"
    )

    fs_faktor = s.freispiel_umsatzfaktor if s.freispiel_umsatzfaktor is not None else s.umsatzfaktor
    umsatz_fs = s.freispiel_gewinn * fs_faktor
    if s.freispiel_gewinn > 0:
        schritte.append(
            f"Umsatz (Freispielgewinn) = {s.freispiel_gewinn:.2f} x {fs_faktor:.0f} "
            f"= {umsatz_fs:.2f} {s.waehrung}"
        )

    mindestumsatz = umsatz_haupt + umsatz_fs
    schritte.append(
        f"Mindestumsatz gesamt = {umsatz_haupt:.2f} + {umsatz_fs:.2f} "
        f"= {mindestumsatz:.2f} {s.waehrung}"
    )

    # --- 4) Hausvorteil & erwarteter Verlust ---------------------------
    hausvorteil = 1.0 - s.rtp
    erwarteter_verlust = mindestumsatz * hausvorteil
    schritte.append(
        f"Hausvorteil = 1 - RTP = 1 - {s.rtp:.4f} = {hausvorteil*100:.2f}%"
    )
    schritte.append(
        f"Erwarteter (theoretischer) Verlust ueber den Umsatz = "
        f"{mindestumsatz:.2f} x {hausvorteil*100:.2f}% = {erwarteter_verlust:.2f} {s.waehrung}"
    )

    # --- 5) Erwartungswert des Bonus -----------------------------------
    brutto = bonus + s.freispiel_gewinn
    ev_roh = brutto - erwarteter_verlust
    schritte.append(
        f"Brutto-Bonuswert = Bonus + Freispielgewinn = {bonus:.2f} + {s.freispiel_gewinn:.2f} "
        f"= {brutto:.2f} {s.waehrung}"
    )
    schritte.append(
        f"Erwartungswert (EV) = Brutto-Bonuswert - erwarteter Verlust = "
        f"{brutto:.2f} - {erwarteter_verlust:.2f} = {ev_roh:.2f} {s.waehrung}"
    )

    ev = ev_roh
    if s.max_gewinn is not None and brutto > s.max_gewinn:
        gekappt = s.max_gewinn - erwarteter_verlust
        schritte.append(
            f"Gewinn-Cap greift: max. Auszahlung {s.max_gewinn:.2f} {s.waehrung} "
            f"< Brutto-Bonuswert {brutto:.2f} -> gekappter EV = {gekappt:.2f} {s.waehrung}"
        )
        warnungen.append(
            f"Maximalgewinn ist auf {s.max_gewinn:.2f} {s.waehrung} gedeckelt – "
            f"darueber hinausgehende Gewinne verfallen."
        )
        ev = min(ev, gekappt)

    # --- 6) Machbarkeit / Zeit -----------------------------------------
    benoetigte_spins = mindestumsatz / s.durchschnittseinsatz if s.durchschnittseinsatz > 0 else float("inf")
    spins_pro_tag = s.spins_pro_stunde * s.spielstunden_pro_tag
    benoetigte_tage = (benoetigte_spins / spins_pro_tag) if spins_pro_tag > 0 else float("inf")
    schritte.append(
        f"Benoetigte Spins = Mindestumsatz / Einsatz = {mindestumsatz:.2f} / "
        f"{s.durchschnittseinsatz:.2f} = {benoetigte_spins:.0f} Spins"
    )
    schritte.append(
        f"Spieltempo = {s.spins_pro_stunde:.0f} Spins/h x {s.spielstunden_pro_tag:.1f} h/Tag "
        f"= {spins_pro_tag:.0f} Spins/Tag -> ca. {benoetigte_tage:.1f} Tage reine Spielzeit"
    )

    zeit_machbar: Optional[bool] = None
    if s.zeitlimit_tage is not None:
        zeit_machbar = benoetigte_tage <= s.zeitlimit_tage
        schritte.append(
            f"Zeitlimit = {s.zeitlimit_tage:.1f} Tage -> "
            + ("machbar" if zeit_machbar else "NICHT realistisch machbar")
        )
        if not zeit_machbar:
            warnungen.append(
                f"Der Umsatz erfordert ca. {benoetigte_tage:.1f} Tage reine Spielzeit, "
                f"das Zeitlimit betraegt nur {s.zeitlimit_tage:.1f} Tage."
            )

    # --- 7) Zusatzwarnungen --------------------------------------------
    if s.max_einsatz_pro_spin is not None and s.durchschnittseinsatz > s.max_einsatz_pro_spin:
        warnungen.append(
            f"Geplanter Einsatz {s.durchschnittseinsatz:.2f} {s.waehrung} liegt ueber dem "
            f"erlaubten Maximaleinsatz {s.max_einsatz_pro_spin:.2f} {s.waehrung} – "
            f"Verstoss kann zur Bonus-/Gewinnstreichung fuehren."
        )
    if s.rtp < 0.94:
        warnungen.append(
            f"Niedriger RTP ({s.rtp*100:.1f}%) – der Hausvorteil frisst den Bonus "
            f"ueberdurchschnittlich schnell auf."
        )

    # --- 8) Empfehlung --------------------------------------------------
    empfehlung = _empfehlung(ev, brutto, zeit_machbar)
    if empfehlung == Empfehlung.STORNIEREN:
        schritte.append(
            "Empfehlung: Bonus stornieren/loeschen und Echtgeld sichern – "
            "der erwartete Verlust bzw. das Zeitlimit macht das Erfuellen unwirtschaftlich."
        )
    elif empfehlung == Empfehlung.RISIKO:
        schritte.append(
            "Empfehlung: grenzwertig – nur mit klarem Bewusstsein fuer den moeglichen Verlust."
        )
    else:
        schritte.append("Empfehlung: Bedingungen sind vertretbar erfuellbar.")

    return Ergebnis(
        bonus=_round(bonus),
        umsatzbasis_betrag=_round(basis),
        mindestumsatz=_round(mindestumsatz),
        hausvorteil=_round(hausvorteil, 4),
        erwarteter_verlust=_round(erwarteter_verlust),
        brutto_bonuswert=_round(brutto),
        erwartungswert=_round(ev),
        benoetigte_spins=_round(benoetigte_spins, 0),
        benoetigte_tage=_round(benoetigte_tage, 1),
        zeit_machbar=zeit_machbar,
        empfehlung=empfehlung,
        schritte=schritte,
        warnungen=warnungen,
    )


def _empfehlung(ev: float, brutto: float, zeit_machbar: Optional[bool]) -> Empfehlung:
    """Ableitung im Sinne des Spielerschutzes und der Kapitalerhaltung."""
    if zeit_machbar is False:
        return Empfehlung.STORNIEREN
    # Negativer Erwartungswert: erfuellen kostet im Schnitt Geld.
    if ev <= 0:
        return Empfehlung.STORNIEREN
    # Kleiner positiver EV relativ zum Einsatz -> grenzwertig.
    if brutto > 0 and ev < 0.15 * brutto:
        return Empfehlung.RISIKO
    return Empfehlung.SPIELEN


# --------------------------------------------------------------------------
# Formatierung
# --------------------------------------------------------------------------

_EMOJI = {
    Empfehlung.SPIELEN: "✅",      # ✅
    Empfehlung.RISIKO: "⚠️",  # ⚠️
    Empfehlung.STORNIEREN: "\U0001f6d1",  # 🛑
}

_TEXT = {
    Empfehlung.SPIELEN: "SPIELEN – Bedingungen realistisch erfuellbar",
    Empfehlung.RISIKO: "RISIKO – grenzwertig, bewusst entscheiden",
    Empfehlung.STORNIEREN: "STORNIEREN – Bonus loeschen, Echtgeld sichern",
}


def formatiere(e: Ergebnis, s: BonusSzenario) -> str:
    """Erzeugt einen menschenlesbaren Analyse-Report (z. B. fuer Telegram/CLI)."""
    w = s.waehrung
    lines: List[str] = []
    lines.append("\U0001f4ca CASINO-BONUS-ANALYSE")
    lines.append("=" * 34)
    lines.append("")
    lines.append("Rechenweg:")
    for i, schritt in enumerate(e.schritte, 1):
        lines.append(f"  {i}. {schritt}")
    lines.append("")
    lines.append("Kennzahlen:")
    lines.append(f"  • Bonusbetrag:        {e.bonus:.2f} {w}")
    lines.append(f"  • Mindestumsatz:      {e.mindestumsatz:.2f} {w}")
    lines.append(f"  • Hausvorteil:        {e.hausvorteil*100:.2f} %")
    lines.append(f"  • Erwarteter Verlust: {e.erwarteter_verlust:.2f} {w}")
    lines.append(f"  • Erwartungswert (EV):{e.erwartungswert:+.2f} {w}")
    lines.append(f"  • Benoetigte Spins:   {e.benoetigte_spins:.0f}")
    lines.append(f"  • Reine Spielzeit:    {e.benoetigte_tage:.1f} Tage")
    if e.zeit_machbar is not None:
        lines.append(f"  • Zeitlimit machbar:  {'ja' if e.zeit_machbar else 'NEIN'}")
    lines.append("")
    if e.warnungen:
        lines.append("⚠️ Warnungen:")
        for warn in e.warnungen:
            lines.append(f"  • {warn}")
        lines.append("")
    lines.append(f"{_EMOJI[e.empfehlung]} EMPFEHLUNG: {_TEXT[e.empfehlung]}")
    lines.append("")
    lines.append(
        "Hinweis: Werte sind theoretische Erwartungswerte (Langzeit). "
        "Kurzfristig sind Ergebnisse hoch volatil. Kein Rat zum Gluecksspiel – "
        "Spiele verantwortungsbewusst. Hilfe: www.bzga.de / Tel. 0800 1 37 27 00."
    )
    return "\n".join(lines)
