import os, requests
from flask import Flask, request
TOKEN=os.environ.get("TELEGRAM_TOKEN","").strip()
URL=f"https://api.telegram.org/bot{TOKEN}"
app=Flask(__name__)
LAST_CHATS=set()
LAST_ALERT=""

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

def macd(p): return ema(p,12)-ema(p,26) if len(p)>=26 else 0

def stoch(c,h,l,per=14):
 if len(c)<per: return 50
 hh=max(h[-per:]); ll=min(l[-per:])
 return 100*(c[-1]-ll)/(hh-ll) if hh!=ll else 50

def analyze(interval,label):
 closes,highs,lows=get_candles(interval)
 if len(closes)<50: return None
 price=closes[-1]; r=rsi(closes); e20=ema(closes,20); e50=ema(closes,50)
 m=macd(closes); st=stoch(closes,highs,lows)
 sup=min(lows[-20:]); res=max(highs[-20:]); b=ema(closes,20)
 buy=sell=0; det=[]
 if r<40: buy+=1; det.append("RSI")
 elif r>60: sell+=1; det.append("RSI")
 if closes[-1]>e20: buy+=1; det.append("EMA20")
 else: sell+=1; det.append("EMA20")
 if e20>e50: buy+=1; det.append("Trend")
 else: sell+=1; det.append("Trend")
 if m>0: buy+=1; det.append("MACD")
 else: sell+=1; det.append("MACD")
 if closes[-1]<b*0.998: buy+=1; det.append("BB")
 elif closes[-1]>b*1.002: sell+=1; det.append("BB")
 else:
  if st<30: buy+=1; det.append("Stoch")
  elif st>70: sell+=1; det.append("Stoch")
 if price<=sup*1.003: buy+=1; det.append("دعم")
 elif price>=res*0.997: sell+=1; det.append("مقاومة")
 score=max(buy,sell); dir_="buy" if buy>sell else "sell"
 return {"tf":label,"price":price,"sup":sup,"res":res,"score":score,"dir":dir_,"det":det,"rsi":r}

def build():
 tfs=[("1m","دقيقة"),("5m","5 دقايق"),("15m","ربع ساعة"),("60m","ساعة")]
 results=[]
 for i,l in tfs:
  a=analyze(i,l)
  if a and a["score"]>=3: results.append(a)
 if not results: return None
 price=get_price() or results[0]["price"]
 buys=[r for r in results if r["dir"]=="buy"]
 sells=[r for r in results if r["dir"]=="sell"]
 agree=None; trades_list=[]
 if len(buys)>=3: agree="BUY"; trades_list=buys
 elif len(sells)>=3: agree="SELL"; trades_list=sells
 else: return None, price, 0, "no agree"
 count=len(trades_list)
 risk_pct=0.0010 # 0.10% = حوالي 4$ فقط - مناسب للمحفظة الصغيرة
 final_trades=[]
 for r in trades_list:
  if r["dir"]=="buy":
   sl_tight=price*(1-risk_pct)
   sl_sup=r["sup"]
   sl=max(sl_tight, sl_sup) if sl_sup < price else sl_tight
   if price - sl > price*0.003: sl=sl_tight
   risk=price-sl; tp=price+2*risk
   final_trades.append(f"🟢 {r['tf']} {r['dir'].upper()} {r['score']}/6 RSI:{r['rsi']:.0f}")
   final_trades.append(f" دخول ${price:.2f} وقف ${sl:.2f} (-${risk:.2f}) هدف ${tp:.2f}")
  else:
   sl_tight=price*(1+risk_pct)
   sl_res=r["res"]
   sl=min(sl_tight, sl_res) if sl_res > price else sl_tight
   if sl - price > price*0.003: sl=sl_tight
   risk=sl-price; tp=price-2*risk
   final_trades.append(f"🔴 {r['tf']} {r['dir'].upper()} {r['score']}/6 RSI:{r['rsi']:.0f}")
   final_trades.append(f" دخول ${price:.2f} وقف ${sl:.2f} (-${risk:.2f}) هدف ${tp:.2f}")
 return final_trades, price, count, agree

def send(cid,txt): requests.post(f"{URL}/sendMessage
