import os
import re
from dataclasses import dataclass, field
from typing import List


def _env_bool(name: str, default: bool) -> bool:
    wert = os.getenv(name)
    return default if wert is None else wert.strip().lower() in {"1", "true", "yes", "ja", "on"}


def _env_int(name: str, default: int) -> int:
    wert = os.getenv(name)
    if wert is None or not wert.strip():
        return default
    try:
        return int(wert)
    except ValueError:
        raise ValueError(f"{name} muss eine ganze Zahl sein, ist aber {wert!r}.") from None


def parse_user_ids(roh: str, name: str = "ALLOWED_USER_IDS") -> List[int]:
    """Kommagetrennte Telegram-User-IDs. Fehlerhafte Eintraege brechen ab (fail-closed):
    still verworfene IDs wuerden die Allowlist leeren und den Bot ungewollt oeffentlich machen."""
    ids: List[int] = []
    for teil in (roh or "").split(","):
        teil = teil.strip()
        if not teil:
            continue
        if not re.fullmatch(r"\d+", teil):
            raise ValueError(f"{name}: ungueltiger Eintrag {teil!r} (erwartet: kommagetrennte Zahlen).")
        ids.append(int(teil))
    return ids


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
    # Der RPC-Server ist ein Mock ohne Authentifizierung und wird vom Bot nicht gestartet:
    # standardmaessig aus und nur lokal gebunden.
    ENABLE_RPC: bool = False
    RPC_HOST: str = "127.0.0.1"
    RPC_PORT: int = 8000
    CHAIN_ID: str = "0x21A8"
    NET_VERSION: str = "205000"
    ENABLE_WEB: bool = False
    WEB_HOST: str = "0.0.0.0"  # noqa: S104 - Render/Container brauchen die oeffentliche Bindung
    WEB_PORT: int = 8080
    RATE_LIMIT_PER_MINUTE: int = 10

    def __post_init__(self):
        self._load_from_env()

    def _load_from_env(self):
        try:  # .env ist optional: Rechner/CLI laufen auch ohne installiertes python-dotenv
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", self.TELEGRAM_TOKEN)
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", self.DEEPSEEK_API_KEY)
        self.ENABLE_RPC = _env_bool("ENABLE_RPC", self.ENABLE_RPC)
        self.ENABLE_WEB = _env_bool("ENABLE_WEB", self.ENABLE_WEB)
        self.WEB_PORT = _env_int("PORT", _env_int("WEB_PORT", self.WEB_PORT))
        self.RATE_LIMIT_PER_MINUTE = max(0, _env_int("RATE_LIMIT_PER_MINUTE", self.RATE_LIMIT_PER_MINUTE))
        self.ALLOWED_USER_IDS = parse_user_ids(os.getenv("ALLOWED_USER_IDS", ""))
        self.ADMIN_USER_IDS = parse_user_ids(os.getenv("ADMIN_USER_IDS", ""), "ADMIN_USER_IDS")

    def is_user_allowed(self, user_id: int) -> bool:
        if not self.ALLOWED_USER_IDS:
            return True
        return user_id in self.ALLOWED_USER_IDS

    def to_dict(self):
        return {"ai_model": self.AI_MODEL, "rpc_port": self.RPC_PORT, "web_port": self.WEB_PORT}
