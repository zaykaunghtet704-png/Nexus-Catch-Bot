import os
import time
import datetime
import random
import psutil
from PIL import Image, ImageDraw
from flask import Flask, jsonify

class CanvasEngine:
    @staticmethod
    def generate_card_image(title="Astraea", rarity="Premium Edition", print_no="#0001", mint="100%", price=15000):
        img = Image.new("RGB", (400, 550), color="#101018")
        draw = ImageDraw.Draw(img)
        
        draw.rectangle([10, 10, 390, 540], outline="#FFD700", width=4)
        draw.text((20, 25), f"[{rarity}]", fill="#FFD700")
        draw.text((280, 25), f"Print {print_no}", fill="#FFFFFF")
        
        draw.rectangle([30, 60, 370, 380], fill="#1E1E2C", outline="#444466")
        draw.text((120, 200), f"[{title.upper()}]", fill="#8888AA")
        
        draw.text((30, 400), f"Character: {title}", fill="#FFFFFF")
        draw.text((30, 430), f"Condition: Mint {mint} | Base Price: {price} Coins", fill="#AAAAAA")
        draw.text((30, 470), "HP: 3,500 | ATK: 1,200 | DEF: 850", fill="#00FFCC")
        
        out_path = f"card_{random.randint(1000,9999)}.png"
        img.save(out_path)
        return out_path

app_flask = Flask(__name__)
BOT_START_TIME = datetime.datetime.now()

@app_flask.route('/')
def home():
    uptime = datetime.datetime.now() - BOT_START_TIME
    return f"🤖 Nexus Bot Active | Uptime: {str(uptime).split('.')[0]}"

@app_flask.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()}), 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)
