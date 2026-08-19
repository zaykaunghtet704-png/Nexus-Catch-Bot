import os

# Render Environment Variables မှ ယူမည် (သို့မဟုတ် တိုက်ရိုက်ထည့်ပါ)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8823072889:AAHKIzIzYVm4CjRJzoJWCktJhI5ZYn4mn4Y")
OWNER_IDS = [7974865879, 7869852655]

SPAWN_THRESHOLD = 5   # Message ၅ စာ ရိုက်လျှင် ၁ ကတ် ကျမည်
PORT = int(os.getenv("PORT", 8080))
