# datenbank/ — öffentlicher Spiele-Katalog (v3)

Generiert `docs/games.json` als **Snapshot/Cache** eines öffentlichen Katalogs.

```
öffentliche Quellen → Source-Adapter → Validation → Normalization
→ Deduplication → Katalog → Freshness/Source-Health → docs/games.json → Frontend
```

## Aufruf

```bash
python -m datenbank                       # schreibt docs/games.json
python -m datenbank --dry-run             # Vorschau, nichts schreiben
python -m datenbank --out pfad.json       # anderes Ziel
python -m datenbank --alternativen "Gates of Olympus"   # ähnliche Spiele (Metadaten)
```

## Datenquellen konfigurieren

Über die Umgebungs-/Repo-Variable **`GAMES_SOURCES`** (kommagetrennte URLs
öffentlicher JSON-Feeds). Weitere Regler: `GAMES_TIMEOUT` (Sek.),
`GAMES_MAX_ITEMS` (Deckel je Quelle).

Der Basissatz (`SEED_GAMES`, veröffentlichte Studio-RTPs) ist immer vorhanden;
fällt eine externe Quelle aus, bleibt der Katalog erhalten und der Ausfall wird
in `source_status` dokumentiert.

## Erwartetes Feed-Schema (Adapter-Interface)

Ein Feed ist ein JSON-Array **oder** ein Objekt mit einer Liste unter
`spiele`/`games`/`items`/`results`/`data`. Pro Datensatz werden folgende
Feld-Aliase akzeptiert:

| intern | akzeptierte Aliase | Pflicht |
|--------|--------------------|---------|
| name | `name`, `title`, `game_name` | ✅ |
| anbieter | `anbieter`, `provider`, `studio`, `vendor` | ✅ |
| rtp | `rtp`, `return`, `return_to_player` (0.965, 96.5, "96.5%") | – |
| vola | `vola`, `volatility`, `variance` (low/medium/high → niedrig/mittel/hoch) | – |
| max | `max`, `maxwin`, `max_win`, `max_multiplier` | – |
| minb/maxb | `min_bet`/`minimum_bet`, `max_bet`/`maximum_bet` | – |
| game_id | `game_id`, `id`, `slug` | – |
| variant | `variant`, `rtp_version`, `version` | – |
| source_url | `source_url`, `url`, `link` | – |
| reported_recent_win | `reported_recent_win`, `recent_win`, `last_win` | – |

RTP wird auf `0.80–1.00` plausibilisiert; unplausible/fehlende Werte bleiben
`null` (es wird **nichts erfunden**). Dedup-Schlüssel: `game_id`, sonst
`Anbieter + Name + variant` — unterschiedliche RTP-Versionen bleiben getrennt.

## Neue Quelle hinzufügen

Für eine reguläre öffentliche JSON-URL genügt `GAMES_SOURCES`. Für Quellen mit
abweichendem Format einen dedizierten Adapter analog `http_json_source` in
`sources.py` ergänzen (eigene Normalisierung → `normalisiere`-Ausgabeschema),
mit Fixture-Test. **Keine** erfundenen URLs/APIs, keine authentifizierten
Casino-Sessions, keine privaten Endpunkte. Fehlt eine vertrauenswürdige Quelle,
wird nur das Interface dokumentiert (siehe `prompts/AI_SOURCE_EXPANSION_PROMPT.md`).

## `reported_recent_win`

Von der Quelle gemeldete **Beobachtung** mit Herkunft/Zeitstempel — ausdrücklich
**kein Beweis** und **keine** Aussage über den nächsten Spin.
