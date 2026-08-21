from telegram.inlinekeyboardbuilder import InlineKeyboardBuilder

# ကဒ်အဆင့် ၁၃ ဆင့် သတ်မှတ်ခြင်း
TIER_NAMES = [
    "Common",           # 1
    "Uncommon",         # 2
    "Rare",             # 3
    "Epic",             # 4
    "Legendary",        # 5
    "Mythic",           # 6
    "Celestial",        # 7
    "Divine",           # 8
    "Radiant",          # 9
    "Supreme",          # 10
    "Immortal",         # 11
    "Exclusive",        # 12
    "Premium Edition"   # 13
]

def get_hmode_keyboard():
    builder = InlineKeyboardBuilder()
    # ၁၃ ခုလုံးအတွက် ခလုတ်များ တည်ဆောက်ခြင်း
    for i, name in enumerate(TIER_NAMES, 1):
        builder.button(text=f"✨ T{i}: {name}", callback_data=f"hmode_{i}")
    
    builder.button(text="🔄 Reset Filter", callback_data="hmode_reset")
    # ခလုတ်များ အဆင်ပြေအောင် ချိန်ညှိခြင်း (၂ ခုစီ တန်းစီ)
    builder.adjust(2) 
    return builder.as_markup()

# အခြားသော လိုအပ်တဲ့ Keyboard များ (လိုအပ်ပါက ထည့်ပါ)
def get_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 ဈေးကွက် (Market)", callback_data="market_main")
    builder.button(text="📖 အကူအညီ (Help)", callback_data="help_p1")
    builder.adjust(2)
    return builder.as_markup()
