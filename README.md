# Codex2050

Telegram bot powered by DeepSeek AI with optional RPC endpoints.

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy the sample environment file and fill in your private tokens (never commit them):
   ```bash
   cp .env.example .env
   # edit .env to add TELEGRAM_TOKEN and any other overrides
   ```
3. Start the bot locally:
   ```bash
   python main.py
   ```

Das Web-Dashboard ist jetzt standardmäßig aktiviert (`ENABLE_WEB=true`) und die benötigten Pakete sind in `requirements.txt` enthalten.

## Deployment
Render configuration (`render.yaml`) reference secret environment variables. Keep deine TELEGRAM_TOKEN und DEEPSEEK_API_KEY in Renders Dashboard; sie werden nicht im Repository gespeichert. Der Bot läuft als Worker, das Dashboard als eigener Web Service.

### Render secrets
- Secrets such as `TELEGRAM_TOKEN` and `DEEPSEEK_API_KEY` stay in Render's Environment Variables page (already set up in the dashboard screenshot) and are **not** checked into git.
- If you need to rotate or review a value, open the Render dashboard, edit the corresponding key, and redeploy—no code changes are required.

## Render-Deployment neu aufsetzen (Worker + Web)
So stellst du den Bot und das Dashboard in einem sauberen GitHub→Render-Flow wieder her:

1. **Repository vorbereiten**: `main.py`, `requirements.txt`, `render.yaml` und `Procfile` müssen im Root liegen (keine Unterordner). `render.yaml` enthält jetzt **zwei Services**: `codex2050-bot` (Worker) und `codex2050-dashboard` (Web).
2. **Render anlegen**: Auf Render „New Web Service“ → GitHub-Repo `codex2050bot` wählen → Runtime Python 3.11 → Build Command leer lassen oder `pip install -r requirements.txt`.
   - Worker-Start: `python main.py` (Procfile nutzt `worker: python main.py`).
   - Dashboard-Start: `uvicorn web.dashboard:app --host 0.0.0.0 --port $PORT` (im Render-Webservice definiert).
3. **Build-Cache leeren** (falls vorherige Deploys fehlschlugen): Render → *Advanced* → *Clear build cache* → *Manual Deploy → Deploy latest commit*.
4. **Secrets kontrollieren**: `TELEGRAM_TOKEN` und `DEEPSEEK_API_KEY` nur im Render-Dashboard hinterlegen und bei Bedarf rotieren. Für das Dashboard reicht `PORT`, das in `render.yaml` gesetzt ist.

Damit erhältst du einen Neustart ohne alte Cache-Artefakte und einen getrennten Webservice, der das Dashboard wieder erreichbar macht.
