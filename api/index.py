import os
import io
import base64
import requests
import cv2
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

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    if 'photo' not in request.files:
        return "File tidak ditemukan", 400
    try:
        file = request.files['photo']
        img = Image.open(file.stream).convert("RGB")
        for _ in range(2):
            img = img.filter(ImageFilter.SMOOTH_MORE)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=400, threshold=1))
        img = img.filter(ImageFilter.DETAIL)
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Sharpness(img).enhance(2.5)
        img = ImageEnhance.Color(img).enhance(1.1)
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=100, subsampling=0)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')
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



