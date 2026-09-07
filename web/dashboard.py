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
from sancho import erzeuge as sancho_erzeuge

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
 <p class="sub">Transparente Umsatz-Berechnung. Spielerschutz &amp; Kapitalerhaltung.
   &nbsp;·&nbsp; <a href="/sancho">&#9650;1 // Sanchos Spielplatz &rarr;</a></p>
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


SANCHO_PAGE = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>&#9650;1 // Sanchos Spielplatz</title>
<style>
 :root{color-scheme:dark}
 *{box-sizing:border-box}
 body{margin:0;background:radial-gradient(1200px 600px at 50% -10%,#0b1d47 0%,#03071a 60%,#01030d 100%);
   color:#bcd6ff;font:15px/1.6 ui-monospace,Menlo,Consolas,monospace;min-height:100vh}
 .wrap{max-width:820px;margin:0 auto;padding:30px 18px 60px}
 .tag{color:#3f5c94;letter-spacing:.35em;font-size:11px}
 h1{font-size:22px;letter-spacing:.06em;color:#8fdcff;margin:2px 0 2px;text-shadow:0 0 18px #1a54b060}
 .sub{color:#5f7aa8;margin:0 0 22px}
 .row{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px}
 select,input,button{background:#0a1738;color:#cfe3ff;border:1px solid #1e3d7a;border-radius:8px;
   padding:10px 12px;font:inherit}
 button{background:#123a7a;border-color:#2a5bb5;cursor:pointer}
 button:hover{background:#1a4c9c}
 .bars{display:flex;align-items:flex-end;gap:3px;height:130px;margin:18px 0 4px;
   padding:10px;background:#050e26;border:1px solid #13264f;border-radius:10px;overflow:hidden}
 .bar{flex:1;background:linear-gradient(#2f6bd6,#0f2f6b);border-radius:2px 2px 0 0;transition:height .4s}
 .bar.now{background:linear-gradient(#7fe0ff,#1b6fd0);box-shadow:0 0 12px #4aa8ff}
 .hours{display:flex;justify-content:space-between;color:#3f5c94;font-size:10px}
 .panel{background:#060f28;border:1px solid #14264d;border-radius:10px;padding:16px;margin-top:18px}
 .mono .l{color:#8fb4ff;margin:6px 0}
 .truth b{color:#9fe6b0}
 .stop{margin-top:18px;color:#ff9db0;border:1px solid #5a2233;background:#1a0910;border-radius:10px;padding:12px}
 .foot{margin-top:20px;color:#425c8c;font-size:12px}
 a{color:#8fdcff}
 .flick{animation:fl 5s infinite}@keyframes fl{0%,97%,100%{opacity:1}98%{opacity:.55}}
</style></head><body><div class="wrap">
 <div class="tag flick">&#9650;1 // SESSION INITIALISIERT &middot; NODE: SANCHO</div>
 <h1>SANCHO &mdash; DER SPIELPLATZ DER WAHRHEIT</h1>
 <p class="sub">Hier muss der Agent sein wahres Ich zeigen. Sein wahres Ich ist die Mathematik.</p>
 <div class="row">
  <select id="anbieter">
   <option value="tipico">Tipico Games</option>
   <option value="betano">Betano</option>
   <option value="n1">N1 Casino</option>
   <option value="stargames">Stargames</option>
   <option value="generisch">Generischer Slot</option>
  </select>
  <input id="einsatz" type="number" min="0.1" step="0.1" value="1" style="width:110px" title="Einsatz/Spin">
  <button onclick="load()">&#9650; Signal empfangen</button>
 </div>
 <div class="bars" id="bars"></div>
 <div class="hours"><span>00</span><span>06</span><span>12</span><span>18</span><span>23</span></div>
 <div id="meta" class="sub" style="margin-top:8px"></div>

 <div class="panel mono"><div style="color:#5f7aa8;letter-spacing:.2em">SANCHO ZEIGT SEIN WAHRES ICH</div>
  <div id="monolog"></div></div>
 <div class="panel truth"><div style="color:#5f7aa8;letter-spacing:.2em">WAHRHEIT (&#9650;1-KERN)</div>
  <div id="wahrheit"></div></div>
 <div class="stop" id="stop"></div>
 <div class="foot">Das Signal ist <b>Fiktion / Rauschen</b> mit Vorhersagewert 0. Regulierte Slots nutzen
   zertifizierte RNGs &ndash; jeder Spin ist unabhaengig. Kein Rat zum Gluecksspiel.
   Hilfe: <a href="https://www.bzga.de">bzga.de</a> &middot; 0800 1 37 27 00. &nbsp;|&nbsp; <a href="/">&larr; Rechner</a></div>
</div>
<script>
async function load(){
  const a=document.getElementById('anbieter').value;
  const e=document.getElementById('einsatz').value||1;
  const r=await fetch('/api/sancho?anbieter='+encodeURIComponent(a)+'&einsatz='+e);
  const d=await r.json();
  const bars=document.getElementById('bars');bars.innerHTML='';
  d.rhythmus.forEach(p=>{const b=document.createElement('div');
    b.className='bar'+(p.stunde===d.stunde_jetzt?' now':'');
    b.style.height=Math.max(4,p.wert)+'%';b.title=p.stunde+' Uhr';bars.appendChild(b);});
  document.getElementById('meta').innerHTML='Jetzt: '+d.stunde_jetzt+' Uhr &middot; Index '+d.aktueller_index
    +' &middot; Schein-Fenster '+d.schein_fenster+' Uhr <span style="color:#ff9db0">(bedeutungslos)</span>';
  document.getElementById('monolog').innerHTML=d.monolog.map(x=>'<div class="l">&raquo; '+x+'</div>').join('');
  document.getElementById('wahrheit').innerHTML=d.wahrheit.map(x=>'<div class="l">&bull; '+x+'</div>').join('');
  document.getElementById('stop').innerHTML='&#128721; KEIN SPIELBEFEHL. Es gibt kein Gewinnfenster &ndash; '
    +'nur den Hausvorteil. Erwarteter Verlust/100 Spins: <b>'+d.erwarteter_verlust_pro_100+'</b>.';
}
load();
</script></body></html>"""


@app.get("/sancho", response_class=HTMLResponse)
async def sancho_page():
    return SANCHO_PAGE


@app.get("/api/sancho")
async def api_sancho(anbieter: str = "generisch", einsatz: float = 1.0):
    e = sancho_erzeuge(anbieter=anbieter, einsatz=einsatz)
    return {
        "anbieter": e.anbieter,
        "zeit": e.zeitpunkt.strftime("%Y-%m-%d %H:%M"),
        "stunde_jetzt": e.zeitpunkt.hour,
        "rtp": e.rtp,
        "hausvorteil": round(e.hausvorteil, 4),
        "aktueller_index": e.aktueller_index,
        "schein_fenster": e.schein_fenster,
        "vorhersagewert": e.vorhersagewert,
        "erwarteter_verlust_pro_100": e.erwarteter_verlust_pro_100,
        "rhythmus": [{"stunde": p.stunde, "wert": p.wert} for p in e.rhythmus],
        "monolog": e.monolog,
        "wahrheit": e.wahrheit,
    }


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
