import asyncio
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from ai.providers import AIManager
from utils.logger import get_logger
from utils.storage import UserStorage

logger = get_logger("Bot")

class Codex2050Bot:
    def __init__(self, config):
        self.config = config
        self.ai_manager = None
        self.user_storage = UserStorage()
        
    async def initialize(self):
        if self.config.DEEPSEEK_API_KEY:
            self.ai_manager = AIManager(self.config)
            await self.ai_manager.initialize()
            
    async def shutdown(self):
        if self.ai_manager: await self.ai_manager.close()
        
    async def start_command(self, update: Update, context):
        await update.message.reply_text("👋 Welcome to Codex2050! /help for commands.")
        
    async def help_command(self, update: Update, context):
        await update.message.reply_text("Commands:\n/codex <q> - Ask AI\n/analyze <code>\n/status")

    async def codex_command(self, update: Update, context):
        query = " ".join(context.args)
        if not query: return await update.message.reply_text("Please provide a question.")
        if self.ai_manager:
            msg = await update.message.reply_text("🤔 Thinking...")
            resp = await self.ai_manager.chat(query)
            await msg.edit_text(resp)
            
    async def analyze_command(self, update: Update, context):
        code = " ".join(context.args)
        if not code: return await update.message.reply_text("Provide code.")
        if self.ai_manager:
            msg = await update.message.reply_text("🔍 Analyzing...")
            deepseek = self.ai_manager.providers.get("deepseek")
            resp = await deepseek.analyze_code(code)
            await msg.edit_text(str(resp))

    async def run(self):
        app = Application.builder().token(self.config.TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("codex", self.codex_command))
        app.add_handler(CommandHandler("analyze", self.analyze_command))
        
        await self.initialize()
        logger.info("🤖 Bot polling...")
        await app.run_polling(drop_pending_updates=True)
