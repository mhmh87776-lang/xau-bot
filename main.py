import os, requests
from flask import Flask, request
TOKEN=os.environ.get("TELEGRAM_TOKEN","").strip()
URL=f"https://api.telegram.org/bot{TOKEN}"
app=Flask(__name__)
LAST_CHATS=set()

def get_price():
 try: return float(requests.get("https://api.gold-api.com/price/XAU",timeout=8).json().get("price",0))
 except: return 0

def get_candles(interval):
 try:
  url=f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range=5d"
  r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=10).json()
  q=r["chart"]["result"][0]["indicators"]["quote"][0]
  closes=[c for c in q["close"] if c]
  highs=[h for h in q.get("high",[]) if h]
  lows=[l for l in q.get("low",[]) if l]
  return closes,highs,lows
 except: return [],[],[]

def rsi(p,per=14):
 if len(p)<per+1: return 50
 g=l=0
 for i in range(1,per+1):
  d=p[-i]-p[-i-1]
  if d>0: g+=d
  else: l+=-d
 return 100-(100/(1+g/(l or 0.001)))

def ema(p,per):
 if len(p)<per: return p[-1]
 k=2/(per+1); e=sum(p[:per])/per
 for x in p[per:]: e=x*k+e*(1-k)
 return e

def macd(p):
 if len(p)<26: return 0
 return ema(p,12)-ema(p,26)

def bb(p,per=20):
 e=ema(p,per)
 return e

def stoch(closes,highs,lows,per=14):
 if len(closes)<per: return 50
 hh=max(highs[-per:]); ll=min(lows[-per:])
 return 100*(closes[-1]-ll)/(hh-ll) if hh!=ll else 50

def analyze(interval,label):
 closes,highs,lows=get_candles(interval)
 if len(closes)<50: return None
 price=closes[-1]
 r=rsi(closes); e20=ema(closes,20); e50=ema(closes,50)
 m=macd(closes); b=bb(closes); st=stoch(closes,highs,lows)
 sup=min(lows[-20:]); res=max(highs[-20:])
 buy=sell=0; det=[]
 #1 RSI
 if r<40: buy+=1; det.append("RSI")
 elif r>60: sell+=1; det.append("RSI")
 #2 EMA20 vs 50
 if closes[-1]>e20: buy+=1; det.append("EMA20")
 else: sell+=1; det.append("EMA20")
 #3 Trend EMA20 vs EMA50
 if e20>e50: buy+=1; det.append("Trend")
 else: sell+=1; det.append("Trend")
 #4 MACD
 if m>0: buy+=1; det.append("MACD")
 else: sell+=1; det.append("MACD")
 #5 Bollinger + Stochastic
 if b:
  if closes[-1]<b*0.998: buy+=1; det.append("BB")
  elif closes[-1]>b*1.002: sell+=1; det.append("BB")
  else:
   if st<30: buy+=1; det.append("Stoch")
   elif st>70: sell+=1; det.append("Stoch")
 #6 Support/Resistance
 if price<=sup*1.003: buy+=1; det.append("دعم")
 elif price>=res*0.997: sell+=1; det.append("مقاومة")
 else:
  if st<30: buy+=1; det.append("Stoch")
  elif st>70: sell+=1; det.append("Stoch")

 score=max(buy,sell); dir_="buy" if buy>sell else "sell"
 return {"tf":label,"price":price,"sup":sup,"res":res,"score":score,"dir":dir_,"det":det,"rsi":r}

def build():
 tfs=[("1m","دقيقة"),("5m","5 دقايق"),("15m","ربع ساعة"),("60m","ساعة")]
 res=[]
 for i,l in tfs:
  a=analyze(i,l)
  if a: res.append(a)
 if not res: return None
 price=get_price() or res[0]["price"]
 trades=[]
 for r in res:
  if r["score"]>=3:
   if r["dir"]=="buy":
    sl=r["sup"] if r["sup"]<price else price*0.997
    risk=price-sl
    if risk<=0: risk=price*0.003
    tp=price+2*risk
    trades.append(f"🟢 {r['tf']} BUY {r['score']}/6\n💰 دخول: ${price:.2f}\n🔻 وقف: ${sl:.2f}\n🎯 هدف: ${tp:.2f} (1:2)\nRSI:{r['rsi']:.0f} {','.join(r['det'])}")
   else:
    sl=r["res"] if r["res"]>price else price*1.003
    risk=sl-price
    if risk<=0: risk=price*0.003
    tp=price-2*risk
    trades.append(f"🔴 {r['tf']} SELL {r['score']}/6\n💰 دخول: ${price:.2f}\n🔺 وقف: ${sl:.2f}\n🎯 هدف: ${tp:.2f} (1:2)\nRSI:{r['rsi']:.0f} {','.join(r['det'])}")
 return trades,price

def send(cid,txt): requests.post(f"{URL}/sendMessage",json={"chat_id":cid,"text":txt})

@app.route("/")
def home(): return "V12 6STRAT OK"

@app.route(f"/{TOKEN}",methods=["POST"])
def webhook():
 data=request.get_json(force=True)
 if "message" in data:
  cid=data["message"]["chat"]["id"]; LAST_CHATS.add(cid)
  txt=data["message"].get("text","")
  if "/start" in txt: send(cid,"✅ V12 رجعنا 6 استراتيجيات\n/sniper فحص 1m+5m+15m+1H")
  if "sniper" in txt:
   send(cid,"⏳ افحص بـ 6 استراتيجيات...")
   b=build()
   if not b: send(cid,"جرب بعد شوي")
   else:
    trades,_=b
    if not trades: send(cid,"⚪ لا توجد صفقات +3/6 الآن - السوق هادي")
    else:
     for t in trades: send(cid,t)
 return "ok"

@app.route("/check")
def check():
 b=build()
 if not b: return "no"
 trades,price=b
 if not trades: return "no trade"
 msg="\n\n".join(trades)
 for cid in list(LAST_CHATS)[-20:]: send(cid,f"🚨 تنبيه 6 استراتيجيات ${price:.2f}\n\n{msg}")
 return "sent"

@app.route("/setwebhook")
def sethook():
 r=requests.get(f"{URL}/setWebhook",params={"url":f"https://xau-bot-gjfk.onrender.com/{TOKEN}"})
 return r.text

if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
