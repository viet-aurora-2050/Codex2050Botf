"""Tests fuer den Melde-Assistenten (Mathematik + Beschwerde/Anzeige).

Kernzusicherungen: korrekte Mathematik; bei fehlender/unbekannter Lizenz wird
NUR ein Verdacht formuliert; bei gueltiger Lizenz KEIN Vorwurf unerlaubten
Angebots; die Schutzhinweise (falsche Anzeige strafbar, keine Rechtsberatung)
sind immer vorhanden.
"""

import unittest

from melde import Lizenz, MeldeSzenario, erstelle


class TestMelde(unittest.TestCase):
    def test_mathematik_korrekt(self):
        e = erstelle(MeldeSzenario(anbieter="X", einzahlung_gesamt=300,
                                   verlust=300, rtp=0.96))
        self.assertAlmostEqual(e.hausvorteil, 0.04, places=4)
        self.assertAlmostEqual(e.erwarteter_verlust_struktur, 12.0, places=2)  # 300*0.04

    def test_keine_lizenz_nur_verdacht(self):
        e = erstelle(MeldeSzenario(anbieter="X", lizenz=Lizenz.KEINE,
                                   einzahlung_gesamt=300))
        self.assertIn("§ 4", e.text)
        self.assertIn("Verdacht", e.text)
        self.assertIn("nicht als feststehende Behauptung", e.text)

    def test_gueltige_lizenz_kein_vorwurf(self):
        e = erstelle(MeldeSzenario(anbieter="X", lizenz=Lizenz.GUELTIG,
                                   einzahlung_gesamt=300))
        self.assertNotIn("unerlaubten Gluecksspielangebots", e.text)
        self.assertIn("Whitelist gelistet", e.text)

    def test_schutzhinweise_immer_da(self):
        for liz in (Lizenz.UNBEKANNT, Lizenz.KEINE, Lizenz.GUELTIG):
            e = erstelle(MeldeSzenario(anbieter="X", lizenz=liz, einzahlung_gesamt=100))
            self.assertIn("§ 164 StGB", e.text)           # falsche Anzeige strafbar
            self.assertIn("Keine Rechtsberatung", e.text)
            self.assertIn("wahrheitsgemaess", e.text)

    def test_wahrheitsversicherung_vorhanden(self):
        e = erstelle(MeldeSzenario(anbieter="X", einzahlung_gesamt=50))
        self.assertIn("nach bestem Wissen wahrheitsgemaess", e.text)


if __name__ == "__main__":
    unittest.main()
