from typing import Optional

from .deepseek_client import DeepSeekClient


class AIManager:
    """Verwaltet KI-Provider (aktuell DeepSeek)."""

    def __init__(self, config):
        self.config = config
        self.providers = {}
        if config.DEEPSEEK_API_KEY:
            self.providers["deepseek"] = DeepSeekClient(config)

    @property
    def available(self) -> bool:
        return bool(self.providers)

    async def initialize(self):
        for p in self.providers.values():
            await p.connect()

    async def close(self):
        for p in self.providers.values():
            await p.close()

    async def ask(self, frage: str, system_prompt: Optional[str] = None) -> str:
        if "deepseek" in self.providers:
            return await self.providers["deepseek"].ask(frage, system_prompt=system_prompt)
        return (
            "Keine KI konfiguriert. Setze DEEPSEEK_API_KEY, um die AGB-Analyse "
            "per KI zu aktivieren. Die Bonus-Berechnung funktioniert auch ohne KI."
        )

    def get_stats(self):
        return {"providers": list(self.providers.keys())}
