import os, requests
from flask import Flask, request

TOKEN=os.environ.get("TELEGRAM_TOKEN","").strip()
URL=f"https://api.telegram.org/bot{TOKEN}"
app=Flask(__name__)

@app.route("/")
def home():
    return "OK V13.1"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data=request.get_json(force=True)
    if "message" in data:
        cid=data["message"]["chat"]["id"]
        txt=data["message"].get("text","")
        if "/sniper" in txt:
            price=0
            try:
                price=float(requests.get("https://api.gold-api.com/price/XAU",timeout=8).json().get("price",0))
            except:
                price=4160.0
            # وقف ضيق 0.10%
            sl_buy=price*0.999
            tp_buy=price*1.002
            sl_sell=price*1.001
            tp_sell=price*0.998
            msg=f"السعر ${price:.2f}\n\nوقف ضيق 0.10% ~4$\nBUY وقف ${sl_buy:.2f} هدف ${tp_buy:.2f}\nSELL وقف ${sl_sell:.2f} هدف ${tp_sell:.2f}\n\nملاحظة: هذا فحص سريع، النسخة الكاملة باتفاق 3 فريمات بتجي بعد ما يشتغل"
            requests.post(f"{URL}/sendMessage",json={"chat_id":cid,"text":msg})
        elif "/start" in txt:
            requests.post(f"{URL}/sendMessage",json={"chat_id":cid,"text":"شغال /sniper"})
    return "ok"

@app.route("/setwebhook")
def sethook():
    r=requests.get(f"{URL}/setWebhook",params={"url":f"https://xau-bot-gjfk.onrender.com/{TOKEN}"})
    return r.text

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
