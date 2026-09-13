"""Tests fuer das QUELLENPRINZIP-Modul."""

import unittest

from quellen import Ergebnis, Quellenkette, formatiere, pruefe_behauptung


class TestQuellen(unittest.TestCase):
    def test_marketing_erkannt(self):
        flags = pruefe_behauptung("Dieser Slot ist heiss und zahlt jetzt, bestes Spiel!")
        self.assertIn("heiss", flags)
        self.assertIn("zahlt jetzt", flags)
        self.assertIn("bestes spiel", flags)

    def test_keine_marketing_reizwoerter(self):
        self.assertEqual(pruefe_behauptung("RTP laut Spielinfo 96,0 %."), [])

    def test_unvollstaendige_kette_ist_offen(self):
        k = Quellenkette(behauptung="X", quelle="a")
        self.assertFalse(k.vollstaendig())
        self.assertIn("OFFEN", formatiere(k))

    def test_vollstaendige_kette(self):
        k = Quellenkette(behauptung="RTP 96%", quelle="Spielinfo", gegenquelle="Testportal",
                         primaerdokument="Herstellerdoku", mathe_check="1-0.96=4% Hausvorteil",
                         ergebnis=Ergebnis.BESTAETIGT)
        self.assertTrue(k.vollstaendig())
        self.assertIn("BESTAETIGT", formatiere(k))

    def test_formatierung_warnt_bei_marketing(self):
        text = formatiere(Quellenkette(behauptung="ist fällig und muss treffen"))
        self.assertIn("MARKETING erkannt", text)
        self.assertIn("KEIN mathematischer Beweis", text)


if __name__ == "__main__":
    unittest.main()
