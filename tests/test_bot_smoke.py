"""Smoke-Test: der Bot lässt sich offline aufbauen, das Gate ist registriert, Entferntes fehlt."""

import asyncio
import importlib.util
import time
import unittest

HAT_TELEGRAM = importlib.util.find_spec("telegram") is not None


@unittest.skipUnless(HAT_TELEGRAM, "python-telegram-bot nicht installiert")
class TestBotAufbau(unittest.TestCase):
    def _bot(self, **cfg):
        from config import Config
        from bot.core import CasinoBonusBot
        c = Config()
        c.TELEGRAM_TOKEN = "123456:TEST-TOKEN-NICHT-ECHT"
        for k, v in cfg.items():
            setattr(c, k, v)
        return CasinoBonusBot(c)

    def test_gate_laeuft_vor_allen_befehlen(self):
        app = self._bot(ALLOWED_USER_IDS=[1]).build_application()
        self.assertIn(-1, app.handlers)                          # Gruppe -1 = Gate
        self.assertTrue(all(g >= -1 for g in app.handlers))

    def test_befehle_vorhanden_entfernte_nicht(self):
        app = self._bot().build_application()
        befehle = {c for gruppe in app.handlers.values() for h in gruppe
                   for c in getattr(h, "commands", [])}
        for erwartet in ("sancho", "signal", "bonus", "risiko", "melde", "gewinner", "help"):
            self.assertIn(erwartet, befehle)
        self.assertNotIn("traeger", befehle)
        self.assertNotIn("node", befehle)


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
    def __init__(self):
        self.message = _Msg()


class _Ctx:
    def __init__(self, *args):
        self.args = list(args)


@unittest.skipUnless(HAT_TELEGRAM, "python-telegram-bot nicht installiert")
class TestRisikoBefehl(unittest.TestCase):
    """/risiko darf weder abstuerzen noch den Event-Loop blockieren (oeffentlicher Bot, Nutzereingaben)."""

    def _lauf(self, *args):
        from config import Config
        from bot.core import CasinoBonusBot
        c = Config()
        c.TELEGRAM_TOKEN = "123456:TEST-TOKEN-NICHT-ECHT"
        bot, upd = CasinoBonusBot(c), _Upd()
        asyncio.run(bot.risiko_command(upd, _Ctx(*args)))
        return upd.message.texte[-1]

    def test_normale_anfrage_zeigt_konfidenzintervalle(self):
        text = self._lauf("budget=100", "einsatz=1", "spins=200", "rtp=0.96")
        self.assertIn("95%-KI", text)
        self.assertIn("KEINE Spin-Vorhersage", text)

    def test_riesige_spinzahl_wird_abgelehnt_statt_zu_rechnen(self):
        t0 = time.perf_counter()
        text = self._lauf("spins=100000000", "budget=1000000000")
        self.assertIn("❌", text)
        self.assertLess(time.perf_counter() - t0, 2)

    def test_unsinnswerte_geben_fehlermeldung(self):
        for arg in ("spins=inf", "budget=nan", "einsatz=-3", "rtp=7"):
            text = self._lauf("budget=100", arg)
            self.assertTrue("❌" in text or "95%-KI" in text, arg)   # nie ein Absturz


if __name__ == "__main__":
    unittest.main()
