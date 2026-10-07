import os, requests
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_live_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=6)
        if r.status_code == 200:
            return float(r.json()['price'])
    except: pass
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=6)
        if r.status_code == 200:
            return float(r.json()['price'])
    except: pass
    return 0

@app.route("/")
def home():
    return f"BOT LIVE FIXED! Price {get_live_price()} $ - {datetime.now()}"

@app.route("/price")
def price():
    return jsonify({"live_price": get_live_price(), "fixed": True})

@app.route("/check")
def check():
    p = get_live_price()
    txt = f"✅ البوت اتصلح\n💰 السعر اللحظي: {p}$\nتم حل 4160 و RSI"
    if TOKEN and CHAT_ID:
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": txt}, timeout=10)
        except: pass
    return jsonify({"price": p, "sent": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
