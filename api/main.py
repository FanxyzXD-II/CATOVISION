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
    """Halaman Utama - Mengirim data foto agar grid muncul"""
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur Photo Enhancer - TETAP DIPERTAHANKAN"""
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
    """Fitur AI Analyst - Fokus 100% Crypto & Harga Live"""
    user_query = request.form.get('query', '')
    lang = request.form.get('lang', 'id')
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key Groq tidak ditemukan."})

    # 1. Optimasi Pencarian CoinGecko (Ambil kata kunci saja, misal: 'BTC')
    market_context = "Tidak disediakan."
    clean_query = user_query.split()[-1].strip('().') # Ambil kata terakhir (misal 'SOL')
    
    try:
        # Cari ID koin
        search_res = requests.get(f"https://api.coingecko.com/api/v3/search?query={clean_query}", timeout=5).json()
        if search_res.get('coins'):
            coin_id = search_res['coins'][0]['id']
            # Ambil harga detail
            p_res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true", timeout=5).json()
            if coin_id in p_res:
                data = p_res[coin_id]
                market_context = f"HARGA {coin_id.upper()} SAAT INI: ${data['usd']} USD | PERUBAHAN 24J: {round(data.get('usd_24h_change', 0), 2)}%."
    except Exception:
        pass

    # 2. Request ke Groq dengan Instruksi Ketat
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_prompt = (
            f"You are CATOVISION AI, a world-class Cryptocurrency technical analyst. "
            f"Mandatory: Respond 100% in {lang}. "
            f"Strict Rules: "
            f"1. Always start your analysis by mentioning the 'DATA HARGA SAAT INI' provided. "
            f"2. Focus 100% on Candlestick patterns, market trends (Bullish/Bearish), and crypto structure. "
            f"3. Provide signals: BUY/SELL/WAIT, Entry price (must be near current price), TP, and SL. "
            f"4. 'SOL' refers ONLY to Solana cryptocurrency, NEVER Linux. "
            f"5. Use a professional trader tone."
        )

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"MARKET DATA: {market_context}\n\nUSER QUESTION: {user_query}"}
            ],
            "temperature": 0.3 # Diperendah agar AI lebih patuh pada angka harga
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        res_json = response.json()
        
        if response.status_code == 200 and 'choices' in res_json:
            return jsonify({"reply": res_json['choices'][0]['message']['content']})
        
        return jsonify({"reply": "Maaf, CATOVISION sedang sibuk memproses data market."})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

app = app

