import os, requests, asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler

print(">>> VERSION 4 FINAL", flush=True)

TOKEN = os.environ.get("TELEGRAM_TOKEN","").strip()
app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

def get_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        if r.status_code == 200:
            return float(r.json().get("price",0))
    except: pass
    return None

async def gold(update, context):
    p = get_price()
    if p: await update.message.reply_text(f"💰 الذهب الآن: ${p:,.2f}")
    else: await update.message.reply_text("❌ حاول مرة ثانية")

async def start(update, context):
    await update.message.reply_text("أهلاً! أرسل /gold لمعرفة السعر")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("gold", gold))

@app.route("/")
def home():
    return "Bot OK"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run(application.process_update(update))
    except Exception as e:
        print(f"ERR {e}", flush=True)
    return "ok"

# تشغيل الـ webhook مرة واحدة عند الإقلاع
async def setup():
    await application.initialize()
    url = "https://xau-bot-gjfk.onrender.com/" + TOKEN
    await application.bot.set_webhook(url=url)
    print(f">>> WEBHOOK SET {url}", flush=True)

asyncio.run(setup())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
