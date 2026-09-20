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
    token=os.getenv('BOT_TOKEN','').strip(); owner=int(os.getenv('OWNER_ID','0')); db=os.getenv('DATABASE_URL','').strip()
    if not token or owner<=0 or not db: raise RuntimeError('Set BOT_TOKEN, OWNER_ID and DATABASE_URL in .env')
    return Settings(token,owner,db,os.getenv('WEB_HOST','0.0.0.0'),int(os.getenv('WEB_PORT','8000')))
settings=load_settings()
