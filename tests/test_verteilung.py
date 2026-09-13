"""Tests fuer die Auszahlungsverteilungs-Mathematik."""

import unittest

from verteilung import Verteilung, datenqualitaet, multiplikator_analyse, multiplikator_ziele


class TestVerteilung(unittest.TestCase):
    def setUp(self):
        # Einfache Beispielverteilung: 70% Verlust (0x), 20% 2x, 10% 5x
        # EV = 0*0.7 + 2*0.2 + 5*0.1 = 0.9  -> Hausvorteil 10%
        self.v = Verteilung([(0.0, 0.7), (2.0, 0.2), (5.0, 0.1)])

    def test_ev_und_hausvorteil(self):
        self.assertAlmostEqual(self.v.ev(), 0.9, places=6)
        self.assertAlmostEqual(self.v.hausvorteil(), 0.1, places=6)

    def test_p_ge(self):
        self.assertAlmostEqual(self.v.p_ge(2), 0.3, places=6)   # 2x oder 5x
        self.assertAlmostEqual(self.v.p_ge(5), 0.1, places=6)
        self.assertAlmostEqual(self.v.p_ge(6), 0.0, places=6)

    def test_gueltigkeit(self):
        self.assertTrue(self.v.ist_gueltig())
        self.assertFalse(Verteilung([]).ist_gueltig())

    def test_ziele_umrechnung(self):
        z = multiplikator_ziele(5, [1, 2, 10])
        self.assertEqual(z[2.0], 10.0)
        self.assertEqual(z[10.0], 50.0)

    def test_analyse_ohne_verteilung_gibt_kein_p(self):
        r = multiplikator_analyse(None, 5)
        self.assertIsNone(r["wahrscheinlichkeiten"])
        self.assertIn("unavailable", r["grund"].lower())

    def test_analyse_mit_verteilung_gibt_p(self):
        r = multiplikator_analyse(self.v, 10, [2, 5])
        self.assertAlmostEqual(r["wahrscheinlichkeiten"][2.0], 0.3, places=6)
        self.assertEqual(r["betraege"][2.0], 20.0)

    def test_datenqualitaet_stufen(self):
        self.assertEqual(datenqualitaet(True, False, True, True), "A")
        self.assertEqual(datenqualitaet(False, True, True, True), "B")
        self.assertEqual(datenqualitaet(False, False, True, True), "C")
        self.assertEqual(datenqualitaet(False, False, True, False), "D")
        self.assertEqual(datenqualitaet(False, False, False, False), "F")


if __name__ == "__main__":
    unittest.main()
