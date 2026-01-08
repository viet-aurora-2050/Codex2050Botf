import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

app = FastAPI()
tg_app: Application | None = None


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("✅ Codex2050 Webhook ist live.")


@app.on_event("startup")
async def on_startup():
    global tg_app
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN fehlt im Webservice Env!")

    tg_app = Application.builder().token(TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start_cmd))

    # python-telegram-bot muss für Webhooks initialisiert & gestartet werden
    await tg_app.initialize()
    await tg_app.start()


@app.on_event("shutdown")
async def on_shutdown():
    global tg_app
    if tg_app:
        await tg_app.stop()
        await tg_app.shutdown()


@app.get("/", response_class=HTMLResponse)
async def root():
    return "<html><body><h1>Codex2050 Dashboard ✅</h1></body></html>"


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    if tg_app is None:
        raise HTTPException(status_code=503, detail="Bot not ready")

    data = await request.json()
    update = Update.de_json(data, tg_app.bot)

    # verarbeitet das Update direkt (kein Worker nötig)
    await tg_app.process_update(update)
    return {"ok": True}
