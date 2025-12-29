import os
import io
import requests
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance

# Inisialisasi Flask dengan penyesuaian folder untuk struktur Vercel
app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

# Konfigurasi API Key
# Disarankan mengisi via Environment Variables di Dashboard Vercel dengan nama 'GROQ_API_KEY'
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "MASUKKAN_KEY_GROQ_ANDA_DI_SINI")

@app.route("/")
def index():
    """Menampilkan halaman utama dengan data galeri asli."""
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
        {"id": 3, "name": "Caton Profile", "img": "100003748.jpg"}
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    """Fitur pengolah gambar: Meningkatkan ketajaman dan kontras."""
    if 'photo' not in request.files:
        return "File tidak ditemukan", 400
    
    try:
        file = request.files['photo']
        img = Image.open(file.stream).convert("RGB")
        
        # Proses Enhancing (Sharpness & Contrast)
        img = ImageEnhance.Sharpness(img).enhance(2.5)
        img = ImageEnhance.Contrast(img).enhance(1.4)
        
        # Simpan ke memori (bukan disk) agar kompatibel dengan Vercel
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="CATO_HD.jpg")
    except Exception as e:
        return f"Error processing image: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    """Fitur AI Analyst Pro dengan integrasi data pasar real-time."""
    user_query = request.form.get('query')
    lang = request.form.get('lang', 'id') # Default ke Indonesia jika tidak ada
    
    if not user_query:
        return jsonify({"reply": "Silakan masukkan pertanyaan atau nama koin."})

    try:
        # 1. Mengambil Data Harga dari CoinGecko (Public API)
        market_context = ""
        search_res = requests.get(f"https://api.coingecko.com/api/v3/search?query={user_query}").json()
        
        if search_res.get('coins'):
            coin_id = search_res['coins'][0]['id']
            price_res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true").json()
            
            if coin_id in price_res:
                data = price_res[coin_id]
                market_context = f"Data Pasar {coin_id}: Harga ${data['usd']}, Perubahan 24j: {round(data.get('usd_24h_change', 0), 2)}%."

        # 2. Permintaan ke AI Groq (Llama 3 70B)
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Menyesuaikan instruksi bahasa berdasarkan input 'lang' dari HTML
        system_instruction = f"You are CATOVISION AI, a pro crypto analyst. Focus on Market Structure and SMC. Answer strictly in {lang} language. End with: Trade with care, NFA."
        
        payload = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Query: {user_query}. Context: {market_context}"}
            ],
            "temperature": 0.5
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload).json()
        
        if 'choices' in response:
            return jsonify({"reply": response['choices'][0]['message']['content']})
        else:
            return jsonify({"reply": "CATOVISION AI sedang memantau grafik lain. Coba lagi nanti."})

    except Exception as e:
        return jsonify({"reply": f"Terjadi gangguan sistem: {str(e)}"})

# Diperlukan oleh Vercel Serverless
app = app
