import os, requests, asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

print(">>> VERSION 4 FINAL", flush=True)

TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
RENDER_URL = "https://xau-bot-gjfk.onrender.com"

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        if r.status_code == 200:
            return float(r.json().get("price", 0))
    except:
        pass
    return 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت شغال - VERSION 4 FINAL\nاكتب /gold")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_price()
    if price > 0:
        await update.message.reply_text(f"💰 سعر الذهب: ${price:.2f}")
    else:
        await update.message.reply_text("⚠️ فشل جلب السعر حاليا")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("gold", gold))

@app.route("/")
def home():
    return "VERSION 4 FINAL - OK"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))
    except Exception as e:
        print(f"Webhook error: {e}", flush=True)
    return "ok"

def setup_webhook():
    url = f"{RENDER_URL}/{TOKEN}"
    print(f">>> WEBHOOK SET TO {url}", flush=True)
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={url}", timeout=10)
    except Exception as e:
        print(f"Webhook setup failed: {e}", flush=True)

if __name__ == "__main__":
    setup_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
