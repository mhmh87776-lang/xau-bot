import os, requests, threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت شغال! أرسل /gold")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        price = float(r['price'])
        await update.message.reply_text(f"💰 الذهب الآن: {price:,.2f} $ للأونصة")
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

def main():
    threading.Thread(target=run_flask).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("gold", gold))
    bot.add_handler(CommandHandler("now", gold))
    bot.run_polling()

if __name__ == "__main__":
    main()
