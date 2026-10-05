import os, requests
from flask import Flask, request
TOKEN=os.environ.get("TELEGRAM_TOKEN","").strip()
URL=f"https://api.telegram.org/bot{TOKEN}"
app=Flask(__name__)
LAST_CHATS=set()
def get_price():
 try: return float(requests.get("https://api.gold-api.com/price/XAU",timeout=8).json().get("price",0))
 except: return 4150.0
def get_candles(interval):
 try:
  url=f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range=1d"
  r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=10).json()
  q=r["chart"]["result"][0]["indicators"]["quote"][0]
  closes=[c for c in q["close"] if c]
  highs=[h for h in q.get("high",[]) if h]
  lows=[l for l in q.get("low",[]) if l]
  return closes,highs,lows
 except: return [],[],[]
def rsi(prices):
 if len(prices)<15: return 50
 g=l=0
 for i in range(1,15):
  d=prices[-i]-prices[-i-1]
  if d>0: g+=d
  else: l+=-d
 return 100-(100/(1+g/(l or 0.001)))
def ema(prices,p):
 if len(prices)<p: return prices[-1]
 k=2/(p+1); e=sum(prices[:p])/p
 for x in prices[p:]: e=x*k+e*(1-k)
 return e
def analyze(interval,label):
 closes,highs,lows=get_candles(interval)
 if len(closes)<30: return None
 price=closes[-1]; r=rsi(closes); e50=ema(closes,20); e200=ema(closes,50)
 sup=min(lows[-20:]); res=max(highs[-20:])
 buy=sell=0; det=[]
 if r<40: buy+=1; det.append("RSI")
 elif r>60: sell+=1; det.append("RSI")
 if closes[-1]>e50: buy+=1; det.append("EMA")
 else: sell+=1; det.append("EMA")
 if closes[-1]>e200: buy+=1; det.append("Trend")
 else: sell+=1; det.append("Trend")
 if price<=sup*1.005: buy+=1; det.append("دعم")
 elif price>=res*0.995: sell+=1; det.append("مقاومة")
 score=max(buy,sell); dir_="buy" if buy>sell else "sell"
 return {"tf":label,"price":price,"sup":sup,"res":res,"score":score,"dir":dir_,"det":det,"rsi":r}
def build():
 tfs=[("1m","دقيقة"),("5m","5 دقايق"),("15m","ربع ساعة"),("60m","ساعة")]
 res=[]
 for i,l in tfs:
  a=analyze(i,l)
  if a: res.append(a)
 if not res: return None
 price=get_price()
 trades=[]
 for r in res:
  if r["score"]>=3:
   if r["dir"]=="buy":
    sl=r["sup"] if r["sup"]<price else price*0.997
    risk=price-sl
    if risk<=0: risk=price*0.003
    tp=price+2*risk
    trades.append(f"🟢 {r['tf']} BUY {r['score']}/4\n💰 دخول: ${price:.2f}\n🔻 وقف: ${sl:.2f}\n🎯 هدف: ${tp:.2f} (1:2)\nRSI:{r['rsi']:.0f} {','.join(r['det'])}")
   else:
    sl=r["res"] if r["res"]>price else price*1.003
    risk=sl-price
    if risk<=0: risk=price*0.003
    tp=price-2*risk
    trades.append(f"🔴 {r['tf']} SELL {r['score']}/4\n💰 دخول: ${price:.2f}\n🔺 وقف: ${sl:.2f}\n🎯 هدف: ${tp:.2f} (1:2)\nRSI:{r['rsi']:.0f} {','.join(r['det'])}")
 return trades,price
def send(cid,txt): requests.post(f"{URL}/sendMessage",json={"chat_id":cid,"text":txt})
@app.route("/")
def home(): return "V11 OK"
@app.route(f"/{TOKEN}",methods=["POST"])
def webhook():
 data=request.get_json(force=True)
 if "message" in data:
  cid=data["message"]["chat"]["id"]; LAST_CHATS.add(cid)
  txt=data["message"].get("text","")
  if "/start" in txt: send(cid,"✅ V11 شغال تمام\n/sniper فحص شامل 1m+5m+15m+1H")
  if "sniper" in txt:
   send(cid,"⏳ افحص دقيقة+5+ربع+ساعة...")
   b=build()
   if not b: send(cid,"جرب بعد شوي")
   else:
    trades,_=b
    if not trades: send(cid,"⚪ لا توجد صفقات +3 الآن - السوق هادي")
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
 for cid in list(LAST_CHATS)[-20:]: send(cid,f"🚨 تنبيه صفقة ${price:.2f}\n\n{msg}")
 return "sent"
@app.route("/setwebhook")
def sethook():
 r=requests.get(f"{URL}/setWebhook",params={"url":f"https://xau-bot-gjfk.onrender.com/{TOKEN}"})
 return r.text
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
