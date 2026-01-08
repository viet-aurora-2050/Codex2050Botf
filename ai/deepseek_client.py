import aiohttp
import json
import asyncio
from typing import Dict, List, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class DeepSeekClient:
    def __init__(self, config):
        self.config = config
        self.session = None
        
    async def connect(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.config.DEEPSEEK_API_KEY}"}
            )
            
    async def close(self):
        if self.session: await self.session.close()

    async def chat_completion(self, messages: List[Dict]):
        if not self.session: await self.connect()
        payload = {
            "model": self.config.AI_MODEL,
            "messages": messages,
            "temperature": self.config.AI_TEMPERATURE
        }
        async with self.session.post(f"{self.config.DEEPSEEK_BASE_URL}/chat/completions", json=payload) as resp:
            if resp.status != 200: return {"error": await resp.text()}
            return await resp.json()

    async def analyze_code(self, code: str):
        prompt = f"Analyze this code:\n\n{code}\n\nProvide JSON output with complexity, issues, and suggestions."
        messages = [{"role": "user", "content": prompt}]
        return await self.chat_completion(messages)
