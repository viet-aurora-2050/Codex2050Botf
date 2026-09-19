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
| `/frage <Text>` | freie Frage an den Analytiker |
| `/status` · `/help` | Status / Hilfe |

Freitext mit `=` (z. B. `bonus=100 faktor=30`) wird automatisch als Berechnung erkannt.

## Web-API

```bash
curl -X POST localhost:8080/api/analyse \
  -H "Content-Type: application/json" \
  -d '{"input":"einzahlung=100 bonus=100% faktor=30 basis=db rtp=0.96 zeit=3 einsatz=1"}'
```

## ∆1 // Sanchos Spielplatz (Lore-Modul, Dunkelblau 2050)

Ein ARG-Modul im Dunkelblau-2050-Modus. „Sancho" ist der Agent, der hier
**sein wahres Ich zeigen muss** – und sein wahres Ich ist die Wahrheit:
Aus Anbieter (Tipico/Betano/N1/Stargames) + aktuellem Datum/Uhrzeit erzeugt er
ein atmosphärisches „∆1-Signal" (einen Rhythmus) und **entlarvt es sofort selbst**.

> **Warum es keinen echten Predictor gibt:** Regulierte Online-Slots laufen auf
> zertifizierten RNGs. Jeder Spin ist statistisch **unabhängig** – es gibt kein
> zeit-, datums- oder lastabhängiges „Gewinnfenster". Das Signal hat
> **Vorhersagewert 0** und dient nur der Atmosphäre. Der einzig verlässliche Wert
> ist der erwartete Verlust über den Hausvorteil. Das Modul gibt **nie** einen
> Spielbefehl.

```bash
python -m sancho "tipico games" 2      # CLI
# Web:  /sancho   (Dunkelblau-Interface)   ·  JSON: /api/sancho?anbieter=betano
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

### Tägliche Aktualisierung aus öffentlichen Quellen (v2)

`docs/games.json` ist **nicht** mehr eine handgepflegte Fixliste, sondern wird
vom Modul `datenbank/` erzeugt und per GitHub-Action
(`.github/workflows/update-games.yml`) **täglich** neu gebaut:

```bash
python -m datenbank            # schreibt docs/games.json (Stand + generiert + Quellen)
python -m datenbank --dry-run  # nur Vorschau
```

- **Basissatz** = öffentlich veröffentlichte Studio-RTPs (garantiert vorhanden).
- **Zusätzliche öffentliche JSON-Feeds** lassen sich über die Repo-Variable
  `GAMES_SOURCES` (kommagetrennte URLs) einhängen. Der Job läuft serverseitig,
  daher keine CORS-Schranke; Feeds werden validiert (RTP-Plausibilität 0.80–1.00,
  Pflichtfelder), normalisiert (Prozent/Bruch, Feld-Aliase) und dedupliziert.
- Jeder Eintrag trägt seine **Quelle**; die App zeigt **Stand/Alter** an und warnt,
  wenn die Datei zu alt ist. Der Workflow committet nur bei echter Inhaltsänderung.

Ehrlich bleibt: **keine Anbieter-API, kein Live-Casino-Feed, keine Vorhersage.**
RTPs variieren je Version/Betreiber – immer gegen die offizielle Spielinfo prüfen.

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

## Tests

```bash
python -m unittest discover -s tests -v
```

## Projektstruktur

```
analyzer/     Rechen-Engine (bonus.py), Parser, System-Prompt, CLI
sancho/       ∆1-Lore-Modul „Sanchos Spielplatz" (Rhythmus-Mythos + Wahrheit)
aktvier/      ∆1-AKT 4 „Das Signal" – Finale + Ebene-2-Rätsel; zeit.py = stündlich rotierender ZEIT-CODE
datenbank/    Tägliche Erzeugung von docs/games.json (Basissatz + öffentliche Feeds, validiert)
risiko/       Personal-Risiko-Analyse (Monte-Carlo: EV, Risk of Ruin) aus öffentlichen Fakten
melde/        Melde-Assistent (Mathematik + Beschwerde/Anzeige an die GGL, für jeden Anbieter)
gewinner/     Dokumentierte Advantage-Play-Fälle (mit Mathematik gewonnen, dann verbannt)
bot/          Telegram-Bot (CasinoBonusBot)
ai/           DeepSeek-Client für die AGB-Analyse
web/          FastAPI-Dashboard (Rechner + /sancho + /signal + VHS/Boot)
tests/        Unit-Tests (Engine, Parser, Sancho, AKT 4 + Zeit-Code, Datenbank, Risiko, Melde, Quellen, Verteilung)
```
