"""Tests für bot.zugriff: Allowlist + Rate-Limit (reine Logik, ohne Telegram-Netzwerk)."""

import asyncio
import importlib.util
import unittest

from bot.zugriff import FENSTER_SEKUNDEN, Zugriff

HAT_TELEGRAM = importlib.util.find_spec("telegram") is not None


class Uhr:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class TestAllowlist(unittest.TestCase):
    def test_leere_liste_erlaubt_alle(self):
        self.assertTrue(Zugriff().ist_erlaubt(42))

    def test_liste_sperrt_fremde(self):
        z = Zugriff([1, 2])
        self.assertTrue(z.ist_erlaubt(1))
        self.assertFalse(z.ist_erlaubt(3))

    def test_warnung_nur_bei_oeffentlichem_bot(self):
        self.assertIsNone(Zugriff([1]).warnung(ki_aktiv=True))
        self.assertIn("API-Kosten", Zugriff().warnung(ki_aktiv=True))
        self.assertIn("öffentlich", Zugriff().warnung(ki_aktiv=False))


class TestRateLimit(unittest.TestCase):
    def test_limit_und_gleitendes_fenster(self):
        uhr = Uhr()
        z = Zugriff(limit_pro_minute=3, uhr=uhr)
        self.assertTrue(all(z.zaehle_und_pruefe(7) for _ in range(3)))
        self.assertFalse(z.zaehle_und_pruefe(7))                 # 4. Anfrage in der Minute
        uhr.t += FENSTER_SEKUNDEN                                # Fenster vorbei
        self.assertTrue(z.zaehle_und_pruefe(7))

    def test_nutzer_sind_unabhaengig(self):
        z = Zugriff(limit_pro_minute=1, uhr=Uhr())
        self.assertTrue(z.zaehle_und_pruefe(1))
        self.assertTrue(z.zaehle_und_pruefe(2))
        self.assertFalse(z.zaehle_und_pruefe(1))

    def test_limit_null_schaltet_ab(self):
        z = Zugriff(limit_pro_minute=0, uhr=Uhr())
        self.assertTrue(all(z.zaehle_und_pruefe(1) for _ in range(100)))

    def test_aufraeumen_begrenzt_speicher(self):
        import bot.zugriff as modul
        uhr = Uhr()
        z = Zugriff(limit_pro_minute=5, uhr=uhr)
        alt = modul.MAX_BEKANNTE_NUTZER
        modul.MAX_BEKANNTE_NUTZER = 10
        try:
            for uid in range(10):
                z.zaehle_und_pruefe(uid)
            uhr.t += FENSTER_SEKUNDEN + 1
            z.zaehle_und_pruefe(999)                             # loest Aufraeumen aus
            self.assertLessEqual(len(z._anfragen), 2)
        finally:
            modul.MAX_BEKANNTE_NUTZER = alt


class _Nutzer:
    def __init__(self, uid):
        self.id = uid


class _Nachricht:
    def __init__(self):
        self.antworten = []

    async def reply_text(self, text):
        self.antworten.append(text)


class _Update:
    def __init__(self, uid, nachricht=None):
        self.effective_user = _Nutzer(uid) if uid is not None else None
        self.effective_message = nachricht


@unittest.skipUnless(HAT_TELEGRAM, "python-telegram-bot nicht installiert")
class TestGate(unittest.TestCase):
    def _lauf(self, z, update):
        from telegram.ext import ApplicationHandlerStop
        try:
            asyncio.run(z.gate(update, None))
            return False
        except ApplicationHandlerStop:
            return True

    def test_erlaubter_nutzer_passiert(self):
        self.assertFalse(self._lauf(Zugriff([5], 10, Uhr()), _Update(5, _Nachricht())))

    def test_fremder_wird_still_blockiert(self):
        n = _Nachricht()
        self.assertTrue(self._lauf(Zugriff([5], 10, Uhr()), _Update(6, n)))
        self.assertEqual(n.antworten, [])                        # nichts verraten

    def test_update_ohne_nutzer_wird_blockiert(self):
        self.assertTrue(self._lauf(Zugriff([], 10, Uhr()), _Update(None)))

    def test_drosselung_antwortet_nur_einmal_pro_fenster(self):
        uhr, n = Uhr(), _Nachricht()
        z = Zugriff([], 1, uhr)
        self.assertFalse(self._lauf(z, _Update(9, n)))           # 1. Anfrage ok
        self.assertTrue(self._lauf(z, _Update(9, n)))            # gedrosselt -> Hinweis
        self.assertTrue(self._lauf(z, _Update(9, n)))            # gedrosselt -> kein 2. Hinweis
        self.assertEqual(len(n.antworten), 1)


if __name__ == "__main__":
    unittest.main()
