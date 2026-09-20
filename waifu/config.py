import os
from dotenv import load_dotenv

load_dotenv()

def _req(key: str) -> str:
    v = os.environ.get(key, "").strip()
    if not v:
        raise RuntimeError(f"Required env var '{key}' not set in Railway Variables!")
    return v

def _int_list(key: str) -> list[int]:
    val = os.environ.get(key, "").strip()
    if not val:
        return []
    return [int(x.strip()) for x in val.split(",") if x.strip().lstrip("-").isdigit()]

class Config:
    TOKEN: str = _req("BOT_TOKEN")
    BOT_USERNAME: str = _req("BOT_USERNAME")
    OWNER_ID: int = int(_req("OWNER_ID"))
    SUDO_USERS: list[int] = _int_list("SUDO_IDS")
    GROUP_ID: int = int(_req("GROUP_ID"))
    CHARA_CHANNEL_ID: int = int(_req("CHARA_CHANNEL_ID"))
    MONGO_URL: str = _req("MONGO_URI")
    DB_NAME: str = os.environ.get("DB_NAME", "waifu_bot")
    SUPPORT_CHAT: str = os.environ.get("SUPPORT_CHAT", "")
    UPDATE_CHAT: str = os.environ.get("UPDATE_CHAT", "")
    
    photo_raw = os.environ.get("PHOTO_URLS", "")
    PHOTO_URL: list[str] = [u.strip() for u in photo_raw.split(",") if u.strip().startswith("http")]

    DROP_INTERVAL_MIN: int = int(os.environ.get("DROP_INTERVAL_MIN", "10"))
    DEFAULT_MSG_FREQUENCY: int = int(os.environ.get("DEFAULT_MSG_FREQUENCY", "100"))

    DAILY_COINS: int = 200
    DUEL_WIN_COINS: int = 150
    DUEL_LOSE_COINS: int = 30

    # Rarity 13 ဆင့် (9 နေရာတွင် Exotic ပြောင်းထားသည်)
    RARITY_MAP: dict[int, str] = {
        1: "⚪ Common",
        2: "🟢 Uncommon",
        3: "🔵 Rare",
        4: "🟣 Epic",
        5: "🟡 Legendary",
        6: "🟠 Mythic",
        7: "🔴 Ancient",
        8: "🔮 Celestial",
        9: "🌟 Exotic",
        10: "🌌 Cosmic",
        11: "✨ Immortal",
        12: "👑 Exclusive Edition",
        13: "🏆 Premium Edition",
    }

    @classmethod
    def all_sudo(cls) -> set[int]:
        return {cls.OWNER_ID, *cls.SUDO_USERS}
