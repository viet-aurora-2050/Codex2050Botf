"""Tests für das persönliche Risikoprofil (risiko.profil): Mathematik, Selbst-Check, Grenzen, Bot, API."""

import asyncio
import importlib
import importlib.util
import math
import os
import unittest
from unittest import mock

from risiko.profil import (FRAGEN, ProfilEingabe, berechne, eingabe_aus_text, formatiere_profil,
                           stufe_fuer)

HAT_TELEGRAM = importlib.util.find_spec("telegram") is not None
HAT_FASTAPI = (importlib.util.find_spec("fastapi") is not None
               and importlib.util.find_spec("httpx") is not None)


class TestProfil(unittest.TestCase):
    def test_mathematik_exakt(self):
        e = ProfilEingabe(budget=100, einsatz=2, rtp=0.96, spins_pro_stunde=500, stunden_pro_woche=2)
        p = berechne(e, runs=600)
        self.assertAlmostEqual(p.verlust_pro_stunde, 40.0)          # 2 * 4 % * 500
        self.assertAlmostEqual(p.verlust_pro_woche, 80.0)
        self.assertAlmostEqual(p.verlust_pro_monat, 80.0 * 52 / 12, places=2)
        self.assertAlmostEqual(p.puffer_einsaetze, 50.0)
        self.assertAlmostEqual(p.lebensdauer_stunden, 2.5)

    def test_stufen_grenzen(self):
        self.assertEqual(stufe_fuer(0)[0], "niedrig")
        self.assertEqual(stufe_fuer(3)[0], "niedrig")
        self.assertEqual(stufe_fuer(4)[0], "erhöht")
        self.assertEqual(stufe_fuer(8)[0], "erhöht")
        self.assertEqual(stufe_fuer(9)[0], "hoch")
        self.assertEqual(stufe_fuer(18)[0], "hoch")

    def test_selbstcheck_aendert_nur_empfehlung_nie_die_wahrscheinlichkeit(self):
        basis = dict(budget=100, einsatz=1, rtp=0.96)
        a = berechne(ProfilEingabe(**basis, antworten=[0] * 6), runs=600)
        b = berechne(ProfilEingabe(**basis, antworten=[3] * 6), runs=600)
        self.assertEqual(a.sitzung.risk_of_ruin, b.sitzung.risk_of_ruin)
        self.assertEqual(a.verlust_pro_stunde, b.verlust_pro_stunde)
        self.assertGreater(a.empf_max_einsatz, b.empf_max_einsatz)
        self.assertGreater(a.empf_sitzung_minuten, b.empf_sitzung_minuten)
        self.assertEqual(b.stufe, "hoch")

    def test_ohne_selbstcheck_kein_score(self):
        p = berechne(ProfilEingabe(), runs=600)
        self.assertIsNone(p.score)
        self.assertIn("nicht beantwortet", formatiere_profil(p, ProfilEingabe()))

    def test_aufklaerung_ueber_fehlschluesse(self):
        e = ProfilEingabe(antworten=[0, 3, 0, 3, 0, 0])
        text = " ".join(berechne(e, runs=600).hinweise)
        self.assertIn("fällig", text)
        self.assertIn("Verlustjagd", text)

    def test_ungueltige_eingaben(self):
        for kw in ({"spins_pro_stunde": 5}, {"spins_pro_stunde": math.inf}, {"stunden_pro_woche": -1},
                   {"sitzungs_minuten": 0}, {"antworten": [1, 2]}, {"antworten": [0, 0, 0, 0, 0, 4]},
                   {"budget": -5}, {"rtp": 3.0}, {"einsatz": math.nan}):
            with self.assertRaises(ValueError, msg=str(kw)):
                berechne(ProfilEingabe(**kw), runs=500)
        with self.assertRaises(ValueError):
            berechne(ProfilEingabe(antworten=[True] * 6), runs=500)

    def test_parser(self):
        e = eingabe_aus_text("budget=250 einsatz=0,5 rtp=94 vola=hoch spins_h=300 std_woche=3 minuten=45 check=1,0,2,0,1,0")
        self.assertEqual((e.budget, e.einsatz, e.rtp, e.spins_pro_stunde, e.stunden_pro_woche, e.sitzungs_minuten),
                         (250, 0.5, 0.94, 300, 3, 45))
        self.assertEqual(e.antworten, [1, 0, 2, 0, 1, 0])
        for schlecht in ("", "hallo welt", "budget=abc", "vola=extrem", "check=a,b"):
            with self.assertRaises(ValueError, msg=schlecht):
                eingabe_aus_text(schlecht)

    def test_ausgabe_ruhig_und_ehrlich(self):
        e = ProfilEingabe(antworten=[1] * 6)
        text = formatiere_profil(berechne(e, runs=600), e)
        self.assertIn("keine Spin-Vorhersage", text)
        self.assertIn("keine Diagnose", text)
        self.assertNotIn("🎰", text)
        self.assertEqual(len(FRAGEN), 6)

    def test_hohe_stufe_verweist_auf_beratung(self):
        e = ProfilEingabe(antworten=[3] * 6)
        self.assertIn("Beratung", " ".join(berechne(e, runs=600).hinweise))


class _Msg:
    def __init__(self):
        self.texte = []

    async def reply_text(self, text, **kwargs):
        self.texte.append(text)
        return self


class _Upd:
    def __init__(self):
        self.message = _Msg()


class _Ctx:
    def __init__(self, *args):
        self.args = list(args)


@unittest.skipUnless(HAT_TELEGRAM, "python-telegram-bot nicht installiert")
class TestBotProfil(unittest.TestCase):
    def _bot(self):
        from config import Config
        from bot.core import CasinoBonusBot
        c = Config()
        c.TELEGRAM_TOKEN = "123456:TEST-TOKEN-NICHT-ECHT"
        return CasinoBonusBot(c)

    def test_registriert(self):
        app = self._bot().build_application()
        befehle = {c for g in app.handlers.values() for h in g for c in getattr(h, "commands", [])}
        self.assertIn("profil", befehle)

    def test_ohne_angaben_zeigt_fragen(self):
        upd = _Upd()
        asyncio.run(self._bot().profil_command(upd, _Ctx()))
        self.assertIn("Selbst-Check", upd.message.texte[-1])

    def test_rechnet(self):
        upd = _Upd()
        asyncio.run(self._bot().profil_command(upd, _Ctx("budget=100", "einsatz=2", "check=1,2,1,2,0,0")))
        self.assertIn("Stufe erhöht", upd.message.texte[-1])

    def test_unsinn_gibt_fehler_statt_absturz(self):
        upd = _Upd()
        asyncio.run(self._bot().profil_command(upd, _Ctx("budget=-5")))
        self.assertIn("❌", upd.message.texte[-1])


@unittest.skipUnless(HAT_FASTAPI, "fastapi/httpx nicht installiert")
class TestApiProfil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TELEGRAM_TOKEN", None)
            os.environ.pop("TELEGRAM_WEBHOOK_SECRET", None)
            import web.dashboard as dash
            cls.dash = importlib.reload(dash)
        cls.client = TestClient(cls.dash.app)

    def test_ok(self):
        r = self.client.get("/api/profil", params={"q": "budget=100 einsatz=2 check=1,2,1,2,0,0"})
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual(d["stufe"], "erhöht")
        self.assertAlmostEqual(d["verlust_pro_stunde"], 40.0)

    def test_fehler(self):
        self.assertEqual(self.client.get("/api/profil", params={"q": ""}).status_code, 422)
        self.assertEqual(self.client.get("/api/profil", params={"q": "budget=-1"}).status_code, 422)
        self.assertEqual(self.client.get("/api/profil", params={"q": "x" * 401}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
