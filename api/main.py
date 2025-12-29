import os
import io
import requests
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance

app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

# Ambil API Key dari Environment Variable Vercel
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/")
def index():
    """Halaman Utama - Menjaga data foto kucing agar tetap tampil"""
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur Photo Enhancer - Tetap dipertahankan tanpa perubahan"""
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
    """AI Analyst - Menggunakan API Binance & Instruksi Bahasa yang Ketat"""
    user_query = request.form.get('query', '')
    lang_code = request.form.get('lang', 'id')
    
    # Mapping bahasa eksplisit untuk kepatuhan AI
    lang_map = {
        'id': 'Indonesian / Bahasa Indonesia',
        'en': 'English',
        'zh': 'Chinese / Mandarin (Simplified Chinese)'
    }
    target_lang = lang_map.get(lang_code, 'Indonesian / Bahasa Indonesia')

    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key Groq tidak ditemukan."})

    # 1. Integrasi Data Real-time Binance (Ticker 24 jam)
    market_context = ""
    try:
        # Mengambil simbol koin (misal: 'SOL' dari query)
        clean_coin = user_query.split()[-1].strip('().').upper()
        symbol = f"{clean_coin}USDT" # Format standar Binance
        
        # Panggilan API Binance publik
        res = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=5).json()
        
        if 'lastPrice' in res:
            price = float(res['lastPrice'])
            change = float(res['priceChangePercent'])
            # Format data untuk dibaca oleh AI
            market_context = f"BINANCE LIVE DATA: {symbol} Price ${price:,.2f} USD ({change}% 24h)."
    except Exception:
        market_context = "Market data currently unavailable from Binance."

    # 2. Request ke Groq (Llama 3.3) dengan Prompt Khusus Crypto
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        # Aturan sistem yang memaksa penggunaan bahasa dan data harga
        system_prompt = (
            f"MANDATORY: YOU MUST RESPOND 100% IN {target_lang}. "
            f"You are CATOVISION AI, a world-class professional crypto analyst. "
            f"Tasks: Provide candlestick analysis, trend direction, and entry zones. "
            f"Requirement: Start your response with the provided price: '{market_context}'. "
            f"If 'SOL' is mentioned, analyze Solana cryptocurrency, NOT Linux. "
            f"Ensure Buy/Sell signals include Entry, TP, and SL targets."
        )

        payload = {
            "model": "llama-3.3-70b-versatile", # Model terbaru yang aktif
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Language: {target_lang}. Analyze this query using current data: {user_query}. Price Context: {market_context}"}
            ],
            "temperature": 0.2 # Kepatuhan maksimal terhadap data dan instruksi bahasa
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        res_json = response.json()
        
        if response.status_code == 200 and 'choices' in res_json:
            return jsonify({"reply": res_json['choices'][0]['message']['content']})
        
        return jsonify({"reply": "CATO is busy analyzing market data."})

    except Exception as e:
        return jsonify({"reply": f"System Error: {str(e)}"})

app = app
