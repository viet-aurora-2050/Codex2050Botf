"""Tests fuer die Personal-Risiko-Analyse (oeffentliche Parameter, kein Server)."""

import unittest

from risiko import RisikoSzenario, Volatilitaet, analysiere


class TestRisiko(unittest.TestCase):
    def test_erwarteter_verlust_exakt(self):
        s = RisikoSzenario(budget=100, einsatz=1, spins=500, rtp=0.96)
        e = analysiere(s, runs=2000)
        self.assertAlmostEqual(e.erwarteter_verlust, 20.0, places=2)   # 500*1*0.04
        self.assertAlmostEqual(e.erwartetes_endkapital, 80.0, places=2)
        self.assertAlmostEqual(e.hausvorteil, 0.04, places=4)

    def test_p_im_plus_unter_50_prozent(self):
        s = RisikoSzenario(budget=100, einsatz=1, spins=500, rtp=0.96)
        e = analysiere(s, runs=4000)
        self.assertLess(e.p_im_plus, 0.5)   # negativer EV -> meist im Minus

    def test_risk_of_ruin_im_intervall(self):
        s = RisikoSzenario(budget=100, einsatz=1, spins=500, rtp=0.96)
        e = analysiere(s, runs=3000)
        self.assertGreaterEqual(e.risk_of_ruin, 0.0)
        self.assertLessEqual(e.risk_of_ruin, 1.0)

    def test_hoehere_volatilitaet_hoeheres_ruin(self):
        basis = dict(budget=40, einsatz=2, spins=400, rtp=0.95)
        niedrig = analysiere(RisikoSzenario(volatilitaet=Volatilitaet.NIEDRIG, **basis), runs=4000)
        hoch = analysiere(RisikoSzenario(volatilitaet=Volatilitaet.HOCH, **basis), runs=4000)
        self.assertGreater(hoch.risk_of_ruin, niedrig.risk_of_ruin)

    def test_deterministisch_bei_gleichem_seed(self):
        s = RisikoSzenario(budget=100, einsatz=1, spins=300, rtp=0.96)
        a = analysiere(s, runs=2000, seed=42)
        b = analysiere(s, runs=2000, seed=42)
        self.assertEqual(a.median_endkapital, b.median_endkapital)
        self.assertEqual(a.risk_of_ruin, b.risk_of_ruin)


if __name__ == "__main__":
    unittest.main()
