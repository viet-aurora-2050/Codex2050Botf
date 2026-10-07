"""Smoke- und Sicherheitstests für das FastAPI-Dashboard (web.dashboard).

Fängt u. a. kaputte Importe ab (z. B. nach dem Entfernen von Modulen) – früher lief das Dashboard
nach der TRÄGER/NODES-Entfernung gar nicht mehr an und kein Test hat es bemerkt.
"""

import importlib
import importlib.util
import os
import unittest
from unittest import mock

HAT_FASTAPI = (importlib.util.find_spec("fastapi") is not None
               and importlib.util.find_spec("httpx") is not None)


@unittest.skipUnless(HAT_FASTAPI, "fastapi/httpx nicht installiert")
class TestDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TELEGRAM_TOKEN", None)
            os.environ.pop("TELEGRAM_WEBHOOK_SECRET", None)
            import web.dashboard as dash
            cls.dash = importlib.reload(dash)
        cls.client = TestClient(cls.dash.app)

    def test_importiert_ohne_entfernte_module(self):
        import sys
        self.assertNotIn("traeger", sys.modules)
        self.assertNotIn("nodes", sys.modules)

    def test_hauptseiten_erreichbar(self):
        for pfad in ("/", "/sancho", "/signal"):
            r = self.client.get(pfad)
            self.assertEqual(r.status_code, 200, pfad)
            self.assertIn("text/html", r.headers["content-type"])

    def test_entfernte_seiten_sind_weg_und_nicht_verlinkt(self):
        for pfad in ("/traeger", "/nodes", "/api/traeger", "/api/node"):
            self.assertEqual(self.client.get(pfad).status_code, 404, pfad)
        for pfad in ("/", "/signal"):
            html = self.client.get(pfad).text
            self.assertNotIn('href="/traeger"', html)
            self.assertNotIn('href="/nodes"', html)

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.json()["status"], "ok")

    def test_sicherheits_header(self):
        h = self.client.get("/").headers
        self.assertEqual(h["x-content-type-options"], "nosniff")
        self.assertEqual(h["x-frame-options"], "DENY")
        self.assertEqual(h["referrer-policy"], "no-referrer")
        self.assertIn("frame-ancestors 'none'", h["content-security-policy"])

    def test_sancho_api_unveraendert_und_ehrlich(self):
        d = self.client.get("/api/sancho?anbieter=jackpotpirat&einsatz=2").json()
        self.assertEqual(d["vorhersagewert"], 0.0)
        self.assertEqual(d["anbieter"], "jackpotpirat")
        self.assertEqual(len(d["rhythmus"]), 24)

    def test_sancho_api_lehnt_unsinnige_werte_ab_statt_500(self):
        for q in ("einsatz=nan", "einsatz=-1", "einsatz=0", "einsatz=inf", "einsatz=abc"):
            self.assertEqual(self.client.get("/api/sancho?" + q).status_code, 422, q)

    def test_analyse_api_robust(self):
        ok = self.client.post("/api/analyse", json={"input": "einzahlung=100 bonus=100% faktor=30 rtp=0.96 zeit=3 einsatz=1"})
        self.assertEqual(ok.status_code, 200)
        self.assertIn("report", ok.json())
        self.assertEqual(self.client.post("/api/analyse", content=b"{kaputt", headers={"content-type": "application/json"}).status_code, 400)
        self.assertEqual(self.client.post("/api/analyse", json=[1, 2]).status_code, 400)
        self.assertEqual(self.client.post("/api/analyse", json={"input": 5}).status_code, 400)
        self.assertEqual(self.client.post("/api/analyse", json={"input": "x" * 6000}).status_code, 413)

    def test_webhook_ohne_aktiven_bot_503(self):
        self.assertEqual(self.client.post("/telegram/webhook", json={}).status_code, 503)


@unittest.skipUnless(HAT_FASTAPI, "fastapi/httpx nicht installiert")
class TestWebhookGeheimnis(unittest.TestCase):
    """Der Webhook ist secure-by-default: ohne korrektes Geheimnis wird nichts angenommen."""

    def setUp(self):
        import web.dashboard as dash
        self.dash = dash
        self._alt = (dash.tg_app, dash.WEBHOOK_SECRET)
        dash.tg_app = object()                       # "Bot aktiv", aber nie wirklich benutzt
        from fastapi.testclient import TestClient
        self.client = TestClient(dash.app)

    def tearDown(self):
        self.dash.tg_app, self.dash.WEBHOOK_SECRET = self._alt

    def test_ohne_konfiguriertes_geheimnis_403(self):
        self.dash.WEBHOOK_SECRET = ""
        r = self.client.post("/telegram/webhook", json={})
        self.assertEqual(r.status_code, 403)

    def test_falsches_geheimnis_403(self):
        self.dash.WEBHOOK_SECRET = "richtig"
        r = self.client.post("/telegram/webhook", json={}, headers={"X-Telegram-Bot-Api-Secret-Token": "falsch"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.client.post("/telegram/webhook", json={}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
