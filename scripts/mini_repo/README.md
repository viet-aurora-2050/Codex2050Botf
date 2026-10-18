# KI Taktik-Protokoll & Casino-Bonus-Analyzer (v2)

Kleines, abhängigkeitsfreies Mini-Repo (nur Python-Standardbibliothek, Python ≥ 3.11).

## Inhalt
| Pfad | Zweck |
|------|-------|
| `index.html` | GitHub-Pages-Seite mit Prompt-Vorlagen (barrierefrei, hell/dunkel, ohne Tracking, eigene CSP) |
| `analyzer/` | Rechen-Engine für Bonusbedingungen (`bonus.py`) und **AGB-Scanner** (`scan.py`) |
| `risiko/` | Monte-Carlo-Risikoanalyse mit Konfidenzintervallen und **persönliches Risikoprofil** (`profil.py`) |
| `bonus_analyzer.py` | Kompatibilitäts-Wrapper für die alte Klasse `CasinoBonusAnalyzer` |
| `tests/` | Unit-Tests (`python -m unittest discover -s tests`) |

## Benutzung
```bash
# AGB-Text einlesen und durchrechnen (offline, ohne KI)
python -m analyzer.scan "Bonus 100 % bis 200 €. Umsatz 35x innerhalb von 30 Tagen. Max. Einsatz 5 €." einzahlung=50

# Risikoanalyse einer Session
python -m risiko budget=100 einsatz=1 spins=500 rtp=0.96 vola=mittel
```
```python
from risiko import eingabe_aus_text, berechne, formatiere_profil
e = eingabe_aus_text("budget=100 einsatz=2 rtp=96 minuten=60 check=0,1,0,0,2,0")
print(formatiere_profil(berechne(e), e))
```

## Ehrlichkeitsregeln
* Der Scanner zeigt zu jedem Fund den **Textbeleg**. Was nicht im Text steht (RTP, Einsatz, ggf. Einzahlung), steht getrennt als **Annahme**, es wird nichts erfunden.
* Bei widersprüchlichen Angaben gilt der **für dich ungünstigere** Wert, mit Hinweis. Ohne erkennbaren Bonus wird nicht gerechnet.
* Ein Regex-Scanner kann Formulierungen missverstehen: Belege am Original prüfen. Keine Rechtsberatung.
* Der Selbst-Check im Risikoprofil verändert nur empfohlene Grenzen, nie Wahrscheinlichkeiten. Keine Diagnose.
* **Keine Spin-Vorhersage.** Bei zertifizierten Zufallsgeneratoren sind Spins unabhängig. Der Erwartungswert bleibt negativ.

## Entwicklung
```bash
pip install ruff==0.15.8
ruff check .
python -m unittest discover -s tests
```
Die Datei `.github/workflows/ci.yml` führt beides bei jedem Push aus. Für GitHub Pages: Settings → Pages → Branch `main`, Ordner `/ (root)`.

Das vollständige Projekt (Telegram-Bot, Dashboard, Datenbank) liegt im Haupt-Repository `Codex2050Botf`; dieses Mini-Repo ist ein Auszug daraus.
