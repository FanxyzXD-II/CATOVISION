import os
import io
import base64
import requests
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageChops

# [span_0](start_span)Konfigurasi path untuk EdgeOne: templates dan static berada di luar folder api/[span_0](end_span)
app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/")
def index():
    koleksi_kucing = [
        {"id": 1, "name": "Green Cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "Turquoise Cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/remove-watermark", methods=["POST"])
def remove_watermark():
    if 'photo' not in request.files:
        return "File tidak ditemukan", 400
        
    # Ambil API Token dari Environment Variable Vercel
    # Daftar di PixelBin untuk mendapatkan Cloud Name dan API Token
    PIXELBIN_TOKEN = os.environ.get("PIXELBIN_TOKEN")
    CLOUD_NAME = "Rian" # Ganti dengan Cloud Name Anda

    try:
        file = request.files['photo']
        img_bytes = file.read()

        # URL Endpoint PixelBin untuk Plugin Erase (Object Removal)
        # Format: https://api.pixelbin.io/v1/upload/direct
        url = "https://api.pixelbin.io/v1/upload/direct"
        
        # Parameter untuk menghapus objek secara otomatis (af_remove)
        # Sesuai dokumentasi PixelBin isolateFlow=true
        params = {
            "plugin": "af_remove",
            "isolateFlow": "true"
        }

        headers = {
            "Authorization": f"Bearer {PIXELBIN_TOKEN}"
        }

        files = {
            "file": (file.filename, img_bytes, file.content_type)
        }

        response = requests.post(url, headers=headers, files=files, params=params, timeout=40)

        if response.status_code == 200:
            # PixelBin biasanya mengembalikan URL gambar yang sudah diproses
            data = response.json()
            processed_url = data.get("url")
            
            # Ambil konten gambar dari URL hasil proses
            img_res = requests.get(processed_url)
            
            return send_file(
                io.BytesIO(img_res.content),
                mimetype='image/jpeg'
            )
        else:
            return f"PixelBin Error: {response.text}", 500

    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route("/remove-watermark", methods=["POST"])
def remove_watermark():
    if 'photo' not in request.files:
        return "File tidak ditemukan", 400
    try:
        file = request.files['photo']
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        # 1. Buat Mask (mendeteksi area putih/terang seperti coretan di foto Anda)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

        # 2. Inpaint (Menambal area mask)
        # cv2.INPAINT_TELEA atau cv2.INPAINT_NS
        dst = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

        # Simpan kembali
        _, buffer = cv2.imencode('.jpg', dst, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_io = io.BytesIO(buffer)
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/chat", methods=["POST"])
def chat():
    user_query = request.form.get('query', '')
    lang = request.form.get('lang', 'id')
    image_file = request.files.get('image')
    if not GROQ_API_KEY:
        return jsonify({"reply": "API Key Groq tidak ditemukan."})
    
    content_list = [{"type": "text", "text": user_query}]
    if image_file:
        img = Image.open(image_file).convert("RGB")
        img.thumbnail((1024, 1024))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=80)
        image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}})

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, 
            json={"model": "meta-llama/llama-4-scout-17b-16e-instruct", "messages": [{"role": "user", "content": content_list}]}
        )
        return jsonify({"reply": response.json()['choices'][0]['message']['content']})
    except:
        return jsonify({"reply": "Koneksi AI timeout."})

# WAJIB UNTUK TENCENT CLOUD EDGEONE: WSGI Entry Point
# WAJIB: Ekspos objek app untuk Vercel
app = app






