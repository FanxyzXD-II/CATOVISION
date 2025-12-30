import os
import io
import base64
import requests
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance

# Konfigurasi Path untuk Vercel
app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

@app.route("/")
def index():
    # Data tampilan kucing (Opsional: Bisa diganti dengan data koin)
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur AI Photo Enhancer untuk gambar chart"""
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
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="chart_HD.jpg")
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    """Fitur AI Analyst 100% Crypto menggunakan API Gemini Gimita"""
    user_query = request.form.get('query', '')
    lang = request.form.get('lang', 'id')
    image_file = request.files.get('image')
    
    # URL API Gemini sesuai permintaan Anda
    GIMITA_URL = "https://api.gimita.id/api/ai/gemini"
    
    try:
        # Prompt sistem agar AI berperan sebagai Ahli Kripto & Paxi L1
        system_instruction = (
            f"Anda adalah CATOVISION AI, pakar pasar Crypto dan Paxi L1 Blockchain. "
            f"Berikan analisa teknikal, sinyal trading, atau informasi on-chain. "
            f"Jawab dalam bahasa {lang}. "
        )
        
        combined_query = f"{system_instruction} Pertanyaan User: {user_query}"
        
        # Parameter dasar untuk GET Request
        params = {"message": combined_query}

        # Jika user mengunggah gambar (Analisa Chart)
        if image_file:
            # Kompresi gambar sederhana sebelum encode (untuk menghindari limitasi panjang URL GET)
            img = Image.open(image_file)
            img.thumbnail((800, 800)) # Resize agar Base64 tidak terlalu panjang
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=70)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Format pengiriman gambar untuk API Gimita
            params["image"] = f"data:image/jpeg;base64,{img_base64}"

        # Eksekusi ke API Gimita
        response = requests.get(GIMITA_URL, params=params, timeout=20)
        res_json = response.json()
        
        # Ambil hasil respons dari API
        # Catatan: Sesuaikan key 'result' sesuai format kembalian asli api.gimita.id
        reply = res_json.get('result') or res_json.get('response') or "AI sedang melakukan sinkronisasi dengan blockchain..."
        
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": "Koneksi ke sistem AI terputus. Pastikan API Gimita aktif."})

# Export app untuk Vercel
app = app

