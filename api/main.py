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
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur Photo Enhancer"""
    if 'photo' not in request.files:
        return "File tidak ditemukan", 400
    
    try:
        file = request.files['photo']
        img = Image.open(file.stream).convert("RGB")
        
        # Sharpness & Contrast
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
    """Fitur AI Analyst"""
    user_query = request.form.get('query')
    lang = request.form.get('lang', 'id')
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key tidak terdeteksi di server."})

    try:
        # Ambil Data Market
        market_context = ""
        search_res = requests.get(f"https://api.coingecko.com/api/v3/search?query={user_query}").json()
        
        if search_res.get('coins'):
            coin_id = search_res['coins'][0]['id']
            p_res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true").json()
            if coin_id in p_res:
                data = p_res[coin_id]
                market_context = f"Harga {coin_id}: ${data['usd']} ({round(data.get('usd_24h_change', 0), 2)}%)"

        # Request ke Groq
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": f"You are CATOVISION AI. Answer in {lang}."},
                {"role": "user", "content": f"Query: {user_query}. Context: {market_context}"}
            ],
            "temperature": 0.5
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
        
        if 'choices' in response:
            return jsonify({"reply": response['choices'][0]['message']['content']})
        return jsonify({"reply": "CATOVISION AI sedang sibuk. Coba lagi nanti."})

    except Exception as e:
        return jsonify({"reply": f"Error sistem: {str(e)}"})

app = app
