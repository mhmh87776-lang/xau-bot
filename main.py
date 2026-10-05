import os, requests
from flask import Flask, request
import telegram

print(">>> VERSION 5 ULTRA", flush=True)

TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
RENDER_URL = "https://xau-bot-gjfk.onrender.com"
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        if r.status_code == 200:
            return float(r.json().get("price", 0))
    except Exception as e:
        print(f"price error {e}", flush=True)
    return 0

@app.route("/")
def home():
    return "VERSION 5 ULTRA - OK"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print(f">>> Got update: {data}", flush=True)
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            print(f">>> Message {text} from {chat_id}", flush=True)
            
            if text == "/start":
                bot.send_message(chat_id=chat_id, text="✅ البوت شغال - VERSION 5 ULTRA\nاكتب /gold")
            elif text == "/gold":
                price = get_price()
                if price > 0:
                    bot.send_message(chat_id=chat_id, text=f"💰 سعر الذهب: ${price:.2f}")
                else:
                    bot.send_message(chat_id=chat_id, text="⚠️ فشل جلب السعر")
            else:
                bot.send_message(chat_id=chat_id, text="اكتب /gold لسعر الذهب")
    except Exception as e:
        print(f"Webhook error: {e}", flush=True)
    return "ok"

@app.route("/setwebhook")
def setwebhook():
    url = f"{RENDER_URL}/{TOKEN}"
    try:
        bot.delete_webhook()
        result = bot.set_webhook(url=url)
        return f"Webhook set to {url}: {result}"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    # set webhook on start
    try:
        url = f"{RENDER_URL}/{TOKEN}"
        print(f">>> SETTING WEBHOOK TO {url}", flush=True)
        bot.set_webhook(url=url)
    except Exception as e:
        print(f"Webhook setup failed: {e}", flush=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
