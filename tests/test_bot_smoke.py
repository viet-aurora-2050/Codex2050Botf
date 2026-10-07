"""Smoke-Test: der Bot lässt sich offline aufbauen, das Gate ist registriert, Entferntes fehlt."""

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
