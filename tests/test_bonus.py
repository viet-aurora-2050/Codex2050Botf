"""Tests fuer die Bonus-Rechen-Engine – ohne externe Abhaengigkeiten (nur stdlib)."""

import unittest

from analyzer.bonus import BonusSzenario, Empfehlung, UmsatzBasis, analysiere
from analyzer.parser import parse


class TestMindestumsatz(unittest.TestCase):
    def test_bonus_prozent_und_deckel(self):
        s = BonusSzenario(einzahlung=200, bonus_prozent=100, bonus_deckel=150)
        self.assertEqual(s.bonus(), 150.0)

    def test_bonus_direkt(self):
        s = BonusSzenario(bonus_betrag=100)
        self.assertEqual(s.bonus(), 100.0)

    def test_umsatz_nur_bonus(self):
        s = BonusSzenario(bonus_betrag=100, umsatzfaktor=30, umsatz_basis=UmsatzBasis.BONUS)
        e = analysiere(s)
        self.assertEqual(e.mindestumsatz, 3000.0)

    def test_umsatz_einzahlung_plus_bonus(self):
        s = BonusSzenario(
            einzahlung=100, bonus_betrag=100, umsatzfaktor=30,
            umsatz_basis=UmsatzBasis.EINZAHLUNG_PLUS_BONUS,
        )
        e = analysiere(s)
        self.assertEqual(e.mindestumsatz, 6000.0)  # (100+100) * 30

    def test_freispielgewinn_addiert_umsatz(self):
        s = BonusSzenario(bonus_betrag=100, umsatzfaktor=30, freispiel_gewinn=50)
        e = analysiere(s)
        # 100*30 + 50*30 = 4500
        self.assertEqual(e.mindestumsatz, 4500.0)

    def test_freispiel_eigener_faktor(self):
        s = BonusSzenario(bonus_betrag=100, umsatzfaktor=30,
                          freispiel_gewinn=50, freispiel_umsatzfaktor=40)
        e = analysiere(s)
        self.assertEqual(e.mindestumsatz, 3000.0 + 2000.0)


class TestErwartungswertUndEmpfehlung(unittest.TestCase):
    def test_hausvorteil_und_verlust(self):
        s = BonusSzenario(bonus_betrag=100, umsatzfaktor=30, rtp=0.96)
        e = analysiere(s)
        self.assertAlmostEqual(e.hausvorteil, 0.04, places=4)
        self.assertAlmostEqual(e.erwarteter_verlust, 120.0, places=2)  # 3000 * 0.04

    def test_negativer_ev_fuehrt_zu_stornieren(self):
        s = BonusSzenario(bonus_betrag=100, umsatzfaktor=40, rtp=0.95)
        e = analysiere(s)
        # 100*40=4000; Verlust=200; EV=100-200=-100 -> stornieren
        self.assertLess(e.erwartungswert, 0)
        self.assertEqual(e.empfehlung, Empfehlung.STORNIEREN)

    def test_zeitlimit_unrealistisch_stornieren(self):
        s = BonusSzenario(
            einzahlung=100, bonus_betrag=100, umsatzfaktor=30,
            umsatz_basis=UmsatzBasis.EINZAHLUNG_PLUS_BONUS,
            rtp=0.96, zeitlimit_tage=3, durchschnittseinsatz=1,
            spins_pro_stunde=500, spielstunden_pro_tag=3,
        )
        e = analysiere(s)
        self.assertFalse(e.zeit_machbar)
        self.assertEqual(e.empfehlung, Empfehlung.STORNIEREN)

    def test_maxgewinn_cap_kappt_ev(self):
        s = BonusSzenario(bonus_betrag=1000, umsatzfaktor=1, rtp=0.99, max_gewinn=200)
        e = analysiere(s)
        # Brutto 1000 > Cap 200 -> EV auf Basis von 200 gekappt
        self.assertLessEqual(e.erwartungswert, 200.0)
        self.assertTrue(any("Cap" in w or "gedeckelt" in w for w in e.warnungen))


class TestParser(unittest.TestCase):
    def test_parse_prozent_und_basis(self):
        s, hinweise = parse("einzahlung=100 bonus=100% faktor=30 basis=db rtp=96 zeit=3 einsatz=1")
        self.assertEqual(s.einzahlung, 100.0)
        self.assertEqual(s.bonus_prozent, 100.0)
        self.assertEqual(s.umsatzfaktor, 30.0)
        self.assertEqual(s.umsatz_basis, UmsatzBasis.EINZAHLUNG_PLUS_BONUS)
        self.assertAlmostEqual(s.rtp, 0.96, places=4)  # 96 -> 0.96
        self.assertEqual(s.zeitlimit_tage, 3.0)

    def test_parse_komma_dezimal(self):
        s, _ = parse("bonus=50 einsatz=0,50 rtp=0,955")
        self.assertEqual(s.durchschnittseinsatz, 0.5)
        self.assertAlmostEqual(s.rtp, 0.955, places=4)

    def test_parse_leere_eingabe_wirft(self):
        with self.assertRaises(ValueError):
            parse("kein gueltiges format")

    def test_parse_unbekannter_parameter_hinweis(self):
        s, hinweise = parse("bonus=100 quatsch=5")
        self.assertTrue(any("quatsch" in h for h in hinweise))


if __name__ == "__main__":
    unittest.main()
