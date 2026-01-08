from .deepseek_client import DeepSeekClient
class AIManager:
    def __init__(self, config):
        self.providers = {}
        if config.DEEPSEEK_API_KEY:
            self.providers["deepseek"] = DeepSeekClient(config)
            
    async def initialize(self):
        for p in self.providers.values(): await p.connect()
            
    async def close(self):
        for p in self.providers.values(): await p.close()
            
    async def chat(self, message: str):
        if "deepseek" in self.providers:
            resp = await self.providers["deepseek"].chat_completion([{"role": "user", "content": message}])
            return resp.get("choices", [{}])[0].get("message", {}).get("content", "Error")
        return "No AI provider configured."
    
    def get_stats(self):
        return {"providers": list(self.providers.keys())}
