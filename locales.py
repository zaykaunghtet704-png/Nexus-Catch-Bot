TEXTS = {
    'my': {
        'low_group': "⚠️ *ဤ Group တွင် အဖွဲ့ဝင်ဦးရေ {count} ဦးသာ ရှိပါသည် (အနည်းဆုံး ၅၀ ဦး လိုအပ်ပါသည်)* ❌\n\nကျေးဇူးပြု၍ အုံနာထံ ခွင့်တောင်းပါရှင်။",
        'force_join_msg': "⚠️ *ဘော့တ်ကို အသုံးပြုရန် အောက်ပါ Group နှင့် Channel တို့ကို အရင် Join ပေးပါရှင်။*",
        'welcome': "✨ **မင်္ဂလာပါရှင် Mr/Ms. {name}** ✨\n\n💎 Telegram ၏ အမိုက်ဆုံး **Ultimate Card & Gacha Bot** မှ ကြိုဆိုပါတယ်ရှင်။",
        'footer': "\n\n⚡ *Powered by 'maybe'*"
    },
    'en': {
        'low_group': "⚠️ *This group has only {count} members (Minimum 50 required)* ❌\n\nPlease request permission from the owner.",
        'force_join_msg': "⚠️ *Please join our Group and Channel before using this bot!*",
        'welcome': "✨ **Welcome Mr/Ms. {name}** ✨\n\n💎 Welcome to the **Ultimate Card & Gacha Bot**!",
        'footer': "\n\n⚡ *Powered by 'maybe'*"
    }
}

def get_text(lang, key, **kwargs):
    text = TEXTS.get(lang, TEXTS['my']).get(key, "")
    return text.format(**kwargs) if kwargs else text
