import os, threading
from flask import Flask
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN", "")
app = Flask(__name__)

@app.route('/')
def home(): return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك في بوت الذهب\n/price - سعر الذهب")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r=requests.get("https://api.gold-api.com/price/XAU",timeout=10)
        await update.message.reply_text(f"💰 السعر: ${r.json().get('price')}")
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

def run_bot():
    appb=ApplicationBuilder().token(TOKEN).build()
    appb.add_handler(CommandHandler("start",start))
    appb.add_handler(CommandHandler("price",price))
    appb.run_polling()

if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    run_bot()
