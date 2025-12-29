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
    """Halaman Utama - Data foto kucing tetap ada agar Home tidak kosong"""
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
    """Fitur AI Analyst - Paksa AI Menggunakan Bahasa Pilihan & Data Harga"""
    user_query = request.form.get('query', '')
    lang_code = request.form.get('lang', 'id')
    
    # Mapping bahasa agar AI paham instruksi eksplisit
    lang_map = {
        'id': 'Indonesian / Bahasa Indonesia',
        'en': 'English',
        'zh': 'Chinese / Mandarin (Simplified Chinese)'
    }
    target_lang = lang_map.get(lang_code, 'Indonesian / Bahasa Indonesia')

    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key Groq tidak ditemukan."})

    # 1. Ambil Data Harga Real-time (Pembersihan Query)
    market_context = ""
    clean_coin = user_query.split()[-1].strip('().')
    
    try:
        search_res = requests.get(f"https://api.coingecko.com/api/v3/search?query={clean_coin}", timeout=5).json()
        if search_res.get('coins'):
            coin_id = search_res['coins'][0]['id']
            p_res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true", timeout=5).json()
            if coin_id in p_res:
                data = p_res[coin_id]
                price = data['usd']
                change = round(data.get('usd_24h_change', 0), 2)
                market_context = f"DATA: {coin_id.upper()} Price ${price} USD ({change}% 24h)."
    except Exception:
        market_context = "Market data not available."

    # 2. Request ke Groq dengan 'Strict Language Rule'
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        # Penegasan Bahasa di System Prompt agar AI tidak membangkang
        system_prompt = (
            f"STRICT RULE: YOU MUST ANSWER EXCLUSIVELY IN {target_lang}. "
            f"You are CATOVISION AI, a crypto analysis expert. "
            f"Tasks: Analyze candlestick patterns, market trends, and crypto zones. "
            f"Mandatory: Include the price data '{market_context}' in your {target_lang} response. "
            f"If 'SOL' is mentioned, it is Solana cryptocurrency. "
            f"NEVER respond in English unless the chosen language is English."
        )

        payload = {
            "model": "llama-3.3-70b-versatile", # Model terbaru yang didukung
            "messages": [
                {"role": "system", "content": system_prompt},
                # Tambahkan instruksi di user message sebagai pengingat kedua
                {"role": "user", "content": f"Answer strictly in {target_lang}. \nContext: {market_context}\nQuery: {user_query}"}
            ],
            "temperature": 0.2 # Diturunkan agar model lebih patuh dan kaku pada instruksi
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        res_json = response.json()
        
        if response.status_code == 200 and 'choices' in res_json:
            return jsonify({"reply": res_json['choices'][0]['message']['content']})
        
        return jsonify({"reply": "CATO sedang sibuk / CATO is busy."})

    except Exception as e:
        return jsonify({"reply": f"System Error: {str(e)}"})

app = app
