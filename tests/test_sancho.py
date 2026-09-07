"""Tests fuer das ∆1/Sancho-Modul.

Kernzusicherung: Das Modul liefert IMMER Vorhersagewert 0 und einen
korrekten erwarteten Verlust – es gibt niemals einen 'Spielbefehl'.
"""

import unittest
from datetime import datetime

from sancho import erzeuge, formatiere, normalisiere_anbieter


class TestSancho(unittest.TestCase):
    def test_vorhersagewert_ist_immer_null(self):
        for name in ["tipico games", "betano", "n1 casino", "stargames", "irgendwas"]:
            e = erzeuge(anbieter=name)
            self.assertEqual(e.vorhersagewert, 0.0)

    def test_anbieter_normalisierung(self):
        self.assertEqual(normalisiere_anbieter("Tipico Games"), "tipico")
        self.assertEqual(normalisiere_anbieter("N1 Casino"), "n1")
        self.assertEqual(normalisiere_anbieter("Voellig unbekannt"), "generisch")

    def test_erwarteter_verlust_korrekt(self):
        e = erzeuge(anbieter="n1", einsatz=1.0, zeitpunkt=datetime(2050, 1, 1, 12, 0))
        # RTP 0.96 -> Hausvorteil 0.04 -> 100 * 1 * 0.04 = 4.0
        self.assertAlmostEqual(e.erwarteter_verlust_pro_100, 4.0, places=2)

    def test_rhythmus_deterministisch(self):
        t = datetime(2050, 6, 15, 9, 0)
        a = erzeuge(anbieter="betano", zeitpunkt=t)
        b = erzeuge(anbieter="betano", zeitpunkt=t)
        self.assertEqual([p.wert for p in a.rhythmus], [p.wert for p in b.rhythmus])
        self.assertEqual(len(a.rhythmus), 24)

    def test_ausgabe_enthaelt_kein_spielbefehl_aber_wahrheit(self):
        text = formatiere(erzeuge(anbieter="tipico"))
        self.assertIn("KEIN SPIELBEFEHL", text)
        self.assertIn("UNABHAENGIG", text)
        self.assertIn("bzga.de", text)


if __name__ == "__main__":
    unittest.main()
