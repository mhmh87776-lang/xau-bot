import os, requests
from flask import Flask
import yfinance as yf
import pandas as pd

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOLD_KEY = os.getenv("GOLD_API_KEY")

def send_tg(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        params={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_live_price():
    try:
        r = requests.get("https://www.gold-api.com/price/XAU", headers={"x-access-token": GOLD_KEY}, timeout=10).json()
        return float(r['price'])
    except:
        try:
            data = yf.Ticker("GC=F").history(period="1d")
            return float(data['Close'].iloc[-1])
        except: return None

def get_history():
    try:
        df = yf.Ticker("GC=F").history(period="5d", interval="15m")
        return df
    except: return None

def analyze():
    live = get_live_price()
    df = get_history()
    if df is None or live is None: return None
    close = df['Close']
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss))
    rsi_val = rsi.iloc[-1]
    ema50 = close.ewm(span=50).mean().iloc[-1]
    ema200 = close.ewm(span=200).mean().iloc[-1]
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    macd_val = macd.iloc[-1]
    signal_val = signal.iloc[-1]
    sma20 = close.rolling(20).mean().iloc[-1]
    std20 = close.rolling(20).std().iloc[-1]
    upper = sma20 + (std20*2)
    lower = sma20 - (std20*2)
    resistance = df['High'].rolling(10).max().iloc[-20:].max()
    support = df['Low'].rolling(10).min().iloc[-20:].min()
    
    signals=[]; reasons=[]
    if rsi_val > 70: signals.append("SELL"); reasons.append(f"RSI تشبع شرائي {rsi_val:.1f}")
    elif rsi_val < 30: signals.append("BUY"); reasons.append(f"RSI تشبع بيعي {rsi_val:.1f}")
    elif rsi_val > 60: signals.append("SELL"); reasons.append(f"RSI مائل للبيع {rsi_val:.1f}")
    elif rsi_val < 40: signals.append("BUY"); reasons.append(f"RSI مائل للشراء {rsi_val:.1f}")
    
    if live < ema50: signals.append("SELL"); reasons.append("تحت EMA50 ترند هابط")
    else: signals.append("BUY"); reasons.append("فوق EMA50 ترند صاعد")
    
    if macd_val < signal_val: signals.append("SELL"); reasons.append("MACD سلبي")
    else: signals.append("BUY"); reasons.append("MACD إيجابي")
    
    if live >= upper*0.998: signals.append("SELL"); reasons.append("لمس البولنجر العلوي")
    elif live <= lower*1.002: signals.append("BUY"); reasons.append("لمس البولنجر السفلي")
    
    if abs(live-resistance)/live < 0.003: signals.append("SELL"); reasons.append(f"عند مقاومة ${resistance:.2f}")
    elif abs(live-support)/live < 0.003: signals.append("BUY"); reasons.append(f"عند دعم ${support:.2f}")
    
    if live < sma20: signals.append("SELL"); reasons.append("تحت متوسط 20")
    else: signals.append("BUY"); reasons.append("فوق متوسط 20")
    
    return {"price":live,"rsi":rsi_val,"res":resistance,"sup":support,"signals":signals,"reasons":reasons,"sell":signals.count("SELL"),"buy":signals.count("BUY")}

@app.route("/")
def home(): return "Gold Sniper 6 Indicators LIVE - Flexible 4/6"
@app.route("/price")
def price_route():
    p=get_live_price()
    return {"price":p}
@app.route("/check")
def check_route():
    data=analyze()
    if not data: return {"error":"data fail"}
    price=data['price']
    if data['sell']>=4:
        msg=f"🔴 *SELL GOLD - {data['sell']}/6*\n\n💰 دخول: ${price:.2f}\n🛑 وقف: ${price+4:.2f}\n🎯 هدف: ${price-8:.2f}\n\n"
        for r in data['reasons'][:6]: msg+=f"• {r}\n"
        msg+=f"\n📍 مقاومة: ${data['res']:.2f} | دعم: ${data['sup']:.2f}\nRSI: {data['rsi']:.1f}"
        send_tg(msg)
        return {"action":"SELL","price":price}
    elif data['buy']>=4:
        msg=f"🟢 *BUY GOLD - {data['buy']}/6*\n\n💰 دخول: ${price:.2f}\n🛑 وقف: ${price-4:.2f}\n🎯 هدف: ${price+8:.2f}\n\n"
        for r in data['reasons'][:6]: msg+=f"• {r}\n"
        msg+=f"\n📍 مقاومة: ${data['res']:.2f} | دعم: ${data['sup']:.2f}\nRSI: {data['rsi']:.1f}"
        send_tg(msg)
        return {"action":"BUY","price":price}
    else:
        msg=f"⏳ *فحص ربع ساعة - لا فرصة قوية*\n\n💰 السعر: ${price:.2f}\nSELL: {data['sell']}/6 | BUY: {data['buy']}/6\nRSI: {data['rsi']:.1f}\nمقاومة: ${data['res']:.2f} | دعم: ${data['sup']:.2f}"
        send_tg(msg)
        return {"action":"WAIT","price":price}

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
