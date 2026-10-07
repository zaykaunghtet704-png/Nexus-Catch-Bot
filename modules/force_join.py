from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, PeerIdInvalid

# ---------------------------------------------------------
# မိမိ Join ခိုင်းလိုသော Channel / Group များကို ဒီမှာ ပြင်ပါ
# ---------------------------------------------------------
MUST_JOIN_CHATS = [
    {
        "chat_id": "@NexusCatchNews",  # Public Channel ဆိုလျှင် @ ထည့်ပါ
        "title": "📢 Main Channel သို့ Join ရန်",
        "link": "https://t.me/NexusCatchNews"
    },
    {
        "chat_id": -1001234567890,     # Private Channel ဆိုလျှင် ID ထည့်ပါ
        "title": "💬 Chat Group သို့ Join ရန်",
        "link": "https://t.me/+AbCdEfGhIjK12345"
    }
]

async def check_must_join(bot: Client, message: Message) -> bool:
    """User က Channel အားလုံးကို Join ထားခြင်း ရှိမရှိ စစ်ဆေးပေးမည့် Function"""
    user_id = message.from_user.id
    not_joined_buttons = []

    for chat in MUST_JOIN_CHATS:
        try:
            # User သည် Channel ထဲတွင် ရှိမရှိ စစ်ဆေးခြင်း
            member = await bot.get_chat_member(chat["chat_id"], user_id)
            if member.status in ["banned", "kicked"]:
                await message.reply_text("❌ သင်သည် လိုအပ်သော Channel မှ Ban ခံထားရသဖြင့် Bot သုံးခွင့်မရှိပါ။")
                return False
                
        except UserNotParticipant:
            # Join မထားသေးသော Channel များကို Button စာရင်းထဲ ထည့်မည်
            not_joined_buttons.append([
                InlineKeyboardButton(chat["title"], url=chat["link"])
            ])
        except (ChatAdminRequired, PeerIdInvalid):
            print(f"⚠️ Warning: Bot ကို {chat['chat_id']} ထဲတွင် Admin အဖြစ် မခန့်ရသေးပါ။")
            continue
        except Exception as e:
            print(f"Error checking join status: {e}")
            continue

    # Join ရန် ကျန်နေသော Channel များ ရှိနေပါက
    if not_joined_buttons:
        bot_username = (await bot.get_me()).username
        
        # '✅ Join ပြီးပါပြီ' ခလုတ်ကို အောက်ဆုံးတွင် ထည့်မည်
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
