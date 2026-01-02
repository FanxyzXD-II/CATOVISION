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
        return jsonify({"error": "No file"}), 400
    try:
        file = request.files['photo']
        img = Image.open(file.stream).convert("RGB")
        original_size = img.size 
        
        # Kompresi memori agar stabil di Edge Function
        if max(original_size) > 1000:
            img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
        
        width, height = img.size
        roi_top = int(height * 0.75)
        bottom_area = img.crop((0, roi_top, width, height))
        
        mask = bottom_area.convert("L").point(lambda x: 255 if x > 230 else 0, mode='1')
        mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(radius=3))
        patch = bottom_area.filter(ImageFilter.ModeFilter(size=9)).filter(ImageFilter.GaussianBlur(radius=10))
        
        clean_bottom = Image.composite(patch, bottom_area, mask)
        img.paste(clean_bottom, (0, roi_top))
        
        # Restorasi ke ukuran asli
        if img.size != original_size:
            img = img.resize(original_size, Image.Resampling.LANCZOS)

        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=95, subsampling=0)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
