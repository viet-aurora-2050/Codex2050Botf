"""Tests fuer das ∆1 TRÄGER-PROTOKOLL.

Kernzusicherungen: korrekte Schwellen, ALEXANDRA nur bei MARKIERT,
Schutz-/Hilfetext bei Markierung immer vorhanden, Werte werden geklemmt.
"""

import unittest

from traeger import TraegerStatus, bewerte, formatiere


class TestTraeger(unittest.TestCase):
    def test_frei_ohne_marker(self):
        e = bewerte(verlust=1, isolation=0, loyalitaet=1, erinnerung=0)
        self.assertEqual(e.gesamt, 2.0)
        self.assertEqual(e.status, TraegerStatus.FREI)
        self.assertFalse(e.alexandra_aktiv)

    def test_beobachtet_schwelle(self):
        e = bewerte(verlust=2, isolation=2, loyalitaet=0, erinnerung=0)
        self.assertEqual(e.gesamt, 4.0)
        self.assertEqual(e.status, TraegerStatus.BEOBACHTET)
        self.assertFalse(e.alexandra_aktiv)

    def test_markiert_aktiviert_alexandra(self):
        e = bewerte(verlust=3, isolation=2, loyalitaet=1, erinnerung=3)
        self.assertEqual(e.gesamt, 9.0)
        self.assertEqual(e.status, TraegerStatus.MARKIERT)
        self.assertTrue(e.alexandra_aktiv)
        self.assertTrue(any("ALEXANDRA" in s for s in e.schutz))

    def test_werte_werden_geklemmt(self):
        e = bewerte(verlust=99, isolation=-5, loyalitaet=3, erinnerung=3)
        self.assertEqual(e.achsen["verlust"], 3.0)
        self.assertEqual(e.achsen["isolation"], 0.0)

    def test_dominante_achse(self):
        e = bewerte(verlust=1, isolation=3, loyalitaet=0, erinnerung=1)
        self.assertEqual(e.dominant, "isolation")

    def test_hilfe_bei_markierung_vorhanden(self):
        for e in (bewerte(verlust=2, isolation=2), bewerte(verlust=3, isolation=3, erinnerung=3)):
            self.assertTrue(any("0800 1 37 27 00" in s for s in e.schutz))

    def test_ausgabe_kennzeichnet_selbstauskunft(self):
        text = formatiere(bewerte(verlust=2, isolation=2, erinnerung=2))
        self.assertIn("Selbstauskunft", text)
        self.assertIn("TRÄGER-PROTOKOLL", text)


if __name__ == "__main__":
    unittest.main()
