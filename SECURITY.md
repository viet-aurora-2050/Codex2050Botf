# Sicherheit

## Schwachstellen melden
Bitte **nicht** als öffentliches Issue. Nutze auf GitHub *Security → „Report a vulnerability"*
(privater Meldeweg). Beschreibe kurz, was betroffen ist und wie man es nachvollzieht.

## Was im Betrieb wichtig ist
| Thema | Empfehlung |
|-------|-----------|
| `TELEGRAM_TOKEN`, `DEEPSEEK_API_KEY` | Nur als Umgebungsvariablen (Render/GitHub Secrets), **nie** committen. `.env` ist in `.gitignore`. |
| `ALLOWED_USER_IDS` | **Setzen**, sobald eine KI aktiv ist. Leer = öffentlicher Bot; dann kann jeder über `/analyse` und `/frage` API-Kosten verursachen. Das Rate-Limit (`RATE_LIMIT_PER_MINUTE`, Standard 10) begrenzt den Schaden, ersetzt aber keine Allowlist. Ein fehlerhafter Eintrag (z. B. `123;456`) stoppt den Start, statt den Bot still zu öffnen. |
| Telegram-Webhook | Nur mit `TELEGRAM_WEBHOOK_SECRET` aktiv. Beim Registrieren denselben Wert als `secret_token` setzen; ohne Geheimnis lehnt der Server Anfragen mit 403 ab. |
| RPC-Mock | Standardmäßig **aus** und nur an `127.0.0.1` gebunden; er hat keine Authentifizierung. |
| Abhängigkeiten | Gepinnt und per `pip-audit` geprüft; Dependabot schlägt wöchentlich Updates vor. |

## Grenzen
Das Projekt rechnet mit **öffentlichen Daten** und gibt **keine Vorhersagen**. Es greift nicht auf
Konten, Sitzungen oder private Schnittstellen von Anbietern zu und umgeht keine Schutzmaßnahmen.
