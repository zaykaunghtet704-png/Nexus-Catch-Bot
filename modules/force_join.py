import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, PeerIdInvalid

# ---------------------------------------------------------
# ဆာဗာ Env ထဲမှ ADMIN_IDS ကို လှမ်းဖတ်ခြင်း
# ---------------------------------------------------------
env_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in env_admins.split(",") if admin_id.strip().isdigit()]

# Memory တွင် Join ခိုင်းလိုသည့် လင့်ခ်များ သိမ်းဆည်းရန် စာရင်း
# Structure: [{"chat_id": "@channel", "title": "Main Channel", "link": "https://t.me/channel"}]
MUST_JOIN_CHATS = []


# =========================================================
# ၁။ User များ Join ထားခြင်း ရှိမရှိ စစ်ဆေးသည့် Function
# =========================================================
async def check_must_join(bot: Client, message: Message) -> bool:
    if not MUST_JOIN_CHATS:
        return True

    user_id = message.from_user.id
    not_joined_buttons = []

    for chat in MUST_JOIN_CHATS:
        try:
            member = await bot.get_chat_member(chat["chat_id"], user_id)
            if member.status in ["banned", "kicked"]:
                await message.reply_text("❌ သင်သည် လိုအပ်သော Channel မှ Ban ခံထားရသဖြင့် Bot သုံးခွင့်မရှိပါ။")
                return False
        except UserNotParticipant:
            not_joined_buttons.append([
                InlineKeyboardButton(chat["title"], url=chat["link"])
            ])
        except (ChatAdminRequired, PeerIdInvalid):
            continue
        except Exception as e:
            print(f"Error checking join status: {e}")
            continue

    if not_joined_buttons:
        bot_username = (await bot.get_me()).username
        not_joined_buttons.append([
            InlineKeyboardButton("✅ Join ပြီးပါပြီ (ပြန်လည်စစ်ဆေးမည်)", url=f"https://t.me/{bot_username}?start=start")
        ])

        await message.reply_text(
            "⚠️ **Bot ကို အသုံးပြုရန်အတွက် အောက်ပါ လင့်ခ်များအားလုံးကို မဖြစ်မနေ Join ပေးရပါမည်။**\n\n"
            "အောက်ပါ Button များကို နှိပ်၍ Join ပြီးမှ **'✅ Join ပြီးပါပြီ'** ကို နှိပ်ပါ။",
            reply_markup=InlineKeyboardMarkup(not_joined_buttons)
        )
        return False

    return True


# =========================================================
# ၂။ Bot ထဲမှ လင့်ခ်အသစ် ထည့်သွင်းသည့် Command (/addjoin)
# =========================================================
@Client.on_message(filters.command("addjoin") & filters.private)
async def add_must_join(bot: Client, message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply_text("❌ ဤ Command ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")

    # Format: /addjoin [Chat ID သို့မဟုတ် Username] | [Button စာသား] | [Invite Link]
    try:
        args = message.text.split(maxsplit=1)[1]
        parts = [p.strip() for p in args.split("|")]

        if len(parts) < 3:
            raise ValueError()

        chat_id_input = parts[0]
        title = parts[1]
        link = parts[2]

        # Chat ID သည် ဂဏန်း (-100xxx) ဖြစ်ပါက int သို့ ပြောင်းမည်
        chat_id = int(chat_id_input) if (chat_id_input.startswith("-") and chat_id_input[1:].isdigit()) else chat_id_input

        # List ထဲသို့ ထည့်သွင်းမည်
        chat_data = {"chat_id": chat_id, "title": title, "link": link}
        MUST_JOIN_CHATS.append(chat_data)

        await message.reply_text(
            f"✅ **Must Join လင့်ခ် အောင်မြင်စွာ ထည့်ပြီးပါပြီ!**\n\n"
            f"📢 **Chat:** `{chat_id}`\n"
            f"🏷️ **Title:** `{title}`\n"
            f"🔗 **Link:** `{link}`"
        )

    except (IndexError, ValueError):
        await message.reply_text(
            "⚠️ **အသုံးပြုပုံ မှားယွင်းနေပါသည်။**\n\n"
            "**Format:**\n"
            "`/addjoin [Chat ID သို့မဟုတ် @Username] | [Button Title] | [Invite Link]`\n\n"
            "**ဥပမာများ:**\n"
            "• `/addjoin @NexusCatchNews | 📢 Main Channel | https://t.me/NexusCatchNews`\n"
            "• `/addjoin -1001234567890 | 💬 Chat Group | https://t.me/+AbCdEfGh`"
        )


# =========================================================
# ၃။ လက်ရှိ ထည့်ထားသော လင့်ခ်များ ကြည့်သည့် Command (/joinlist)
# =========================================================
@Client.on_message(filters.command("joinlist") & filters.private)
async def list_must_join(bot: Client, message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    if not MUST_JOIN_CHATS:
        return await message.reply_text("ℹ️ လက်ရှိတွင် Join ခိုင်းထားသော လင့်ခ်များ မရှိသေးပါ။")

    text = "📋 **Must Join Links စာရင်း:**\n\n"
    for idx, chat in enumerate(MUST_JOIN_CHATS, 1):
        text += f"`{idx}.` **{chat['title']}** (`{chat['chat_id']}`)\n🔗 {chat['link']}\n\n"

    await message.reply_text(text)


# =========================================================
# ၄။ လင့်ခ် ပြန်ဖျက်သည့် Command (/deljoin)
# =========================================================
@Client.on_message(filters.command("deljoin") & filters.private)
async def del_must_join(bot: Client, message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        idx_to_del = int(message.text.split()[1]) - 1
        if 0 <= idx_to_del < len(MUST_JOIN_CHATS):
            removed = MUST_JOIN_CHATS.pop(idx_to_del)
            await message.reply_text(f"🗑️ **{removed['title']}** ကို Must Join စာရင်းမှ ဖျက်လိုက်ပါပြီ။")
        else:
            await message.reply_text("❌ မှားယွင်းသော နံပါတ်ဖြစ်ပါသည်။ `/joinlist` ဖြင့် ပြန်စစ်ပါ။")
    except (IndexError, ValueError):
        await message.reply_text("⚠️ **အသုံးပြုပုံ:** `/deljoin [ဖျက်ချင်သည့် နံပါတ်]` (ဥပမာ: `/deljoin 1`)")
