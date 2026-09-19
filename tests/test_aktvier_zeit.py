"""Tests fuer den rotierenden AKT-4-ZEIT-CODE (Ebene 4)."""

import unittest
from datetime import datetime, timezone

from aktvier.zeit import (
    IMPS,
    KEYS,
    caesar,
    make_rng,
    zyklus_id,
    zyklus_signal,
)


class TestPRNG(unittest.TestCase):
    def test_deterministisch(self):
        a = make_rng("DELTA1-2026091914")
        b = make_rng("DELTA1-2026091914")
        self.assertEqual([a() for _ in range(5)], [b() for _ in range(5)])

    def test_werte_in_einheitsintervall(self):
        r = make_rng("seed")
        for _ in range(100):
            v = r()
            self.assertGreaterEqual(v, 0.0)
            self.assertLess(v, 1.0)

    def test_js_paritaet_referenzvektoren(self):
        # Exakt gegen die JS-Fassung (node) verifiziert.
        r = make_rng("DELTA1-2026091914")
        got = [round(r(), 8) for _ in range(4)]
        self.assertEqual(got, [0.50891379, 0.82676109, 0.15398282, 0.94786285])


class TestCaesar(unittest.TestCase):
    def test_roundtrip(self):
        t = "Geh wenn du gehen musst."
        for n in range(1, 26):
            self.assertEqual(caesar(caesar(t, n), 26 - n), t)

    def test_nichtbuchstaben_bleiben(self):
        self.assertEqual(caesar("A1:B", 1), "B1:C")


class TestZyklus(unittest.TestCase):
    def test_zyklus_id_utc_stunde(self):
        dt = datetime(2026, 9, 19, 14, 59, tzinfo=timezone.utc)
        self.assertEqual(zyklus_id(dt), "2026091914")

    def test_roundtrip_alle_schichten(self):
        z = zyklus_signal(datetime(2026, 9, 19, 14, tzinfo=timezone.utc))
        self.assertEqual(z.entschluesselt["MORSE"], z.schluessel)
        self.assertEqual(z.entschluesselt["UHRZEITEN"], z.imperativ)
        self.assertEqual(
            z.entschluesselt["ROT_N"],
            "Erinnert zu werden heisst nicht gefangen zu bleiben. Geh wenn du gehen musst.",
        )

    def test_gleiche_stunde_gleiches_signal(self):
        a = zyklus_signal(datetime(2026, 9, 19, 14, 5, tzinfo=timezone.utc))
        b = zyklus_signal(datetime(2026, 9, 19, 14, 55, tzinfo=timezone.utc))
        self.assertEqual((a.schluessel, a.imperativ, a.rot_n), (b.schluessel, b.imperativ, b.rot_n))

    def test_andere_stunde_rotiert(self):
        # Ueber 24 Stunden muss sich mindestens ein Element aendern (kein Fixpunkt).
        base = datetime(2026, 9, 19, 0, tzinfo=timezone.utc)
        sig = [zyklus_signal(base.replace(hour=h)) for h in range(24)]
        keys = {s.schluessel for s in sig}
        imps = {s.imperativ for s in sig}
        rots = {s.rot_n for s in sig}
        self.assertGreater(len(keys) + len(imps) + len(rots), 3)

    def test_werte_aus_pools(self):
        z = zyklus_signal(datetime(2026, 3, 3, 3, tzinfo=timezone.utc))
        self.assertIn(z.schluessel, KEYS)
        self.assertIn(z.imperativ, IMPS)
        self.assertTrue(1 <= z.rot_n <= 25)
        self.assertTrue(100 <= z.node_sig <= 999)

    def test_imperative_sind_schuetzend(self):
        # Keine Spiel-/Weiter-Aufforderung im Imperativ-Pool.
        verboten = {"SPIEL", "SPIELE", "WEITER", "MEHR", "SETZE", "ALL", "ALLIN"}
        self.assertEqual(set(IMPS) & verboten, set())


if __name__ == "__main__":
    unittest.main()
