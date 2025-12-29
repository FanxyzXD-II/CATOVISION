import os
import io
import requests
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance
from datetime import datetime

app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

# API Key Groq dari Environment Variable Vercel
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/")
def index():
    """Halaman Utama dengan data grid foto kucing"""
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur Photo Enhancer HD"""
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
    """AI Analyst PRO - Integrasi Binance & Sentimen 2025/2030"""
    user_query = request.form.get('query', '')
    lang_code = request.form.get('lang', 'id')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Pemetaan bahasa eksplisit agar AI tidak salah bahasa
    lang_map = {
        'id': 'Indonesian / Bahasa Indonesia',
        'en': 'English',
        'zh': 'Chinese / Mandarin (Simplified Chinese)'
    }
    target_lang = lang_map.get(lang_code, 'Indonesian / Bahasa Indonesia')

    if not GROQ_API_KEY:
        return jsonify({"reply": "CATOVISION ERROR: Protokol API tidak terkonfigurasi."})

    # 1. PENGAMBILAN DATA MARKET REAL-TIME (BINANCE & SENTIMEN)
    market_context = ""
    try:
        # Mencari simbol koin dari query (Contoh: SOL, BTC, ETH)
        words = user_query.upper().split()
        coin_list = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP', 'ADA', 'DOT']
        clean_coin = next((c for c in words if c in coin_list), words[-1].strip('().'))
        symbol = f"{clean_coin}USDT"
        
        # Panggilan ke Binance API (Harga & Volume)
        ticker = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=5).json()
        # Panggilan ke Binance API (Order Book / Tembok Harga)
        depth = requests.get(f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5", timeout=5).json()
        # Panggilan ke Fear & Greed Index
        fg_res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        fng = f"{fg_res['data'][0]['value']} ({fg_res['data'][0]['value_classification']})"

        if 'lastPrice' in ticker:
            price = float(ticker['lastPrice'])
            change = float(ticker['priceChangePercent'])
            vol = float(ticker['quoteVolume'])
            market_context = (
                f"WAKTU: {current_time}. ASET: {symbol}. HARGA: ${price:,.2f} ({change}%). "
                f"VOL 24H: ${vol:,.0f} USDT. SENTIMEN: {fng}. "
                f"ORDER BOOK: Bid ${depth['bids'][0][0]}, Ask ${depth['asks'][0][0]}."
            )
    except Exception:
        market_context = f"Data live terbatas. Sinkronisasi protokol CATO pada {current_time}."

    # 2. REQUEST KE MODEL AI (Llama 3.3)
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        system_prompt = (
            f"MANDATORY: RESPONSE MUST BE 100% IN {target_lang}. "
            f"You are CATOVISION AI PRO, an elite crypto analyst. "
            f"You MUST use this real-time data for analysis: '{market_context}'. "
            f"Tasks: 1. Sentiment impact 2. Order book walls 3. Candlestick/Trend. "
            f"Signals: Entry, TP, SL. 'SOL' is Solana crypto. No Linux talk. "
            f"Respond using a professional trading tone for the year 2025/2030."
        )

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Answer strictly in {target_lang}. Data: {market_context}. Query: {user_query}"}
            ],
            "temperature": 0.2
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        res_json = response.json()
        
        if response.status_code == 200:
            return jsonify({"reply": res_json['choices'][0]['message']['content']})
        
        return jsonify({"reply": "CATOVISION PRO: Sistem sedang melakukan sinkronisasi data kuantum dan sentimen global."})

    except Exception:
        return jsonify({"reply": "CATOVISION ERROR: Terdeteksi anomali pada protokol analitik."})

app = app

