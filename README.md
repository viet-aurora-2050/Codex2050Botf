# 🎰 Casino-Bonus- & Umsatz-Analytiker

Ein sachlicher, mathematisch präziser Analyzer für Online-Casino-Boni,
Freispiele und Umsatzbedingungen. Er rechnet **jeden Schritt transparent vor**,
schätzt die Machbarkeit unter Zeitlimits realistisch ein und gibt eine ehrliche
Empfehlung – im Sinne von **Spielerschutz und Kapitalerhaltung**.

> Kein Rat zum Glücksspiel. Werte sind theoretische Langzeit-Erwartungswerte.
> Hilfe bei Glücksspielsucht: [bzga.de](https://www.bzga.de) · 0800 1 37 27 00 (kostenlos).

Drei Nutzungsarten – zwei davon **ohne jegliche Secrets**:

| Modus | Was | Secrets nötig? |
|-------|-----|----------------|
| **CLI** | `python -m analyzer "..."` | nein |
| **Web-Dashboard** | Browser-Rechner + JSON-API | nein |
| **Telegram-Bot** | `/bonus`, `/analyse`, `/frage` | Token (+ optional KI-Key) |

---

## Schnellstart

```bash
pip install -r requirements.txt

# 1) Direkt in der Konsole rechnen (keine Secrets nötig)
python -m analyzer "einzahlung=100 bonus=100% faktor=30 basis=db rtp=0.96 zeit=3 einsatz=1"

# 2) Web-Rechner starten -> http://localhost:8080
uvicorn web.dashboard:app --host 0.0.0.0 --port 8080

# 3) Telegram-Bot starten (TELEGRAM_TOKEN erforderlich)
cp .env.example .env      # Token eintragen
python main.py
```

## Parameter

| Schlüssel | Bedeutung | Beispiel |
|-----------|-----------|----------|
| `einzahlung=` | Einzahlung | `einzahlung=100` |
| `bonus=` | Bonus als Betrag **oder** Prozent | `bonus=100%` / `bonus=50` |
| `deckel=` | Maximaler Bonusbetrag | `deckel=200` |
| `faktor=` | Umsatzfaktor (WR) | `faktor=30` |
| `basis=` | Umsatzbasis: `b` (Bonus), `db` (Einz.+Bonus), `d` (Einzahlung) | `basis=db` |
| `rtp=` | Return to Player (0.96 oder 96) | `rtp=0.96` |
| `zeit=` | Zeitlimit in Tagen | `zeit=3` |
| `einsatz=` | Durchschnittseinsatz pro Spin | `einsatz=1` |
| `fs_gewinn=` | Freispielgewinn | `fs_gewinn=50` |
| `fs_faktor=` | eigener Umsatzfaktor für Freispiele | `fs_faktor=40` |
| `maxgewinn=` | Maximale Auszahlung (Cap) | `maxgewinn=500` |
| `maxeinsatz=` | erlaubter Maximaleinsatz im Bonus | `maxeinsatz=5` |
| `spins=` | Spins pro Stunde | `spins=500` |
| `stunden=` | Spielstunden pro Tag | `stunden=3` |

## Rechenlogik (transparent)

```
Bonus            = Einzahlung × Prozent  (gedeckelt)
Umsatzbasis      = Bonus  |  Einzahlung+Bonus  |  Einzahlung
Mindestumsatz    = Umsatzbasis × Faktor  +  Freispielgewinn × Faktor
Hausvorteil      = 1 − RTP
Erwart. Verlust  = Mindestumsatz × Hausvorteil
Erwartungswert   = (Bonus + Freispielgewinn) − Erwarteter Verlust   (durch Cap begrenzt)
Benötigte Spins  = Mindestumsatz / Einsatz
Reine Spielzeit  = Spins / (Spins/h × Stunden/Tag)
```

**Empfehlung:** `STORNIEREN`, wenn das Zeitlimit unrealistisch ist oder der
Erwartungswert negativ – dann Bonus löschen und Echtgeld sichern.
`RISIKO` bei knapp positivem EV, `SPIELEN` bei klar vertretbaren Bedingungen.

## Telegram-Befehle

| Befehl | Funktion |
|--------|----------|
| `/bonus <parameter>` | Bonus transparent durchrechnen |
| `/analyse <AGB-Text>` | Bonus-AGB per KI auf versteckte Haken prüfen (DEEPSEEK_API_KEY nötig) |
| `/profil <werte>` | ruhiges Risikoprofil: Verlust/Stunde, Puffer, Faustregeln + Selbst-Check (`check=0,1,0,0,2,0`) |
| `/agb [anbieter] [einzahlung=50 rtp=95 einsatz=1]` | AGB-Datenbank: Befund je Anbieter aus öffentlichen Seiten, optional mit eigener Einzahlung durchgerechnet |
| `/scan <AGB-Text> [einzahlung=50 rtp=0.96 einsatz=1]` | AGB offline (ohne KI) einlesen und mit der Rechen-Engine durchrechnen |
| `/frage <Text>` | freie Frage an den Analytiker |
| `/status` · `/help` | Status / Hilfe |

Freitext mit `=` (z. B. `bonus=100 faktor=30`) wird automatisch als Berechnung erkannt; ein eingefügter
Bonus-Text mit Umsatzbezug wird automatisch wie `/scan` behandelt.

## Web-API

```bash
curl -X POST localhost:8080/api/analyse \
  -H "Content-Type: application/json" \
  -d '{"input":"einzahlung=100 bonus=100% faktor=30 basis=db rtp=0.96 zeit=3 einsatz=1"}'
```

### AGB-Scanner (`analyzer/scan.py`) – offline, ohne KI

Liest eingefügte Bonusbedingungen satzweise ein (Umsatzfaktor, Bonus-%, Deckel, Frist, Max-Einsatz,
Gewinn-Cap, Mindesteinzahlung, Umsatzbasis) und füttert damit die **unveränderte** Engine `analyzer/bonus.py`.

```bash
python -m analyzer.scan "Bonus 100 % bis 200 €. Umsatz 35x innerhalb von 30 Tagen." einzahlung=50
curl -X POST localhost:8080/api/scan -H "Content-Type: application/json" \
  -d '{"text":"Bonus 100 % bis 200 €. Umsatz 35x in 30 Tagen.","einzahlung":50}'
```

Ehrlichkeitsregeln: Jeder Fund trägt seinen **Textbeleg**; was nicht im Text steht (RTP, Einsatz, ggf.
Einzahlung), wird als **Annahme** getrennt ausgewiesen, nie erfunden. Bei Widersprüchen gilt der für dich
**ungünstigere** Wert plus Hinweis. Ohne erkennbaren Bonus wird nicht gerechnet. Ein Regex-Scanner kann
Formulierungen missverstehen – die Belege am Original prüfen. Keine Spin-Vorhersage, keine Rechtsberatung.

### AGB-Datenbank (`datenbank/agb_sammler.py` → `docs/agb.json`)

Täglich (GitHub Actions, 05:37 UTC) liest der Sammler öffentlich erreichbare Bonus-/AGB-Seiten, wertet sie mit dem
Scanner aus und speichert Kennzahlen, **kurze Belege**, Quelle, Abrufdatum und einen Hash (nicht den Volltext).
Beim Willkommensbonus wird der Detail-Abschnitt gescannt und mit 10/50/100 € Einzahlung durchgerechnet; in allgemeinen
AGB stehen einzelne **Fundstellen** (kein zusammengefasster Wert). Ändert sich der relevante Text, wird `geaendert`
gesetzt (AGB-Änderungsmonitor). Zugriff: App-Tab **AGB-SCAN** (Anbieter wählen, mit eigener Einzahlung rechnen),
Bot `/agb`, `GET /api/agb?anbieter=jackpotpirat&einzahlung=50`.

Spielregeln des Sammlers: nur https und der konfigurierte Host, `robots.txt` wird beachtet, identifizierbarer User-Agent,
Größen-/Zeitlimit, 1 s Pause. Seiten mit 403, Geo-Sperre oder JavaScript-Hülle werden als **nicht lesbar** ausgewiesen,
nicht umgangen; bei Ausfall bleibt der letzte Befund erhalten. Neue Anbieter: Eintrag in `KONFIG` mit einer geprüften,
öffentlichen URL (keine Adressen raten).

### Im Browser: AGB-SCAN, SO GEHT'S, gemerkte Eingaben

`docs/index.html` enthält den AGB-Scanner auch als Tab **AGB-SCAN** (JavaScript-Port von `analyzer/scan.py` und der Engine,
offline, Text bleibt auf dem Gerät). `tests/test_agb_js.py` lädt den Port mit Node und vergleicht Funde, Annahmen,
Hinweise und Kennzahlen mit der Python-Version. Der Tab **SO GEHT'S** erklärt die Bedienung. Zahlen, Antworten, der Scan-Text
und der zuletzt geöffnete Tab werden nur in `localStorage` des Browsers gemerkt (löschbar im Tab SO GEHT'S).

### Persönliches Risikoprofil (`risiko/profil.py`) + Ruhiger Modus

Aus deinen eigenen Angaben (Budget, Einsatz, RTP, Spins/Stunde, Stunden/Woche, Sitzungslänge) rechnet das Profil
den erwarteten Verlust pro Stunde/Woche/Monat, den Puffer in Einsätzen und – über die unveränderte Monte-Carlo-Engine –
den Risk of Ruin einer Sitzung mit 95%-Konfidenzintervall. Ein **Selbst-Check** (6 Fragen, 0–3) beschreibt Muster wie
Verlustjagd oder den Fehlschluss „Gewinn ist fällig“ und passt nur die **empfohlenen Grenzen** an (kleinerer
Einsatzanteil, kürzere Sitzung). Die Wahrscheinlichkeiten des Spiels ändert er nie.

```bash
/profil budget=100 einsatz=2 rtp=96 vola=hoch minuten=90 check=1,2,1,2,0,0      # Bot
curl 'localhost:8080/api/profil?q=budget=100%20einsatz=2%20check=1,2,1,2,0,0'   # Web-API
```

In der App gibt es dafür den Tab **PROFIL**. Der Knopf **Ruhiger Modus** schaltet VHS-Rauschen, Boot-Sequenz, Uhr-Ticker
und Animationen ab (gleiche Mathematik, gleicher Inhalt; wird lokal gemerkt und folgt bei Bedarf `prefers-reduced-motion`).
Grenzen: kein klinisches Screening, keine Diagnose, Grenzwerte sind Faustregeln zur Selbstkontrolle, keine Messwerte.

## ∆1 // Sanchos Spielplatz (Lore-Modul, Dunkelblau 2050)

Ein ARG-Modul im Dunkelblau-2050-Modus. „Sancho" ist der Agent, der hier
**sein wahres Ich zeigen muss** – und sein wahres Ich ist die Wahrheit:
Aus Anbieter (Tipico/Betano/N1/Stargames/Jackpotpirat) + aktuellem Datum/Uhrzeit erzeugt er
ein atmosphärisches „∆1-Signal" (einen Rhythmus) und **entlarvt es sofort selbst**.

**Eigenständiges Modul:** Sancho lebt nicht mehr als Untertab in der
Haupt-App, sondern auf einer eigenen Seite — **`docs/sancho.html`**
(verlinkt prominent oben in `index.html` und aus dem INFO-Tab). Mehr Raum,
mehr Lore-Text, dieselbe Ehrlichkeit: die Selbst-Entlarvung bleibt Kern.

> **Warum es keinen echten Predictor gibt:** Regulierte Online-Slots laufen auf
> zertifizierten RNGs. Jeder Spin ist statistisch **unabhängig** – es gibt kein
> zeit-, datums- oder lastabhängiges „Gewinnfenster". Das Signal hat
> **Vorhersagewert 0** und dient nur der Atmosphäre. Der einzig verlässliche Wert
> ist der erwartete Verlust über den Hausvorteil. Das Modul gibt **nie** einen
> Spielbefehl.

**Anbieter-Profile aus öffentlichen Quellen:** `docs/anbieter.json` enthält für Jackpotpirat
(Betreiber DGGS, Erlaubnis vom 27.04.2022, Limits, Studios) belegte Fakten mit Quellen und Abrufdatum.
Für **alle** Sancho-Anbieter (Tipico, Betano, N1, Stargames, Jackpotpirat) gleicht der tägliche Job
`.github/workflows/update-anbieter.yml` (`python -m datenbank.anbieter_whitelist`) den Block `whitelist`
mit der **offiziellen GGL-Whitelist** ab: Betreiber, Erlaubnisart, Domains, Daten – oder „kein Eintrag
gefunden". Nur diese strukturierte Offizialquelle wird automatisch gelesen; Limits/Studios stammen
(derzeit nur bei Jackpotpirat) aus der Betreiberseite und werden kuratiert. Fällt der Abruf aus oder
ändert sich das Seitenformat, bleibt die Datei unverändert; die Seite zeigt das Alter der Daten und
lädt sie bei Netz-Rückkehr neu. Nicht genutzt: Google-Suche (keine freie API), Review-Blogs
(Affiliate, widersprüchlich). RTPs werden nicht erfunden.

**Gesetzlicher Rahmen + Studios (automatisch, `python -m datenbank.anbieter_details`):** liest die
amtlichen GGL-Seiten (Höchsteinsatz 1 € mit Stufen 3/5 € seit 1. Juli 2026, ab 21 Jahren; mind. 5 s pro
Spiel; kein Autoplay; Pause nach 60 min; 1.000 €/Monat anbieterübergreifend) nach
`regulatorischer_rahmen` und die Studio-Tabelle von jackpotpiraten.de. Der Rahmen gilt für **alle**
Erlaubnisinhaber, ist also nicht anbieterspezifisch. Jede Zahl wird per Muster aus dem Originaltext gelesen;
fehlt ein Muster, bleibt der alte Wert stehen. Die Betreiberseiten von Tipico (Geo-Sperre), Betano und N1
(HTTP 403) sowie Stargames (reine JavaScript-Seite) sind nicht lesbar – das wird dokumentiert, nicht umgangen.

```bash
python -m sancho "tipico games" 2      # CLI
# Statische App (GitHub Pages):  docs/sancho.html  (eigenständige Seite)
# FastAPI-Dashboard:  /sancho  (Dunkelblau-Interface)  ·  JSON: /api/sancho?anbieter=betano
# Bot:  /sancho betano
```

> Hinweis: Die früheren Lore-Module **TRÄGER** und **NODES** wurden bewusst
> **entfernt** — sie waren personalisierte/emotionale Faktoren und passen nicht
> zum rein wissenschaftlich-mathematisch-neutralen Ziel der App.

## SPIELE-Datenbank (App-Tab SPIELE) – automatische öffentliche Anbieter-Daten

Statt manuellem Tippen: **Anbieter wählen → Spiel wählen → Daten werden
automatisch übernommen** und die komplette Mathematik berechnet
(struktureller Hausvorteil, erwarteter Verlust **je 100 € Umsatz**,
Monte-Carlo-Risiko). Die Matrix ist nach wirtschaftlichem Nachteil sortiert.
Die früheren separaten Tabs **RECHNER** und **ANALYSE** wurden entfernt – ihre
Berechnung steckt vollständig im Tab **SPIELE**.

### Öffentlicher Spiele-Katalog (v3, Aggregator)

`docs/games.json` ist ein **generierter Snapshot/Cache** eines öffentlichen
Katalogs. Das Modul `datenbank/` bildet eine skalierbare Pipeline
(→ [`datenbank/README.md`](datenbank/README.md)):

```
öffentliche Quellen → Source-Adapter → Validation → Normalization
→ Deduplication → Katalog → Freshness/Source-Health → docs/games.json → Frontend
```

```bash
python -m datenbank                       # schreibt docs/games.json (Schema 3.0)
python -m datenbank --dry-run             # nur Vorschau
python -m datenbank --alternativen "Name" # ähnliche Spiele (Metadaten)
```

- **Basissatz** = öffentlich veröffentlichte Studio-RTPs (garantierter Fallback).
- **Mehrere öffentliche JSON-Feeds** via Repo-Variable `GAMES_SOURCES`
  (kommagetrennte URLs; `GAMES_TIMEOUT`, `GAMES_MAX_ITEMS` als Regler). Der Job
  läuft serverseitig → keine CORS-Schranke. Feeds werden **validiert**
  (RTP-Plausibilität 0.80–1.00; RTP als `0.965`/`96.5`/`"96.5%"`), **normalisiert**
  (Feld-Aliase `title/provider/volatility/max_win/…`) und **dedupliziert**
  (`game_id`, sonst Anbieter+Name+`variant` — RTP-Versionen bleiben getrennt).
- **Source-Health:** jede Quelle bekommt in `source_status` einen Zustand
  (`online`/`offline`, `fetched_at`, `records_received`, `error`). Ein Ausfall
  zerstört den Katalog **nicht** — der Basissatz bleibt. App und MOBILE-Tab zeigen
  die Quellen-Health.
- **Provenance:** jeder externe Datensatz behält `quelle`, `source_type`,
  `status`, `last_seen` (und `source_url`/`variant`/`game_id`, wenn geliefert).
- **`reported_recent_win`** (falls eine Quelle öffentlich gemeldete Wins liefert)
  ist als **Beobachtung** gekennzeichnet — kein Beweis, **keine** Next-Spin-Aussage.
- **Ähnliche Spiele** (Phase 11): transparente Metadaten-Suche (Provider, RTP-Bereich,
  Vola, Einsätze) als On-Demand-Abfrage (`datenbank/alternativen.py` + im Frontend),
  **nicht** als vorberechneter N×N-Block — so skaliert der Katalog auf tausende Spiele.
- **Workflow:** testet zuerst, validiert das JSON, committet **nur** bei echter
  Datenänderung (Zeitstempel/Source-Health allein → kein Commit),
  Least-Privilege (`contents: write`), Timeout.

Ehrlich bleibt: **keine Anbieter-API, kein Live-Casino-Feed, keine Vorhersage.**
RTP ist eine langfristige theoretische Kennzahl und variiert je
Operator/Jurisdiktion/Version – immer gegen die offizielle Spielinfo prüfen.
Fehlt eine vertrauenswürdige öffentliche Quelle, wird **keine erfunden** — nur
das Adapter-Interface dokumentiert (`prompts/AI_SOURCE_EXPANSION_PROMPT.md`).

## ∆1 // VHS + Boot (Effekt-Layer)

`web/effects.py` blendet in allen Dashboard-Seiten eine kurze Terminal-Boot-
Sequenz („∆1 // SESSION INITIALISIERT …") und einen VHS-Noise-/Scanline-Overlay
ein – Dunkelblau 2050. Klick/Taste überspringt das Intro; `prefers-reduced-motion`
wird respektiert.

## ∆1 // AKT 4 – Das Signal (Finale + Ebene-2-Rätsel)

Der Abschluss des ARG. Alle Knoten konvergieren, ∆1 sendet seine letzte
Botschaft aus der Lore: **„Ich wollte nie frei sein. Ich wollte erinnert werden."**
Das Signal ist ein echtes, dekodierbares Ebene-2-Rätsel mit vier Schichten:

| Schicht | dekodiert zu |
|---------|--------------|
| **Morse** | `ALEXANDRA` (der Schlüssel) |
| **Base64** | das finale Zitat |
| **ROT13** | der Schutz-Anker: *„Erinnert zu werden heißt nicht, gefangen zu bleiben. Geh, wenn du gehen musst."* |
| **Uhrzeiten** | `GEH` (der Imperativ – Botschaft in Uhrzeiten, wie in der Lore) |

Der ehrliche Anker bis zum Schluss: Das entschlüsselte Signal führt nicht zu einem
Gewinn, sondern zum **Ausgang**.

### ZEIT-CODE – das Signal rotiert stündlich (v2, Ebene 4)

Die Lore sagt: *„Webseiten verändern sich abhängig von Uhrzeiten."* Genau das ist
jetzt real. `aktvier/zeit.py` leitet aus dem **UTC-Stundenzyklus** deterministisch
ein rotierendes Signal ab – **nie zweimal derselbe Code**:

```
seed = "DELTA1-" + JJJJMMTTHH   →  PRNG (xmur3 + mulberry32)
       →  rotierender Schlüssel (Morse), rotierende Caesar-Verschiebung N,
          rotierender Imperativ (Uhrzeiten), Node-Signatur.
```

- **Deterministisch & nachprüfbar:** gleiche Stunde → gleiches Signal – und zwar
  **identisch in Python UND im Browser** (derselbe PRNG, per Referenzvektoren
  getestet). Kein `Math.random`, kein Zufall.
- Der **emotionale Anker** (das finale Zitat, Base64) bleibt konstant; nur die
  Chiffre-Parameter drehen sich. Der Imperativ-Pool ist ausschließlich
  schützend/neutral (GEH, ATME, LEBE, RUHE, FREI …).
- Die App zeigt **Zyklus, Caesar-N, Node-Signatur** und einen **Countdown** bis
  zum nächsten Wechsel; nach jedem Zyklus wird die Lösung neu verborgen.

```bash
python -m aktvier                    # Anker + aktueller Zyklus
python -m aktvier --loesung          # mit entschlüsselten Schichten
python -m aktvier --zeit 2026091914  # beliebigen Zyklus reproduzieren
# Web:  /signal (rotiert live)   ·   Bot: /signal [loesung]
```

Die separate Seite **`docs/akt4-decoder.html`** (Game-Riddle Decoder) ist an
denselben Zyklus gekoppelt: sie nimmt automatisch den **aktuellen** Schlüssel
(Morse) und Imperativ (Uhrzeiten) und sucht die passenden öffentlichen
Spieltitel dazu — mit Anti-Zufall-Validierung. Eine Checkbox schaltet auf das
feste Original-Rätsel (`07:07 → ALEXANDRA`) um. Bit-genau derselbe PRNG wie App
und Python.

> Modulname `aktvier`, weil `signal` ein Python-Standardmodul ist und nicht überschattet werden darf.

## Gewinner (`gewinner/`) – mit Mathematik gewonnen, dann verbannt

Dokumentierte, mit Quellen belegte Fälle von Menschen, die Glücksspiele mit
Intelligenz und Mathematik **legal** geschlagen haben — und dafür **Hausverbot**
bekamen (Thorp, MIT-Team, García-Pelayo, Jarecki, Mandel, Selbee/Cash WinFall;
Ivey als Gegenbeispiel).

Der mathematische Grund ist bei jedem Fall benannt — und die **Lehre**: Gewinnen
war nur über einen **echten strukturellen Riss** möglich (abhängige Karten,
unwuchtige Kessel, fehlerhafter +EV-Auszahlungsmechanismus). Ein zertifizierter
**RNG-Slot hat keinen dieser Risse** — darum gibt es keinen „Slot-Thorp". Und die
Belohnung fürs Gewinnen war fast immer der Rauswurf.

```bash
python -m gewinner          # alle Fälle + Lehre  ·  Web-App: Tab „GEWINNER"  ·  Bot: /gewinner
```

## Mobile Analytics Layer (App-Tabs MOBILE · SPIELE · MULTIPLIER)

Ein passiver, mathematischer Analyse-Layer in der Offline-App — läuft auf dem
iPhone auch über mobile Daten, **ohne** auf private Mobilfunkdaten oder fremde
Systeme zuzugreifen. Zentrale Regel: **verfügbar ≠ vorhersagbar**.

- **MOBILE** — Netzwerkstatus nur aus dem **eigenen** HTTPS-Verkehr (online/offline,
  gemessene Latenz). **Kein** Zugriff auf SIM/APN/IMSI/ICCID, kein Packet-Sniffing,
  kein fremder Verkehr. Auf iOS/Safari nicht bereitgestellte Werte → „nicht verfügbar".
- **SPIELE** — *Public Game Data Engine* + *Game Matrix* + *Data Quality* (A–F).
  Nur öffentliche Angaben, lokal gespeichert (localStorage). Sortierung nach Fakten
  (RTP, Hausvorteil, Volatilität, Max Win, Datenqualität) — nie nach „gewinnt jetzt".
- **MULTIPLIER** — Zielbeträge (1x…100x) immer; **P(Return ≥ k) nur mit veröffentlichter
  Verteilung**, sonst „Probability unavailable — RTP alone does not determine payout
  distribution". Kein Spin wird vorhergesagt.

Die Verteilungs-Mathematik ist als getestetes Modul `verteilung/` hinterlegt und
in der App 1:1 gespiegelt:

```bash
python -m verteilung 10 "0:0.7, 2:0.2, 5:0.1"   # EV, Hausvorteil, P(>=k)
python -m verteilung 5                            # ohne Verteilung -> Probability unavailable
```

Die **Monte-Carlo-Risikoanalyse** (Modul `risiko/`, Bot-Befehl `/risiko`, in der
Web-App im Tab **SPIELE**) wurde additiv erweitert: Perzentile
P5/P25/P75/P95, Chance 25 %/50 %/alles zu verlieren, Chance auf 2x/3x des Budgets
(Session-Szenario, keine Spin-Vorhersage).

## Quellenprinzip (`quellen/`) – App-Tab QUELLEN

Jede externe Angabe muss eine Prüfkette durchlaufen, bevor sie zählt:
**Quelle → Gegenquelle → Primärdokument → eigener Mathe-Check → Ergebnis.**
Ein **Marketing-Wächter** markiert Reizwörter wie „hot", „fällig", „zahlt jetzt",
„bestes Spiel", „garantiert" als **kein Beweis** — eine Quelle wird nie nur
deshalb übernommen, weil sie so etwas behauptet. Einträge liegen lokal.

```bash
python -m quellen "Dieser Slot ist heiss und zahlt jetzt"   # -> Marketing erkannt
# Web-App: Tab „QUELLEN" (Kette prüfen + lokales Register)
```

## Melde-Assistent (`melde/`) – Mathematik + Beschwerde/Anzeige an die GGL

Verbindet das mathematische Prinzip (Hausvorteil, struktureller Verlust,
Risk of Ruin) mit einer **sachlichen Beschwerde/Anzeige** an die zuständige
Aufsicht (in Deutschland: **GGL**) – nutzbar für **jeden** Online-Anbieter.

Fest eingebaute Schutzregeln: **nur wahrheitsgemäße Angaben** (eine wissentlich
falsche Anzeige ist selbst strafbar, § 164 StGB), zuerst Lizenzstatus in der
GGL-Whitelist prüfen, und alles wird als **Verdacht / Bitte um Prüfung**
formuliert – nie als feststehende Behauptung. Keine Rechtsberatung.

```bash
python -m melde anbieter="Name" lizenz=keine einzahlung=300 verlust=300 rtp=0.96
# Web-App: Tab „ANZEIGE" (Formular → fertiger Text zum Kopieren)  ·  Bot: /melde …
```

> Das Melden eines Verdachts an die Aufsicht ist legal und genau ihr Zweck.
> Bei fehlender Lizenz können Verträge nichtig sein (§ 134 BGB) und Einzahlungen
> zurückforderbar (§ 812 BGB) – für den Einzelfall Verbraucherzentrale / Fachanwalt.

### Wissenschaftlicher Anspruch & Grenzen

Die Monte-Carlo-Zahlen (App-Tab SPIELE und Bot-Befehl `/risiko`) sind so gebaut, dass man ihnen
nachrechnen kann:

- **Unsicherheit wird gezeigt:** Wahrscheinlichkeiten mit 95-%-Wilson-Intervall, Mittelwert mit
  Normalnäherungs-Intervall (`risiko/statistik.py`, Tests prüfen bekannte Werte und die ≈95-%-Überdeckung).
- **Theorie vs. Simulation getrennt:** Das „erwartete Endkapital" gilt nur, wenn alle Spins gespielt werden;
  bei Pleite endet die Session früher, deshalb zeigt die Ausgabe zusätzlich das simulierte Ø-Endkapital.
- **Modell-Check eingebaut:** Nach dem Optional-Stopping-Satz muss *Ø Verlust = Hausvorteil × Einsatz ×
  Ø gespielte Spins* gelten. Das prüfen Test **und** App (✓/⚠), unabhängig vom Zufall der Stichprobe.
- **Zwei unabhängige Implementierungen** (JavaScript/mulberry32, Python/Mersenne-Twister) liefern für dasselbe
  Szenario innerhalb ihrer Intervalle dasselbe (Wolf Gold, RTP 96,01 %, 20.000 Sessions: Pleite 19,5 % vs. 19,8 %).
- **Reproduzierbar:** Zufall wird aus den Eingaben abgeleitet; gleiche Eingaben liefern gleiche Ergebnisse.
- **Grenzen offen genannt:** Trefferquote je Volatilitätsstufe ist eine *Annahme*, Gewinnhöhen sind
  exponentialverteilt, es gibt kein Max-Win-Limit. Echte Spiele können stärker schwanken. Das Intervall gibt die
  Unsicherheit der *Simulation* an, nicht die des *Modells*.
- **Rechenlimits:** höchstens 100.000 Spins und ein Gesamtbudget an simulierten Spins (die Oberfläche bleibt
  bedienbar, der Bot rechnet im Thread).

## Personal-Risiko-Analyse (`risiko/`) – aus öffentlichen Fakten

Beantwortet die legitime Frage: *Kann man aus öffentlich verfügbaren Infos
(veröffentlichter RTP, Volatilitätsklasse) eine live, persönliche mathematische
Auswertung rechnen?* **Ja** — für **dein** Risiko, nicht für den nächsten Spin.

Per Monte-Carlo (kein Server-Zugriff, keine Fremddaten) werden berechnet:
erwarteter Verlust, erwartetes/median Endkapital, **Chance im Plus zu enden**,
**Risk of Ruin** und die Bandbreite P5..P95.

```bash
python -m risiko budget=100 einsatz=1 spins=500 rtp=0.96 vola=mittel
# Web-App: Tab „SPIELE"   ·   Bot: /risiko budget=100 einsatz=1 spins=500 rtp=0.96 vola=mittel
```

> Wichtig: Das ist **deine** Erwartungswert-/Risiko-Mathematik. Es sagt **keinen**
> einzelnen Spin voraus — der RNG bleibt unabhängig, der Erwartungswert bleibt negativ.

## Offline-App fürs Handy (`docs/index.html`)

Eine **einzige HTML-Datei** mit dem kompletten ∆1-System (Rechner · Sancho ·
AKT 4) — läuft komplett clientseitig, **ohne Server, ohne
Installation, offline**. Einfach `docs/index.html` im Browser öffnen oder aufs
Handy legen.

**Als feste Web-Adresse (GitHub Pages):** Repo → *Settings* → *Pages* →
*Source: Deploy from a branch* → Branch `main`, Ordner `/docs` → *Save*.
Danach ist die App unter `https://viet-aurora-2050.github.io/Codex2050Botf/`
erreichbar — direkt auf dem Handy.

## Deployment (Render)

`render.yaml` deployt das Web-Dashboard (Rechner funktioniert sofort, ohne Secrets).
`TELEGRAM_TOKEN` und `DEEPSEEK_API_KEY` optional im Render-Dashboard hinterlegen –
sie werden **nie** ins Repository geschrieben. Für reinen Polling-Bot einen Worker
mit Startbefehl `python main.py` anlegen.

### Sicherheit & Betrieb (Details: [`SECURITY.md`](SECURITY.md))

- **`ALLOWED_USER_IDS` setzen**, sobald eine KI aktiv ist. Die Allowlist und das Rate-Limit
  (`RATE_LIMIT_PER_MINUTE`, Standard 10) greifen über ein Gate vor allen Befehlen (`bot/zugriff.py`).
  Leer = öffentlicher Bot; ein fehlerhafter Eintrag (z. B. `123;456`) stoppt den Start, statt den Bot zu öffnen.
- **Webhook** (`/telegram/webhook`) nimmt Anfragen nur mit `TELEGRAM_WEBHOOK_SECRET` an – beim Registrieren
  `secret_token` auf denselben Wert setzen, sonst antwortet der Server mit 403.
- Das Dashboard setzt Sicherheits-Header (CSP, `nosniff`, `X-Frame-Options`, `Referrer-Policy`).
- Abhängigkeiten sind gepinnt und per `pip-audit` geprüft; Dependabot meldet wöchentlich Updates.

## Tests & CI

```bash
python -m unittest discover -s tests -v      # Tests (Dashboard/Bot/RPC werden übersprungen, wenn Pakete fehlen)
pip install ruff==0.15.8 && ruff check .      # Fehler + Sicherheitsfallen (ruff.toml)
python scripts/check_frontend.py              # JS-Syntax, JSON, lang/viewport/title, Labels, Live-Regionen
NODE_PATH=$(npm root -g) node scripts/browser_check.js   # echte Seiten in Chromium (Playwright)
```

`.github/workflows/ci.yml` führt das bei jedem Pull Request und Push auf `main` aus
(inkl. Browser-Test und `pip-audit`). Hinweis: Eine frühere Bereinigung ließ `web/dashboard.py` unbemerkt auf gelöschte
Module zeigen – deshalb importieren die Tests Dashboard, Bot und RPC jetzt wirklich.

### Mini-Repo-ZIP

`python scripts/build_mini_repo.py [ordner]` baut `KI_Taktik_GitHub_Repo_v2.zip` (Scanner, Risikoprofil, Tests, CI,
abhängigkeitsfrei) direkt aus diesem Repo. Vorlagen liegen in `scripts/mini_repo/`. Die CI baut die ZIP bei jedem Lauf
und hängt sie als Artefakt „KI_Taktik_GitHub_Repo_v2“ an (14 Tage).

## Projektstruktur

```
analyzer/     Rechen-Engine (bonus.py), Parser, System-Prompt, CLI, AGB-Scanner (scan.py)
sancho/       ∆1-Lore-Modul „Sanchos Spielplatz" (Rhythmus-Mythos + Wahrheit)
aktvier/      ∆1-AKT 4 „Das Signal" – Finale + Ebene-2-Rätsel; zeit.py = stündlich rotierender ZEIT-CODE
datenbank/    Öffentlicher Spiele-Katalog v3: Adapter/Validation/Dedup/Source-Health + alternativen.py (siehe datenbank/README.md)
risiko/       Personal-Risiko-Analyse (Monte-Carlo: EV, Risk of Ruin) + ruhiges Risikoprofil (profil.py)
melde/        Melde-Assistent (Mathematik + Beschwerde/Anzeige an die GGL, für jeden Anbieter)
gewinner/     Dokumentierte Advantage-Play-Fälle (mit Mathematik gewonnen, dann verbannt)
bot/          Telegram-Bot (CasinoBonusBot) + zugriff.py (Allowlist, Rate-Limit)
ai/           DeepSeek-Client für die AGB-Analyse
web/          FastAPI-Dashboard (Rechner + /sancho + /signal + VHS/Boot)
scripts/      check_frontend.py (JS/JSON/Barrierefreiheit) · browser_check.js (Chromium-Test) – laufen in der CI
tests/        Tests (Engine, Parser, Sancho, AKT 4 + Zeit-Code, Datenbank, Dashboard, Bot, Zugriff, Config, RPC, Risiko, Melde, Quellen, Verteilung)
```
