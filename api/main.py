import os
import io
import requests
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance

# Inisialisasi Flask
app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

# Ambil API Key dari Environment Variable Vercel
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/")
def index():
    """Halaman Utama"""
    # Menampilkan koleksi kucing di halaman home
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur Photo Enhancer - TETAP ADA"""
    if 'photo' not in request.files:
        return "File tidak ditemukan", 400
    
    try:
        file = request.files['photo']
        img = Image.open(file.stream).convert("RGB")
        
        # Proses penjernihan gambar
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
    """Fitur AI Analyst - Update Model ke Llama 3.3"""
    user_query = request.form.get('query')
    lang = request.form.get('lang', 'id')
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key Groq tidak ditemukan di Vercel."})

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}", 
            "Content-Type": "application/json"
        }
        
        # MENGGANTI MODEL YANG SUDAH MATI KE MODEL TERBARU
        payload = {
            "model": "llama-3.3-70b-versatile", # Update dari llama3-70b-8192
            "messages": [
                {"role": "system", "content": f"You are CATOVISION AI. You are a crypto expert. Answer in {lang}."},
                {"role": "user", "content": user_query}
            ],
            "temperature": 0.5
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            headers=headers, 
            json=payload,
            timeout=15
        )
        
        res_json = response.json()
        
        if response.status_code == 200 and 'choices' in res_json:
            return jsonify({"reply": res_json['choices'][0]['message']['content']})
        
        # Menampilkan pesan error spesifik jika API bermasalah
        error_msg = res_json.get('error', {}).get('message', 'AI sedang sibuk.')
        return jsonify({"reply": f"CATOVISION Error: {error_msg}"})

    except Exception as e:
        return jsonify({"reply": f"Error sistem: {str(e)}"})

app = app
