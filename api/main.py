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
    """Halaman Utama - Mengirim data kucing agar grid muncul"""
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur Photo Enhancer tetap aktif"""
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
    """AI Analyst - Data Binance 2025/2030 (Harga + Volume + Order Book + Sentimen)"""
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

    # 1. Integrasi Data Real-time (Binance & Sentimen Global)
    market_context = ""
    try:
        # Membersihkan query untuk mencari ID koin (misal: 'SOL')
        clean_coin = user_query.split()[-1].strip('().').upper()
        symbol = f"{clean_coin}USDT"
        
        # A. Data Binance (Harga & Volume)
        ticker = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=5).json()
        # B. Data Order Book (Tembok Harga)
        depth = requests.get(f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5", timeout=5).json()
        # C. Data Sentimen (Fear & Greed Index)
        fg_res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        fng_val = fg_res['data'][0]['value']
        fng_status = fg_res['data'][0]['value_classification']

        if 'lastPrice' in ticker:
            price = float(ticker['lastPrice'])
            change = float(ticker['priceChangePercent'])
            vol = float(ticker['quoteVolume'])
            top_bid = depth['bids'][0][0] # Antrian Beli
            top_ask = depth['asks'][0][0] # Antrian Jual
            
            market_context = (
                f"BINANCE LIVE DATA ({current_time}): {symbol} Price ${price:,.2f} USD ({change}% 24h). "
                f"24h Volume: {vol:,.2f} USDT. Order Book: Bid ${top_bid}, Ask ${top_ask}. "
                f"Market Sentiment: {fng_val}/100 ({fng_status})."
            )
    except Exception:
        market_context = f"Data Binance sedang sibuk. Waktu server: {current_time}."

    # 2. Request ke Groq (Llama 3.3) dengan instruksi bahasa yang sangat ketat
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_prompt = (
            f"MANDATORY: RESPONSE MUST BE 100% IN {target_lang}. NEVER USE OTHER LANGUAGES. "
            f"You are CATOVISION AI, an elite crypto analyst in year 2025. "
            f"Start your response by mentioning the live price, volume, and Fear & Greed index from: '{market_context}'. "
            f"Analysis Tasks: 1. Sentiment impact. 2. Order book walls. 3. Candlestick & Trend. "
            f"Provide Trading Signals: BUY/SELL/WAIT with Entry, TP, and SL targets. "
            f"Rule: 'SOL' is Solana crypto. No Linux talk. Use data for the year 2025/2030."
        )

        payload = {
            "model": "llama-3.3-70b-versatile", # Model terbaru aktif
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Answer strictly in {target_lang}. Market Context: {market_context}. User Query: {user_query}"}
            ],
            "temperature": 0.2 # Kepatuhan maksimal terhadap data
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        res_json = response.json()
        
        if response.status_code == 200 and 'choices' in res_json:
            return jsonify({"reply": res_json['choices'][0]['message']['content']})
        
        return jsonify({"reply": "CATOVISION sedang menghitung psikologi market."})

    except Exception as e:
        return jsonify({"reply": f"System Error: {str(e)}"})

app = app
