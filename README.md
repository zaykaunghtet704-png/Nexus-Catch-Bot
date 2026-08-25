# Advanced Card Bot

Telegram card collection bot built with Python, Aiogram, FastAPI and SQLAlchemy.

## Features

- Card collection
- Rarity system
- Pack opening
- Coins and gems
- Daily rewards
- User levels and XP
- PostgreSQL database
- Async SQLAlchemy
- Telegram bot with Aiogram

## Requirements

- Python 3.13+
- PostgreSQL
- Telegram Bot Token

## Environment Variables

Set these variables in the deployment environment:

```env
BOT_TOKEN=your_telegram_bot_token
OWNER_ID=your_telegram_user_id
DATABASE_URL=your_postgresql_database_url
WEB_HOST=0.0.0.0
WEB_PORT=8000
