import os
import io
import base64
import requests
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance
from datetime import datetime

app = Flask(__name__)

# Mengambil API Key dari Environment Variables Vercel
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def encode_image(image_file):
    """Mengonversi gambar ke Base64 tanpa simpan ke disk (Vercel Friendly)."""
    return base64.b64encode(image_file.read()).decode('utf-8')

@app.route("/")
def index():
    """Halaman Utama dengan Data Galeri Kucing."""
    koleksi_kucing = [
        {"id": 1, "name": "Cat 1", "img": "1000037411.jpg"},
        {"id": 2, "name": "Cat 2", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur Penjernih Foto AI HD."""
    if 'photo' not in request.files: return "File tidak ditemukan", 400
    try:
        file = request.files['photo']
        img = Image.open(file.stream).convert("RGB")
        img = ImageEnhance.Sharpness(img).enhance(2.5)
        img = ImageEnhance.Contrast(img).enhance(1.4)
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="CATO_HD.jpg")
    except Exception as e: return str(e), 500

@app.route("/chat", methods=["POST"])
def chat():
    """AI Analyst PRO - 100% Crypto Focus & Real-time Market Data."""
    user_query = request.form.get('query', '')
    lang_code = request.form.get('lang', 'id')
    image_file = request.files.get('image')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. INTEGRASI DATA MARKET REAL-TIME (BINANCE API)
    market_info = ""
    try:
        # Deteksi koin dari input user (Default BTC)
        coin = "BTC"
        for c in ['ETH', 'SOL', 'BNB', 'DOGE', 'XRP', 'ADA', 'LINK']:
            if c in user_query.upper(): coin = c; break
        
        # Panggilan cepat ke Binance API
        res = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={coin}USDT", timeout=3).json()
        market_info = (
            f"DATA LIVE {coin}USDT per {current_time}: "
            f"Harga ${float(res['lastPrice']):,.2f} ({res['priceChangePercent']}%). "
            f"High: ${float(res['highPrice']):,.2f}, Low: ${float(res['lowPrice']):,.2f}."
        )
    except:
        market_info = "Data pasar sedang sinkronisasi. Gunakan parameter teknikal umum."

    # 2. PEMETAAN BAHASA & PEMILIHAN MODEL
    lang_map = {
        'id': 'Bahasa Indonesia', 
        'en': 'English', 
        'zh': 'Chinese (Mandarin/Simplified Chinese)'
    }
    target_lang = lang_map.get(lang_code, 'Bahasa Indonesia')
    
    # Gunakan Vision jika ada gambar, Versatile jika teks saja
    model = "llama-3.2-11b-vision-preview" if image_file else "llama-3.3-70b-versatile"

    # 3. SYSTEM PROMPT: 100% CRYPTO ANALYST GUARDRAILS
    system_prompt = (
        f"Anda adalah CATOVISION PRO, Analis Crypto Senior era 2025-2030.\n"
        f"TUGAS UTAMA: Memberikan analisis market kripto profesional dalam {target_lang}.\n"
        f"BATASAN KETAT: Hanya jawab topik Crypto, Blockchain, dan Web3. Tolak topik lain dengan sopan.\n"
        f"DATA PASAR SAAT INI: {market_info}.\n"
        f"FORMAT WAJIB: 1. Sentimen Market, 2. Analisis Teknikal (SMC/Price Action), 3. Strategi (Entry, TP, SL).\n"
        f"PENTING: Jangan memotong jawaban. Selesaikan kalimat sepenuhnya."
    )

    messages = [{"role": "system", "content": system_prompt}]
    
    if image_file:
        b64_img = encode_image(image_file)
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"Analisis chart ini secara teknikal: {user_query}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
            ]
        })
    else:
        messages.append({"role": "user", "content": user_query})

    try:
        payload = {
            "model": model, 
            "messages": messages, 
            "temperature": 0.1, # Rendah agar akurat (faktual)
            "max_tokens": 3000   # Tinggi agar jawaban lengkap
        }
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}", 
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            json=payload, headers=headers, timeout=15
        )
        return jsonify({"reply": response.json()['choices'][0]['message']['content']})
    except Exception as e:
        return jsonify({"reply": "Protokol analitik sedang sibuk. Silakan coba sesaat lagi."})

if __name__ == "__main__":
    app.run(debug=True)

