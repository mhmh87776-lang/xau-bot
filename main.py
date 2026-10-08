import os
import time
import threading
import requests
import yfinance as yf
import pandas as pd
from flask import Flask

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

last_signal = {"type": None, "price": 0, "time": 0}
last_sent_time = 0

def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("No token/chat_id")
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print("Sent:", msg[:50])
    except Exception as e:
        print("Send error", e)

def get_data():
    try:
        # نجلب بيانات الذهب 5 دقايق
        data = yf.download("GC=F", period="2d", interval="5m", progress=False)
        if data.empty:
            data = yf.download("XAUUSD=X", period="2d", interval="5m", progress=False)
        return data
    except Exception as e:
        print(e)
        return None

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_strategies():
    global last_signal, last_sent_time
    data = get_data()
    if data is None or len(data) < 50:
        return

    # تسطيح الاعمدة
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    close = data['Close']
    high = data['High']
    low = data['Low']
    price = float(close.iloc[-1])
    
    rsi_series = calc_rsi(close)
    rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50

    recent_high = float(high.tail(20).max())
    recent_low = float(low.tail(20).min())
    
    # 1- BOS
    bos_buy = price > recent_high - 1
    bos_sell = price < recent_low + 1
    
    # 2- سيولة (سحب قمة/قاع)
    last_candle_high = float(high.iloc[-2])
    last_candle_low = float(low.iloc[-2])
    liquidity_buy = last_candle_low < recent_low and price > recent_low  # كسر كاذب للقاع
    liquidity_sell = last_candle_high > recent_high and price < recent_high

    # 3- FVG (فجوة سعرية - شمعة كبيرة)
    prev_close = float(close.iloc[-2])
    prev_open = float(data['Open'].iloc[-2])
    body_size = abs(prev_close - prev_open)
    fvg_buy = body_size > 2.5 and prev_close > prev_open # شمعة صاعدة قوية
    fvg_sell = body_size > 2.5 and prev_close < prev_open

    # 4- Order Block (دعم/مقاومة)
    ob_buy = price < recent_low + 3  # قريب من قاع
    ob_sell = price > recent_high - 3 # قريب من قمة

    # 5- RSI
    rsi_buy = rsi < 35
    rsi_sell = rsi > 65

    # تجميع الاشارات
    buy_score = sum([bos_buy, liquidity_buy, fvg_buy, ob_buy, rsi_buy])
    sell_score = sum([bos_sell, liquidity_sell, fvg_sell, ob_sell, rsi_sell])

    print(f"Price {price:.2f} RSI {rsi:.1f} Buy:{buy_score} Sell:{sell_score}")

    now = time.time()
    # منع تكرار نفس السعر خلال 3 دقايق
    if now - last_sent_time < 180 and abs(price - last_signal["price"]) < 2 and last_signal["type"] in ["BUY","SELL"]:
        return

    if buy_score >= 3:
        reasons = []
        if bos_buy: reasons.append("✅ BOS كسر قمة")
        if liquidity_buy: reasons.append("✅ سحب سيولة من القاع")
        if fvg_buy: reasons.append("✅ FVG شرائي")
        if ob_buy: reasons.append("✅ Order Block دعم")
        if rsi_buy: reasons.append(f"✅ RSI تشبع بيعي {rsi:.1f}")

        msg = f"""🔥 **فرصة شراء ذهب حقيقية XAUUSD** 🔥

💰 السعر الحالي: `{price:.2f}`
📊 RSI: {rsi:.1f}

**الأسباب ({buy_score}/5):**
{chr(10).join(reasons)}

🎯 دخول: {price:.2f}
⛔
    

