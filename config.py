import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    owner_id: int
    database_url: str
    redis_url: str
    web_host: str
    web_port: int


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "")
    owner_id = int(os.getenv("OWNER_ID", "0"))

    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not configured")

    if owner_id == 0:
        raise RuntimeError("OWNER_ID is not configured")

    return Settings(
        bot_token=bot_token,
        owner_id=owner_id,
        database_url=os.getenv("DATABASE_URL", ""),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        web_host=os.getenv("WEB_HOST", "0.0.0.0"),
        web_port=int(os.getenv("WEB_PORT", "8000")),
    )


settings = load_settings()
