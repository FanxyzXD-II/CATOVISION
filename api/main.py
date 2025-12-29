import os
import io
import base64
import requests
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance
from datetime import datetime

app = Flask(__name__)

# Ambil API Key dari Vercel Environment Variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def encode_image(image_file):
    """Mengonversi gambar ke Base64 tanpa menyimpan ke disk."""
    return base64.b64encode(image_file.read()).decode('utf-8')

@app.route("/")
def index():
    # Data statis untuk demo grid kucing
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "cat1.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "cat2.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur AI Photo Enhancer"""
    if 'photo' not in request.files:
        return "No file uploaded", 400
    try:
        file = request.files['photo']
        img = Image.open(file.stream).convert("RGB")
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=85)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="CATO_HD.jpg")
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    """AI Analyst PRO dengan Dukungan Bahasa ID, EN, ZH"""
    user_query = request.form.get('query', '')
    lang_code = request.form.get('lang', 'id')
    image_file = request.files.get('image')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. MAPPING BAHASA (PENTING)
    lang_map = {
        'id': 'Indonesian (Bahasa Indonesia)',
        'en': 'English',
        'zh': 'Chinese (Simplified Mandarin / 普通话)'
    }
    target_lang = lang_map.get(lang_code, 'Indonesian (Bahasa Indonesia)')

    # 2. DATA MARKET REAL-TIME (BINANCE)
    market_context = ""
    try:
        coin = "BTC"
        words = user_query.upper().split()
        for c in ['ETH', 'SOL', 'BNB', 'DOGE', 'XRP']:
            if c in words:
                coin = c
                break
        
        # Panggilan cepat ke Binance
        res = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={coin}USDT", timeout=3).json()
        price = float(res['lastPrice'])
        change = res['priceChangePercent']
        market_context = f"LIVE DATA {coin}: ${price:,.2f} ({change}%). Time: {current_time}."
    except:
        market_context = f"Market sync pending for {current_time}."

    # 3. SETTING MODEL
    model = "llama-3.2-11b-vision-preview" if image_file else "llama-3.3-70b-versatile"

    # 4. SYSTEM PROMPT MULTI-BAHASA
    system_prompt = (
        f"You are CATOVISION AI PRO Analyst (2025-2030 Post-Halving Era).\n"
        f"CRITICAL RULE: You MUST respond 100% in {target_lang}. No other language allowed.\n"
        f"MARKET DATA: {market_context}.\n"
        f"INSTRUCTIONS:\n"
        f"- Analyze the current market structure and provide technical levels (Entry, TP, SL).\n"
        f"- If a chart image is provided, focus on candlestick patterns and volume.\n"
        f"- Maintain a professional, data-driven trading tone."
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Menangani Input Gambar vs Teks
    if image_file:
        b64_img = encode_image(image_file)
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"Language: {target_lang}. Analyze this: {user_query}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
            ]
        })
    else:
        messages.append({
            "role": "user", 
            "content": f"Answer strictly in {target_lang}. Query: {user_query}"
        })

    # 5. EXECUTION
    try:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1, # Menjaga akurasi angka
            "max_tokens": 1024
        }
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=15)
        res_data = response.json()
        
        return jsonify({"reply": res_data['choices'][0]['message']['content']})
    except Exception as e:
        # Pesan error juga disesuaikan bahasa (Opsional, di sini default Inggris agar dev tahu)
        return jsonify({"reply": "CATOVISION PRO: Protocol timeout or connection error. Please try again."})

if __name__ == "__main__":
    app.run(debug=True)
