import os
import requests
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live - OK"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت شغال\nاكتب /gold")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get("https://api.gold-api.com/price/XAU", timeout=15)
        data = resp.json()
        price = data.get('price', 0)
        if price:
            await update.message.reply_text(f"💰 سعر الذهب الآن:\n${price:.2f} للأونصة")
        else:
            await update.message.reply_text(f"رد الـ API: {data}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

def run_bot():
    print(">>> BOT STARTING...", flush=True)
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("gold", gold))
    bot_app.add_handler(CommandHandler("now", gold))
    print(">>> BOT POLLING...", flush=True)
    bot_app.run_polling(drop_pending_updates=True)

# شغل البوت مع gunicorn
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
