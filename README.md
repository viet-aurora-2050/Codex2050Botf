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
bot/          Telegram-Bot (CasinoBonusBot)
ai/           DeepSeek-Client für die AGB-Analyse
web/          FastAPI-Dashboard (Rechner + /sancho + Webhook)
tests/        Unit-Tests (Engine, Parser, Sancho)
```
