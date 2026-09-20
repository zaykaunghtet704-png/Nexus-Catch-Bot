import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler
from waifu import StartTime, application, sudo_users


def _uptime(s: float) -> str:
    s = int(s)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


async def ping(update: Update, context: CallbackContext) -> None:
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    sudo_list = [int(x) for x in sudo_users] if isinstance(sudo_users, (list, set, tuple)) else []

    if user_id not in sudo_list:
        await update.message.reply_text("❌ Sudo only.")
        return

    t0 = time.monotonic()
    msg = await update.message.reply_text("🏓 Pong!")
    ms = round((time.monotonic() - t0) * 1000, 2)

    uptime_str = _uptime(time.time() - StartTime)
    await msg.edit_text(
        f"🏓 <b>Pong!</b> <code>{ms} ms</code>\n"
        f"⏱️ Uptime: <code>{uptime_str}</code>",
        parse_mode=ParseMode.HTML,
    )


application.add_handler(CommandHandler("ping", ping, block=False))
