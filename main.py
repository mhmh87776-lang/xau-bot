import os, requests
from flask import Flask, request

TOKEN = os.environ.get("TELEGRAM_TOKEN","").strip()
URL = f"https://api.telegram.org/bot{TOKEN}"
app = Flask(__name__)
LAST_CHATS=set()
LAST_ALERT=""

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
    if len(closes)<k: return
