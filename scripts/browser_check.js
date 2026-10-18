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
  pruefe(tabs.length === 11 && konsistent, `Tabs (${tabs.length}): genau einer aktiv, aria-selected passt`);
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

  // 2b) PROFIL: rechnet, Selbst-Check beeinflusst nur die Faustregeln; ruhiger Modus schaltet Reize ab und bleibt gespeichert
  await p.click('nav button[data-t="profil"]');
  await p.evaluate(() => { pf_einsatz.value = '2'; pf_q1.value = '3'; pf_q3.value = '3'; });
  await p.click('#profil button.go');
  const pf = await p.textContent('#pf_out');
  pruefe(pf.includes('40.00 EUR pro Stunde') && pf.includes('Stufe erhöht') && pf.includes('„Gewinn ist fällig“ gibt es nicht'), 'PROFIL: Erwartungsverlust, Stufe und Aufklärung stimmen');
  await p.click('#ruhigbtn');
  pruefe(await p.evaluate(() => document.body.classList.contains('ruhig') && getComputedStyle(document.getElementById('d1-vhs')).display === 'none'), 'Ruhiger Modus: VHS-Rauschen aus');
  await p.reload({ waitUntil: 'networkidle' });
  pruefe(await p.evaluate(() => document.body.classList.contains('ruhig') && !document.getElementById('boot')), 'Ruhiger Modus bleibt nach Neuladen aktiv, ohne Boot-Sequenz');
  await p.click('#ruhigbtn');

  // 2c) AGB-SCAN in der Seite, Anleitung, Eingaben bleiben nach Neuladen erhalten
  await p.click('nav button[data-t="agb"]');
  await p.fill('#agb_text', 'Bonus 100 % bis 200 €. Mindesteinzahlung 20 €. Umsatz 35x (Bonusbetrag + Einzahlung) innerhalb von 30 Tagen. Max. Einsatz 5 €. Maximaler Gewinn 500 €.');
  await p.fill('#agb_einz', '50');
  await p.click('#agb_go');
  const agb = await p.textContent('#agb_out');
  pruefe(agb.includes('Umsatzfaktor: 35x') && agb.includes('„Bonus 100 % bis 200 €.“') && agb.includes('ANNAHMEN') && agb.includes('Mindestumsatz:       3500.00'), 'AGB-SCAN: Funde mit Beleg, Annahmen getrennt, Mindestumsatz (50 + 50) x 35 = 3500');
  await p.fill('#agb_text', '9'.repeat(20000));
  const t0 = Date.now(); await p.click('#agb_go');
  pruefe(Date.now() - t0 < 2000 && (await p.textContent('#agb_out')).startsWith('❌'), 'AGB-SCAN: 20.000 Ziffern blockieren nicht und werden sauber abgelehnt');
  await p.fill('#agb_text', 'Das Wetter ist schön.'); await p.click('#agb_go');
  pruefe((await p.textContent('#agb_out')).startsWith('❌'), 'AGB-SCAN: ohne Bonus wird nicht gerechnet');
  // AGB-Datenbank (docs/agb.json): Anbieter, Belege, Quelle, Rechnung mit eigener Einzahlung
  await p.click('nav button[data-t="agb"]');
  await p.waitForFunction(() => document.getElementById('agbdb_anb').options.length > 0);
  await p.selectOption('#agbdb_anb', 'jackpotpirat');
  const karte = await p.textContent('#agbdb_card');
  pruefe(karte.includes('Umsatzfaktor') && karte.includes('„') && karte.includes('jackpotpiraten.de') && karte.includes('Original prüfen'), 'AGB-Datenbank: Funde mit Beleg, Quelle und Hinweis sichtbar');
  pruefe(await p.evaluate(() => !document.getElementById('agbdb_rechnen').hidden), 'AGB-Datenbank: Rechnen-Knopf erscheint bei berechenbarem Bonus');
  await p.fill('#agb_text', ''); await p.fill('#agb_einz', '50'); await p.click('#agbdb_rechnen');
  const dbr = await p.textContent('#agb_out');
  pruefe(dbr.includes('Quelle: https://www.jackpotpiraten.de/bonus') && dbr.includes('Mindestumsatz:       2000.00') && !dbr.includes('Einzahlung nicht angegeben'), 'AGB-Datenbank: Bonus mit eigener Einzahlung gerechnet (50 € x 40 = 2000 €)');
  await p.selectOption('#agbdb_anb', 'betano');
  pruefe((await p.textContent('#agbdb_card')).includes('nicht lesbar') && (await p.textContent('#agbdb_card')).includes('nicht umgangen'), 'AGB-Datenbank: gesperrte Seiten werden ehrlich als nicht lesbar gezeigt');
  await p.fill('#agb_einz', '');
  await p.click('nav button[data-t="hilfe"]');
  pruefe((await p.textContent('#hilfe')).includes('Spin-Vorhersage'), 'SO GEHT\'S: Anleitung sichtbar');
  await p.click('nav button[data-t="agb"]'); await p.fill('#agb_einz', '77');
  await p.reload({ waitUntil: 'networkidle' });
  pruefe(await p.evaluate(() => document.getElementById('agb_einz').value === '77' && document.getElementById('agb').classList.contains('on')), 'Eingaben und zuletzt geöffneter Tab bleiben nach Neuladen erhalten');
  await p.click('nav button[data-t="hilfe"]'); await p.click('#hilfe button.go');
  pruefe(await p.evaluate(() => document.getElementById('agb_einz').value === '' && !localStorage.getItem('codex_eingaben')), 'Gespeicherte Eingaben lassen sich löschen');
  await p.click('nav button[data-t="spiele"]');
  pruefe(p.probleme.length === 0, 'AGB-SCAN/Anleitung/Speicher: keine Fehler');

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
