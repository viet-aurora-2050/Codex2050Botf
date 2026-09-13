# Akt4GameRiddleDecoder (Zusatz-Ebene · ADD, NOT REPLACE)

Eine **isolierte, zusätzliche** Rätsel-Ebene über dem bestehenden AKT 4 des
CODEX2050. Sie **verändert nichts** am bestehenden System — eigener Namespace,
eigene Dateien.

## Reproduzierbarer Lösungsweg (keine Blackbox)

```
Morse  →  ALEXANDRA
Base64 →  „Ich wollte nie frei sein. Ich wollte erinnert werden."
ROT13  →  „Erinnert zu werden heisst nicht, gefangen zu bleiben. Geh, wenn du gehen musst."
Uhrzeit → 07:07 / 05:05 / 08:08
Alphabet → 07→G · 05→E · 08→H
Game-Titel → G=Gates of Olympus · E=Eye of Horus · H=Holla die Waldfee
Buchstaben → G E H
Wort    →  GEH
```

## Ehrlichkeitsregeln (fest eingebaut)
- **Keine Glücksspiel-Vorhersage.** Game-Titel sind reine Wort-/Buchstabenschlüssel.
- **Keine erfundenen Titel.** Ohne verifizierbaren Treffer: `NO VERIFIED MATCH`.
- **Kein Zufalls-Pick** bei mehreren Treffern — alle Kandidaten mit
  `Confidence / Reason / Source`, nie „definitiv richtig".
- **Anti-Zufall-Validierung** (7 Prüfungen) + Sancho-Check mit Confidence
  `HIGH/MEDIUM/LOW/UNKNOWN`. Das Wort `GEH` stammt aus der **Uhr**, nicht aus den
  Spielen — die Spiele sind eine parallele Bestätigungsschicht.

## Datenquelle (nicht hartcodiert, reproduzierbar)
Priorität: **eigene öffentliche JSON-URL** → **lokaler SPIELE-Datensatz** der
Hauptapp (read-only, gleiche Origin) → **kuratierter öffentlicher Fallback**.
Quelle, Abrufzeit und Datenqualität werden angezeigt. Keine versteckten Requests,
keine Login-Daten, keine geschützten APIs.

## Nutzung
```bash
python -m akt4riddle          # CLI-Demo der vollen Kette
```
Web (eigene Seite, ändert index.html nicht): `docs/akt4-decoder.html`
→ `https://viet-aurora-2050.github.io/Codex2050Botf/akt4-decoder.html`

## Module (Namespace)
`decodeMorse · decodeBase64 · decodeROT13 · decodeClockAlphabet · findGameMatches
· verifyGameSource · validateRiddleChain · sanchoCheck · renderRiddleResult`
