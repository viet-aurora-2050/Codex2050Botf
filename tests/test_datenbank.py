"""Tests für die tägliche Spiele-Datenbank-Erzeugung (datenbank)."""

import json
import os
import tempfile
import unittest

from datenbank import baue, normalisiere, sammle, schreibe
from datenbank.sources import SEED_GAMES, _to_rtp


class TestNormalisierung(unittest.TestCase):
    def test_prozent_und_bruch(self):
        self.assertAlmostEqual(_to_rtp("96.5"), 0.965)
        self.assertAlmostEqual(_to_rtp("96,5%"), 0.965)
        self.assertAlmostEqual(_to_rtp(0.965), 0.965)
        self.assertIsNone(_to_rtp("abc"))

    def test_alias_felder(self):
        n = normalisiere({"title": "X", "provider": "Y", "return": "95%",
                          "volatility": "hoch", "maxwin": 1000}, quelle="q")
        self.assertEqual(n["name"], "X")
        self.assertEqual(n["anbieter"], "Y")
        self.assertAlmostEqual(n["rtp"], 0.95)
        self.assertEqual(n["vola"], "hoch")
        self.assertEqual(n["quelle"], "q")

    def test_verwirft_unplausibel(self):
        self.assertIsNone(normalisiere({"name": "X", "anbieter": "Y", "rtp": 0.30}, "q"))  # zu niedrig
        self.assertIsNone(normalisiere({"name": "", "anbieter": "Y", "rtp": 0.96}, "q"))   # kein Name
        self.assertIsNone(normalisiere({"name": "X", "anbieter": "Y"}, "q"))               # kein RTP

    def test_unbekannte_vola_wird_mittel(self):
        n = normalisiere({"name": "X", "anbieter": "Y", "rtp": 0.96, "vola": "extrem"}, "q")
        self.assertEqual(n["vola"], "mittel")


class TestSammeln(unittest.TestCase):
    def test_basissatz_ohne_feeds(self):
        spiele = sammle(urls=[])
        self.assertEqual(len(spiele), len(SEED_GAMES))
        for g in spiele:
            self.assertTrue(0.80 <= g["rtp"] <= 1.00)
            self.assertIn(g["vola"], {"niedrig", "mittel", "hoch"})
            self.assertTrue(g["name"] and g["anbieter"] and g["quelle"])

    def test_sortiert_nach_anbieter_dann_name(self):
        spiele = sammle(urls=[])
        keys = [(g["anbieter"].lower(), g["name"].lower()) for g in spiele]
        self.assertEqual(keys, sorted(keys))

    def test_keine_duplikate(self):
        spiele = sammle(urls=[])
        paare = [(g["name"].lower(), g["anbieter"].lower()) for g in spiele]
        self.assertEqual(len(paare), len(set(paare)))


class TestBauen(unittest.TestCase):
    def test_struktur(self):
        d = baue(urls=[])
        for key in ("_hinweis", "stand", "generiert", "quellen", "anzahl", "spiele"):
            self.assertIn(key, d)
        self.assertEqual(d["anzahl"], len(d["spiele"]))
        self.assertRegex(d["stand"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(d["generiert"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_hinweis_ehrlich(self):
        d = baue(urls=[])
        h = d["_hinweis"].lower()
        self.assertIn("keine anbieter-api", h)
        self.assertIn("keine vorhersage", h)


class TestSchreiben(unittest.TestCase):
    def test_schreibt_und_erkennt_unveraendert(self):
        d = baue(urls=[])
        with tempfile.TemporaryDirectory() as tmp:
            pfad = os.path.join(tmp, "games.json")
            self.assertTrue(schreibe(d, pfad))          # erstes Mal -> geschrieben
            self.assertFalse(schreibe(baue(urls=[]), pfad))  # gleicher Kern -> nicht erneut
            with open(pfad, encoding="utf-8") as f:
                wieder = json.load(f)
            self.assertEqual(wieder["anzahl"], d["anzahl"])


if __name__ == "__main__":
    unittest.main()
