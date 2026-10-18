"""Tests für den AGB-Scanner (analyzer.scan): findet nur, was im Text steht, erfindet nichts."""

import asyncio
import importlib
import importlib.util
import os
import time
import unittest
from unittest import mock

from analyzer.bonus import UmsatzBasis
from analyzer.scan import (MAX_ZEICHEN, analysiere_text, formatiere_scan, optionen_aus_text,
                           scanne, sieht_nach_agb_aus)

AGB = ("Willkommensbonus: 100 % bis zu 200 € auf deine erste Einzahlung. Mindesteinzahlung 20 €. "
       "Der Bonus muss 35x umgesetzt werden (Bonusbetrag + Einzahlung). Frist: 30 Tage. "
       "Maximaler Einsatz pro Spin 5 €. Maximaler Gewinn 500 €.")

HAT_TELEGRAM = importlib.util.find_spec("telegram") is not None
HAT_FASTAPI = (importlib.util.find_spec("fastapi") is not None
               and importlib.util.find_spec("httpx") is not None)


class TestScanne(unittest.TestCase):
    def test_realistischer_text(self):
        s = scanne(AGB).szenario
        self.assertEqual(s.umsatzfaktor, 35)
        self.assertEqual(s.bonus_prozent, 100)
        self.assertEqual(s.bonus_deckel, 200)
        self.assertEqual(s.zeitlimit_tage, 30)
        self.assertEqual(s.max_einsatz_pro_spin, 5)
        self.assertEqual(s.max_gewinn, 500)
        self.assertEqual(s.umsatz_basis, UmsatzBasis.EINZAHLUNG_PLUS_BONUS)

    def test_mindesteinzahlung_nimmt_betrag_nach_dem_stichwort(self):
        r = scanne("Bonus 50 % bis 100 €. Mindesteinzahlung 10 € (Bonus bis 100 €). Umsatz 30x.")
        self.assertEqual(r.mindesteinzahlung, 10)

    def test_annahmen_werden_ausgewiesen_nichts_erfunden(self):
        r = scanne(AGB)
        text = " ".join(r.annahmen)
        self.assertIn("RTP", text)
        self.assertIn("Mindesteinzahlung", text)
        self.assertEqual(r.szenario.rtp, 0.96)

    def test_nutzerangaben_haben_vorrang(self):
        r = scanne(AGB, einzahlung=50, rtp=0.94, einsatz=2)
        self.assertEqual(r.szenario.einzahlung, 50)
        self.assertEqual(r.szenario.rtp, 0.94)
        self.assertEqual(r.szenario.durchschnittseinsatz, 2)

    def test_widerspruch_waehlt_konservativ_und_warnt(self):
        r = scanne("Bonus 100 % bis 100 €. Umsatz 30x innerhalb von 7 Tagen. "
                   "An anderer Stelle: Bonus-Umsatz 35x, gültig 30 Tage.", einzahlung=50)
        self.assertEqual(r.szenario.umsatzfaktor, 35)
        self.assertEqual(r.szenario.zeitlimit_tage, 7)
        self.assertTrue(r.hinweise)

    def test_stunden_werden_zu_tagen(self):
        r = scanne("Bonus 100 % bis 100 €. Umsatz 30x innerhalb von 48 Stunden.", einzahlung=50)
        self.assertEqual(r.szenario.zeitlimit_tage, 2)

    def test_dezimal_und_tausender_betraege(self):
        r = scanne("Bonus 100 % bis zu 1.000 €. Umsatz 30x. Max. Einsatz 2,50 € pro Spin.", einzahlung=100)
        self.assertEqual(r.szenario.bonus_deckel, 1000)
        self.assertEqual(r.szenario.max_einsatz_pro_spin, 2.5)

    def test_bonus_ohne_einzahlung(self):
        r = scanne("Bonus ohne Einzahlung: 10 € Bonusguthaben. Umsatz 40x.")
        self.assertEqual(r.szenario.einzahlung, 0)
        self.assertEqual(r.szenario.bonus_betrag, 10)

    def test_ohne_bonus_wird_nicht_gerechnet(self):
        for text in ("Das Wetter ist heute schön.", "Umsatzbedingung 35x, sonst nichts Relevantes."):
            with self.assertRaises(ValueError):
                scanne(text)

    def test_leer_und_zu_lang(self):
        with self.assertRaises(ValueError):
            scanne("   ")
        with self.assertRaises(ValueError):
            scanne("Bonus " * MAX_ZEICHEN)

    def test_prozentbonus_ohne_einzahlungsangabe_fragt_nach(self):
        with self.assertRaises(ValueError):
            scanne("Bonus 100 % auf alles. Umsatz 30x.")

    def test_warnungen(self):
        r = scanne("Bonus 100 % bis 100 €. Umsatz 45x. Slots zählen 100 %, Tischspiele 10 % zum Umsatz. "
                   "Maximaler Einsatz 5 € pro Spin, sonst gilt: Bonus verfällt.", einzahlung=50)
        text = " ".join(r.hinweise)
        self.assertIn("45", text)
        self.assertIn("verstoß", text.lower())

    def test_rechnet_mit_unveraenderter_engine(self):
        scan, erg = analysiere_text(AGB, einzahlung=50)
        self.assertIs(erg.__class__.__name__, "Ergebnis")
        report = formatiere_scan(scan, erg)
        self.assertIn("ANNAHMEN", report)
        self.assertIn("Keine Rechtsberatung", report)

    def test_keine_ausweichende_laufzeit_bei_pathologischem_text(self):
        boese = ("1" * 20 + ". " + "bonus 1 € " * 5 + "x" * 50) * 100
        boese = (boese + "9" * MAX_ZEICHEN)[:MAX_ZEICHEN]
        t0 = time.perf_counter()
        try:
            scanne(boese)
        except ValueError:
            pass
        self.assertLess(time.perf_counter() - t0, 2)


class TestHilfsfunktionen(unittest.TestCase):
    def test_optionen_aus_text(self):
        text, opt = optionen_aus_text("Bonus 100 % Umsatz 30x einzahlung=50 rtp=0,96 einsatz=2.5")
        self.assertEqual(opt, {"einzahlung": 50.0, "rtp": 0.96, "einsatz": 2.5})
        self.assertNotIn("einzahlung=", text)

    def test_sieht_nach_agb_aus(self):
        self.assertTrue(sieht_nach_agb_aus(AGB))
        self.assertFalse(sieht_nach_agb_aus("budget=100 einsatz=1"))
        self.assertFalse(sieht_nach_agb_aus("Bonus 10x"))          # zu kurz


class _Msg:
    def __init__(self):
        self.texte = []

    async def reply_text(self, text, **kwargs):
        self.texte.append(text)
        return self

    async def edit_text(self, text, **kwargs):
        self.texte.append(text)
        return self


class _Upd:
    def __init__(self, text=""):
        self.message = _Msg()
        self.message.text = text


class _Ctx:
    def __init__(self, *args):
        self.args = list(args)


@unittest.skipUnless(HAT_TELEGRAM, "python-telegram-bot nicht installiert")
class TestBotScan(unittest.TestCase):
    def _bot(self):
        from config import Config
        from bot.core import CasinoBonusBot
        c = Config()
        c.TELEGRAM_TOKEN = "123456:TEST-TOKEN-NICHT-ECHT"
        return CasinoBonusBot(c)

    def test_scan_befehl_registriert(self):
        app = self._bot().build_application()
        befehle = {c for g in app.handlers.values() for h in g for c in getattr(h, "commands", [])}
        self.assertIn("scan", befehle)

    def test_scan_befehl_rechnet(self):
        upd = _Upd()
        asyncio.run(self._bot().scan_command(upd, _Ctx(*AGB.split(), "einzahlung=50")))
        self.assertIn("AGB-SCAN", upd.message.texte[-1])
        self.assertLessEqual(len(upd.message.texte[-1]), 4096)

    def test_scan_ohne_text_gibt_hilfe_statt_absturz(self):
        upd = _Upd()
        asyncio.run(self._bot().scan_command(upd, _Ctx()))
        self.assertTrue(upd.message.texte)

    def test_freitext_agb_wird_gescannt_parameter_nicht(self):
        bot = self._bot()
        upd = _Upd(AGB)
        asyncio.run(bot.text_message(upd, _Ctx()))
        self.assertIn("AGB-SCAN", upd.message.texte[-1])
        upd = _Upd("budget=100 einsatz=1 spins=200")
        asyncio.run(bot.text_message(upd, _Ctx()))
        self.assertNotIn("AGB-SCAN", upd.message.texte[-1])

    def test_unsinn_ergibt_fehlermeldung(self):
        upd = _Upd()
        asyncio.run(self._bot().scan_command(upd, _Ctx("Das", "Wetter", "ist", "schoen", "heute", "wirklich")))
        self.assertIn("❌", upd.message.texte[-1])


@unittest.skipUnless(HAT_FASTAPI, "fastapi/httpx nicht installiert")
class TestApiScan(unittest.TestCase):
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
        r = self.client.post("/api/scan", json={"text": AGB, "einzahlung": 50})
        self.assertEqual(r.status_code, 200)
        d = r.json()
        for k in ("report", "funde", "annahmen", "hinweise", "kennzahlen"):
            self.assertIn(k, d)

    def test_fehlerfaelle(self):
        self.assertEqual(self.client.post("/api/scan", content=b"{kaputt",
                                          headers={"content-type": "application/json"}).status_code, 400)
        self.assertEqual(self.client.post("/api/scan", json=["x"]).status_code, 400)
        self.assertEqual(self.client.post("/api/scan", json={"text": 5}).status_code, 400)
        self.assertEqual(self.client.post("/api/scan", json={"text": "x" * (MAX_ZEICHEN + 1)}).status_code, 413)
        self.assertEqual(self.client.post("/api/scan", json={"text": "Wetter ist schoen."}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
