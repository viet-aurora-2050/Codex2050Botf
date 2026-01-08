import os
from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class Config:
    TELEGRAM_TOKEN: str = ""
    ALLOWED_USER_IDS: List[int] = field(default_factory=list)
    ADMIN_USER_IDS: List[int] = field(default_factory=list)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    AI_MODEL: str = "deepseek-chat"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 4000
    ENABLE_RPC: bool = True
    RPC_HOST: str = "0.0.0.0"
    RPC_PORT: int = 8000
    CHAIN_ID: str = "0x21A8"
    NET_VERSION: str = "205000"
    ENABLE_WEB: bool = False
    WEB_HOST: str = "0.0.0.0"
    WEB_PORT: int = 8080
    RATE_LIMIT_PER_MINUTE: int = 10
    
    def __post_init__(self):
        self._load_from_env()

    def _load_from_env(self):
        from dotenv import load_dotenv
        load_dotenv()
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", self.TELEGRAM_TOKEN)
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", self.DEEPSEEK_API_KEY)
        self.ENABLE_RPC = os.getenv("ENABLE_RPC", str(self.ENABLE_RPC)).lower() == "true"
        self.ENABLE_WEB = os.getenv("ENABLE_WEB", str(self.ENABLE_WEB)).lower() == "true"
        if os.getenv("PORT"):
            self.WEB_PORT = int(os.getenv("PORT"))

        allowed = os.getenv("ALLOWED_USER_IDS", "")
        self.ALLOWED_USER_IDS = [int(x) for x in allowed.split(",") if x.strip().isdigit()]
        
    def is_user_allowed(self, user_id: int) -> bool:
        if not self.ALLOWED_USER_IDS: return True
        return user_id in self.ALLOWED_USER_IDS
    
    def to_dict(self):
        return {"ai_model": self.AI_MODEL, "rpc_port": self.RPC_PORT, "web_port": self.WEB_PORT}
