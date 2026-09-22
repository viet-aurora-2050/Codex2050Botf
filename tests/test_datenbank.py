"""Tests für den öffentlichen Spiele-Katalog v3 (datenbank)."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from datenbank import baue, finde_alternativen, normalisiere, sammle, schreibe
from datenbank.sources import SEED_GAMES, _dedupe_key, _to_rtp, http_json_source


class TestRTP(unittest.TestCase):
    def test_prozent_zahl(self):
        self.assertAlmostEqual(_to_rtp("96.5"), 0.965)

    def test_prozent_mit_zeichen(self):
        self.assertAlmostEqual(_to_rtp("96,5%"), 0.965)

    def test_bruch(self):
        self.assertAlmostEqual(_to_rtp(0.965), 0.965)

    def test_unplausibel_und_muell(self):
        self.assertIsNone(_to_rtp("abc"))
        self.assertIsNone(_to_rtp(0.30))   # zu niedrig für Slot-RTP
        self.assertIsNone(_to_rtp(140))    # 1.40 unplausibel


class TestNormalisierung(unittest.TestCase):
    def test_alias_felder(self):
        g = normalisiere({"title": "X", "provider": "Y", "return": "95%",
                          "volatility": "high", "maxwin": 1000, "min_bet": 0.1}, "q")
        self.assertEqual((g["name"], g["anbieter"]), ("X", "Y"))
        self.assertAlmostEqual(g["rtp"], 0.95)
        self.assertEqual(g["vola"], "hoch")
        self.assertEqual(g["max"], 1000)
        self.assertEqual(g["minb"], 0.1)
        self.assertEqual(g["source_type"], "public-feed")
        self.assertEqual(g["status"], "online")
        self.assertIn("last_seen", g)

    def test_vola_englisch_wird_deutsch(self):
        self.assertEqual(normalisiere({"name": "X", "provider": "Y", "variance": "medium"}, "q")["vola"], "mittel")

    def test_unbekannte_vola_default(self):
        self.assertEqual(normalisiere({"name": "X", "provider": "Y", "vola": "extrem"}, "q")["vola"], "mittel")

    def test_fehlende_pflichtfelder(self):
        self.assertIsNone(normalisiere({"name": "", "provider": "Y", "rtp": 0.96}, "q"))
        self.assertIsNone(normalisiere({"name": "X", "rtp": 0.96}, "q"))

    def test_rtp_darf_fehlen_ohne_erfinden(self):
        g = normalisiere({"name": "X", "provider": "Y"}, "q")
        self.assertIsNotNone(g)
        self.assertIsNone(g["rtp"])

    def test_provenance_und_recent_win(self):
        g = normalisiere({"name": "X", "provider": "Y", "game_id": "abc-1",
                          "variant": "94%", "source_url": "https://ex/x",
                          "reported_recent_win": "12.000 €", "timestamp": "2026-09-01"}, "feedX")
        self.assertEqual(g["game_id"], "abc-1")
        self.assertEqual(g["variant"], "94%")
        self.assertEqual(g["source_url"], "https://ex/x")
        self.assertEqual(g["reported_recent_win"], "12.000 €")
        self.assertIn("keine Vorhersage", g["reported_recent_win_note"])
        self.assertEqual(g["quelle"], "feedX")


class TestDedup(unittest.TestCase):
    def test_gleiches_spiel_wird_zusammengefuehrt(self):
        a = normalisiere({"name": "Book of X", "provider": "Prov"}, "q")
        b = normalisiere({"name": "book of x", "provider": "prov"}, "q")
        self.assertEqual(_dedupe_key(a), _dedupe_key(b))

    def test_verschiedene_rtp_varianten_bleiben_getrennt(self):
        a = normalisiere({"name": "Book of X", "provider": "Prov", "variant": "94%"}, "q")
        b = normalisiere({"name": "Book of X", "provider": "Prov", "variant": "96%"}, "q")
        self.assertNotEqual(_dedupe_key(a), _dedupe_key(b))

    def test_game_id_hat_vorrang(self):
        a = normalisiere({"name": "A", "provider": "P", "game_id": "same"}, "q")
        b = normalisiere({"name": "B", "provider": "Q", "game_id": "same"}, "q")
        self.assertEqual(_dedupe_key(a), _dedupe_key(b))


class TestSammeln(unittest.TestCase):
    def test_basissatz_ohne_feeds(self):
        spiele, states = sammle(urls=[])
        self.assertEqual(len(spiele), len(SEED_GAMES))
        self.assertEqual(states, [])
        for g in spiele:
            self.assertTrue(g["name"] and g["anbieter"])
            self.assertEqual(g["source_type"], "seed")

    def test_sortiert_und_ohne_duplikate(self):
        spiele, _ = sammle(urls=[])
        keys = [(g["anbieter"].casefold(), g["name"].casefold()) for g in spiele]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(len(keys), len(set(keys)))

    def test_quellen_ausfall_zerstoert_katalog_nicht(self):
        # Nicht auflösbare URL -> offline; Basissatz bleibt vollständig.
        spiele, states = sammle(urls=["https://invalid.invalid/none.json"], timeout=2)
        self.assertEqual(len(spiele), len(SEED_GAMES))
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0]["status"], "offline")
        self.assertIn("error", states[0])
        self.assertEqual(states[0]["records_received"], 0)

    def test_http_meta_struktur(self):
        _, meta = http_json_source("https://invalid.invalid/none.json", timeout=2)
        for key in ("url", "status", "fetched_at", "records_received"):
            self.assertIn(key, meta)


class TestAlternativen(unittest.TestCase):
    def test_findet_aehnliche_ohne_selbst(self):
        spiele, _ = sammle(urls=[])
        ziel = spiele[0]
        alt = finde_alternativen(ziel, spiele, limit=3)
        self.assertEqual(len(alt), 3)
        namen = {a["name"] for a in alt}
        self.assertNotIn(ziel["name"], namen)
        for a in alt:
            self.assertIn("score", a)


class TestBauen(unittest.TestCase):
    def test_schema_und_rueckwaertskompatibilitaet(self):
        d = baue(urls=[])
        self.assertEqual(d["schema_version"], "3.0")
        # Frontend-Pflichtfelder müssen erhalten bleiben.
        for key in ("stand", "generiert", "quellen", "anzahl", "spiele"):
            self.assertIn(key, d)
        self.assertEqual(d["anzahl"], len(d["spiele"]))
        self.assertIn("source_status", d)
        self.assertIn("statistik", d)

    def test_hinweis_ehrlich(self):
        h = baue(urls=[])["_hinweis"].lower()
        self.assertIn("keine anbieter-api", h)
        self.assertIn("keine vorhersage", h)


class TestSchreiben(unittest.TestCase):
    def test_json_erzeugung_und_stabilitaet(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = str(Path(tmp) / "games.json")
            self.assertTrue(schreibe(baue(urls=[]), pfad))       # erstmalig
            self.assertFalse(schreibe(baue(urls=[]), pfad))      # Kern gleich -> kein Rewrite
            data = json.loads(Path(pfad).read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "3.0")

    def test_reiner_zeitstempel_kein_commit(self):
        # Zwei Builds unterscheiden sich nur in generiert/stand/source_status -> kein Rewrite.
        with tempfile.TemporaryDirectory() as tmp:
            pfad = str(Path(tmp) / "games.json")
            schreibe(baue(urls=[]), pfad)
            d2 = baue(urls=[])
            d2["generiert"] = "2099-01-01T00:00:00Z"
            self.assertFalse(schreibe(d2, pfad))


if __name__ == "__main__":
    unittest.main()
