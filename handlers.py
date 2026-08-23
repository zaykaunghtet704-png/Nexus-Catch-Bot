# handlers.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services import check_force_join, generate_math_challenge_drop
from config import OWNER_IDS, RARITIES

# --- Force Join & Harem Command ---
@Client.on_message(filters.command("harem") & filters.group)
async def harem_command(client, message):
    user_id = message.from_user.id
    is_joined = await check_force_join(client, user_id)
    
    if not is_joined:
        buttons = [
            [InlineKeyboardButton("📢 Join Channel", url="https://t.me/+E6BxfAj0gaI2Y2Zl")],
            [InlineKeyboardButton("👥 Join Group", url="https://t.me/+00J7JktW8bJlZTY1")],
            [InlineKeyboardButton("✅ Joined, Check Again", callback_data="recheck_join")]
        ]
        await message.reply(
            "⚠️ **Harem ကို မကြည့်ရှုမီ အောက်ပါ ချန်နယ်နှင့် ဂျီပီ နှစ်ခုကို မဖြစ်မနေ Join ပေးပါရန် တောင်းဆိုအပ်ပါသည်။**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    await message.reply("✨ **Welcome to your Harem Collection!** Select options below to manage your cards.")

# --- HMode Callback UI Flow ---
@Client.on_message(filters.command("hmode") & filters.group)
async def hmode_command(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 DEFAULT", callback_data="hm_default"), InlineKeyboardButton("📋 DETAILED", callback_data="hm_detailed")],
        [InlineKeyboardButton("❌ Close", callback_data="hm_close")]
    ])
    await message.reply("⚙️ **Step 1:** Choose your Harem Interface Display Mode:", reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^hm_detailed$"))
async def hmode_detailed(client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 SORT BY RARITY / EVENT", callback_data="hm_rarity_event")],
        [InlineKeyboardButton("🎬 SORT BY ANIME", callback_data="hm_anime")],
        [InlineKeyboardButton("🔙 Back", callback_data="hm_back")]
    ])
    await callback_query.message.edit_text("⚙️ **Step 2:** Select sorting preference for Detailed view:", reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^hm_rarity_event$"))
async def hmode_rarity_event(client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌟 Rarity Categories", callback_data="hm_rarity_list"), InlineKeyboardButton("🎉 Event Cards", callback_data="hm_event_list")],
        [InlineKeyboardButton("🔙 Back", callback_data="hm_detailed")]
    ])
    await callback_query.message.edit_text("⚙️ **Step 3:** Choose between Rarity or Special Events:", reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^hm_rarity_list$"))
async def hmode_rarity_list(client, callback_query):
    buttons = [
        [InlineKeyboardButton(f"{data['emoji']} {name}", callback_data=f"filter_{name}")] 
        for name, data in list(RARITIES.items())[:6]
    ]
    buttons.append([InlineKeyboardButton("➡️ Next Page (Rarities)", callback_data="hm_rarity_page2")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="hm_rarity_event")])
    
    await callback_query.message.edit_text("⚙️ **Step 4:** Select specific Rarity level:", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^hm_event_list$"))
async def hmode_event_list(client, callback_query):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🐰 Bunny Event", callback_data="ev_bunny"), InlineKeyboardButton("🧹 Maid Event", callback_data="ev_maid")],
        [InlineKeyboardButton("☀️ Summer Event", callback_data="ev_summer")],
        [InlineKeyboardButton("🔙 Back", callback_data="hm_rarity_event")]
    ])
    await callback_query.message.edit_text("🎭 **Step 4 (Events):** Select Event Type:", reply_markup=keyboard)

# --- Game Commands (/catch, /claim, /profile, etc.) ---
@Client.on_message(filters.command("catch") & filters.group)
async def catch_command(client, message):
    await message.reply("🏃‍♂️ **THE CHARACTER HAS ESCAPED! WAIT FOR A NEW CHARACTER TO SPAWN.**")

@Client.on_message(filters.command("claim") & filters.group)
async def claim_command(client, message):
    user_name = message.from_user.first_name
    await message.reply(f"Congratulations, {user_name}! 🎉 Character claimed successfully into your collection.")

@Client.on_message(filters.command("profile") & filters.group)
async def profile_command(client, message):
    user = message.from_user
    profile_text = (
        f"👤 **USER:** {user.first_name}\n"
        f"🆔 **USER ID:** `{user.id}`\n"
        f"📦 **TOTAL CHARACTER:** 42\n"
        f"🏰 **HAREM:** Active Collection\n"
        f"📈 **EXPERIENCE LEVEL:** Level 15 [████████░░] 80%\n"
        f"🏆 **GLOBAL POSITION:** #142"
    )
    await message.reply(profile_text)

# --- OWNER & ADMIN CONTROL COMMANDS ---
@Client.on_message(filters.command("changetime") & filters.group)
async def changetime_command(client, message):
    if message.from_user.id not in OWNER_IDS:
        await message.reply("❌ **Group admin/owner only.**")
        return
    if len(message.command) < 2:
        await message.reply("⚠️ Usage: `/changetime <number_of_messages>`")
        return
    rate = message.command[1]
    await message.reply(f"✅ Spawn rate successfully updated to **{rate} messages**!")

@Client.on_message(filters.command("maintenance") & filters.group)
async def maintenance_command(client, message):
    if message.from_user.id not in OWNER_IDS:
        await message.reply("❌ **Group admin/owner only.**")
        return
    await message.reply("🛠️ **Bot maintenance mode toggled successfully!**")

@Client.on_message(filters.command("broadcast") & filters.user(OWNER_IDS))
async def broadcast_command(client, message):
    if len(message.command) < 2:
        await message.reply("📢 Usage: `/broadcast <message>`")
        return
    text = message.text.split(None, 1)[1]
    await message.reply(f"📢 **Global Broadcast Sent:**\n\n{text}")

@Client.on_message(filters.command("ban") & filters.group)
async def ban_command(client, message):
    if message.from_user.id not in OWNER_IDS:
        await message.reply("❌ **Group admin/owner only.**")
        return
    await message.reply("🚫 **User has been successfully banned from the bot.**")

@Client.on_message(filters.command("unban") & filters.group)
async def unban_command(client, message):
    if message.from_user.id not in OWNER_IDS:
        await message.reply("❌ **Group admin/owner only.**")
        return
    await message.reply("✅ **User has been unbanned successfully.**")
