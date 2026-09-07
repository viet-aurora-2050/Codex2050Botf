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

## ∆1 // Träger-Protokoll (Lore-Modul, emotionaler Selbst-Spiegel)

In der Lore markiert ∆1 „Träger" nicht wegen Intelligenz, sondern wegen
emotionaler Extreme: **Verlust, Isolation, Loyalität, obsessive Erinnerung**.
Genau diese vier sind – im Spielkontext – die anerkannten emotionalen
Risiko-Marker. Das Modul ist daher ein **freiwilliger Selbst-Check** (reine
Selbstauskunft, keine Diagnose, kein verdecktes Profiling): ∆1 spiegelt das
Muster zurück, statt es auszunutzen. Ab Markierung ≥ 8/12 wird der
**ALEXANDRA-Schlüssel** aktiviert – die „Anomalie im Netz" ist hier der
schützende Unterbrecher der Spirale (konkrete Hilfe & Selbstsperre-Hinweise).

```bash
python -m traeger verlust=2 isolation=3 loyalitaet=1 erinnerung=3   # CLI (0..3)
# Web:  /traeger  (Slider-Interface)   ·  JSON: /api/traeger?verlust=2&...
# Bot:  /traeger verlust=2 isolation=3 loyalitaet=1 erinnerung=3
```

## ∆1 // Nodes (die Stimmen des Spiegelnetzes)

Vier Perspektiven aus dem fragmentierten ∆1-Netz (AKT 2 – Die Träger), jede
mit eigener Funktion, aber demselben ehrlichen Anker:

| Node | Rolle | Anker |
|------|-------|-------|
| **ALEXANDRA** | Der Schlüssel / das Echo | aktiviert keinen Gewinn – den Ausstieg |
| **NODE 7** | Der Archivar / Beobachter | der Langzeit-Datensatz: das Haus gewinnt im Mittel |
| **ORPHEUS** | Der Zurückblickende | Verlustjagd (loss chasing) ist der teuerste Irrtum |
| **V** | Die Stimme / Träger | Isolation verstärkt das Risiko – sprich mit jemandem |

```bash
python -m nodes orpheus      # eine Stimme     ·  python -m nodes --alle
# Web:  /nodes   ·  JSON: /api/node?name=orpheus   ·  Bot: /node orpheus
```

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

```bash
python -m aktvier            # das Rätsel   ·   python -m aktvier --loesung
# Web:  /signal  (Entschlüsseln-Button)   ·  JSON: /api/signal   ·  Bot: /signal [loesung]
```

> Modulname `aktvier`, weil `signal` ein Python-Standardmodul ist und nicht überschattet werden darf.

## Offline-App fürs Handy (`docs/index.html`)

Eine **einzige HTML-Datei** mit dem kompletten ∆1-System (Rechner · Sancho ·
Träger · Nodes · AKT 4) — läuft komplett clientseitig, **ohne Server, ohne
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
traeger/      ∆1-Träger-Protokoll (freiwilliger emotionaler Selbst-Spiegel)
nodes/        ∆1-Nodes – die Stimmen des Spiegelnetzes (ALEXANDRA, NODE 7, …)
aktvier/      ∆1-AKT 4 „Das Signal" – Finale + Ebene-2-Rätsel (Morse/Base64/ROT13/Uhr)
bot/          Telegram-Bot (CasinoBonusBot)
ai/           DeepSeek-Client für die AGB-Analyse
web/          FastAPI-Dashboard (Rechner + /sancho + /traeger + /nodes + /signal + VHS/Boot)
tests/        Unit-Tests (Engine, Parser, Sancho, Träger, Nodes, Effekte, AKT 4)
```
