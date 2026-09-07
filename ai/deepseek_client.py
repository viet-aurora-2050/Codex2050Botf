import aiohttp
from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


class DeepSeekClient:
    """Duenner Client fuer die DeepSeek Chat-Completions-API."""

    def __init__(self, config):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.config.DEEPSEEK_API_KEY}"}
            )

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def chat_completion(self, messages: List[Dict]) -> Dict:
        if not self.session:
            await self.connect()
        payload = {
            "model": self.config.AI_MODEL,
            "messages": messages,
            "temperature": self.config.AI_TEMPERATURE,
            "max_tokens": self.config.AI_MAX_TOKENS,
        }
        try:
            async with self.session.post(
                f"{self.config.DEEPSEEK_BASE_URL}/chat/completions", json=payload
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error("DeepSeek API %s: %s", resp.status, text)
                    return {"error": text}
                return await resp.json()
        except aiohttp.ClientError as exc:
            logger.error("DeepSeek Verbindungsfehler: %s", exc)
            return {"error": str(exc)}

    async def ask(self, frage: str, system_prompt: Optional[str] = None) -> str:
        """Stellt eine Frage (optional mit System-Prompt) und liefert reinen Text."""
        messages: List[Dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": frage})
        resp = await self.chat_completion(messages)
        if "error" in resp:
            return f"KI-Fehler: {resp['error']}"
        return (
            resp.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "Keine Antwort erhalten.")
        )
