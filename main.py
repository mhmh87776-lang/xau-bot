from flask import Flask
import os, requests, threading, time
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ضع هنا دوال بوت الذهب حقك (get_price, analyze_5_filters ...)

def run_bot_check():
    # هنا منطق الفحص 3 من 5
    print(f"[{datetime.now()}] Checking XAU...")
    # استدع دالة التحليل والإرسال للتليجرام
    # send_telegram_signal(...)
    return True

@app.route("/")
@app.route("/check")
def keep_alive():
    try:
        run_bot_check()
        return "OK - Live", 200
    except Exception as e:
        return f"Error: {e}", 200

# تشغيل البوت في الخلفية كل دقيقتين
def background_loop():
    while True:
        try:
            run_bot_check()
        except:
            pass
        time.sleep(120)

threading.Thread(target=background_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    

