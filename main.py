# الحل النهائي - يصلح كل مشاكل البوت القديم
import os, requests
from flask import Flask, jsonify
from datetime import datetime
import yfinance as yf
import pandas as pd

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_analysis():
    try:
        data = yf.download("GC=F", period="5d", interval="15m", progress=False)
        if len(data) < 50: return None, None
        
        close = data['Close'].iloc[:,0] if hasattr(data['Close'], 'iloc') else data['Close']
        # RSI صحيح
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain/loss))
        rsi_val = float(rsi.iloc[-1])
        
        # سعر لحظي من مصدر سريع
        try:
            live_price = float(requests.get("https://api.gold-api.com/price/XAU", timeout=4).json()['price'])
        except:
            live_price = float(close.iloc[-1])

        score = 0
        reasons = []
        
        # 1- RSI منطقي
        if rsi_val < 30:
            score += 2
            reasons.append(f"RSI تشبع بيعي {rsi_val:.1f} -> BUY قوي")
        elif rsi_val > 70:
            score -= 2
            reasons.append(f"RSI تشبع شرائي {rsi_val:.1f} -> SELL قوي")
        
        # 2- SMA
        sma50 = close.rolling(50).mean().iloc[-1]
        if live_price > sma50: 
            score += 1
            reasons.append("فوق SMA50")
        else: 
            score -= 1
            reasons.append("تحت SMA50")

        # تقييم نهائي من 6
        final_score = 3 + score  # يحول من -3 الى +3 الى 0-6
        final_score = max(0, min(6, final_score))
        
        signal = "BUY" if score > 0 else "SELL" if score < 0 else "HOLD"
        
        return live_price, {"signal": signal, "score": final_score, "rsi": rsi_val, "reasons": reasons}
    except Exception as e:
        print(e)
        return None, None

@app.route("/")
def home():
    price, _ = get_analysis()
    return f"LIVE Fixed Bot: {price}"

@app.route("/price")
def price():
    price, analysis = get_analysis()
    return jsonify({"price": price, "analysis": analysis, "live": True})

@app.route("/check")
def check():
    price, a = get_analysis()
    if not a: return jsonify({"error": "no data"})
    
    # هنا الحل: ما نرسل الا القوي 5/6 و 6/6 فقط
    if a['score'] >= 5:
        msg = f"🔥 إشارة قوية {a['score']}/6\n{ a['signal']} الذهب\n💰 {price}$\nRSI: {a['rsi']:.1f}\n" + "\n".join(a['reasons'])
        if TOKEN:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg})
        return jsonify({"sent": True, "analysis": a, "price": price})
    else:
        return jsonify({"sent": False, "reason": f"ضعيفة {a['score']}/6 تم تجاهلها", "analysis": a, "price": price})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
