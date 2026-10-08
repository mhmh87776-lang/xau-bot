import os, time, threading, requests, yfinance as yf, pandas as pd
from flask import Flask

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
last_sent_time = 0
last_price = 0

def send_telegram(msg):
    if not TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_data():
    try:
        data = yf.download("GC=F", period="2d", interval="5m", progress=False)
        if data.empty:
            data = yf.download("XAUUSD=X", period="2d", interval="5m", progress=False)
        return data
    except:
        return None

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_strategies():
    global last_sent_time, last_price
    data = get_data()
    if data is None or len(data) < 50: return
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    close = data['Close']
    high = data['High']
    low = data['Low']
    price = float(close.iloc[-1])
    rsi_series = calc_rsi(close)
    rsi_val = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50
    recent_high = float(high.tail(20).max())
    recent_low = float(low.tail(20).min())
    last_high = float(high.iloc[-2])
    last_low = float(low.iloc[-2])
    prev_close = float(close.iloc[-2])
    prev_open = float(data['Open'].iloc[-2])
    body = abs(prev_close - prev_open)

    bos_buy = price > recent_high - 1
    bos_sell = price < recent_low + 1
    liq_buy = last_low < recent_low and price > recent_low
    liq_sell = last_high > recent_high and price < recent_high
    fvg_buy = body > 2.5 and prev_close > prev_open
    fvg_sell = body > 2.5 and prev_close < prev_open
    ob_buy = price < recent_low + 3
    ob_sell = price > recent_high - 3
    rsi_buy = rsi_val < 35
    rsi_sell = rsi_val > 65

    buy_score = sum([bos_buy, liq_buy, fvg_buy, ob_buy, rsi_buy])
    sell_score = sum([bos_sell, liq_sell, fvg_sell, ob_sell, rsi_sell])

    now = time.time()
    if now - last_sent_time < 180 and abs(price - last_price) < 2:
        return

    if buy_score >= 3:
        reasons = ""
        if bos_buy: reasons += "- BOS Buy\n"
        if liq_buy: reasons += "- Liquidity Sweep Buy\n"
        if fvg_buy: reasons += "- FVG Buy\n"
        if ob_buy: reasons += "- Order Block Support\n"
        if rsi_buy: reasons += f"- RSI Oversold {rsi_val:.1f}\n"
        msg = f"BUY XAUUSD Gold\nPrice: {price:.2f}\nRSI: {rsi_val:.1f}\nScore: {buy_score}/5\n{reasons}\nEntry {price:.2f} SL {price-4:.2f} TP1 {price+3:.2f} TP2 {price+6:.2f}"
        send_telegram(msg)
        last_sent_time = now
        last_price = price

    if sell_score >= 3:
        reasons = ""
        if bos_sell: reasons += "- BOS Sell\n"
        if liq_sell: reasons += "- Liquidity Sweep Sell\n"
        if fvg_sell: reasons += "- FVG Sell\n"
        if ob_sell: reasons += "- Order Block Resistance\n"
        if rsi_sell: reasons += f"- RSI Overbought {rsi_val:.1f}\n"
        msg = f"SELL XAUUSD Gold\nPrice: {price:.2f}\nRSI: {rsi_val:.1f}\nScore: {sell_score}/5\n{reasons}\nEntry {price:.2f} SL {price+4:.2f} TP1 {price-3:.2f} TP2 {price-6:.2f}"
        send_telegram(msg)
        last_sent_time = now
        last_price = price

def loop():
    while True:
        try: check_strategies()
        except: pass
        time.sleep(60)

@app.route("/")
def home(): return "XAU Bot V2 Live - 5 Strategies"

@app.route("/test")
def test():
    send_telegram("Test OK - Bot V2 with 5 strategies is working and will send every real opportunity")
    return "sent"

threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    

