import os
import time
import datetime
import random
import psutil
from flask import Flask, jsonify

class CaptchaService:
    @staticmethod
    def generate_math_captcha():
        a = random.randint(1, 15)
        b = random.randint(1, 15)
        c = random.randint(1, 10)
        answer = a + b + c
        question = f"{a} + {b} + {c} = ?"
        
        options = {answer}
        while len(options) < 4:
            options.add(answer + random.randint(-5, 5))
            
        opts_list = list(options)
        random.shuffle(opts_list)
        return question, answer, opts_list

# Flask Server for Render Health Checks & Port Binding
app_flask = Flask(__name__)
BOT_START_TIME = datetime.datetime.now()

@app_flask.route('/')
def home():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    uptime = datetime.datetime.now() - BOT_START_TIME
    return f"<h2>🤖 Nexus Bot Active</h2><p>Uptime: {str(uptime).split('.')[0]}</p><p>CPU: {cpu}% | RAM: {ram}%</p>"

@app_flask.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()}), 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)
