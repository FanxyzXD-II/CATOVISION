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
    """Halaman Utama dengan data foto kucing - TETAP DIPERTAHANKAN"""
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
    """Fitur AI Analyst - Fokus 100% Crypto & Wajib Menggunakan Harga Live"""
    user_query = request.form.get('query')
    lang = request.form.get('lang', 'id')
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key Groq tidak ditemukan."})

    # 1. Ambil Data Harga Real-time (Market Context)
    market_context = ""
    try:
        search_res = requests.get(f"https://api.coingecko.com/api/v3/search?query={user_query}", timeout=3).json()
        if search_res.get('coins'):
            coin_id = search_res['coins'][0]['id']
            p_res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true", timeout=3).json()
            if coin_id in p_res:
                data = p_res[coin_id]
                # Label kapital agar AI memberikan perhatian penuh pada data ini
                market_context = f"DATA HARGA SAAT INI UNTUK {coin_id.upper()}: ${data['usd']} USD (Perubahan 24j: {round(data.get('usd_24h_change', 0), 2)}%)."
    except Exception:
        market_context = "Data harga live saat ini sedang tidak tersedia."

    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        # SYSTEM PROMPT YANG DIPERKETAT
        system_prompt = (
            f"You are CATOVISION AI, a world-class professional Cryptocurrency technical analyst. "
            f"Mandatory: Respond 100% in {lang}. "
            f"Instructions: "
            f"1. You MUST use the 'DATA HARGA SAAT INI' provided in the context for your analysis. "
            f"2. Focus 100% on Candlestick patterns, market trends, and crypto structure. "
            f"3. Provide trading signals (Buy/Sell) with specific Entry (near current price), TP, and SL. "
            f"4. Always analyze based on real-time data provided. Never use old or hallucinated prices. "
            f"5. 'SOL' always means Solana Cryptocurrency, never Linux or other topics."
        )

        payload = {
            "model": "llama-3.3-70b-versatile", # Model terbaru
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"MARKET CONTEXT: {market_context}\n\nQUERY: {user_query}"}
            ],
            "temperature": 0.4 # Diturunkan agar AI lebih patuh pada data angka
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
        res_json = response.json()
        
        if response.status_code == 200 and 'choices' in res_json:
            return jsonify({"reply": res_json['choices'][0]['message']['content']})
        
        error_msg = res_json.get('error', {}).get('message', 'AI sedang sibuk.')
        return jsonify({"reply": f"CATOVISION Error: {error_msg}"})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

app = app
