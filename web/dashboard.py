"""FastAPI-Dashboard: Web-Rechner + optionaler Telegram-Webhook.

Start:  uvicorn web.dashboard:app --host 0.0.0.0 --port $PORT

- GET  /              -> Browser-Rechner (funktioniert ohne Secrets)
- POST /api/analyse   -> JSON-Analyse   {"input": "einzahlung=100 bonus=100% ..."}
- POST /telegram/webhook -> nur aktiv, wenn TELEGRAM_TOKEN gesetzt ist
"""

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from analyzer import analysiere, formatiere, parse

TOKEN = os.getenv("TELEGRAM_TOKEN")

app = FastAPI(title="Casino-Bonus-Analytiker")
tg_app = None  # wird nur bei gesetztem Token initialisiert

BEISPIEL = "einzahlung=100 bonus=100% faktor=30 basis=db rtp=0.96 zeit=3 einsatz=1 fs_gewinn=0"

PAGE = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Casino-Bonus-Analytiker</title>
<style>
 :root{{color-scheme:dark}}
 body{{margin:0;background:#050a1a;color:#cfe3ff;font:15px/1.5 ui-monospace,Menlo,Consolas,monospace}}
 .wrap{{max-width:760px;margin:0 auto;padding:28px 18px}}
 h1{{font-size:20px;letter-spacing:.06em;color:#7fd1ff;margin:0 0 4px}}
 p.sub{{color:#5f7aa8;margin:0 0 20px}}
 textarea{{width:100%;box-sizing:border-box;min-height:80px;background:#0a1430;color:#cfe3ff;
   border:1px solid #1e3468;border-radius:8px;padding:12px;font:inherit}}
 button{{margin-top:12px;background:#123a7a;color:#dfeaff;border:1px solid #2a5bb5;
   border-radius:8px;padding:10px 18px;cursor:pointer;font:inherit}}
 button:hover{{background:#1a4c9c}}
 pre{{white-space:pre-wrap;background:#070f24;border:1px solid #16264d;border-radius:8px;
   padding:16px;margin-top:18px;color:#bcd6ff}}
 code{{color:#7fd1ff}} a{{color:#7fd1ff}}
 .foot{{margin-top:22px;color:#4a628f;font-size:12px}}
</style></head><body><div class="wrap">
 <h1>&#9650;1 // CASINO-BONUS-ANALYTIKER</h1>
 <p class="sub">Transparente Umsatz-Berechnung. Spielerschutz &amp; Kapitalerhaltung.</p>
 <textarea id="in">{beispiel}</textarea>
 <div><button onclick="run()">Analysieren</button></div>
 <pre id="out">Parameter eingeben und &bdquo;Analysieren&ldquo; druecken.
Format: einzahlung=100 bonus=100% faktor=30 basis=b|db|d rtp=0.96 zeit=3 einsatz=1</pre>
 <div class="foot">Werte sind theoretische Erwartungswerte. Kein Rat zum Gluecksspiel &ndash;
   spiele verantwortungsbewusst. Hilfe: <a href="https://www.bzga.de">bzga.de</a> / 0800 1 37 27 00.</div>
</div>
<script>
async function run(){{
  const out=document.getElementById('out');
  out.textContent='...';
  try{{
    const r=await fetch('/api/analyse',{{method:'POST',headers:{{'Content-Type':'application/json'}},
      body:JSON.stringify({{input:document.getElementById('in').value}})}});
    const d=await r.json();
    out.textContent = d.report || d.error || 'Fehler';
  }}catch(e){{ out.textContent='Fehler: '+e; }}
}}
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return PAGE.format(beispiel=BEISPIEL)


@app.get("/health")
async def health():
    return {"status": "ok", "telegram": bool(TOKEN)}


@app.post("/api/analyse")
async def api_analyse(request: Request):
    data = await request.json()
    text = (data or {}).get("input", "")
    try:
        szenario, hinweise = parse(text)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    ergebnis = analysiere(szenario)
    return {
        "report": formatiere(ergebnis, szenario),
        "kennzahlen": {
            "bonus": ergebnis.bonus,
            "mindestumsatz": ergebnis.mindestumsatz,
            "hausvorteil": ergebnis.hausvorteil,
            "erwarteter_verlust": ergebnis.erwarteter_verlust,
            "erwartungswert": ergebnis.erwartungswert,
            "benoetigte_tage": ergebnis.benoetigte_tage,
            "zeit_machbar": ergebnis.zeit_machbar,
            "empfehlung": ergebnis.empfehlung.value,
        },
        "hinweise": hinweise,
    }


@app.on_event("startup")
async def on_startup():
    global tg_app
    if not TOKEN:
        return
    from bot.core import CasinoBonusBot
    from config import Config

    bot = CasinoBonusBot(Config())
    tg_app = bot.build_application()
    await tg_app.initialize()
    await tg_app.start()


@app.on_event("shutdown")
async def on_shutdown():
    global tg_app
    if tg_app:
        await tg_app.stop()
        await tg_app.shutdown()
        tg_app = None


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    if tg_app is None:
        raise HTTPException(status_code=503, detail="Telegram-Bot nicht aktiv (TELEGRAM_TOKEN fehlt).")
    from telegram import Update

    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
