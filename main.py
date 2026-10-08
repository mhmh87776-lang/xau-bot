import os
from flask import Flask
import yfinance as yf
import pandas as pd
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8416364746:AAE4KUUUWE1oU84VNDSKU2ImeB6gBYYj_k")
CHAT_ID = os.environ.get("CHAT_ID", "7834805608")

def get_price():
    try:
        data = yf.download("GC=F", period="1d", interval="1m", progress=False)
        return float(data['Close'].iloc[-1])
    except:
        return 4145.0

@app.route('/')
def home():
    return "Gold Sniper LIVE - OK - use /price and /check"

@app.route('/price')
def price():
    p = get_price()
    return {"price": p, "status": "live"}

@app.route('/check')
def check():
    p = get_price()
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text=Gold:{p}")
    except:
        pass
    return f"Sent {p}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    

