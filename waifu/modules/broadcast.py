import asyncio
from telegram import Update
from telegram.error import Forbidden, BadRequest, RetryAfter
from telegram.ext import CallbackContext, CommandHandler
from waifu import (
    application,
    top_global_groups_collection,
    pm_users,
    OWNER_ID,
    LOGGER,
)

_SEM = asyncio.Semaphore(15)  # Telegram limits ချိန်ညှိထားသည်
_DELAY = 0.05


async def _copy(bot, chat_id: int, from_chat: int, msg_id: int) -> bool:
    async with _SEM:
        try:
            await bot.copy_message(chat_id=chat_id, from_chat_id=from_chat, message_id=msg_id)
            await asyncio.sleep(_DELAY)
            return True
        except RetryAfter as e:
            # Rate limit မိပါက စောင့်ပြီး ပြန်လည် ကြိုးစားမည်
            await asyncio.sleep(e.retry_after)
            try:
                await bot.copy_message(chat_id=chat_id, from_chat_id=from_chat, message_id=msg_id)
                return True
            except Exception:
                return False
        except (Forbidden, BadRequest) as e:
            LOGGER.debug("Broadcast skip %s: %s", chat_id, e)
        except Exception as e:
            LOGGER.warning("Broadcast err %s: %s", chat_id, e)
    return False


async def broadcast(update: Update, context: CallbackContext) -> None:
    if not update.effective_user or update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Owner သာ သုံးစွဲခွင့်ရှိသည်။")
        return

    src = update.message.reply_to_message
    if not src:
        await update.message.reply_text("⚠️ Broadcast လုပ်ချင်သည့် စာကို Reply ပြန်ပြီး Command ရိုက်ပါ။")
        return

    # Database မှ Group နှင့် User ID များကို ယူခြင်း
    groups = await top_global_groups_collection.distinct("group_id")
    if not groups:
        groups = await top_global_groups_collection.distinct("chat_id")

    users = await pm_users.distinct("user_id")
    if not users:
        users = await pm_users.distinct("_id")

    # ID မဟုတ်သော/မှားယွင်းနေသော Target များကို စစ်ထုတ်ခြင်း
    targets = list(set([int(x) for x in (groups + users) if str(x).replace("-", "").isdigit()]))
    total = len(targets)

    if total == 0:
        await update.message.reply_text("❌ Broadcast ပို့ရန် Target Group/User မရှိသေးပါ။")
        return

    status = await update.message.reply_text(f"📢 Target {total} ခုသို့ စာစတင် ပို့ဆောင်နေပါပြီ…")

    ok = 0
    fail = 0

    # FloodLimit မမိစေရန် Chunk လိုက် ခွဲ၍ ပို့ဆောင်ခြင်း
    chunk_size = 20
    for i in range(0, total, chunk_size):
        chunk = targets[i : i + chunk_size]
        tasks = [_copy(context.bot, t, src.chat_id, src.message_id) for t in chunk]
        results = await asyncio.gather(*tasks)
        
        ok += sum(results)
        fail += results.count(False)
        
        # ၅၀ ခု ပို့ပြီးတိုင်း Status UPDATE ပေးခြင်း
        if (i + chunk_size) % 50 == 0 or (i + chunk_size) >= total:
            try:
                await status.edit_text(
                    f"📢 Broadcasting… ({min(i + chunk_size, total)}/{total})\n"
                    f"✔️ Delivred: {ok}\n"
                    f"❌ Failed: {fail}"
                )
            except Exception:
                pass

    await status.edit_text(
        f"✅ **Broadcast ပို့ဆောင်မှု ပြီးစီးပါပြီ!**\n\n"
        f"🎯 စုစုပေါင်း: `{total}`\n"
        f"✔️ အောင်မြင်: `{ok}`\n"
        f"❌ မအောင်မြင်: `{fail}`",
        parse_mode="Markdown",
    )


application.add_handler(CommandHandler("broadcast", broadcast, block=False))
