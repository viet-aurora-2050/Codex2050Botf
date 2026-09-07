#!/usr/bin/env python3
"""Einstiegspunkt: startet den Casino-Bonus- & Umsatz-Analytiker als Telegram-Bot.

Ohne TELEGRAM_TOKEN laeuft die Rechen-Engine weiterhin per CLI:
    python -m analyzer "einzahlung=100 bonus=100% faktor=30 zeit=3 einsatz=1"
"""

import sys

from config import Config
from utils.logger import setup_logging

logger = setup_logging()


def main() -> int:
    config = Config()

    if not config.TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN nicht gesetzt.")
        print(
            "Bitte TELEGRAM_TOKEN als Umgebungsvariable setzen (z. B. in Render "
            "oder in einer .env-Datei).\n\n"
            "Tipp: Die Bonus-Berechnung laeuft auch ohne Bot direkt in der Konsole:\n"
            '  python -m analyzer "einzahlung=100 bonus=100% faktor=30 zeit=3 einsatz=1"'
        )
        return 1

    from bot.core import CasinoBonusBot

    logger.info("🚀 Starte Casino-Bonus-Analytiker (Token %s...)", config.TELEGRAM_TOKEN[:8])
    bot = CasinoBonusBot(config)
    bot.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
