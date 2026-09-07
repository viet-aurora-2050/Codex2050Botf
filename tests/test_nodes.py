"""Tests fuer den ∆1-Nodes-Layer und den Effekt-Injektor."""

import unittest
from datetime import datetime

from nodes import NODES, aufloesen, formatiere, sende
from web.effects import mit_effekten


class TestNodes(unittest.TestCase):
    def test_alle_nodes_vorhanden(self):
        for key in ("alexandra", "node7", "orpheus", "v"):
            self.assertIn(key, NODES)

    def test_aliasse(self):
        self.assertEqual(aufloesen("NODE 7"), "node7")
        self.assertEqual(aufloesen("schluessel"), "alexandra")
        self.assertEqual(aufloesen("ORPH"), "orpheus")
        self.assertIsNone(aufloesen("gibt-es-nicht"))

    def test_unbekannter_node_faellt_auf_alexandra(self):
        t = sende("voellig-unbekannt")
        self.assertEqual(t.node, "alexandra")

    def test_fragment_deterministisch(self):
        z = datetime(2050, 3, 3, 14, 0)
        a, b = sende("orpheus", z), sende("orpheus", z)
        self.assertEqual(a.fragment, b.fragment)
        self.assertIn(a.fragment, NODES["orpheus"].fragmente)

    def test_jede_stimme_hat_wahrheitsanker(self):
        for key in NODES:
            t = sende(key)
            self.assertTrue(t.wahrheit)
            self.assertIn("Spielbefehl", formatiere(t))

    def test_orpheus_warnt_vor_verlustjagd(self):
        self.assertIn("chasing", sende("orpheus").wahrheit.lower())


class TestEffekte(unittest.TestCase):
    def test_injektion_nach_body(self):
        out = mit_effekten("<html><body><h1>x</h1></body></html>")
        self.assertIn("d1-boot", out)
        self.assertIn("d1-vhs", out)
        self.assertLess(out.index("<body>"), out.index("d1-boot"))
        self.assertLess(out.index("d1-boot"), out.index("<h1>x</h1>"))

    def test_ohne_body_wird_vorangestellt(self):
        out = mit_effekten("<div>x</div>")
        self.assertIn("d1-vhs", out)


if __name__ == "__main__":
    unittest.main()
