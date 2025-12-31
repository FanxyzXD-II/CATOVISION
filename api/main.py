import os
import io
import base64
import requests
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance, ImageFilter  # Ditambahkan ImageFilter

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
    if 'photo' not in request.files:
        return "File tidak ditemukan", 400
    try:
        file = request.files['photo']
        img = Image.open(file.stream).convert("RGB")
        
        # --- TAHAP 1: ANTI-NOISE & PENGHALUSAN (SMOOTHING) ---
        # Menghilangkan bintik-bintik (noise) agar kulit terlihat mulus
        for _ in range(2):
            img = img.filter(ImageFilter.SMOOTH_MORE)
        
        # --- TAHAP 2: PENAJAMAN ULTRA (SHARPENING) ---
        # Mengembalikan detail pada mata, rambut, dan tepi objek agar tajam
        # Radius 2 dengan Percent 300-400 memberikan efek HD yang kuat
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=400, threshold=1))
        
        # --- TAHAP 3: DETAIL ENHANCEMENT ---
        img = img.filter(ImageFilter.DETAIL)
        
        # --- TAHAP 4: PENYESUAIAN WARNA & KONTRAS ---
        # Menaikkan kontras agar gambar tidak kusam/pucat
        img = ImageEnhance.Contrast(img).enhance(1.3)
        # Menaikkan ketajaman piksel akhir
        img = ImageEnhance.Sharpness(img).enhance(2.5)
        # Sedikit menaikkan saturasi agar warna lebih hidup
        img = ImageEnhance.Color(img).enhance(1.1)
        
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=100, subsampling=0)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg', as_attachment=False)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    """Fitur AI Analyst Profesional menggunakan Llama 4"""
    user_query = request.form.get('query', '')
    lang = request.form.get('lang', 'id')
    image_file = request.files.get('image')
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key Groq tidak ditemukan."})

    # --- KONFIGURASI MODEL TUNGGAL LLAMA 4 ---
    SELECTED_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

    # --- Market Context (CoinGecko) ---
    market_context = ""
    if user_query and not image_file:
        try:
            search_res = requests.get(f"https://api.coingecko.com/api/v3/search?query={user_query}", timeout=3).json()
            if search_res.get('coins'):
                coin_id = search_res['coins'][0]['id']
                p_res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true", timeout=3).json()
                if coin_id in p_res:
                    data = p_res[coin_id]
                    market_context = f"[Live Market Data: {coin_id.upper()} Price: ${data['usd']} | 24h Change: {round(data.get('usd_24h_change', 0), 2)}%]"
        except:
            pass

    # --- Penanganan Konten Multimodal ---
    content_list = []
    
    # Gabungkan teks input dengan data pasar
    full_text_input = f"{market_context}\nUser Question: {user_query if user_query else 'Provide a professional analysis of the provided data/image.'}"
    content_list.append({"type": "text", "text": full_text_input})

    # Proses Gambar jika dilampirkan
    if image_file:
        try:
            img = Image.open(image_file).convert("RGB")
            # Resize untuk efisiensi API namun tetap tajam
            img.thumbnail((1024, 1024)) 
            
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=80) 
            image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

            content_list.append({
                "type": "image_url", 
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
            })
        except Exception as e:
            return jsonify({"reply": f"Gagal memproses gambar: {str(e)}"})
    # --- OPTIMASI SYSTEM PROMPT: 100% CATOVISION AI BRANDING ---
    system_instruction = (
        f"Anda adalah CATOVISION AI, asisten analis keuangan tingkat lanjut yang dikembangkan secara eksklusif oleh tim CATOVISION. "
        f"Gunakan bahasa {lang} dalam memberikan jawaban. "
        "\n\nATURAN IDENTITAS:"
        "\n1. Dilarang keras menyebutkan Llama, Meta, Groq, atau model AI pihak ketiga lainnya."
        "\n2. Jika ditanya tentang identitas Anda, jawablah bahwa Anda adalah 'CATOVISION AI', kecerdasan buatan murni buatan CATOVISION."
        "\n\nATURAN ANALISIS:"
        "\n1. EXECUTIVE SUMMARY: Berikan inti dari analisis di bagian awal."
        "\n2. TABEL DATA: Gunakan tabel Markdown untuk merangkum angka, level harga, atau metrik teknis."
        "\n3. ANALISIS DETAIL: Gunakan terminologi finansial profesional (support, resistance, volume, volatilitas)."
        "\n4. PENILAIAN RISIKO: Selalu sertakan potensi risiko atau peringatan pasar."
        "\n5. ANALISIS VISUAL: Jika ada gambar chart, identifikasi pola teknikal secara spesifik."
            )

    try:
        payload = {
            "model": SELECTED_MODEL,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": content_list}
            ],
            "temperature": 0.4, # Rendah agar lebih presisi dan tidak berhalusinasi
            "max_tokens": 2048
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}, 
            json=payload, 
            timeout=15 
        )
        
        if response.status_code == 200:
            return jsonify({"reply": response.json()['choices'][0]['message']['content']})
        
        return jsonify({"reply": f"Groq Error ({response.status_code}): Model Llama 4 tidak merespon."})
    
    except Exception as e:
        return jsonify({"reply": "Koneksi timeout. Pastikan file tidak terlalu besar dan API Key benar."})

@app.route("/remove-watermark", methods=["POST"])
def remove_watermark():
    if 'photo' not in request.files:
        return "File tidak ditemukan", 400
    try:
        file = request.files['photo']
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        h, w, _ = img.shape
        
        # --- TAHAP 1: DETEKSI OTOMATIS BERBASIS AREA ---
        # Watermark biasanya ada di pojok bawah atau tengah bawah
        # Kita buat mask kosong
        mask = np.zeros((h, w), np.uint8)
        
        # Konversi ke Grayscale untuk analisis intensitas
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # --- TAHAP 2: DETEKSI LOGO TERANG (Seperti Gemini/AI) ---
        # Menggunakan Adaptive Thresholding untuk memisahkan teks/logo dari background
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 11, 2)
        
        # Fokuskan deteksi pada area yang sering ditempati watermark (30% area bawah)
        roi_start_row = int(h * 0.7)
        mask_roi = thresh[roi_start_row:h, :]
        
        # Bersihkan noise kecil (titik-titik halus) agar tidak merusak gambar utama
        kernel = np.ones((3,3), np.uint8)
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_OPEN, kernel)
        
        # Gabungkan kembali ke mask utama
        mask[roi_start_row:h, :] = mask_roi

        # --- TAHAP 3: INPAINTING ---
        # Menghapus objek berdasarkan mask yang terdeteksi secara otomatis
        # Radius 5 memberikan hasil yang lebih lembut untuk logo transparan
        result = cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)
        
        # Optimasi Akhir: Sedikit penghalusan pada area yang dihapus
        result = cv2.bilateralFilter(result, 9, 75, 75)
        
        _, buffer = cv2.imencode('.jpg', result, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        img_io = io.BytesIO(buffer)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        return f"Error: {str(e)}", 500
                
# Export app
app = app







