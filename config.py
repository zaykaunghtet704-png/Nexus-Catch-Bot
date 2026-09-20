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

def load_settings():
    token = os.getenv('BOT_TOKEN', '').strip()
    
    # OWNER_ID ကို စစ်ဆေးခြင်း
    try:
        owner = int(os.getenv('OWNER_ID', '0'))
    except ValueError:
        owner = 0

    # DATABASE_URL သို့မဟုတ် MONGO_URI ကို ဖတ်ခြင်း
    db = os.getenv('DATABASE_URL', '').strip() or os.getenv('MONGO_URI', '').strip()
    
    if not token or owner <= 0 or not db:
        raise RuntimeError('Set BOT_TOKEN, OWNER_ID and DATABASE_URL (or MONGO_URI) in Railway Variables!')
        
    web_host = os.getenv('WEB_HOST', '0.0.0.0').strip()
    
    try:
        web_port = int(os.getenv('WEB_PORT', '8000'))
    except ValueError:
        web_port = 8000

    return Settings(
        bot_token=token,
        owner_id=owner,
        database_url=db,
        web_host=web_host,
        web_port=web_port
    )

settings = load_settings()
