from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import REQUIRED_GROUP_LINK, REQUIRED_CHANNEL_LINK

def get_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(" My Waifu", url="https://t.me/c/4461314187/10360")],
        [InlineKeyboardButton(" Group", url=REQUIRED_GROUP_LINK),
         InlineKeyboardButton(" Channel", url=REQUIRED_CHANNEL_LINK)]
    ])

def get_force_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Group", url=REQUIRED_GROUP_LINK)],
        [InlineKeyboardButton("Join Channel", url=REQUIRED_CHANNEL_LINK)]
    ])

def get_hmode_keyboard():
    buttons = []
    for i in range(1, 14, 3):
        row = [InlineKeyboardButton(f"Tier {j}", callback_data=f"hmode_{j}") for j in range(i, min(i+3, 14))]
        buttons.append(row)
    buttons.append([InlineKeyboardButton(" Reset Filter", callback_data="hmode_reset")])
    return InlineKeyboardMarkup(buttons)
