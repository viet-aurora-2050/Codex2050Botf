"""Telegram-Bot: Casino-Bonus- und Umsatz-Analytiker."""

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ai.providers import AIManager
from analyzer import SYSTEM_PROMPT, analysiere, formatiere, parse
from utils.logger import get_logger

logger = get_logger("Bot")

BEISPIEL = "einzahlung=100 bonus=100% faktor=30 basis=db rtp=0.96 zeit=3 einsatz=1"

HELP_TEXT = (
    "🎰 *Casino-Bonus- & Umsatz-Analytiker*\n\n"
    "Ich rechne Umsatzbedingungen transparent durch und sage ehrlich, "
    "ob sich ein Bonus lohnt – oder ob Stornieren dein Echtgeld schuetzt.\n\n"
    "*Befehle*\n"
    "`/bonus <parameter>` – Bonus berechnen\n"
    "`/analyse <AGB-Text>` – Bonus-AGB per KI auf Haken pruefen\n"
    "`/frage <Text>` – freie Frage an den Analytiker\n"
    "`/status` – Systemstatus\n"
    "`/help` – diese Hilfe\n\n"
    "*Parameter fuer /bonus*\n"
    "`einzahlung=` `bonus=`(€ oder %) `faktor=` `basis=`b|db|d\n"
    "`rtp=0.96` `zeit=`(Tage) `einsatz=` `fs_gewinn=` `fs_faktor=`\n"
    "`maxgewinn=` `maxeinsatz=` `deckel=` `spins=` `stunden=`\n\n"
    f"*Beispiel*\n`/bonus {BEISPIEL}`\n\n"
    "_Kein Rat zum Gluecksspiel. Spiele verantwortungsbewusst._"
)


class CasinoBonusBot:
    def __init__(self, config):
        self.config = config
        self.ai_manager = AIManager(config)

    # ---- Lifecycle ----------------------------------------------------
    async def _post_init(self, app: Application):
        if self.ai_manager.available:
            await self.ai_manager.initialize()
            logger.info("KI-Provider bereit: %s", self.ai_manager.get_stats())
        else:
            logger.info("Keine KI konfiguriert – Rechen-Engine laeuft eigenstaendig.")

    async def _post_shutdown(self, app: Application):
        await self.ai_manager.close()

    # ---- Commands -----------------------------------------------------
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎰 Willkommen beim *Casino-Bonus- & Umsatz-Analytiker*.\n"
            "Sende `/help` fuer alle Befehle oder direkt z. B.:\n"
            f"`/bonus {BEISPIEL}`",
            parse_mode="Markdown",
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        ki = "aktiv" if self.ai_manager.available else "nicht konfiguriert"
        await update.message.reply_text(
            f"✅ Online\nRechen-Engine: aktiv\nKI (AGB-Analyse): {ki}"
        )

    async def bonus_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = " ".join(context.args)
        await self._analysiere_und_antworte(update, text)

    async def analyse_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        agb = " ".join(context.args)
        if not agb:
            return await update.message.reply_text(
                "Bitte AGB-/Bonustext anhaengen:\n`/analyse <Text der Bonusbedingungen>`",
                parse_mode="Markdown",
            )
        msg = await update.message.reply_text("🔍 Analysiere AGB ...")
        antwort = await self.ai_manager.ask(
            "Analysiere die folgenden Casino-Bonus-AGB auf versteckte Haken, "
            "Maximalgewinne, ausgeschlossene Spiele und unrealistische "
            "Umsatzbedingungen. Rechne Beispielumsaetze vor:\n\n" + agb,
            system_prompt=SYSTEM_PROMPT,
        )
        await msg.edit_text(antwort[:4000])

    async def frage_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        frage = " ".join(context.args)
        if not frage:
            return await update.message.reply_text("Bitte eine Frage anhaengen: `/frage ...`",
                                                    parse_mode="Markdown")
        msg = await update.message.reply_text("🤔 Denke nach ...")
        antwort = await self.ai_manager.ask(frage, system_prompt=SYSTEM_PROMPT)
        await msg.edit_text(antwort[:4000])

    async def text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Freitext: sieht wie Bonus-Parameter aus? Dann direkt rechnen."""
        text = update.message.text or ""
        if "=" in text:
            await self._analysiere_und_antworte(update, text)
        else:
            await update.message.reply_text(
                "Sende `/help` oder Bonus-Parameter, z. B.:\n"
                f"`{BEISPIEL}`",
                parse_mode="Markdown",
            )

    # ---- Helper -------------------------------------------------------
    async def _analysiere_und_antworte(self, update: Update, text: str):
        if not text.strip():
            return await update.message.reply_text(
                "Bitte Parameter angeben, z. B.:\n" f"`/bonus {BEISPIEL}`",
                parse_mode="Markdown",
            )
        try:
            szenario, hinweise = parse(text)
        except ValueError as exc:
            return await update.message.reply_text(
                f"❌ {exc}\nBeispiel:\n`/bonus {BEISPIEL}`", parse_mode="Markdown"
            )
        ergebnis = analysiere(szenario)
        report = formatiere(ergebnis, szenario)
        if hinweise:
            report += "\n\nHinweise:\n" + "\n".join(f"• {h}" for h in hinweise)
        await update.message.reply_text(report)

    # ---- Runner -------------------------------------------------------
    def build_application(self) -> Application:
        app = (
            Application.builder()
            .token(self.config.TELEGRAM_TOKEN)
            .post_init(self._post_init)
            .post_shutdown(self._post_shutdown)
            .build()
        )
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("status", self.status_command))
        app.add_handler(CommandHandler("bonus", self.bonus_command))
        app.add_handler(CommandHandler("analyse", self.analyse_command))
        app.add_handler(CommandHandler("analyze", self.analyse_command))
        app.add_handler(CommandHandler("frage", self.frage_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_message))
        return app

    def run(self):
        app = self.build_application()
        logger.info("🤖 Bot startet Polling ...")
        app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
