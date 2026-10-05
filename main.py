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
  return 0

def get_candles(interval):
 try:
  url=f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval={interval}&range=5d"
  r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=10).json()
  q=r["chart"]["result"][0]["indicators"]["quote"][0]
  closes=[c for c in q["close"] if c]
  highs=[h for h in q.get("high",[]) if h]
  lows=[l for l in q.get("low",[]) if l]
  return closes,highs,lows
 except:
  return [],[],[]

def rsi(prices, per=14):
 if len(prices) < per+1:
  return 50
 gains=0
 losses=0
 for i in range(1, per+1):
  d=prices[-i]-prices[-i-1]
  if d>0:
   gains+=d
  else:
   losses+=-d
 if losses==0:
  return 70
 rs=gains/losses
 return 100-(100/(1+rs))

def ema(prices, per):
 if len(prices) < per:
  return prices[-1]
 k=2/(per+1)
 e=sum(prices[:per])/per
 for x in prices[per:]:
  e=x*k+e*(1-k)
 return e

def macd(prices):
 if len(prices) < 26:
  return 0
 return ema(prices,12)-ema(prices,26)

def stoch(closes, highs, lows, per=14):
 if len(closes) < per:
  return 50
 hh=max(highs[-per:])
 ll=min(lows[-per:])
 if hh==ll:
  return 50
 return 100*(closes[-1]-ll)/(hh-ll)

def analyze(interval, label):
 closes,highs,lows=get_candles(interval)
 if len(closes) < 50:
  return None
 price=closes[-1]
 r=rsi(closes)
 e20=ema(closes,20)
 e50=ema(closes,50)
 m=macd(closes)
 st=stoch(closes,highs,lows)
 sup=min(lows[-20:])
 res=max(highs[-20:])
 b=ema(closes,20)
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
 if
