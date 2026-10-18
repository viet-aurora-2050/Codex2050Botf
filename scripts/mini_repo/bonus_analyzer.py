"""Kompatibilitäts-Wrapper: die alte Klasse `CasinoBonusAnalyzer` bleibt, rechnet aber mit dem echten Paket.

    python bonus_analyzer.py                  # Beispiel
    python -m analyzer.scan "<AGB-Text>" einzahlung=50      # vollständiger Scan + Rechnung
"""

import re

from analyzer.scan import analysiere_text, formatiere_scan


class CasinoBonusAnalyzer:
    def __init__(self, promo_text):
        self.promo_text = promo_text
        self.results = {}

    def extract_conditions(self):
        t = self.promo_text
        m = re.search(r"mindest\w*einzahlung\W{0,3}(\d{1,9}(?:[.,]\d{1,2})?)\s*(?:€|eur)", t, re.I)
        self.results["Mindesteinzahlung"] = float(m.group(1).replace(",", ".")) if m else "Nicht gefunden"
        m = re.search(r"umsatz\w*\W{0,3}(\d{1,4}(?:[.,]\d)?)\s*x\b", t, re.I)
        self.results["Umsatzbedingung"] = float(m.group(1).replace(",", ".")) if m else "Nicht gefunden"

    def print_tactical_report(self):
        print("\n--- [ KI CASINO SCANNER - BERICHT ] ---")
        for key, value in self.results.items():
            print(f"{key.ljust(20)}: {value}")
        print("Für die vollständige Rechnung: python -m analyzer.scan \"<AGB-Text>\"")
        print("---------------------------------------\n")

    def vollstaendig(self, **optionen):
        """Voller Scan (Bonus, Frist, Limits ...) + Rechnung der Engine. Wirft ValueError, wenn kein Bonus erkennbar."""
        scan, ergebnis = analysiere_text(self.promo_text, **optionen)
        return formatiere_scan(scan, ergebnis)


if __name__ == "__main__":
    beispiel = "Spiel: Book of Oasis, Mindesteinzahlung: 20 €, Umsatz: 40x"
    a = CasinoBonusAnalyzer(beispiel)
    a.extract_conditions()
    a.print_tactical_report()
