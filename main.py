import os, time, threading, requests, yfinance as yf, pandas as pd
from flask import Flask

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHATID")
last_sent_time = 0
last_price = 0

def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("Missing TOKEN or CHAT_ID")
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print(f"Telegram response: {r.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

def get_data():
    try:
        data = yf.download("GC=F", period="2d", interval="5m", progress=False)
        if data.empty:
            data = yf.download("XAUUSD=X", period="2d", interval="5m", progress=False)
        return data
    except Exception as e:
        print(f"Data error: {e}")
        return None

def calc_r
    

