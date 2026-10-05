import os, threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yfinance as yf

TOKEN = os.environ.get("BOT_TOKEN", "")
app = Flask(__name__)

@app.route('/')
def home(): return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال ✅\nارسل /gold")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = yf.Ticker("GC=F").history(period="1d")
        price = data['Close'].iloc[-1]
        await update.message.reply_text(f"سعر الذهب: ${price:.2f}")
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gold", gold))
    application.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
