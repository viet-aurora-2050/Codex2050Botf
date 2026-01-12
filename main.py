#!/usr/bin/env python3
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging einrichten
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token aus Umgebung holen
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 Hallo {user.first_name}!\n"
        f"Codex2050 Bot ist online.\n"
        f"Deine ID: {user.id}"
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /test command"""
    await update.message.reply_text("✅ Alles funktioniert!")

def main():
    """Starte den Bot"""
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN nicht gesetzt!")
        print("Bitte TELEGRAM_TOKEN in Render Environment setzen")
        return
    
    print(f"🚀 Starte Bot mit Token: {TELEGRAM_TOKEN[:20]}...")
    
    # Application erstellen
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Commands hinzufügen
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test))
    
    # Bot starten
    logger.info("Bot wird gestartet...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
