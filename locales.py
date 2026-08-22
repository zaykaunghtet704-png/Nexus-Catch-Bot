TEXTS = {
    'my': {
        'group_low_members': "⚠️ *ဤ Group တွင် အဖွဲ့ဝင်ဦးရေ {count} ဦးသာ ရှိပါသည် (အနည်းဆုံး ၅၀ ဦး လိုအပ်သည်)* ❌\n\nကျေးဇူးပြု၍ အုံနာထံ ခွင့်တောင်းပါရှင်။ ID: `{owner_id}`",
        'force_join': "⚠️ *ဘော့တ်ကို အသုံးပြုရန် အောက်ပါ Channel နှင့် Group တို့ကို အရင် Join ပေးပါရှင်။*",
        'welcome': "✨ **မင်္ဂလာပါရှင် Mr/Ms. {name}** ✨\n\n💎 Telegram ၏ အမိုက်ဆုံး **Ultimate Card & Gacha Bot** မှ ကြိုဆိုပါတယ်ရှင်။",
        'no_card': "🎒 သင့်ထံတွင် ကဒ်များ မရှိသေးပါ။ `/claim` သို့မဟုတ် `/nexus` ဖြင့် ကဒ်များ စုဆောင်းပါရှင်။",
        'daily_success': "🎁 **Daily Reward!** Coins 500 ရရှိပါသည်ရှင်။ လက်ကျန်: `{coins}` Coins 🪙",
        'footer': "\n\n⚡ *Powered by 'maybe'*"
    },
    'en': {
        'group_low_members': "⚠️ *This group has only {count} members (Minimum 50 required)* ❌\n\nPlease request permission from the owner. ID: `{owner_id}`",
        'force_join': "⚠️ *Please join our Channel and Group to use this bot!*",
        'welcome': "✨ **Welcome Mr/Ms. {name}** ✨\n\n💎 Welcome to the **Ultimate Card & Gacha Bot**!",
        'no_card': "🎒 You don't have any cards yet. Use `/claim` or `/nexus` to collect cards!",
        'daily_success': "🎁 **Daily Reward!** You received 500 Coins! Balance: `{coins}` Coins 🪙",
        'footer': "\n\n⚡ *Powered by 'maybe'*"
    }
}

def get_text(lang, key, **kwargs):
    text = TEXTS.get(lang, TEXTS['my']).get(key, "")
    return text.format(**kwargs) if kwargs else text
