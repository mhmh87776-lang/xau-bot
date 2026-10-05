import os, requests, threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Live"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ شغال! اكتب /gold")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=15).json()
        price = r.get('price', 0)
        await update.message.reply_text(f"💰 سعر الذهب: ${float(price):,.2f}")
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("gold", gold))
    bot_app.add_handler(CommandHandler("now", gold))
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
