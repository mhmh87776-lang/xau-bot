import os, requests, time
from flask import Flask, request
TOKEN = os.environ.get("TELEGRAM_TOKEN","").strip()
URL = f"https://api.telegram.org/bot{TOKEN}"
app = Flask(__name__)
LAST_CHATS = set()
LAST_SENT = {}

def get_live_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
        p = float(r.get("price",0))
        if p>0: return p
    except: pass
    return 0

def get_candles(interval="15m", range_="1d"):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range={range_}"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10).json()
        q = r["chart"]["result"][0]["indicators"]["quote"][0]
        closes = [c for c in q["close"] if c]
        highs = [h for h in q.get("high",[]) if h]
        lows = [l for l in q.get("low",[]) if l]
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
    e12=ema(prices,12); e26=ema(prices,26)
    return e12-e26, (e12-e26)-ema(prices[-9:],9)

def stochastic(closes, highs, lows, k=14):
    if len(closes)<k: return 50
    hh=max(highs[-k:]); ll=min(lows[-k:]) or 1
    return 100*(closes[-1]-ll)/(hh-ll) if hh!=ll else 50

def analyze_tf(interval, label, live_price):
    closes, highs, lows = get_candles(interval, "2d" if "m" in interval else "5d")
    if len(closes)<30: return None
    r=rsi(closes); e50=ema(closes,50); e200=ema(closes,20) if len(closes)<200 else ema(closes,200)
    m_line, m_hist = macd(closes); stoch=stochastic(closes, highs, lows)
    sup=min(lows[-20:]); res=max(highs[-20:]); bb_mid=ema(closes,20)
    price = live_price or closes[-1]
    votes={"buy":0,"sell":0,"details":[]}
    if r<35: votes["buy"]+=1; votes["details"].append("RSI شراء")
    elif r>65: votes["sell"]+=1; votes["details"].append("RSI بيع")
    if e50>e200: votes["buy"]+=1; votes["details"].append("EMA صاعد")
    else: votes["sell"]+=1; votes["details"].append("EMA هابط")
    if m_hist>0: votes["buy"]+=1; votes["details"].append("MACD شراء")
    else: votes["sell"]+=1; votes["details"].append("MACD بيع")
    if price <= sup*1.003: votes["buy"]+=1; votes["details"].append("عند دعم")
    elif price >= res*0.997: votes["sell"]+=1; votes["details"].append("عند مقاومة")
    if price < bb_mid*0.998: votes["buy"]+=1; votes["details"].append("BB ارتداد")
    elif price > bb_mid*1.002: votes["sell"]+=1; votes["details"].append("BB ارتداد")
    if stoch<25: votes["buy"]+=1; votes["details"].append("Stoch شراء")
    elif stoch>75: votes["sell"]+=1; votes["details"].append("Stoch بيع")
    direction="buy" if votes["buy"]>votes["sell"] else "sell"
    score=max(votes["buy"],votes["sell"])
    return {"tf":label,"price":price,"sup":sup,"res":res,"score":score,"dir":direction,"details":votes["details"][:4],"rsi":round(r,1)}

def build_signal():
    live = get_live_price()
    if not live or live==0: return None
    price = live
    tfs=[("5m","5 دقايق"),("15m","15 دقيقة"),("30m","30 دقيقة"),("60m","ساعة")]
    results=[]
    for interval,label in tfs:
        a=analyze_tf(interval,label, live)
        if a: results.append(a)
    if not results: return None
    trades=[]
    for r in results:
        if r["score"]>=3:
            key = f"{r['tf']}_{r['dir']}"
            if key in LAST_SENT and time.time()-LAST_SENT[key] < 60: continue
            LAST_SENT[key]=time.time()
            if r["dir"]=="buy":
                # وقف صحيح: لازم يكون تحت الدخول
                sl = r["sup"]
                if sl >= price or sl==0: # لو الدعم فوق السعر (غلط Yahoo) صححه
                    sl = price * 0.997 # 0.3% تحت
                risk = price - sl
                if risk < price*0.001: risk = price*0.003
                tp = price + 2*risk
                trades.append(f"🟢 {r['tf']} | BUY | قوة {r['score']}/6\n💰 دخول: ${price:.2f}\n🔴 وقف: ${sl:.2f} (تحت)\n🟢 هدف: ${tp:.2f} (1:2)\n{', '.join(r['details'])} RSI:{r['rsi']}")
            else:
                sl = r["res"]
                if sl <= price or sl==0:
                    sl = price * 1.003 # 0.3% فوق
                risk = sl - price
                if risk < price*0.001: risk = price*0.003
                tp = price - 2*risk
                trades.append(f"🔴 {r['tf']} | SELL | قوة {r['score']}/6\n💰 دخول: ${price:.2f}\n🔴 وقف: ${sl:.2f} (فوق)\n🟢 هدف: ${tp:.2f} (1:2)\n{', '.join(r['details'])} RSI:{r['rsi']}")
    if not trades: return None
    header=f"🔥 فرصة فورية - {len(trades)} إشارات\n💰 السعر اللحظي: ${price:.2f}\n\n"
    return header + "\n\n".join(trades)

def send(chat_id, text):
    try: requests.post(f"{URL}/sendMessage", json={"chat_id":chat_id,"text":text}, timeout=10)
    except: pass

@app.route("/")
@app.route("/check")
def auto_check():
    msg=build_signal()
    if msg:
        for cid in list(LAST_CHATS)[-20:]:
            send(cid, msg)
        return msg
    live = get_live_price()
    return f"OK - Live ${live:.2f} - No trade >=3"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data=request.get_json(force=True)
    if "message" in data:
        chat_id=data["message"]["chat"]["id"]; LAST_CHATS.add(chat_id)
        txt=data["message"].get("text","")
        if "/start" in txt:
            send(chat_id,"✅ V8.3 تم إصلاح الوقف والهدف\n/sniper - فحص الآن\n/gold - السعر اللحظي")
        elif "/gold" in txt:
            send(chat_id,f"💰 الذهب اللحظي: ${get_live_price():.2f}")
        elif "/sniper" in txt:
            send(chat_id,"⏳ فحص لحظي...")
            m=build_signal()
            send(chat_id, m or f"⚪ لا توجد 3+ الآن - السعر ${get_live_price():.2f}")
    return "ok"

@app.route("/setwebhook")
def sethook():
    r=requests.get(f"{URL}/setWebhook", params={"url":f"https://xau-bot-gjfk.onrender.com/{TOKEN}"})
    return r.text

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
    

