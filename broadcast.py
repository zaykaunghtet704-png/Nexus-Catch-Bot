import asyncio
import logging
from telegram import Update
from telegram.error import Forbidden, BadRequest
from telegram.ext import ContextTypes, CommandHandler

# သင့်ကိုယ်ပိုင် config နှင့် database ဖိုင်များမှ Import လုပ်ခြင်း
from config import OWNER_ID
from database import chats_col, users_col

logger = logging.getLogger(__name__)

# Concurrent Requests ကို ထိန်းချုပ်ရန် Semaphore သတ်မှတ်ခြင်း
_SEM   = asyncio.Semaphore(20)
_DELAY = 0.05

async def _copy(bot, chat_id: int, from_chat: int, msg_id: int) -> bool:
    async with _SEM:
        try:
            await bot.copy_message(chat_id=chat_id, from_chat_id=from_chat, message_id=msg_id)
            await asyncio.sleep(_DELAY)
            return True
        except (Forbidden, BadRequest) as e:
            logger.debug("Broadcast skip %s: %s", chat_id, e)
        except Exception as e:
            logger.warning("Broadcast err %s: %s", chat_id, e)
    return False

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Owner သာ အသုံးပြုနိုင်ရန် စစ်ဆေးခြင်း
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Bot Owner သာ အသုံးပြုနိုင်ပါသည်။")
        return

    src = update.message.reply_to_message
    if not src:
        await update.message.reply_text("❌ အခြားသူများဆီ Broadcast ပို့လိုသော Message ကို Reply ပြန်၍ /broadcast ဟု ရိုက်ပါ။")
        return

    # Database ထဲမှ Group နှင့် User ID များကို ဆွဲထုတ်ခြင်း
    groups = await chats_col.distinct("chat_id")
    users  = await users_col.distinct("user_id")
    
    # ID အထပ်ထပ်မဖြစ်စေရန် set သုံး၍ ပေါင်းစည်းခြင်း
    targets = list(set(groups + users))
    total   = len(targets)

    if total == 0:
        await update.message.reply_text("❌ Broadcast ပို့ရန် Target (User/Group) မရှိသေးပါ။")
        return

    status = await update.message.reply_text(f"📢 စုစုပေါင်း {total} ခုထံသို့ Broadcast ပို့နေပါသည်...")

    tasks = [_copy(context.bot, t, src.chat_id, src.message_id) for t in targets]
    res   = await asyncio.gather(*tasks)

    ok, fail = sum(res), res.count(False)
    await status.edit_text(
        f"✅ <b>Broadcast ပို့ဆောင်မှု ပြီးစီးပါပြီ!</b>\n\n"
        f"✔️ အောင်မြင်စွာ ပို့ပြီး: <b>{ok}</b>\n"
        f"❌ ပို့၍မရသော ပမာဏ: <b>{fail}</b>",
        parse_mode="HTML"
    )

# ── Handlers များကို Main File သို့ လှမ်းပေးရန် ────────────────────────────────
def get_broadcast_handlers():
    return [CommandHandler("broadcast", broadcast, block=False)]
