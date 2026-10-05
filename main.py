import os, requests
from flask import Flask, request

TOKEN = os.environ.get("TELEGRAM_TOKEN","").strip()
URL = f"https://api.telegram.org/bot{TOKEN}"
app = Flask(__name__)
LAST_CHATS=set()
LAST_ALERT="" # عشان ما يكرر نفس التنبيه

def get_price():
    try: return float(requests.get("https://api.gold-api.com/price/XAU", timeout=8).json().get("price",0))
    except: return 0

def get_candles(interval="1m", range_="1d"):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range={range_}"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10).json()
        q=r["chart"]["result"][0]["indicators"]["quote"][0]
        closes=[c for c in q["close"] if c]
        highs=[h for h in q.get("high",[]) if h]
        lows=[l for l in q.get("low",[]) if l]
        return closes, highs, lows
    except: return [], [], []

def rsi(prices, p=14):
    if len(prices)<p+1: return 50
    g=l=0
    for i in range(1,p+1):
        d=prices[-i]-prices[-i-1]
        if d>0: g+=d
        else: l+=-d
    return 100 - (100/(1+g/(l or 0.001)))

def ema(prices, p):
    if len(prices)<p: return prices[-1]
    k=2/(p+1); e=sum(prices[:p])/p
    for x in prices[p:]: e=x*k+e*(1-k)
    return e

def macd(prices):
    if len(prices)<26: return 0,0
    return ema(prices,12)-ema(prices,26), 0

def stochastic(closes, highs, lows, k=14):
    if len(closes)<k: return 50
    hh=max(highs[-k:]); ll=min(lows[-k:])
    return 100*(closes[-1]-ll)/(hh-ll) if hh!=ll else 50

def analyze_tf(interval,label):
    closes,highs,lows=get_candles(interval,"1d" if "m" in interval else "5d")
    if len(closes)<30: return None
    price=closes[-1]; r=rsi(closes); e50=ema(closes,50); e200=ema(closes,20)
    m,_=macd(closes); stoch=stochastic(closes,highs,lows)
    sup=min(lows[-20:]); res=max(highs[-20:]); bb=ema(closes,20)
    buy=sell=0; det=[]
    if r<35: buy+=1; det.append("RSI")
    elif r>65: sell+=1; det.append("RSI")
    if e50>e200: buy+=1; det.append("EMA")
    else: sell+=1; det.append("EMA")
    if m>0: buy+=1; det.append("MACD")
    else: sell+=1; det.append("MACD")
    if price<=sup*1.003: buy+=1; det.append("دعم")
    elif price>=res*0.997: sell+=1; det.append("مقاومة")
    if price<bb*0.998: buy+=1; det.append("BB")
    elif price>bb*1.002: sell+=1; det.append("BB")
    if stoch<25: buy+=1; det.append("Stoch")
    elif stoch>75: sell+=1; det.append("Stoch")
    dir_="buy" if buy>sell else "sell"
    score=max(buy,sell)
    return {"tf":label,"interval":interval,"price":price,"sup":sup,"res":res,"score":score,"dir":dir_,"details":det,"rsi":r}

def build_signal(min_score=3):
    tfs=[("1m","دقيقة"),("5m","5 دقايق"),("15m","15 دقيقة"),("30m","30 دقيقة"),("60m","ساعة")]
    results=[]
    for i,l in tfs:
        a=analyze_tf(i,l)
        if a: results.append(a)
    if not results: return None
    price=get_price() or results[0]["price"]
    trades=[]
    for r in results:
        if r["score"]>=min_score:
            if r["dir"]=="buy":
                sl=r["sup"]; risk=price-sl or price*0.002; tp=price+2*risk
                trades.append((r,f"🟢 {r['tf']} BUY {r['score']}/6\n💰 دخول: ${price:.2f}\n🔻 وقف: ${sl:.2f} ({risk/price*100:.2f}%)\n🎯 هدف: ${tp:.2f} (1:2)\n📊 RSI:{r['rsi']:.0f} | {','.join(r['details'])}"))
            else:
                sl=r["res"]; risk=sl-price or price*0.002; tp=price-2*risk
                trades.append((r,f"🔴 {r['tf']} SELL {r['score']}/6\n💰 دخول: ${price:.2f}\n🔺 وقف: ${sl:.2f} ({risk/price*100:.2f}%)\n🎯 هدف: ${tp:.2f} (1:2)\n📊 RSI:{r['rsi']:.0f} | {','.join(r['details'])}"))
    return trades, price

def send(cid,txt): requests.post(f"{URL}/sendMessage", json={"chat_id":cid,"text":txt})

@app.route("/")
def home(): return "V9 1MIN ALERT WORKING"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data=request.get_json(force=True)
    if "message" in data:
        cid=data["message"]["chat"]["id"]; LAST_CHATS.add(cid)
        txt=data["message"].get("text","")
        if "/start" in txt: send(cid,"✅ V9 شغال - فريم الدقيقة مفعل\n/sniper - فحص الآن\n/auto - تفعيل التنبيه كل دقيقة")
        elif "sniper" in txt or "gold" in txt:
            send(cid,"⏳ افحص 1m+5m+15m+30m+1H...")
            res=build_signal(3)
            if not res: send(cid,"جرب بعد ثواني")
            else:
                trades,_=res
                if not trades: send(cid,"⚪ لا توجد صفقات 3+ الآن")
                else:
                    for _,t in trades: send(cid,t)
        elif "auto" in txt:
            send(cid,"🔔 التنبيه التلقائي تفعّل!\nبيجيك تنبيه على أي صفقة قوية حتى على شارت الدقيقة\n\nمهم: عشان يشتغل 24 ساعة سوي الخطوة اللي تحت 👇")
    return "ok"

@app.route("/check")
def auto_check():
    global LAST_ALERT
    res=build_signal(3)
    if not res: return "no data"
    trades, price = res
    if not trades: return f"NO TRADE - ${price:.2f}"
    # لا تكرر نفس الصفقة
    msg_hash = trades[0][1][:80]
    if msg_hash == LAST_ALERT: return "SAME AS LAST"
    LAST_ALERT = msg_hash
    full = f"🚨 تنبيه صفقة قوية {len(trades)} فرص - السعر ${price:.2f}\n\n" + "\n\n".join([t for _,t in trades])
    for cid in list(LAST_CHATS)[-20:]:
        send(cid, full)
    return "ALERT SENT"

@app.route("/setwebhook")
def sethook():
    r=requests.get(f"{URL}/setWebhook", params={"url":f"https://xau-bot-gjfk.onrender.com/{TOKEN}"})
    return r.text

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
