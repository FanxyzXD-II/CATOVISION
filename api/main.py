import os
import io
import base64
import requests
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance

# Path disesuaikan untuk struktur folder Vercel
app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

# API Key Groq dari Environment Variable Vercel
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/")
def index():
    """Halaman Utama"""
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur AI Photo Enhancer (Asli - Tetap Kualitas Tinggi)"""
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
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="gambar_HD.jpg")
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    """Fitur AI Analyst dengan Kompresi Otomatis untuk Kecepatan"""
    user_query = request.form.get('query', '')
    lang = request.form.get('lang', 'id')
    image_file = request.files.get('image')
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key Groq tidak ditemukan."})

    # --- Market Context ---
    market_context = ""
    if user_query and not image_file:
        try:
            search_res = requests.get(f"https://api.coingecko.com/api/v3/search?query={user_query}", timeout=3).json()
            if search_res.get('coins'):
                coin_id = search_res['coins'][0]['id']
                p_res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true", timeout=3).json()
                if coin_id in p_res:
                    data = p_res[coin_id]
                    market_context = f"[Harga {coin_id}: ${data['usd']} ({round(data.get('usd_24h_change', 0), 2)}%)]"
        except:
            pass

    # --- Penanganan Input (Vision vs Text) ---
    if image_file:
        selected_model = "llama-3.2-11b-vision-preview"
        try:
            # PROSES KOMPRESI: Agar tidak timeout di Vercel
            img = Image.open(image_file).convert("RGB")
            
            # Batasi ukuran maksimal 1024px (tetap tajam untuk AI)
            img.thumbnail((1024, 1024)) 
            
            buffered = io.BytesIO()
            # Simpan dengan kualitas 75% untuk mengecilkan ukuran file secara drastis
            img.save(buffered, format="JPEG", quality=75) 
            image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

            content = [
                {"type": "text", "text": f"Instruction: {user_query if user_query else 'Analyze this chart'}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ]
        except Exception as e:
            return jsonify({"reply": f"Gagal memproses gambar: {str(e)}"})
    else:
        selected_model = "llama-3.3-70b-versatile"
        content = f"Context: {market_context}\nQuery: {user_query}"

    try:
        payload = {
            "model": selected_model,
            "messages": [
                {
                    "role": "system", 
                    "content": f"You are CATOVISION AI, financial expert. Answer in {lang}."
                },
                {"role": "user", "content": content}
            ],
            "temperature": 0.5
        }
        
        # Kirim ke Groq dengan timeout ketat
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}, 
            json=payload, 
            timeout=8.5 
        )
        
        if response.status_code == 200:
            return jsonify({"reply": response.json()['choices'][0]['message']['content']})
        
        return jsonify({"reply": "AI Sedang sibuk atau limit tercapai. Coba beberapa saat lagi."})
    
    except Exception as e:
        return jsonify({"reply": "Koneksi terputus atau timeout (gambar terlalu besar)."})

# Export app
app = app

