"""Tests für docs/anbieter.json (Anbieter-Profile aus öffentlichen Quellen)."""

import json
import unittest
from pathlib import Path

PFAD = Path(__file__).resolve().parents[1] / "docs" / "anbieter.json"


class TestAnbieterProfile(unittest.TestCase):
    def setUp(self):
        self.d = json.loads(PFAD.read_text(encoding="utf-8"))

    def test_struktur_und_abrufdatum(self):
        self.assertIn("anbieter", self.d)
        self.assertRegex(self.d["abgerufen"], r"^\d{4}-\d{2}-\d{2}$")

    def test_jeder_anbieter_hat_quellen_mit_primaer_oder_betreiber(self):
        for key, p in self.d["anbieter"].items():
            arten = {q["art"] for q in p["quellen"]}
            self.assertTrue(arten & {"primaer", "betreiber"}, key)
            for q in p["quellen"]:
                self.assertTrue(q["url"].startswith("https://"), q)

    def test_jackpotpirat_profil(self):
        p = self.d["anbieter"]["jackpotpirat"]
        self.assertEqual(p["domain"], "jackpotpiraten.de")
        self.assertEqual(p["lizenz"]["erteilt"], "2022-04-27")
        self.assertFalse(p["limits"]["autoplay"])
        self.assertGreater(p["limits"]["min_sekunden_pro_spin_durchschnitt"], 0)

    def test_keine_erfundenen_rtp_werte(self):
        # Profile nennen keinen Betreiber-RTP, nur den Hinweis darauf.
        for p in self.d["anbieter"].values():
            self.assertNotIn("rtp", p)
            self.assertIn("rtp_hinweis", p)


if __name__ == "__main__":
    unittest.main()
