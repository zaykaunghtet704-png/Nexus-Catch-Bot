import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    owner_id: int
    database_url: str
    web_host: str
    web_port: int


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    owner_raw = os.getenv("OWNER_ID", "0").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()

    try:
        owner_id = int(owner_raw)
    except ValueError:
        owner_id = 0

    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    if owner_id <= 0:
        raise RuntimeError("OWNER_ID is not set correctly")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return Settings(
        bot_token=token,
        owner_id=owner_id,
        database_url=database_url,
        web_host=os.getenv("WEB_HOST", "0.0.0.0"),
        web_port=int(os.getenv("WEB_PORT", "8000")),
    )


settings = load_settings()
