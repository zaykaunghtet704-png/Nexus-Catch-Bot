# 🎴 Nexus Catch Bot

A Telegram Anime Card Collection Bot built with Python.

## ✨ Features

- 🎴 Card Collection System
- 🏆 13 Card Editions
- 💎 Premium Edition
- 🎯 Weighted Card Drop System
- 🖱️ First-Click GET CARD
- 👑 Harem System
- 👤 User Profile
- 🔎 Card Search
- 🏆 Global & Group Rankings
- 💰 Coin Economy
- 🎁 Daily Reward
- 🛒 Card Market
- 🤝 Gift & Trade
- ⚔️ Duel System
- ❤️ Favorite Cards
- 📊 Card Level / EXP System
- 👮 Admin System
- 🔐 Group Approval System
- 📢 Group Installation Notifications
- 🇲🇲 Myanmar / English Support
- 💾 SQLite Database
- 🚀 Render Deployment Support

## 🎴 Card Editions

1. Common Edition
2. Uncommon Edition
3. Rare Edition
4. Super Rare Edition
5. Epic Edition
6. Ultra Edition
7. Elite Edition
8. Master Edition
9. Grandmaster Edition
10. Mythic Edition
11. Legendary Edition
12. Ultimate Edition
13. Premium Edition

## 🤖 Main Commands

/start
/help
/harem
/profile
/search
/check
/top
/ctop
/rankings
/todayNexusCatch

/daily
/balance
/sellprice
/market
/sell
/buy
/delist

/gift
/trade
/duel

/fav
/unfav
/claim
/hmode
/reset

## 👑 Owner / Admin

/drop
/addcard
/deletecard
/givecard
/takecard
/givecoin
/takecoin
/setprice
/setdrop
/setadmin
/deladmin
/approve
/reject
/stats
/maintenance
/changetime
/broadcast

## 💰 Economy

Daily reward:

500 Coins

Premium maximum sale price:

15,000 Coins

## 🎯 Drop System

Cards use weighted drop rates.

The first user who successfully presses:

🎴 GET CARD

receives the dropped card.

The claim operation is atomic to prevent multiple users from receiving the same card.

## 👥 Group Requirements

For group usage:

- Bot must be Administrator
- Group must have at least 50 members
- Owner approval is required

## 🗄️ Database

The bot uses SQLite for storing:

- Users
- Groups
- Cards
- User Collections
- Drops
- Market
- Favorites
- Trades
- Admins
- Duels
- Settings

## 🚀 Deployment

This project is designed to run on Render using:

```text
worker: python bot.py
