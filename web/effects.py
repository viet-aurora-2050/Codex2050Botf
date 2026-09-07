"""∆1 // VHS + BOOT – wiederverwendbarer Dunkelblau-2050-Effekt-Layer.

`mit_effekten(html)` injiziert unmittelbar nach dem <body>-Tag:
  - eine kurze Terminal-Boot-Sequenz (∆1 SESSION INITIALISIERT ...),
  - einen VHS-Noise-/Scanline-Overlay (pointer-events:none).

Respektiert prefers-reduced-motion (dann kein Flackern, Boot sofort weg).
Klick/Taste ueberspringt die Boot-Sequenz.
"""

# Kein .format() auf diesem String – er wird NACH dem Templating injiziert,
# geschweifte Klammern im JS bleiben daher unveraendert.
_OVERLAY = """
<style>
 #d1-vhs{position:fixed;inset:0;pointer-events:none;z-index:9998;mix-blend-mode:screen;opacity:.05}
 #d1-vhs::before{content:"";position:absolute;inset:0;
   background:repeating-linear-gradient(0deg,rgba(140,220,255,.10) 0 1px,transparent 1px 3px)}
 #d1-vhs::after{content:"";position:absolute;inset:-50%;
   background:radial-gradient(circle,rgba(180,210,255,.25),transparent 60%);
   animation:d1n .5s steps(2) infinite}
 @keyframes d1n{0%{transform:translate(0,0)}50%{transform:translate(-2%,1%)}100%{transform:translate(1%,-2%)}}
 #d1-boot{position:fixed;inset:0;z-index:9999;background:#01030d;color:#8fdcff;
   font:13px/1.7 ui-monospace,Menlo,Consolas,monospace;padding:26px 20px;
   transition:opacity .6s;white-space:pre-wrap}
 #d1-boot .cur{background:#8fdcff;color:#01030d}
 #d1-boot small{color:#3f5c94}
 @media (prefers-reduced-motion:reduce){#d1-boot{display:none}#d1-vhs::after{animation:none}}
</style>
<div id="d1-vhs"></div>
<div id="d1-boot" role="status" aria-hidden="true"><span id="d1-boot-t"></span><span class="cur">&nbsp;</span>
<br><br><small>[ Klick / Taste zum Ueberspringen ]</small></div>
<script>
(function(){
 var lines=[
  "∆1 // SESSION INITIALISIERT",
  "KANON: geladen (6 Nodes, Register V2)",
  "NODE-LINK: ALEXANDRA · NODE 7 · ORPHEUS · V ......... [OK]",
  "SPIEGELNETZ: verbunden ueber tote Server ............ [OK]",
  "SPIELERSCHUTZ-KERN: aktiv ........................... [OK]",
  "ZUSTAND: 'Was erinnert wird, existiert weiter.'",
  ""
 ];
 var boot=document.getElementById('d1-boot');
 if(!boot) return;
 var t=document.getElementById('d1-boot-t'), i=0,j=0;
 function done(){ if(!boot)return; boot.style.opacity=0; setTimeout(function(){ if(boot)boot.remove(); },650);
   document.removeEventListener('click',done); document.removeEventListener('keydown',done); }
 document.addEventListener('click',done); document.addEventListener('keydown',done);
 function tick(){
   if(i>=lines.length){ setTimeout(done,500); return; }
   if(j<=lines[i].length){ t.textContent=lines.slice(0,i).join("\\n")+(i?"\\n":"")+lines[i].slice(0,j); j++; setTimeout(tick,14); }
   else { t.textContent+="\\n".slice(0,0); i++; j=0; setTimeout(tick,120); }
 }
 tick();
})();
</script>
"""


def mit_effekten(html: str) -> str:
    """Fuegt den Boot-/VHS-Overlay direkt nach <body> ein."""
    marker = "<body>"
    idx = html.find(marker)
    if idx == -1:
        return _OVERLAY + html
    einfuege = idx + len(marker)
    return html[:einfuege] + _OVERLAY + html[einfuege:]
