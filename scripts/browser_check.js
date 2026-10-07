#!/usr/bin/env node
/* Browser-Smoketest (Chromium via Playwright): echte Seiten, echte Klicks, keine Attrappen.
 *
 * Lokal:  npm i -g playwright   (oder in CI: npm install --no-save playwright@1.56.1)
 *         NODE_PATH=$(npm root -g) node scripts/browser_check.js
 * Startet einen kleinen statischen Server für docs/ – kein weiterer Dienst nötig.
 * Exit-Code 1 bei jedem Fehlschlag.
 */
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright');

const DOCS = path.join(__dirname, '..', 'docs');
const TYPEN = { '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.js': 'text/javascript' };
const server = http.createServer((req, res) => {
  const f = path.join(DOCS, decodeURIComponent(req.url.split('?')[0]).replace(/^\/+$/, 'index.html'));
  if (!f.startsWith(DOCS) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end('nicht gefunden'); }
  res.writeHead(200, { 'Content-Type': TYPEN[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});

const fehler = [];
const pruefe = (ok, text) => { console.log((ok ? 'OK     ' : 'FEHLER ') + text); if (!ok) fehler.push(text); };

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}/`;
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  const seite = async () => {
    const p = await (await browser.newContext({ viewport: { width: 400, height: 800 }, locale: 'de-DE' })).newPage();
    p.probleme = [];
    p.on('console', m => { if (['error', 'warning'].includes(m.type())) p.probleme.push(m.text()); });
    p.on('pageerror', e => p.probleme.push('pageerror: ' + e.message));
    p.on('response', r => { if (r.status() >= 400) p.probleme.push('HTTP ' + r.status() + ' ' + r.url()); });
    return p;
  };
  const oeffne = async (p, url) => { await p.goto(base + url, { waitUntil: 'networkidle' }); await p.click('body').catch(() => {}); await p.waitForTimeout(800); };

  // 1) Jede Seite lädt ohne Konsolen-/CSP-/Netzwerkfehler
  for (const url of ['index.html', 'sancho.html', 'akt4-decoder.html']) {
    const p = await seite(); await oeffne(p, url);
    pruefe(p.probleme.length === 0, `${url}: keine Konsolen-/CSP-/Netzwerkfehler ${p.probleme.slice(0, 2).join(' | ')}`);
  }

  // 2) Haupt-App: Tabs, Barrierefreiheit, Monte-Carlo
  const p = await seite(); await oeffne(p, 'index.html');
  const tabs = await p.$$eval('nav button', bs => bs.map(b => b.dataset.t));
  let konsistent = true;
  for (const t of tabs) {
    await p.click(`nav button[data-t="${t}"]`);
    const sel = await p.$$eval('nav button[aria-selected="true"]', bs => bs.map(b => b.dataset.t));
    const sichtbar = await p.$$eval('section.on', ss => ss.map(s => s.id));
    if (sel.length !== 1 || sel[0] !== t || sichtbar.length !== 1 || sichtbar[0] !== t) konsistent = false;
  }
  pruefe(tabs.length === 8 && konsistent, `Tabs (${tabs.length}): genau einer aktiv, aria-selected passt`);
  await p.click('nav button[data-t="spiele"]');
  pruefe(await p.evaluate(() => [...document.querySelectorAll('input,select,textarea')].every(i => i.labels && i.labels.length)), 'alle Formularfelder haben ein Label');

  await p.evaluate(() => { window.__lang = []; new PerformanceObserver(l => l.getEntries().forEach(e => window.__lang.push(e.duration))).observe({ entryTypes: ['longtask'] }); });
  await p.evaluate(() => { db_budget.value = '1000000'; db_einsatz.value = '1'; db_spins.value = '20000'; db_runs.value = '20000'; });
  await p.click('#db_go');
  await p.waitForFunction(() => document.getElementById('db_out').textContent.includes('MODELL-CHECK'), { timeout: 90000 });
  const laengster = await p.evaluate(() => Math.max(0, ...window.__lang));
  pruefe(laengster < 500, `Worst-Case-Simulation blockiert die Oberfläche nie länger als 500 ms (gemessen ${Math.round(laengster)} ms)`);
  pruefe((await p.textContent('#db_out')).includes('Sessions auf'), 'Rechenlimit wird dem Nutzer angezeigt');

  await p.evaluate(() => { db_budget.value = '100'; db_spins.value = '500'; db_runs.value = '3000'; });
  const lauf = async () => { await p.click('#db_go'); await p.waitForFunction(() => document.getElementById('db_out').textContent.includes('MODELL-CHECK')); return p.textContent('#db_out'); };
  const a = await lauf(), b = await lauf();
  pruefe(a === b, 'Simulation ist reproduzierbar (gleiche Eingaben, gleiches Ergebnis)');
  pruefe(/95%-KI/.test(a) && a.includes('ANNAHMEN') && a.includes('✓ stimmt überein'), 'Ausgabe: Konfidenzintervalle, Annahmen & Grenzen, Modell-Check bestanden');
  pruefe(p.probleme.length === 0, 'Haupt-App: keine Fehler während der Bedienung');

  // 3) Sancho bleibt funktionsfähig (unverändert, nur mitgetestet)
  const s = await seite(); await oeffne(s, 'sancho.html');
  await s.selectOption('#sanb', 'jackpotpirat'); await s.click('button.go'); await s.waitForTimeout(500);
  const t = await s.textContent('#spanel');
  pruefe(t.includes('Vorhersagewert 0') && t.includes('KEIN SPIELBEFEHL'), 'Sancho: Selbst-Entlarvung (Vorhersagewert 0, kein Spielbefehl) sichtbar');

  // 4) Decoder rechnet und zeigt Ergebnis
  const d = await seite(); await oeffne(d, 'akt4-decoder.html');
  await d.waitForFunction(() => document.getElementById('out').textContent.includes('LEVEL 1'), { timeout: 15000 });
  pruefe((await d.textContent('#out')).includes('KEINE Glücksspiel-Vorhersage'), 'Decoder: Ergebnis mit Hinweis „keine Vorhersage"');
  pruefe(d.probleme.length === 0, 'Decoder: keine Fehler');

  await browser.close(); server.close();
  console.log(fehler.length ? `\n${fehler.length} Prüfung(en) fehlgeschlagen` : '\nAlle Browser-Prüfungen bestanden');
  process.exit(fehler.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
