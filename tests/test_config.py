"""Tests für config: fail-closed Parsing der Allowlist und sichere Standardwerte."""

import os
import unittest
from unittest import mock

from config import Config, parse_user_ids

ENV_KEYS = ["ALLOWED_USER_IDS", "ADMIN_USER_IDS", "PORT", "WEB_PORT", "ENABLE_RPC", "ENABLE_WEB",
            "RATE_LIMIT_PER_MINUTE", "TELEGRAM_TOKEN", "DEEPSEEK_API_KEY"]


def sauber(**gesetzt):
    env = {k: v for k, v in os.environ.items() if k not in ENV_KEYS}
    env.update(gesetzt)
    return mock.patch.dict(os.environ, env, clear=True)


class TestParseUserIds(unittest.TestCase):
    def test_gueltig(self):
        self.assertEqual(parse_user_ids("1, 22 ,333"), [1, 22, 333])
        self.assertEqual(parse_user_ids(""), [])

    def test_fehlerhafter_eintrag_bricht_ab_statt_bot_zu_oeffnen(self):
        for roh in ("123;456", "abc", "12,x", "-5"):
            with self.assertRaises(ValueError, msg=roh):
                parse_user_ids(roh)


class TestConfig(unittest.TestCase):
    def test_sichere_standardwerte(self):
        with sauber():
            c = Config()
        self.assertFalse(c.ENABLE_RPC)
        self.assertEqual(c.RPC_HOST, "127.0.0.1")
        self.assertEqual(c.ALLOWED_USER_IDS, [])
        self.assertEqual(c.RATE_LIMIT_PER_MINUTE, 10)

    def test_env_wird_gelesen(self):
        with sauber(ALLOWED_USER_IDS="7,8", PORT="9001", RATE_LIMIT_PER_MINUTE="3", ENABLE_RPC="true"):
            c = Config()
        self.assertEqual(c.ALLOWED_USER_IDS, [7, 8])
        self.assertEqual(c.WEB_PORT, 9001)
        self.assertEqual(c.RATE_LIMIT_PER_MINUTE, 3)
        self.assertTrue(c.ENABLE_RPC)
        self.assertTrue(c.is_user_allowed(7))
        self.assertFalse(c.is_user_allowed(9))

    def test_ungueltiger_port_gibt_klare_fehlermeldung(self):
        with sauber(PORT="abc"):
            with self.assertRaisesRegex(ValueError, "PORT"):
                Config()

    def test_kaputte_allowlist_stoppt_den_start(self):
        with sauber(ALLOWED_USER_IDS="123;456"):
            with self.assertRaises(ValueError):
                Config()


if __name__ == "__main__":
    unittest.main()
