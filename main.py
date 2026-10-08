import os, time, threading, requests, yfinance as yf
from flask import Flask

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

def check():
    try:
        df = yf.download("GC=F", period="1d", interval="5m", progress=False)
        price = float(df['Close'].iloc[-1])
        return price
    except:
        return None

def loop():
    while True:
        p = check()
        if p:
            print(f"price {p}")
        time.sleep(60)

@app.route("/")
def home():
    return "Bot Live"

@app.route("/test")
def test():
    send("Test OK - Bot is working now!")
    return "sent"

threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    

