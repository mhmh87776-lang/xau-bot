import os, requests
from flask import Flask, request
TOKEN=os.environ.get("TELEGRAM_TOKEN","").strip()
URL=f"https://api.telegram.org/bot{TOKEN}"
app=Flask(__name__)
LAST_CHATS=set()
LAST_ALERT=""

def get_price():
 try:
  return float(requests.get("https://api.gold-api.com/price/XAU",timeout=8).json().get("price",0))
 except:
  return 4160.0

def get_candles(interval):
 try:
  url=f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range=5d"
  j=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=10).json()
  q=j["chart"]["result"][0]["indicators"]["quote"][0]
  c=[x for x in q["close"] if x]
  h=[x for x in q.get("high",[]) if x]
  l=[x for x in q.get("low",[]) if x]
  return c,h,l
 except:
  return [],[],[]

def rsi(p):
 if len(p)<15: return 50
 g=0
 l=0
 for i in range(1,15):
  d=p[-i]-p[-i-1]
  if d>0:
   g+=d
  else:
   l+=-d
 if l==0:
  return 70
 return 100-(100/(1+g/l))

def ema(p,per):
 if len(p)<per:
  return p[-1]
 k=2/(per+1)
 e=sum(p[:per])/per
 for x in p[per:]:
  e=x*k+e*(1-k)
 return e

def analyze(interval,label):
 closes,highs,lows=get_candles(interval)
 if len(closes)<50:
  return None
 price=closes[-1]
 r=rsi(closes)
 e20=ema(closes,20)
 e50=ema(closes,50)
 m=ema(closes,12)-ema(closes,26)
 b=ema(closes,20)
 hh=max(highs[-14:])
 ll=min(lows[-14:])
 st=50
 if hh!=ll:
  st=100*(closes[-1]-ll)/(hh-ll)
 sup=min(lows[-20:])
 res=max(highs[-20:])
 buy=0
 sell=0
 if r<40:
  buy+=1
 elif r>60:
  sell+=1
 if closes[-1]>e20:
  buy+=1
 else:
  sell+=1
 if e20>e50:
  buy+=1
 else:
  sell+=1
 if m>0:
  buy+=1
 else:
  sell+=1
 if closes[-1]<b*0.998:
  buy+=1
 elif closes[-1]>b*1.002:
  sell+=1
 else:
  if st<30:
   buy+=1
  elif st>70:
   sell+=1
 if price<=sup*1.003:
  buy+=1
 elif price>=res*0.997:
  sell+=1
 score=max(buy,sell)
 dir_="buy" if buy>sell else "sell"
 return {"tf":label,"price":price,"score":score,"dir":dir_,"rsi":r}

def build():
 tfs=[("1m","دقيقة"),("5m","5 دقايق"),("15m","ربع ساعة"),("60m","ساعة")]
 results=[]
 for inter,label in tfs:
  a=analyze(inter,label)
  if a and a["score"]>=3:
   results.append(a)
 if not results:
  return None
 price=get_price()
 buys=[x for x in results if x["dir"]=="buy"]
 sells=[x for x in results if x["dir"]=="sell"]
 if len(buys)>=3:
  agree="BUY"
  lst=buys
  cnt=len(buys)
 elif len(sells)>=3:
  agree="SELL"
  lst=sells
  cnt=len(sells)
 else:
  return None
 risk_pct=0.0010
 msgs=[]
 for r in lst:
  if agree=="BUY":
   sl=price*(1-risk_pct)
   tp=price+(price-sl)*2
   msgs.append(f"🟢 {r['tf']} BUY {r['score']}/6 RSI {r['rsi']:.0f} دخول ${price:.2f} وقف ${sl:.2f} (-{price-sl:.2f}) هدف ${tp:.2f}")
  else:
   sl=price*(1+risk_pct)
   tp=price-(sl-price)*2
   msgs.append(f"🔴 {r['tf']} SELL {r['score']}/6 RSI {r['rsi']:.0f} دخول ${price:.2f} وقف ${sl:.2f} هدف ${tp:.2f}")
 return msgs,price,cnt,agree

def send(cid,txt):
 requests.post(f"{URL}/sendMessage",json={"chat_id":cid,"text":txt})

@app.route("/")
def home():
 return "V14 0.10% 3/4 AGREE 6STRAT"

@app.route(f"/{TOKEN}",methods=["POST"])
def webhook():
 data=request.get_json(force=True)
 if "message" in data:
  cid=data["message"]["chat"]["id"]
  LAST_CHATS.add(cid)
  txt=data["message"].get("text","")
  if "/start" in txt:
   send(cid,"✅ V14 النهائي\n6 استراتيجيات\nاتفاق 3 فريمات = جيدة\nاتفاق 4 فريمات = قوية جدا\nوقف 0.10% ~4$ مناسب لمحفظتك\n/sniper")
  if "sniper" in txt:
   send(cid,"⏳ افحص 6 استراتيجيات + اتفاق 3-4 فريمات...")
   b=build()
   if not b:
    send(cid,"⚪ لا يوجد اتفاق 3 فريمات الآن - السوق متذبذب، الأفضل الانتظار")
   else:
    msgs,price,cnt,agree=b
    head=f"🚨 اتفاق {cnt} فريمات {agree} السعر ${price:.2f}\n"
    if cnt==4:
     head+="🔥🔥 قوية جدا 4 فريمات متفقين!\n"
    else:
     head+="✅ جيدة 3 فريمات متفقين\n"
    head+=f"وقف 0.10% (~4$) هدف 0.20% (~8$) نسبة 1:2\n\n" + "\n\n".join(msgs)
    send(cid,head)
 return "ok"

@app.route("/check")
def check():
 global LAST_ALERT
 b=build()
 if not b:
  return "no agree"
 msgs,price,cnt,agree=b
 key=f"{agree}{cnt}{int(price)}"
 if key==LAST_ALERT:
  return "same"
 LAST_ALERT=key
 txt=f"🚨 اتفاق {cnt} فريمات {agree} ${price:.2f}\n" + "\n".join(msgs)
 for cid in list(LAST_CHATS)[-20:]:
  send(cid,txt)
 return "sent"

@app.route("/setwebhook")
def sethook():
 r=requests.get(f"{URL}/setWebhook",params={"url":f"https://xau-bot-gjfk.onrender.com/{TOKEN}"})
 return r.text

if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
