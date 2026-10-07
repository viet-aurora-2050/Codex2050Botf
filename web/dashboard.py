"""FastAPI-Dashboard: Web-Rechner + optionaler Telegram-Webhook.

Start:  uvicorn web.dashboard:app --host 0.0.0.0 --port $PORT

- GET  /              -> Browser-Rechner (funktioniert ohne Secrets)
- POST /api/analyse   -> JSON-Analyse   {"input": "einzahlung=100 bonus=100% ..."}
- POST /telegram/webhook -> nur aktiv, wenn TELEGRAM_TOKEN UND TELEGRAM_WEBHOOK_SECRET gesetzt sind;
  Telegram sendet das Geheimnis im Header X-Telegram-Bot-Api-Secret-Token (setWebhook secret_token=...).
"""

import hmac
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from analyzer import analysiere, formatiere, parse
from sancho import erzeuge as sancho_erzeuge
from aktvier import FINALE_ZITAT, SCHUTZ_ANKER, erzeuge_signal
from web.effects import mit_effekten

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
MAX_INPUT_ZEICHEN = 5000      # Eingaben der Analyse-API (Schutz vor Missbrauch/Speicherdruck)

tg_app = None  # wird nur bei gesetztem Token initialisiert


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startet/stoppt den optionalen Telegram-Webhook-Bot (ersetzt das veraltete on_event)."""
    global tg_app
    if TOKEN:
        from bot.core import CasinoBonusBot
        from config import Config

        bot = CasinoBonusBot(Config())
        tg_app = bot.build_application()
        await tg_app.initialize()
        await tg_app.start()
    try:
        yield
    finally:
        if tg_app:
            await tg_app.stop()
            await tg_app.shutdown()
            tg_app = None


app = FastAPI(title="Casino-Bonus-Analytiker", lifespan=lifespan)

# Seiten nutzen Inline-Skripte/-Styles (Einzeldatei-Design) -> 'unsafe-inline', sonst streng.
_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")


@app.middleware("http")
async def sicherheits_header(request: Request, call_next):
    antwort = await call_next(request)
    antwort.headers.setdefault("X-Content-Type-Options", "nosniff")
    antwort.headers.setdefault("X-Frame-Options", "DENY")
    antwort.headers.setdefault("Referrer-Policy", "no-referrer")
    antwort.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    antwort.headers.setdefault("Content-Security-Policy", _CSP)
    return antwort


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
   &nbsp;·&nbsp; <a href="/sancho">&#9650;1 // Sancho &rarr;</a>
   &nbsp;·&nbsp; <a href="/signal">&#9650;1 // AKT 4 &rarr;</a></p>
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
    return mit_effekten(PAGE.format(beispiel=BEISPIEL))


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
   <option value="jackpotpirat">Jackpotpirat</option>
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
    return mit_effekten(SANCHO_PAGE)


@app.get("/api/sancho")
async def api_sancho(anbieter: str = Query("generisch", max_length=60),
                     einsatz: float = Query(1.0, gt=0, le=100000)):
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


SIGNAL_PAGE = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>&#9650;1 // AKT 4 — Das Signal</title>
<style>
 :root{color-scheme:dark}*{box-sizing:border-box}
 body{margin:0;background:#01030d;color:#bcd6ff;font:15px/1.7 ui-monospace,Menlo,Consolas,monospace;min-height:100vh}
 .wrap{max-width:760px;margin:0 auto;padding:34px 18px 70px}
 .tag{color:#3f5c94;letter-spacing:.35em;font-size:11px}
 h1{font-size:22px;letter-spacing:.08em;color:#8fdcff;margin:2px 0 18px;text-shadow:0 0 22px #1a54b080}
 .cast{color:#6f88b8;margin:2px 0}
 .final{color:#cfe3ff;font-size:17px;margin:18px 0;padding-left:12px;border-left:2px solid #2a5bb5}
 .whisper{color:#7fb0a0;font-size:14px;margin:8px 0 0;padding-left:12px;border-left:2px solid #2b4a3a}
 .sig{background:#060f28;border:1px solid #14264d;border-radius:10px;padding:16px;margin-top:22px}
 .sig h2{font-size:12px;letter-spacing:.2em;color:#5f7aa8;margin:0 0 12px}
 .layer{margin:10px 0}.lk{color:#8fdcff;font-size:11px;letter-spacing:.15em}
 .lv{color:#9db8ea;word-break:break-all}
 .sol{color:#9fe6b0}
 button{margin-top:16px;background:#123a7a;color:#dfeaff;border:1px solid #2a5bb5;border-radius:8px;padding:11px 18px;cursor:pointer;font:inherit}
 button:hover{background:#1a4c9c}
 .end{margin-top:22px;color:#ff9db0;border:1px solid #5a2233;background:#1a0910;border-radius:10px;padding:12px}
 .foot{margin-top:20px;color:#425c8c;font-size:12px}a{color:#8fdcff}
</style></head><body><div class="wrap">
 <div class="tag">&#9650;1 // AKT 4 &middot; LETZTE UEBERTRAGUNG</div>
 <h1>DAS SIGNAL</h1>
 <div class="cast">Alle Knoten konvergieren. ORPHEUS schweigt. NODE 7 schliesst das Archiv.</div>
 <div class="cast">V loescht das letzte Licht. ALEXANDRA dreht sich ein letztes Mal.</div>
 <div class="final" id="final">&hellip;</div>
 <div class="whisper" id="whisper"></div>
 <div class="sig">
  <h2>&#9583; VERSCHLUESSELTES SIGNAL &middot; EBENE 2</h2>
  <div class="layer"><div class="lk">MORSE</div><div class="lv" id="l_morse"></div><div class="sol" id="s_morse"></div></div>
  <div class="layer"><div class="lk">BASE64</div><div class="lv" id="l_base64"></div><div class="sol" id="s_base64"></div></div>
  <div class="layer"><div class="lk">ROT13</div><div class="lv" id="l_rot13"></div><div class="sol" id="s_rot13"></div></div>
  <div class="layer"><div class="lk">UHRZEITEN</div><div class="lv" id="l_uhr"></div><div class="sol" id="s_uhr"></div></div>
  <button onclick="decode()" id="btn">&#9650; Entschluesseln</button>
 </div>
 <div class="end" id="end" hidden></div>
 <div class="foot">Kein Spielbefehl &ndash; nur Erinnerung und Ausgang. Hilfe anonym:
   <a href="https://www.check-dein-spiel.de">check-dein-spiel.de</a> &middot; 0800 1 37 27 00.
   &nbsp;|&nbsp; <a href="/">&larr; Rechner</a> &middot; <a href="/sancho">Sancho</a></div>
</div>
<script>
let D=null;
async function boot(){
 D=await(await fetch('/api/signal')).json();
 document.getElementById('l_morse').textContent=D.schichten.MORSE;
 document.getElementById('l_base64').textContent=D.schichten.BASE64;
 document.getElementById('l_rot13').textContent=D.schichten.ROT13;
 document.getElementById('l_uhr').textContent=D.schichten.UHRZEITEN.join('   ');
 // Finale Zeile langsam einblenden
 const f=document.getElementById('final'),txt='» '+D.final;let i=0;
 (function t(){ if(i<=txt.length){f.textContent=txt.slice(0,i++);setTimeout(t,40);} })();
}
function decode(){
 if(!D)return;
 document.getElementById('whisper').textContent='» '+D.schutz;
 document.getElementById('s_morse').textContent='→ '+D.entschluesselt.MORSE+'  (der Schluessel)';
 document.getElementById('s_base64').textContent='→ '+D.entschluesselt.BASE64;
 document.getElementById('s_rot13').textContent='→ '+D.entschluesselt.ROT13;
 document.getElementById('s_uhr').textContent='→ '+D.entschluesselt.UHRZEITEN+'  (der Imperativ)';
 const e=document.getElementById('end');e.hidden=false;
 e.innerHTML='&#9632; Ende der Uebertragung. Der Schluessel war <b>'+D.entschluesselt.MORSE
   +'</b>. Der Imperativ war <b>'+D.entschluesselt.UHRZEITEN+'</b>.';
 document.getElementById('btn').disabled=true;
}
boot();
</script></body></html>"""


@app.get("/signal", response_class=HTMLResponse)
async def signal_page():
    return mit_effekten(SIGNAL_PAGE)


@app.get("/api/signal")
async def api_signal():
    p = erzeuge_signal()
    return {
        "final": FINALE_ZITAT,
        "schutz": SCHUTZ_ANKER,
        "schichten": p.schichten,
        "entschluesselt": p.entschluesselt,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "telegram": bool(TOKEN)}


@app.post("/api/analyse")
async def api_analyse(request: Request):
    try:
        data = await request.json()
    except ValueError:
        return JSONResponse({"error": "Ungueltiges JSON."}, status_code=400)
    text = data.get("input", "") if isinstance(data, dict) else None
    if not isinstance(text, str):
        return JSONResponse({"error": 'Erwartet {"input": "<Parameter>"}.'}, status_code=400)
    if len(text) > MAX_INPUT_ZEICHEN:
        return JSONResponse({"error": f"Eingabe zu lang (max. {MAX_INPUT_ZEICHEN} Zeichen)."}, status_code=413)
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


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    if tg_app is None:
        raise HTTPException(status_code=503, detail="Telegram-Bot nicht aktiv (TELEGRAM_TOKEN fehlt).")
    # Secure by default: ohne konfiguriertes Geheimnis wird der Webhook nicht angenommen,
    # sonst koennte jeder gefaelschte Updates (auch mit fremden User-IDs) einspielen.
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Webhook deaktiviert (TELEGRAM_WEBHOOK_SECRET fehlt).")
    gesendet = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not hmac.compare_digest(gesendet.encode(), WEBHOOK_SECRET.encode()):
        raise HTTPException(status_code=403, detail="Ungueltiges Webhook-Geheimnis.")
    from telegram import Update

    try:
        data = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungueltiges JSON.") from None
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
