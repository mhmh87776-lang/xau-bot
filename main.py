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
  if d>0: g+=d
  else: l+=-d
 if l==0: return 70
 return 100-(100/(1+g/l))

def ema(p,per):
 if len(p)<per: return p[-1]
 k=2/(per+1)
 e=sum(p[:per])/per
 for x in p[per:]: e=x*k+e*(1-k)
 return e

def analyze(interval,label):
 closes,highs,lows=get_candles(interval)
 if len(closes)<50: return None
 price=closes[-1]
 r=rsi(closes)
 e20=ema(closes,20)
 e50=ema(closes,50)
 m=ema(closes,12)-ema(closes,26)
 # Bollinger simple
 b=ema(closes,20)
 # Stochastic
 hh=max(highs[-14:])
 ll=min(lows[-14:])
 st=50
 if hh!=ll: st=100*(closes[-1]-ll)/(hh-ll)
 sup=min(lows[-20:])
 res=max(highs[-20:])
 buy=0
 sell=0
 if r<40: buy+=1
 elif r>60: sell+=1
 if closes[-1]>e20: buy+=1
 else: sell+=1
 if e20>e50: buy+=1
 else: sell+=1
 if m>0: buy+=1
 else: sell+=1
 if closes[-1]<b*0.998: buy+=1
 elif closes[-1]>b*1.002: sell+=1
 else:
  if st<30: buy+=1
  elif st>70: sell+=1
 if price<=sup*1.003: buy+=1
 elif price>=res*0.997: sell+=1
 score=max(buy,sell)
 dir_="buy" if buy>sell else "sell"
 return {"tf":label,"price":price,"score":score,"dir":dir_,"rsi":r}

def build():
 tfs=[("1m","دقيقة"),("5m","5 دقايق"),("15m","ربع ساعة"),("60m","ساعة")]
 results=[]
 for inter,label in tfs:
  a=
