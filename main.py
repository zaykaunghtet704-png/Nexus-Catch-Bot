from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, LOG_CHANNEL_ID
from database import db
from handlers import (
    start_cmd, help_cmd, harem_cmd, hmode_cmd, profile_cmd,
    view_card_cmd, add_sudo_cmd, sudolist_cmd
)

async def on_bot_join_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat = update.effective_chat
            user = update.effective_user
            members_cnt = await chat.get_member_count()
            bot_stat = await chat.get_member(context.bot.id)

            if members_cnt < 50 or bot_stat.status != ChatMember.ADMINISTRATOR:
                await chat.leave()
                return

            log = (
                f"🤖 **Bot Joined New Group!**\n"
                f"📛 **Group**: {chat.title}\n"
                f"🆔 **ID**: `{chat.id}`\n"
                f"👥 **Members**: {members_cnt}\n"
                f"👤 **Added By**: {user.first_name} (`{user.id}`)"
            )
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Register Command Handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("harem", harem_cmd))
    app.add_handler(CommandHandler("hmode", hmode_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("view", view_card_cmd))
    app.add_handler(CommandHandler("sudo", add_sudo_cmd))
    app.add_handler(CommandHandler("sudolist", sudolist_cmd))

    # Event Handlers
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_bot_join_group))

    print("NEXUS CATCH BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
