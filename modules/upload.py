import re
import aiohttp
from pymongo import ReturnDocument
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

# Config နှင့် Database Import ပြုလုပ်ခြင်း
try:
    from config import OWNER_ID, CHARA_CHANNEL_ID
except ImportError:
    OWNER_ID = 0
    CHARA_CHANNEL_ID = 0

from database import db, cards_col, sudo_col

# ── Rarity အဆင့် ၁၃ မျိုး အပြည့်အစုံ ──────────────────────────────────────────
RARITY_MAP = {
    1: "⚪ Common",
    2: "🟢 Uncommon",
    3: "🔵 Rare",
    4: "🟣 Epic",
    5: "🟡 Legendary",
    6: "🔴 Mythic",
    7: "🟠 Ancient",
    8: "🔮 Divine",
    9: "👑 Immortal",
    10: "🌌 Cosmic",
    11: "🔱 Primordial",
    12: "👁️ Omnipotent",
    13: "♾️ Transcendent"
}

RARITY_STRS = {v.lower(): v for v in RARITY_MAP.values()}
RARITY_STRS.update({
    "common": "⚪ Common",
    "uncommon": "🟢 Uncommon",
    "rare": "🔵 Rare",
    "epic": "🟣 Epic",
    "legendary": "🟡 Legendary",
    "mythic": "🔴 Mythic",
    "ancient": "🟠 Ancient",
    "divine": "🔮 Divine",
    "immortal": "👑 Immortal",
    "cosmic": "🌌 Cosmic",
    "primordial": "🔱 Primordial",
    "omnipotent": "👁️ Omnipotent",
    "transcendent": "♾️ Transcendent",
    "crossverse": "💎 CrossVerse",
    "cataphract": "⚔️ Cataphract",
    "supreme": "🔮 Supreme"
})

WRONG_FORMAT = (
    "❌ <b>အသုံးပြုပုံ မှားယွင်းနေပါသည်။</b>\n\n"
    "<code>/upload IMG_URL character-name anime-name rarity_number</code>\n\n"
    "<b>Rarity နံပါတ်များ (1 မှ 13):</b>\n"
    + "\n".join(f"  {k} → {v}" for k, v in RARITY_MAP.items())
)

def _is_sudo(uid: int) -> bool:
    """Owner သို့မဟုတ် Sudo User ဟုတ်မဟုတ် စစ်ဆေးခြင်း"""
    if uid == OWNER_ID:
        return True
    try:
        s = sudo_col.find_one({"user_id": uid})
        if s:
            return True
    except Exception:
        pass
    return False

async def _validate_url(url: str) -> bool:
    """URL အလုပ်လုပ်မလုပ် စစ်ဆေးခြင်း"""
    try:
        async with aiohttp.ClientSession() as s:
            async with s.head(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                return r.status < 400
    except Exception:
        return False

def _next_id() -> str:
    """PyMongo Synchronous Safe Auto-increment ID Generation"""
    try:
        doc = db["sequences"].find_one_and_update(
            {"_id": "character_id"},
            {"$inc": {"sequence_value": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return str(doc["sequence_value"]).zfill(4)
    except Exception:
        import random
        return str(random.randint(1000, 9999))

def _char_caption(char: dict, uploader_id: int, uploader_name: str) -> str:
    return (
        f"🍀 <b>Name:</b> {char['name']}\n"
        f"🍋 <b>Rarity:</b> {char['rarity']}\n"
        f"🌸 <b>Anime:</b> {char['anime']}\n"
        f"🌱 <b>ID:</b> {char['id']}\n\n"
        f"Added by <a href='tg://user?id={uploader_id}'>{uploader_name}</a>"
    )

# ── Method 1: /upload ─────────────────────────────────────────────────────────

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_sudo(update.effective_user.id):
        await update.message.reply_text("❌ Bot Owner / Sudo User သာ အသုံးပြုနိုင်ပါသည်။")
        return

    if len(context.args) != 4:
        await update.message.reply_text(WRONG_FORMAT, parse_mode=ParseMode.HTML)
        return

    img_url, raw_name, raw_anime, raw_rarity = context.args

    if not await _validate_url(img_url):
        await update.message.reply_text("❌ ပုံ၏ URL မှားယွင်းနေသည် (သို့) ဝင်ရောက်၍မရပါ။")
        return

    try:
        rarity = RARITY_MAP[int(raw_rarity)]
    except (KeyError, ValueError):
        await update.message.reply_text(
            f"❌ Rarity နံပါတ် မှားယွင်းနေပါသည်။ 1 မှ {len(RARITY_MAP)} အတွင်းသာ အသုံးပြုပါ။", parse_mode=ParseMode.HTML)
        return

    name    = raw_name.replace("-", " ").title()
    anime   = raw_anime.replace("-", " ").title()
    char_id = _next_id()
    char    = {"img_url": img_url, "name": name, "anime": anime,
               "rarity": rarity, "id": char_id}

    try:
        msg = await context.bot.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=img_url,
            caption=_char_caption(char, update.effective_user.id, update.effective_user.first_name),
            parse_mode=ParseMode.HTML,
        )
        char["message_id"] = msg.message_id
        cards_col.insert_one(char)
        await update.message.reply_text(
            f"✅ <b>{name}</b> ကို အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ!\n"
            f"🎴 Rarity: {rarity}\n"
            f"📺 Anime: {anime}\n"
            f"🆔 ID: <code>{char_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Channel သို့ ပို့ရာတွင် အခက်အခဲဖြစ်ပေါ်နေပါသည်: {e}\nကတ်ကို Database တွင် <b>မသိမ်းဆည်းရသေးပါ။</b>",
            parse_mode=ParseMode.HTML,
        )

# ── Method 2: /uploadchar (Reply to photo with caption) ─────────────────────

def _parse_caption(caption: str) -> dict | None:
    fields: dict[str, str] = {}
    patterns = {
        "name":   r"(?:🍀\s*)?Name\s*:\s*(.+)",
        "rarity": r"(?:🍋\s*)?Rarity\s*:\s*(.+)",
        "anime":  r"(?:🌸\s*)?Anime\s*:\s*(.+)",
        "id":     r"(?:🌱\s*)?ID\s*:\s*(\S+)",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, caption, re.IGNORECASE)
        if m:
            fields[key] = m.group(1).strip()

    if "name" not in fields or "anime" not in fields:
        return None

    raw_rarity = fields.get("rarity", "").lower()
    rarity = RARITY_STRS.get(raw_rarity)
    if not rarity:
        for key, val in RARITY_STRS.items():
            if raw_rarity in key or key in raw_rarity:
                rarity = val
                break
    if not rarity:
        rarity = "⚪ Common"   

    return {
        "name":   fields["name"].title(),
        "anime":  fields["anime"].title(),
        "rarity": rarity,
        "id":     fields.get("id"),       
    }

async def uploadchar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_sudo(update.effective_user.id):
        await update.message.reply_text("❌ Bot Owner / Sudo User သာ အသုံးပြုနိုင်ပါသည်။")
        return

    replied = update.message.reply_to_message
    if not replied:
        await update.message.reply_text(
            "❌ ပုံနှင့် Caption ပါသော Message ကို Reply ပြန်၍ အသုံးပြုပါ။",
            parse_mode=ParseMode.HTML,
        )
        return

    photo = None
    if replied.photo:
        photo = replied.photo[-1].file_id   
    elif replied.document and replied.document.mime_type.startswith("image/"):
        photo = replied.document.file_id
    else:
        await update.message.reply_text("❌ Reply လုပ်ထားသော Message တွင် ပုံပါဝင်ရပါမည်။")
        return

    caption = replied.caption or replied.text or ""
    parsed  = _parse_caption(caption)
    if not parsed:
        await update.message.reply_text(
            "❌ Caption ဖွဲ့စည်းပုံ မှားယွင်းနေပါသည်။ <b>Name</b> နှင့် <b>Anime</b> ပါဝင်ရန် လိုအပ်သည်။",
            parse_mode=ParseMode.HTML,
        )
        return

    if parsed["id"]:
        try:
            existing = cards_col.find_one({"id": parsed["id"]})
        except Exception:
            existing = None
        if existing:
            await update.message.reply_text(
                f"❌ ID <code>{parsed['id']}</code> သည် Database တွင် ရှိနှင့်ပြီးသား ဖြစ်သည်။",
                parse_mode=ParseMode.HTML,
            )
            return
        char_id = parsed["id"]
    else:
        char_id = _next_id()

    char = {
        "img_url": photo,           
        "name":    parsed["name"],
        "anime":   parsed["anime"],
        "rarity":  parsed["rarity"],
        "id":      char_id,
    }

    try:
        msg = await context.bot.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=photo,
            caption=_char_caption(char, update.effective_user.id, update.effective_user.first_name),
            parse_mode=ParseMode.HTML,
        )
        char["message_id"] = msg.message_id
        cards_col.insert_one(char)
        await update.message.reply_text(
            f"✅ <b>{parsed['name']}</b> ကို ထည့်သွင်းပြီးပါပြီ!\n"
            f"🎴 Rarity: {parsed['rarity']}\n"
            f"📺 Anime: {parsed['anime']}\n"
            f"🆔 ID: <code>{char_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Channel သို့ ပို့ရာတွင် အခက်အခဲဖြစ်ပေါ်နေပါသည်: {e}\nကတ်ကို <b>မသိမ်းဆည်းရသေးပါ။</b>",
            parse_mode=ParseMode.HTML,
        )

# ── /delete ───────────────────────────────────────────────────────────────────

async def delete_char(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_sudo(update.effective_user.id):
        await update.message.reply_text("❌ Bot Owner / Sudo User သာ အသုံးပြုနိုင်ပါသည်။")
        return
    if len(context.args) != 1:
        await update.message.reply_text(
            "အသုံးပြုရန်: <code>/delete ID</code>", parse_mode=ParseMode.HTML)
        return

    try:
        char = cards_col.find_one_and_delete({"id": context.args[0]})
    except Exception:
        char = None

    if not char:
        await update.message.reply_text("❌ ထို ID ဖြင့် ကတ်ကို ရှာမတွေ့ပါ။")
        return
    if char.get("message_id"):
        try:
            await context.bot.delete_message(CHARA_CHANNEL_ID, char["message_id"])
        except Exception:
            pass
    await update.message.reply_text(
        f"✅ <b>{char['name']}</b> (<code>{char['id']}</code>) ကို ဖျက်လိုက်ပါပြီ။",
        parse_mode=ParseMode.HTML,
    )

# ── /update ───────────────────────────────────────────────────────────────────

_VALID = {"img_url", "name", "anime", "rarity"}

async def update_char(upd: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_sudo(upd.effective_user.id):
        await upd.message.reply_text("❌ Bot Owner / Sudo User သာ အသုံးပြုနိုင်ပါသည်။")
        return
    if len(context.args) < 3:
        await upd.message.reply_text(
            "အသုံးပြုရန်: <code>/update ID field new_value</code>\n"
            f"ပြင်ဆင်နိုင်သော အချက်အလက်များ: {', '.join(_VALID)}",
            parse_mode=ParseMode.HTML,
        )
        return

    char_id = context.args[0]
    field = context.args[1]
    raw = " ".join(context.args[2:])

    if field not in _VALID:
        await upd.message.reply_text(f"❌ အချက်အလက်အမည် မှားယွင်းနေပါသည်။ {', '.join(_VALID)} ထဲမှ ရွေးချယ်ပါ။")
        return

    try:
        char = cards_col.find_one({"id": char_id})
    except Exception:
        char = None

    if not char:
        await upd.message.reply_text("❌ ထို ID ဖြင့် ကတ်ကို ရှာမတွေ့ပါ။")
        return

    if field in ("name", "anime"):
        new_val = raw.replace("-", " ").title()
    elif field == "rarity":
        try:
            new_val = RARITY_MAP[int(raw)]
        except (KeyError, ValueError):
            await upd.message.reply_text(f"❌ Rarity နံပါတ် မှားယွင်းနေပါသည်။ 1 မှ {len(RARITY_MAP)} အတွင်းသာ အသုံးပြုပါ။")
            return
    elif field == "img_url":
        if not await _validate_url(raw):
            await upd.message.reply_text("❌ ပုံ၏ URL မှားယွင်းနေသည် (သို့) ဝင်ရောက်၍မရပါ။")
            return
        new_val = raw
    else:
        new_val = raw

    try:
        cards_col.update_one({"id": char_id}, {"$set": {field: new_val}})
    except Exception as e:
        await upd.message.reply_text(f"❌ Database update အဆင်မပြေပါ: {e}")
        return

    char[field] = new_val

    try:
        if field == "img_url":
            if char.get("message_id"):
                try:
                    await context.bot.delete_message(CHARA_CHANNEL_ID, char["message_id"])
                except Exception:
                    pass
            msg = await context.bot.send_photo(
                CHARA_CHANNEL_ID, photo=new_val,
                caption=_char_caption(char, upd.effective_user.id, upd.effective_user.first_name),
                parse_mode=ParseMode.HTML,
            )
            cards_col.update_one({"id": char_id}, {"$set": {"message_id": msg.message_id}})
        elif char.get("message_id"):
            await context.bot.edit_message_caption(
                CHARA_CHANNEL_ID, char["message_id"],
                caption=_char_caption(char, upd.effective_user.id, upd.effective_user.first_name),
                parse_mode=ParseMode.HTML,
            )
    except Exception as e:
        await upd.message.reply_text(f"⚠️ Database ထဲတွင် ပြင်ဆင်ပြီးသော်လည်း Channel သို့ ပို့ရာတွင် အခက်အခဲရှိနေသည်: {e}")
        return

    await upd.message.reply_text(
        f"✅ <b>{char['name']}</b> ၏ <code>{field}</code> ကို ပြင်ဆင်ပြီးပါပြီ။",
        parse_mode=ParseMode.HTML,
    )

# ── Handlers များကို Main File သို့ လှမ်းပေးရန် ────────────────────────────────
def get_upload_handlers():
    return [
        CommandHandler("upload", upload, block=False),
        CommandHandler("uploadchar", uploadchar, block=False),
        CommandHandler("delete", delete_char, block=False),
        CommandHandler("update", update_char, block=False)
    ]
