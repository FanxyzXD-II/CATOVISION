import os
import io
import requests
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance
from datetime import datetime

app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

# Ambil API Key dari Environment Variable Vercel
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/")
def index():
    """Halaman Utama - Grid foto kucing tetap muncul"""
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur Photo Enhancer"""
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
    """AI Analyst - Binance + Order Book + Fear & Greed"""
    user_query = request.form.get('query', '')
    lang_code = request.form.get('lang', 'id')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lang_map = {
        'id': 'Indonesian / Bahasa Indonesia',
        'en': 'English',
        'zh': 'Chinese / Mandarin (Simplified Chinese)'
    }
    target_lang = lang_map.get(lang_code, 'Indonesian / Bahasa Indonesia')

    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key Groq tidak ditemukan."})

    # 1. Ambil Data Real-time (Binance & Sentimen)
    market_context = ""
    sentiment_context = ""
    try:
        # A. Data Binance (Harga, Volume, Depth)
        clean_coin = user_query.split()[-1].strip('().').upper()
        symbol = f"{clean_coin}USDT"
        
        ticker = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=5).json()
        depth = requests.get(f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5", timeout=5).json()
        
        # B. Data Fear & Greed Index (Alternative.me API)
        fg_res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        fng_value = fg_res['data'][0]['value']
        fng_status = fg_res['data'][0]['value_classification']
        sentiment_context = f"Sentimen Pasar Global: {fng_value}/100 ({fng_status})."

        if 'lastPrice' in ticker:
            price = float(ticker['lastPrice'])
            change = float(ticker['priceChangePercent'])
            volume = float(ticker['quoteVolume'])
            top_bid = depth['bids'][0][0]
            top_ask = depth['asks'][0][0]
            
            market_context = (
                f"WAKTU: {current_time}. ASET: {symbol}. HARGA: ${price:,.2f} ({change}% 24h). "
                f"VOLUME: {volume:,.2f} USDT. ORDER BOOK: Bid ${top_bid}, Ask ${top_ask}. "
                f"{sentiment_context}"
            )
    except Exception:
        market_context = f"Data real-time terbatas. Waktu: {current_time}. {sentiment_context}"

    # 2. Request ke Groq (Llama 3.3)
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_prompt = (
            f"MANDATORY: RESPONSE MUST BE 100% IN {target_lang}. "
            f"You are CATOVISION AI, an elite crypto analyst operating in year 2025. "
            f"Requirement: Start with Price, Volume, and Fear & Greed Index from: '{market_context}'. "
            f"Analysis: 1. Sentiment impact (Fear/Greed). 2. Order book walls (Bid/Ask). 3. Candlestick & Trend. "
            f"Signals: Buy/Sell/Wait with Entry, TP, and SL. "
            f"Rule: 'SOL' = Solana. No Linux talk. Use 2025 context only."
        )

        payload = {
            "model": "llama-3.3-70b-versatile", #
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Language: {target_lang}. Query: {user_query}. Data: {market_context}"}
            ],
            "temperature": 0.2 #
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        res_json = response.json()
        
        if response.status_code == 200 and 'choices' in res_json:
            return jsonify({"reply": res_json['choices'][0]['message']['content']})
        
        return jsonify({"reply": "CATOVISION sedang menganalisis psikologi market."})

    except Exception as e:
        return jsonify({"reply": f"System Error: {str(e)}"})

app = app

