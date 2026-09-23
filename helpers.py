from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import GROUP_LINK, CHANNEL_LINK, OWNER_ID, OWNER_USERNAME
from database import users_col, bans_col

async def check_forced_sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        return True
        
    # Check ban status
    if bans_col.find_one({"user_id": user_id}):
        await update.message.reply_text("⛔ You are banned from using this bot.")
        return False

    keyboard = [
        [InlineKeyboardButton("📢 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("⭐ Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check group/channel membership using telegram chat member API
    try:
        group_member = await context.bot.get_chat_member(chat_id="@00J7JktW8bJlZTY1", user_id=user_id) # Replace with actual username/id if public
        # For private invites, usually we handle via bot middleware or prompt user once.
    except Exception:
        pass
    
    return True

async def send_with_footer(update: Update, text: str, reply_markup=None):
    footer = "\n\n✨ *Powered by maybe* 💫"
    full_text = text + footer
    sent_msg = await update.message.reply_text(full_text, reply_markup=reply_markup, parse_mode="Markdown")
    
    # Optional: Automatically delete or edit out the footer after a few seconds if desired, or keep it fleeting.
