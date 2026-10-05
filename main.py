import os, threading, requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
TELEGRAM_TOKEN=os.environ.get("TELEGRAM_TOKEN","").strip()
GOLD_API_KEY=os.environ.get("GOLD_API_KEY","").strip()
app=Flask(__name__)
@app.route("/")
def home(): return "Bot is running!"
def get_gold_price():
 try:
  if GOLD_API_KEY:
   r=requests.get("https://www.goldapi.io/api/XAU/USD",headers={"x-access-token":GOLD_API_KEY},timeout=10)
   if r.status_code==200 and r.json().get("price"): return float(r.json()["price"])
  r=requests.get("https://api.gold-api.com/price/XAU",timeout=10)
  return float(r.json().get("price",0)) if r.status_code==200 else None
 except: return None
async def gold_command(update,context):
 price=get_gold_price()
 if price: await update.message.reply_text(f"💰 سعر الذهب: ${price:,.2f} للأونصة")
 else: await update.message.reply_text("❌ جرب بعد شوي")
async def start_command(update,context): await update.message.reply_text("استخدم /gold")
def run_bot():
 print(">>> BOT STARTING...",flush=True)
 app_bot=Application.builder().token(TELEGRAM_TOKEN).build()
 app_bot.add_handler(CommandHandler("gold",gold_command))
 app_bot.add_handler(CommandHandler("start",start_command))
 print(">>> BOT POLLING...",flush=True)
 app_bot.run_polling(drop_pending_updates=True)
if __name__=="__main__":
 threading.Thread(target=run_bot,daemon=True).start()
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
