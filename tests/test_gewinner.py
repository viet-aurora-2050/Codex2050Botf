"""Tests fuer das GEWINNER-Modul (dokumentierte Advantage-Play-Faelle)."""

import unittest

from gewinner import FAELLE, formatiere


class TestGewinner(unittest.TestCase):
    def test_kernfaelle_vorhanden(self):
        namen = " ".join(f.name for f in FAELLE)
        for erwartet in ("Thorp", "MIT", "Garcia-Pelayo", "Jarecki", "Mandel", "Selbee", "Ivey"):
            self.assertIn(erwartet, namen)

    def test_jeder_fall_vollstaendig(self):
        for f in FAELLE:
            for feld in (f.name, f.zeit, f.spiel, f.methode, f.mathe, f.ergebnis, f.legal, f.quelle):
                self.assertTrue(feld and feld.strip(), f"leeres Feld bei {f.name}")

    def test_lehre_nennt_rng_grenze(self):
        text = formatiere()
        self.assertIn("Slot-Thorp", text)
        self.assertIn("unabhaengige Ziehungen", text)
        self.assertIn("Hausverbot", text)

    def test_ivey_ist_gegenbeispiel(self):
        ivey = next(f for f in FAELLE if "Ivey" in f.name)
        self.assertIn("zurueckgeben", ivey.ergebnis)


if __name__ == "__main__":
    unittest.main()
