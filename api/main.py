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
    """Halaman Utama - Data foto kucing tetap ada"""
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur Photo Enhancer - Tetap dipertahankan"""
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
    """Fitur AI Analyst - Perbaikan Bahasa & Harga Real-time"""
    user_query = request.form.get('query', '')
    lang_code = request.form.get('lang', 'id')
    
    # Mapping kode bahasa untuk instruksi AI yang lebih jelas
    lang_map = {
        'id': 'Indonesian (Bahasa Indonesia)',
        'en': 'English',
        'zh': 'Chinese (Mandarin/Simplified Chinese)'
    }
    target_lang = lang_map.get(lang_code, 'Indonesian (Bahasa Indonesia)')

    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key Groq tidak ditemukan."})

    # 1. Ambil Data Harga Real-time
    market_context = ""
    # Membersihkan query untuk mencari ID koin (misal ambil kata terakhir 'SOL')
    clean_coin_name = user_query.split()[-1].strip('().')
    
    try:
        search_res = requests.get(f"https://api.coingecko.com/api/v3/search?query={clean_coin_name}", timeout=5).json()
        if search_res.get('coins'):
            coin_id = search_res['coins'][0]['id']
            p_res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true", timeout=5).json()
            if coin_id in p_res:
                data = p_res[coin_id]
                price_val = data['usd']
                change_val = round(data.get('usd_24h_change', 0), 2)
                # Context dalam bahasa target agar AI langsung paham
                if lang_code == 'zh':
                    market_context = f"{coin_id.upper()} 当前价格: ${price_val} USD (24小时变化: {change_val}%)"
                elif lang_code == 'en':
                    market_context = f"CURRENT {coin_id.upper()} PRICE: ${price_val} USD (24h Change: {change_val}%)"
                else:
                    market_context = f"HARGA {coin_id.upper()} SAAT INI: ${price_val} USD (Perubahan 24j: {change_val}%)"
    except Exception:
        market_context = "Data harga live tidak tersedia / Live price data unavailable."

    # 2. Request ke Groq dengan Prompt Bahasa yang Sangat Ketat
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_prompt = (
            f"STRICT RULE: You MUST respond 100% in {target_lang}. "
            f"You are CATOVISION AI, a Cryptocurrency expert. "
            f"Analyze ONLY crypto markets and candlestick patterns. "
            f"Mandatory: Use the provided price data: '{market_context}' in your first sentence. "
            f"Identify Trends (Bullish/Bearish), Support/Demand, and provide Buy/Sell signals with Entry, TP, and SL. "
            f"Reminder: 'SOL' is Solana crypto, not Linux. "
            f"Do not use any other language than {target_lang}."
        )

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Language: {target_lang}\nMarket Context: {market_context}\nQuestion: {user_query}"}
            ],
            "temperature": 0.3 # Suhu rendah agar AI patuh pada instruksi bahasa dan data
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        res_json = response.json()
        
        if response.status_code == 200 and 'choices' in res_json:
            return jsonify({"reply": res_json['choices'][0]['message']['content']})
        
        return jsonify({"reply": "Error: AI sedang sibuk memproses data."})

    except Exception as e:
        return jsonify({"reply": f"System Error: {str(e)}"})

app = app
