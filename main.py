import os, requests, threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in Render Environment")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ اكتب /gold")

async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        price = r.get('price', 0)
        await update.message.reply_text(f"💰 الذهب: ${price}")
    except Exception as e:
        await update.message.reply_text(f"خطأ: {e}")

def run_bot():
    print(">>> BOT STARTING...")
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("gold", gold))
    bot_app.add_handler(CommandHandler("now", gold))
    print(">>> BOT POLLING...")
    bot_app.run_polling(drop_pending_updates=True)

# هذا هو السطر اللي يصلح المشكلة - يشتغل مع gunicorn
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
