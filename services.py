import os
import time
import datetime
import random
import psutil
from PIL import Image, ImageDraw, ImageFont
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from flask import Flask, jsonify
from config import ENCRYPTION_KEY

# ---------- AES-256 ENCRYPTION SERVICE ----------
class CryptoService:
    @staticmethod
    def encrypt(data: str) -> str:
        key = ENCRYPTION_KEY.encode('utf-8')[:32].ljust(32, b'0')
        cipher = AES.new(key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
        return f"{cipher.iv.hex()}:{ct_bytes.hex()}"

    @staticmethod
    def decrypt(enc_data: str) -> str:
        try:
            key = ENCRYPTION_KEY.encode('utf-8')[:32].ljust(32, b'0')
            iv_hex, ct_hex = enc_data.split(":")
            cipher = AES.new(key, AES.MODE_CBC, bytes.fromhex(iv_hex))
            pt = unpad(cipher.decrypt(bytes.fromhex(ct_hex)), AES.block_size)
            return pt.decode('utf-8')
        except Exception:
            return enc_data

# ---------- MATH CAPTCHA VERIFICATION ----------
class CaptchaService:
    @staticmethod
    def generate_captcha():
        a, b, c = random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)
        ans = a + b + c
        q = f"{a} + {b} + {c} = ?"
        opts = {ans}
        while len(opts) < 4:
            opts.add(ans + random.randint(-5, 5))
        opts_list = list(opts)
        random.shuffle(opts_list)
        return q, ans, opts_list

# ---------- IMAGE CANVAS PROCESSING ENGINE ----------
class CanvasEngine:
    @staticmethod
    def generate_card_image(title="Astraea, Guardian", rarity="MYTHIC", print_no="#0001", mint="100%", dye_color="#FF0055", frame="Gold Neon"):
        img = Image.new("RGB", (400, 550), color="#121212")
        draw = ImageDraw.Draw(img)
        
        # Border & Dye
        border_color = dye_color if dye_color.startswith("#") else "#FFA500"
        draw.rectangle([10, 10, 390, 540], outline=border_color, width=5)
        
        # Header Info
        draw.text((20, 25), f"[{rarity}]", fill="#FFD700")
        draw.text((280, 25), f"Print {print_no}", fill="#FFFFFF")
        
        # Character Space
        draw.rectangle([30, 60, 370, 380], fill="#222222", outline="#555555")
        draw.text((110, 200), "[ CARD IMAGE ]", fill="#888888")
        
        # Stats & Cosmetics Footer
        draw.text((30, 395), f"Character: {title}", fill="#FFFFFF")
        draw.text((30, 425), f"Frame: {frame} | Dye: {dye_color}", fill="#AAAAAA")
        draw.text((30, 455), f"Condition: Mint {mint} | Font: Gothic", fill="#AAAAAA")
        draw.text((30, 490), "HP: 2,400 | ATK: 850 | DEF: 420", fill="#00FFCC")
        
        out_path = f"card_output_{random.randint(1000,9999)}.png"
        img.save(out_path)
        return out_path

# ---------- FLASK SERVER FOR RENDER HOSTING ----------
app_flask = Flask(__name__)
BOT_START_TIME = datetime.datetime.now()

@app_flask.route('/')
def home():
    uptime = datetime.datetime.now() - BOT_START_TIME
    return f"<h2>🤖 Nexus Card Bot Active</h2><p>Uptime: {str(uptime).split('.')[0]}</p><p>CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%</p>"

@app_flask.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()}), 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)
