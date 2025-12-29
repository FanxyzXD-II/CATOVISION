import os
import io
import requests
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance
from datetime import datetime

app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

# API Key dari Environment Vercel
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/")
def index():
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    if 'photo' not in request.files:
        return "File tidak ditemukan", 400
    try:
        file = request.files['photo']
        img = Image.open(file.stream).convert("RGB")
        img = ImageEnhance.Sharpness(img).enhance(2.5)
        img = ImageEnhance.Contrast(img).enhance(1.4)
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="CATO_HD.jpg")
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    user_query = request.form.get('query', '')
    lang_code = request.form.get('lang', 'id')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lang_map = {'id': 'Indonesian', 'en': 'English', 'zh': 'Chinese'}
    target_lang = lang_map.get(lang_code, 'Indonesian')

    if not GROQ_API_KEY:
        return jsonify({"reply": "CATOVISION ERROR: API Key Groq tidak ditemukan."})

    # PROSES DATA BINANCE & SENTIMEN
    market_context = "Data market tidak tersedia."
    try:
        # Menangkap simbol koin dengan lebih akurat
        words = user_query.upper().split()
        coin_list = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP']
        clean_coin = next((c for c in words if c in coin_list), words[-1].strip('().'))
        symbol = f"{clean_coin}USDT"
        
        # Ambil Harga, Volume & Depth dari Binance
        ticker = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=5).json()
        depth = requests.get(f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5", timeout=5).json()
        
        # Ambil Fear & Greed Index
        fg_res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        fng = f"{fg_res['data'][0]['value']} ({fg_res['data'][0]['value_classification']})"

        if 'lastPrice' in ticker:
            price = float(ticker['lastPrice'])
            change = float(ticker['priceChangePercent'])
            vol = float(ticker['quoteVolume'])
            market_context = (
                f"WAKTU: {current_time}. ASET: {symbol}. HARGA: ${price:,.2f} ({change}%). "
                f"VOLUME: ${vol:,.0f} USDT. SENTIMEN: {fng}. "
                f"ORDER BOOK: Bid ${depth['bids'][0][0]}, Ask ${depth['asks'][0][0]}."
            )
    except Exception:
        market_context = f"Data live terbatas. Sinkronisasi waktu: {current_time}."

    # REQUEST KE AI
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        system_prompt = (
            f"MANDATORY: RESPONSE MUST BE 100% IN {target_lang}. "
            f"You are CATOVISION AI PRO, an elite analyst. "
            f"Start with live data: '{market_context}'. "
            f"Analyze: 1. Sentiment 2. Order book walls 3. Candlestick/Trend. "
            f"Signals: Entry, TP, SL. "
            f"Rule: SOL is Solana. Use 2025/2030 data context only."
        )

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze strictly in {target_lang}: {user_query}. Context: {market_context}"}
            ],
            "temperature": 0.2
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        res_json = response.json()
        
        if response.status_code == 200:
            return jsonify({"reply": res_json['choices'][0]['message']['content']})
        
        return jsonify({"reply": "CATOVISION PRO: Sistem sedang melakukan sinkronisasi data kuantum dan sentimen global."})

    except Exception as e:
        return jsonify({"reply": f"CATOVISION ERROR: Terdeteksi anomali pada protokol analitik."})

app = app

