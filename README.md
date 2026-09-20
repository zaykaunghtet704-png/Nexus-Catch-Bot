<div align="center">
<img src="https://i.ibb.co/gbXCJDZy/download-73.jpg" alt="Waifu Catcher Banner" width="400" style="border-radius: 16px;" />
<h1>🌸 Waifu Catcher Bot</h1>
<p><em>A fully-featured anime character collection bot for Telegram<br>check the bot <a href="https://t.me/OtakuFlix_post_bot">ᴡᴀɪғᴜ ɢʀᴀʙʙᴇʀ ʙᴏᴛ</a></em></p>
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-20.6-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://python-telegram-bot.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Motor%20Async-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://motor.readthedocs.io)
[![APScheduler](https://img.shields.io/badge/APScheduler-3.x-FF6B6B?style=for-the-badge&logo=clockify&logoColor=white)](https://apscheduler.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
</div>
---
## ✨ Feature Overview

| Module | Commands | Description |
| :--- | :--- | :--- |
| 🎲 `waifu_drop` | `/guess` `/fav` | Auto-drops in groups — timed + message threshold |
| 🚀 `start` | `/start` | Welcome screen with inline help panel |
| 📚 `harem` | `/harem` `/collection` | Paginated collection grouped by anime |
| 👤 `profile` | `/profile` | Level, XP bar, rarity breakdown, collection value |
| 💰 `economy` | `/daily` `/balance` `/sell` `/market` `/buy` `/delist` | Coins, daily reward, marketplace |
| ⚔️ `duel` | `/duel` | PvP inline-button character battles |
| 🔄 `trade` | `/trade` `/gift` | Trade or gift characters between users |
| 📤 `upload` | `/upload` `/uploadchar` `/delete` `/update` | Two upload methods |
| 🏆 `leaderboard` | `/top` `/ctop` `/TopGroups` `/stats` | Global and per-group rankings |
| 🔍 `inlinequery` | — | Inline search of full catalogue or personal collection |
| 📢 `broadcast` | `/broadcast` | Rate-limited owner broadcast |
| ⚙️ `changetime` | `/changetime` `/resettime` | Per-group drop frequency (admins) |
| 🏓 `ping` | `/ping` | Latency + uptime (sudo) |
| 🛠️ `eval` | `/e` `/py` `/sh` `/clearlocals` | Dev REPL (DEV_LIST only) |

---
## 🚀 Quick Start
```bash
# 1. Clone the repo
git clone [https://github.com/zaykaunghtet/Nexus-Catch-Bot](https://github.com/zaykaunghtet/Nexus-Catch-Bot)
cd Nexus-Catch-Bot
# 2. Install dependencies
pip install -r requirements.txt
# 3. Configure environment
cp .env.example .env
# Open .env and fill in all required values
# 4. Run
python -m waifu
