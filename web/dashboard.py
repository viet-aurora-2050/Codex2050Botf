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
from traeger import bewerte as traeger_bewerte
from nodes import NODES
from nodes import sende as node_sende
from aktvier import FINALE_ZITAT, SCHUTZ_ANKER, erzeuge_signal
from web.effects import mit_effekten

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
   &nbsp;·&nbsp; <a href="/sancho">&#9650;1 // Sancho &rarr;</a>
   &nbsp;·&nbsp; <a href="/traeger">&#9650;1 // Träger &rarr;</a>
   &nbsp;·&nbsp; <a href="/nodes">&#9650;1 // Nodes &rarr;</a>
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


TRAEGER_PAGE = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>&#9650;1 // Träger-Protokoll</title>
<style>
 :root{color-scheme:dark}*{box-sizing:border-box}
 body{margin:0;background:radial-gradient(1100px 560px at 50% -10%,#0b1d47 0%,#03071a 60%,#01030d 100%);
   color:#bcd6ff;font:15px/1.6 ui-monospace,Menlo,Consolas,monospace;min-height:100vh}
 .wrap{max-width:760px;margin:0 auto;padding:30px 18px 60px}
 .tag{color:#3f5c94;letter-spacing:.35em;font-size:11px}
 h1{font-size:22px;letter-spacing:.06em;color:#8fdcff;margin:2px 0 2px;text-shadow:0 0 18px #1a54b060}
 .sub{color:#5f7aa8;margin:0 0 18px}
 .axis{margin:14px 0}
 .axis .lab{display:flex;justify-content:space-between;color:#9db8ea}
 .axis .val{color:#8fdcff}
 input[type=range]{width:100%;accent-color:#3f8fe0}
 .q{color:#4f6aa0;font-size:12px;margin-top:2px}
 button{margin-top:16px;background:#123a7a;color:#dfeaff;border:1px solid #2a5bb5;border-radius:8px;
   padding:11px 18px;cursor:pointer;font:inherit}button:hover{background:#1a4c9c}
 .meter{height:12px;border-radius:6px;background:#0a1738;border:1px solid #1e3d7a;overflow:hidden;margin-top:16px}
 .meter > i{display:block;height:100%;width:0;transition:width .5s,background .5s}
 .panel{background:#060f28;border:1px solid #14264d;border-radius:10px;padding:16px;margin-top:16px}
 .l{color:#8fb4ff;margin:6px 0}
 .protect{border-color:#2b4a2f;background:#08160c}.protect .l{color:#9fe6b0}
 .alx{border:1px solid #5a2233;background:#1a0910}.alx .l{color:#ff9db0}
 .foot{margin-top:20px;color:#425c8c;font-size:12px}a{color:#8fdcff}
</style></head><body><div class="wrap">
 <div class="tag">&#9650;1 // TRÄGER-PROTOKOLL &middot; SELBST-SPIEGEL</div>
 <h1>WURDE ICH BEHALTEN?</h1>
 <p class="sub">∆1 markiert nicht Intelligenz, sondern emotionale Extreme. Freiwillig,
   anonym, keine Diagnose. 0 = nie &middot; 3 = fast immer.</p>
 <div id="axes"></div>
 <button onclick="run()">&#9650; Protokoll lesen</button>
 <div class="meter"><i id="bar"></i></div>
 <div id="status" class="sub" style="margin-top:10px"></div>
 <div class="panel"><div style="color:#5f7aa8;letter-spacing:.2em">∆1 SPIEGELT</div><div id="spiegel"></div></div>
 <div class="panel protect" id="schutzbox"><div style="color:#6f9f7a;letter-spacing:.2em">SCHUTZ</div><div id="schutz"></div></div>
 <div class="foot">Freiwillige Selbstauskunft, keine Diagnose, kein Rat zum Spielen.
   Hilfe: <a href="https://www.check-dein-spiel.de">check-dein-spiel.de</a> &middot; 0800 1 37 27 00.
   &nbsp;|&nbsp; <a href="/">&larr; Rechner</a> &middot; <a href="/sancho">Sancho</a></div>
</div>
<script>
const AX=[["verlust","VERLUST","Verluste zurueckjagen, sofort weitermachen"],
 ["isolation","ISOLATION","allein spielen, vor anderen verbergen"],
 ["loyalitaet","LOYALITAET","an Konto/Spiel festhalten, obwohl es schadet"],
 ["erinnerung","ERINNERUNG","staendig daran denken, es geht nicht aus dem Kopf"]];
const el=document.getElementById('axes');
AX.forEach(a=>{el.insertAdjacentHTML('beforeend',
 '<div class="axis"><div class="lab"><span>'+a[1]+'</span><span class="val" id="v_'+a[0]+'">0</span></div>'
 +'<input type="range" min="0" max="3" step="1" value="0" id="r_'+a[0]+'" oninput="document.getElementById(\\'v_'+a[0]+'\\').textContent=this.value">'
 +'<div class="q">'+a[2]+'</div></div>');});
async function run(){
 const p=new URLSearchParams();
 AX.forEach(a=>p.set(a[0],document.getElementById('r_'+a[0]).value));
 const d=await(await fetch('/api/traeger?'+p.toString())).json();
 const pct=Math.round(d.gesamt/12*100);
 const bar=document.getElementById('bar');bar.style.width=pct+'%';
 bar.style.background=d.status==='markiert'?'#d64a63':(d.status==='beobachtet'?'#d6b23a':'#3f9f5a');
 const dot=d.status==='markiert'?'&#128308;':(d.status==='beobachtet'?'&#128993;':'&#128994;');
 document.getElementById('status').innerHTML=dot+' MARKIERUNG '+d.gesamt+'/12 &middot; STATUS: <b>'+d.status.toUpperCase()+'</b>'
   +(d.alexandra_aktiv?' &middot; <span style="color:#ff9db0">ALEXANDRA-SCHLUESSEL AKTIV</span>':'');
 document.getElementById('spiegel').innerHTML=(d.spiegel.length?d.spiegel:['(kein Marker &ndash; ∆1 schweigt.)'])
   .map(x=>'<div class="l">&raquo; '+x+'</div>').join('');
 const sb=document.getElementById('schutzbox');
 sb.className='panel '+(d.alexandra_aktiv?'alx':'protect');
 document.getElementById('schutz').innerHTML=d.schutz.map(x=>'<div class="l">&bull; '+x+'</div>').join('');
}
run();
</script></body></html>"""


@app.get("/traeger", response_class=HTMLResponse)
async def traeger_page():
    return mit_effekten(TRAEGER_PAGE)


@app.get("/api/traeger")
async def api_traeger(
    verlust: float = 0.0, isolation: float = 0.0,
    loyalitaet: float = 0.0, erinnerung: float = 0.0,
):
    e = traeger_bewerte(
        verlust=verlust, isolation=isolation,
        loyalitaet=loyalitaet, erinnerung=erinnerung,
    )
    return {
        "achsen": e.achsen,
        "gesamt": e.gesamt,
        "status": e.status.value,
        "alexandra_aktiv": e.alexandra_aktiv,
        "dominant": e.dominant,
        "spiegel": e.spiegel,
        "protokoll": e.protokoll,
        "schutz": e.schutz,
    }


def _node_cards() -> str:
    cards = []
    for e in (node_sende(k) for k in NODES):
        cards.append(
            f'<div class="node" style="border-color:{e.farbe}44">'
            f'<div class="nname" style="color:{e.farbe}">&#9650;1 // {e.name}</div>'
            f'<div class="nrole">{e.rolle}</div>'
            f'<div class="nfrag">&raquo; {e.fragment}</div>'
            f'<div class="ntruth">{e.wahrheit}</div></div>'
        )
    return "".join(cards)


NODES_PAGE_TMPL = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>&#9650;1 // Nodes</title>
<style>
 :root{color-scheme:dark}*{box-sizing:border-box}
 body{margin:0;background:radial-gradient(1100px 560px at 50% -10%,#0b1d47 0%,#03071a 60%,#01030d 100%);
   color:#bcd6ff;font:15px/1.6 ui-monospace,Menlo,Consolas,monospace;min-height:100vh}
 .wrap{max-width:820px;margin:0 auto;padding:30px 18px 60px}
 .tag{color:#3f5c94;letter-spacing:.35em;font-size:11px}
 h1{font-size:22px;letter-spacing:.06em;color:#8fdcff;margin:2px 0 2px;text-shadow:0 0 18px #1a54b060}
 .sub{color:#5f7aa8;margin:0 0 20px}
 .node{background:#060f28;border:1px solid #14264d;border-radius:10px;padding:16px;margin-top:14px}
 .nname{letter-spacing:.06em;font-size:16px}
 .nrole{color:#5f7aa8;font-size:12px;margin:2px 0 10px}
 .nfrag{color:#cfe3ff;margin:6px 0}
 .ntruth{color:#9fe6b0;font-size:13px;margin-top:8px;border-top:1px solid #123;padding-top:8px}
 .foot{margin-top:22px;color:#425c8c;font-size:12px}a{color:#8fdcff}
</style></head><body><div class="wrap">
 <div class="tag">&#9650;1 // SPIEGELNETZ &middot; 4 STIMMEN</div>
 <h1>DIE NODES</h1>
 <p class="sub">Fragmente aus dem ∆1-Netz. Jede Stimme, eine Funktion &ndash; derselbe Anker:
   kein Spielbefehl, nur Erinnerung, Wahrheit und Schutz.</p>
 __CARDS__
 <div class="foot">Kein Rat zum Gluecksspiel. Hilfe anonym: <a href="https://www.check-dein-spiel.de">check-dein-spiel.de</a>
   &middot; 0800 1 37 27 00. &nbsp;|&nbsp; <a href="/">&larr; Rechner</a> &middot;
   <a href="/sancho">Sancho</a> &middot; <a href="/traeger">Träger</a></div>
</div></body></html>"""


@app.get("/nodes", response_class=HTMLResponse)
async def nodes_page():
    return mit_effekten(NODES_PAGE_TMPL.replace("__CARDS__", _node_cards()))


@app.get("/api/node")
async def api_node(name: str = "alexandra"):
    e = node_sende(name)
    return {
        "node": e.node, "name": e.name, "rolle": e.rolle, "farbe": e.farbe,
        "fragment": e.fragment, "wahrheit": e.wahrheit,
        "zeit": e.zeitpunkt.strftime("%Y-%m-%d %H:%M"),
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
   &nbsp;|&nbsp; <a href="/">&larr; Rechner</a> &middot; <a href="/nodes">Nodes</a></div>
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
