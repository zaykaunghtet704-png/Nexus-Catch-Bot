from telegram import Update
from telegram.ext import ContextTypes
from database import cards_col

# Bot ပိုင်ရှင် (သို့) Admin တွေရဲ့ User ID များကို ဤနေရာတွင် ထည့်ပါ (ဥပမာ - [123456789, 987654321])
# Railway Environment Variables ကနေလည်း ဖတ်ယူနိုင်အောင် ပြုလုပ်နိုင်ပါသည်
import os
DEV_LIST = [int(uid) for uid in os.getenv("DEV_LIST", "").split(",") if uid.isdigit()]

def is_admin(user_id: int) -> bool:
    """Admin ဟုတ်မဟုတ် စစ်ဆေးခြင်း"""
    if not DEV_LIST:
        return True # DEV_LIST မသတ်မှတ်ထားပါက ပထမအစအနေဖြင့် အားလုံးကို ခွင့်ပြုရန် (သို့မဟုတ် လိုသလို သတ်မှတ်ရန်)
    return user_id in DEV_LIST

async def upload_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ကတ်အသစ်ထည့်သွင်းရန် ပုံစံ -
    /uploadchar [Card ID] | [Name] | [Anime] | [Rarity] | [Image/Video URL]
    ဥပမာ - /uploadchar c004 | Rem | Re:Zero | SR | https://i.imgur.com/example.jpg
    """
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ ဤ Command ကို Bot Owner များသာ အသုံးပြုနိုင်ပါသည်။")
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ ပုံစံမှန်ကန်စွာ ရေးပါ။\n"
            "အသုံးပြုပုံ: `/uploadchar [CardID] | [Name] | [Anime] | [Rarity] | [MediaURL]`\n"
            "ဥပမာ: `/uploadchar c004 | Rem | Re:Zero | SR | https://link.com/image.jpg`",
            parse_mode="Markdown"
        )
    return

    # Text အားလုံးကို ပေါင်းပြီး "|" ဖြင့် ခွဲထုတ်ခြင်း
    full_text = " ".join(context.args)
    parts = [p.strip() for p in full_text.split("|")]

    if len(parts) < 5:
        await update.message.reply_text("❌ အချက်အလက် မပြည့်စုံပါ။ (Card ID, Name, Anime, Rarity, Media URL ၅ ခုလုံး လိုအပ်သည်)")
        return

    card_id, name, anime, rarity, media_url = parts[0], parts[1], parts[2], parts[3], parts[4]

    # ကတ် ID ထပ်နေခြင်း ရှိမရှိ စစ်ဆေးခြင်း
    if cards_col.find_one({"card_id": card_id}):
        await update.message.reply_text(f"❌ ဤ Card ID (`{card_id}`) မှာ ဒေတာဘေ့စ်ထဲတွင် ရှိပြီးသား ဖြစ်ပါသည်။")
        return

    # ဒေတာဘေ့စ်ထဲသို့ အသစ်ထည့်သွင်းခြင်း
    cards_col.insert_one({
        "card_id": card_id,
        "name": name,
        "anime": anime,
        "rarity": rarity.upper(),
        "image_url": media_url # ပုံ သို့မဟုတ် ဗီဒီယို Link (သို့ file_id)
    })

    await update.message.reply_text(
        f"✅ **အောင်မြင်စွာ ကတ်အသစ် ထည့်သွင်းပြီးပါပြီ!**\n\n"
        f"🆔 ID: `{card_id}`\n"
        f"🌸 အမည်: **{name}**\n"
        f"📺 အန်နီမဲ: {anime}\n"
        f"⭐ ရှားပါးမှု: {rarity.upper()}\n"
        f"🖼️ Media: {media_url}",
        parse_mode="Markdown"
    )

async def delete_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ကတ်ဖျက်ရန် - /delete [Card ID]"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ ဤ Command ကို Owner များသာ သုံးနိုင်ပါသည်။")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ဖျက်လိုသော Card ID ကို ထည့်ပါ (ဥပမာ - `/delete c004`)")
        return

    card_id = context.args[0]
    result = cards_col.delete_one({"card_id": card_id})

    if result.deleted_count > 0:
        await update.message.reply_text(f"🗑️ Card ID `{card_id}` ကို ဒေတာဘေ့စ်ထဲမှ ဖျက်ထုတ်လိုက်ပါပြီ။", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ ဤ Card ID (`{card_id}`) ကို မတွေ့ရှိပါ။")
