import os, time, threading, requests, yfinance as yf, pandas as pd
from flask import Flask
app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
last_time = 0

def send(m):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": m}, timeout=10)
        print("sent")
    except Exception as e:
        print(e)

def get_price():
    try:
        df = yf.download("GC=F", period="2d", interval="5m", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

def rsi(s, p=14):
    d = s.diff()
    g = d.where(d > 0, 0).rolling(p).mean()
    l = (-d.where(d < 0, 0)).rolling(p).mean()
    return 100 - (100 / (1 + g / l))

def loop():
    global last_time
    while True:
        try:
            df = get_price()
            if df is None or len(df) < 30:
                time.sleep(60)
                continue
            c = df['Close']
            h = df['High']
            l = df['Low']
            price = float(c.iloc[-1])
            r = float(rsi(c).iloc[-1])
            rh = float(h.tail(20).max())
            rl = float(l.tail(20).min())
            buy = 0
            sell = 0
            txt_b = ""
            txt_s = ""
            if price > rh - 1:
                buy += 1
                txt_b += "- BOS صعود\n"
            if price < rl + 1:
                sell += 1
                txt_s += "- BOS هبوط\n"
            if float(l.iloc[-2]) < rl:
                buy += 1
                txt_b += "- سحب سيولة شراء\n"
            if float(h.iloc[-2]) > rh:
                sell += 1
                txt_s += "- سحب سيولة بيع\n"
            if r < 35:
                buy += 1
                txt_b += f"- RSI متشبع {r:.1f}\n"
            if r > 65:
                sell += 1
                txt_s += f"- RSI متشبع {r:.1f}\n"
            if float(c.iloc[-1]) > float(df['Open'].iloc[-1]) + 2:
                buy += 1
                txt_b += "- FVG شرائي\n"
            if float(c.iloc[-1]) < float(df['Open'].iloc[-1]) - 2:
                sell += 1
                txt_s += "- FVG بيعي\n"
            if price < rl + 3:
                buy += 1
                txt_b += "- OrderBlock دعم\n"
            if price > rh - 3:
                sell += 1
                txt_s += "- OrderBlock مقاومة\n"
            now = time.time()
            if buy >= 3 and now - last_time > 900:
                msg = f"🟢 BUY GOLD\nالسعر {price:.2f}\nRSI {r:.1f}\nقوة {buy}/5\n{txt_b}\nدخول {price:.2f} ستوب {price-5:.2f} هدف {price+7:.2f}"
                send(msg)
                last_time = now
            if sell >= 3 and now - last_time > 900:
                msg = f"🔴 SELL GOLD\nالسعر {price:.2f}\nRSI {r:.1f}\nقوة {sell}/5\n{txt_s}\nدخول {price:.2f} ستوب {price+5:.2f} هدف {price-7:.2f}"
                send(msg)
                last_time = now
        except Exception as e:
            print(e)
        time.sleep(60)

@app.route("/")
def home():
    return "Gold Bot V3 Live"

@app.route("/test")
def test():
    send("✅ Bot V3 جاهز - سيرسل فقط الفرص القوية 3/5")
    return "sent"

threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    

