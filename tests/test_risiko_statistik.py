"""Wissenschaftliche Korrektheitstests der Risiko-Simulation (Statistik, Eingabegrenzen, Modell-Check)."""

import math
import random
import unittest

from risiko import RisikoSzenario, Volatilitaet
from risiko.analyse import MAX_ARBEIT, MAX_SPINS, MIN_SESSIONS, analysiere, formatiere, pruefe, simuliere_sessions
from risiko.statistik import Z95, mittelwert_intervall, wilson_intervall


class TestWilson(unittest.TestCase):
    def test_bekannte_werte(self):
        # Referenzwerte des Wilson-Intervalls (95 %).
        lo, hi = wilson_intervall(50, 100)
        self.assertAlmostEqual(lo, 0.4038, places=3)
        self.assertAlmostEqual(hi, 0.5962, places=3)
        lo, hi = wilson_intervall(0, 100)
        self.assertAlmostEqual(lo, 0.0, places=9)
        self.assertAlmostEqual(hi, 0.0370, places=3)
        lo, hi = wilson_intervall(100, 100)
        self.assertAlmostEqual(lo, 0.9630, places=3)
        self.assertAlmostEqual(hi, 1.0, places=9)

    def test_randfaelle(self):
        self.assertEqual(wilson_intervall(0, 0), (0.0, 1.0))
        with self.assertRaises(ValueError):
            wilson_intervall(5, 3)

    def test_ueberdeckung_ist_nahe_95_prozent(self):
        """Statistischer Test: in ~95 % der wiederholten Experimente liegt das wahre p im Intervall."""
        rng = random.Random(7)
        p, n, wiederholungen, treffer = 0.12, 300, 2000, 0
        for _ in range(wiederholungen):
            x = sum(rng.random() < p for _ in range(n))
            lo, hi = wilson_intervall(x, n)
            treffer += lo <= p <= hi
        quote = treffer / wiederholungen
        self.assertGreater(quote, 0.93)
        self.assertLess(quote, 0.97)

    def test_mittelwert_intervall(self):
        m, lo, hi = mittelwert_intervall([1, 2, 3, 4, 5])
        self.assertEqual(m, 3)
        self.assertAlmostEqual(hi - m, Z95 * math.sqrt(2.5 / 5), places=6)
        self.assertEqual(mittelwert_intervall([]), (0.0, 0.0, 0.0))
        self.assertEqual(mittelwert_intervall([7.0]), (7.0, 7.0, 7.0))


class TestSimulationKorrekt(unittest.TestCase):
    def test_wald_identitaet_optional_stopping(self):
        """Martingal-Eigenschaft: E[Endkapital] = Budget - Hausvorteil * Einsatz * E[gespielte Spins].

        Gilt trotz Pleite-Abbruch (beschraenkte Stoppzeit). Prueft den Simulator selbst: eine falsche
        Auszahlungsverteilung, ein falscher RTP oder ein Stoppfehler wuerde die Identitaet brechen.
        """
        for vola in Volatilitaet:
            s = RisikoSzenario(budget=60, einsatz=1, spins=300, rtp=0.95, volatilitaet=vola)
            end, gesp, _ = simuliere_sessions(s, runs=12000, seed=11)
            n = len(end)
            he = 1 - s.rtp
            rest = [(e - s.budget) + he * s.einsatz * g for e, g in zip(end, gesp, strict=True)]   # Erwartung 0
            m = sum(rest) / n
            sd = math.sqrt(sum((r - m) ** 2 for r in rest) / (n - 1))
            self.assertLess(abs(m), 4 * sd / math.sqrt(n), f"Wald-Identitaet verletzt bei {vola.value}")

    def test_volle_session_ohne_pleite_hat_exakten_erwartungswert(self):
        s = RisikoSzenario(budget=1_000_000, einsatz=1, spins=200, rtp=0.96, volatilitaet=Volatilitaet.NIEDRIG)
        end, gesp, ruin = simuliere_sessions(s, runs=6000, seed=3)
        self.assertEqual(ruin, 0)
        self.assertTrue(all(g == 200 for g in gesp))
        m, lo, hi = mittelwert_intervall(end)
        theorie = s.budget - 200 * 0.04
        self.assertTrue(lo <= theorie <= hi, f"{theorie} nicht in [{lo}, {hi}]")

    def test_reproduzierbar(self):
        s = RisikoSzenario(budget=100, einsatz=1, spins=200, rtp=0.96)
        self.assertEqual(simuliere_sessions(s, 500, seed=5), simuliere_sessions(s, 500, seed=5))

    def test_ergebnis_enthaelt_intervalle_und_theorie_vs_simulation(self):
        s = RisikoSzenario(budget=100, einsatz=1, spins=500, rtp=0.96)
        e = analysiere(s, runs=3000)
        self.assertLessEqual(e.ki_risk_of_ruin[0], e.risk_of_ruin)
        self.assertGreaterEqual(e.ki_risk_of_ruin[1], e.risk_of_ruin)
        self.assertLessEqual(e.ki_p_im_plus[0], e.p_im_plus)
        # Bei Pleite-Abbruch werden weniger Spins gespielt -> simulierter Mittelwert >= Theorie (ca.).
        self.assertLess(e.mittel_gespielte_spins, 500)
        self.assertGreater(e.mittel_endkapital_sim, e.erwartetes_endkapital - 1)
        text = formatiere(e, s)
        for erwartet in ("95%-KI", "Modell & Grenzen", "KEINE Spin-Vorhersage", "theoretisch"):
            self.assertIn(erwartet, text)


class TestEingabeschutz(unittest.TestCase):
    def _s(self, **kw):
        basis = dict(budget=100, einsatz=1, spins=500, rtp=0.96)
        basis.update(kw)
        return RisikoSzenario(**basis)

    def test_unsinnige_eingaben_werden_abgelehnt(self):
        for kw in ({"spins": 0}, {"spins": MAX_SPINS + 1}, {"spins": 10**9}, {"budget": 0}, {"budget": -5},
                   {"budget": float("nan")}, {"budget": float("inf")}, {"einsatz": 0}, {"einsatz": float("nan")},
                   {"rtp": 0.2}, {"rtp": 1.5}, {"rtp": float("nan")}):
            with self.assertRaises(ValueError, msg=str(kw)):
                pruefe(self._s(**kw))

    def test_gueltige_grenzwerte_sind_ok(self):
        pruefe(self._s(spins=MAX_SPINS, rtp=1.0, budget=1e9))

    def test_arbeitsgrenze_reduziert_sessions(self):
        import risiko.analyse as modul
        alt = modul.MAX_ARBEIT
        modul.MAX_ARBEIT = 2_000_000                              # klein halten, damit der Test schnell bleibt
        try:
            e = analysiere(self._s(spins=2000, budget=1e9), runs=20000)   # 2e6 // 2000 = 1000 Sessions
        finally:
            modul.MAX_ARBEIT = alt
        self.assertEqual(e.runs, 1000)
        self.assertEqual(e.runs_angefragt, 20000)
        self.assertIn("reduziert", " ".join(e.schritte))

    def test_untergrenze_der_sessions(self):
        e = analysiere(self._s(spins=MAX_SPINS, budget=10, einsatz=5), runs=20000)   # Pleite in wenigen Spins
        self.assertEqual(e.runs, max(MIN_SESSIONS, MAX_ARBEIT // MAX_SPINS))
        self.assertGreaterEqual(e.runs, MIN_SESSIONS)


if __name__ == "__main__":
    unittest.main()
