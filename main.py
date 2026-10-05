import os, requests
from flask import Flask, request

TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

def get_gold():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return r.json().get("price", 0)
    except:
        return 0

def send(chat_id, text):
    requests.post(f"{URL}/sendMessage", json={"chat_id": chat_id, "text": text})

@app.route("/")
def home():
    return "BOT V6 WORKING"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text","")
        if "/start" in text:
            send(chat_id, "✅ البوت شغال - V6\nارسل /gold")
        elif "/gold" in text:
            p = get_gold()
            send(chat_id, f"💰 الذهب: ${p:.2f}" if p else "فشل جلب السعر")
        else:
            send(chat_id, "ارسل /gold")
    return "ok"

@app.route("/setwebhook")
def sethook():
    r = requests.get(f"{URL}/setWebhook", params={"url": f"https://xau-bot-gjfk.onrender.com/{TOKEN}"})
    return r.text

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
