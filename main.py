import os, threading, requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN", "")
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال ✅\nارسل /gold لسعر الذهب")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=15).json()
        price = r.get('price', 0)
        await update.message.reply_text(f"💰 سعر الذهب الان: ${price:.2f}")
    except Exception as e:
        await update.message.reply_text(f"جرب مرة ثانية: {e}")

def run_bot():
    a = ApplicationBuilder().token(TOKEN).build()
    a.add_handler(CommandHandler("start", start))
    a.add_handler(CommandHandler("gold", gold))
    a.add_handler(CommandHandler("now", gold))
    a.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
