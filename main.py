import os, requests
from flask import Flask, request

TOKEN=os.environ.get("TELEGRAM_TOKEN","")
CHAT_ID=os.environ.get("CHAT_ID","")
URL=f"https://api.telegram.org/bot{TOKEN}/sendMessage"

app=Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        price = data.get('price', data.get('close', '0'))
        signal = data.get('signal', 'XAU')
        score = data.get('score', '5')
        msg = f"🔥 قناص XAU {score}/6\n📊 {signal}\n💰 السعر المباشر: {price}\n🎯 هدف 5$ وقف 3$"
        requests.post(URL, json={"chat_id": CHAT_ID, "text": msg})
        return "ok", 200
    except Exception as e:
        return str(e), 500

@app.route('/')
def home():
    return "Bot Live - Price from TV"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
