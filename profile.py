from telegram import Update
from telegram.ext import ContextTypes
from database import users_col, inventory_col

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # User ဒေတာ ရှာဖွေခြင်း
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        users_col.insert_one({
            "user_id": user_id,
            "username": user.username or user.first_name,
            "balance": 100,
            "xp": 0,
            "level": 1
        })
        user_data = users_col.find_one({"user_id": user_id})

    # Harem ထဲမှာရှိတဲ့ ကတ်စုစုပေါင်း အရေအတွက်ကို ရေတွက်ခြင်း
    total_cards = inventory_col.count_documents({"user_id": user_id})
    
    # ရှားပါးမှုအလိုက် ကတ်အရေအတွက် စစ်ဆေးခြင်း
    sr_count = inventory_col.count_documents({"user_id": user_id, "rarity": "SR"})
    ssr_count = inventory_col.count_documents({"user_id": user_id, "rarity": "SSR"})
    ur_count = inventory_col.count_documents({"user_id": user_id, "rarity": "UR"})

    balance = user_data.get("balance", 0)
    level = user_data.get("level", 1)
    xp = user_data.get("xp", 0)

    profile_text = (
        f"👤 **{user.first_name} ၏ Profile အချက်အလက်** 👤\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"⭐ အဆင့် (Level): {level} (XP: {xp})\n"
        f"💰 လက်ကျန်ငွေ: {balance} Coins\n\n"
        f"🎒 **ကတ်စုဆောင်းမှု အခြေအနေ:**\n"
        f" • စုစုပေါင်း ကတ်ပမာဏ: {total_cards} ခု\n"
        f" • 🌟 UR ကတ်: {ur_count} ခု\n"
        f" • 💫 SSR ကတ်: {ssr_count} ခု\n"
        f" • ✨ SR ကတ်: {sr_count} ခု"
    )

    await update.message.reply_text(profile_text, parse_mode="Markdown")
