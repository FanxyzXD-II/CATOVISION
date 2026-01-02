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

# --- 1. LOGIKA AI ENHANCER (Route: /enhance) ---
@app.route("/enhance", methods=["POST"])
def enhance_photo():
    if 'photo' not in request.files:
        return "File tidak ditemukan", 400
    try:
        file = request.files['photo']
        img = Image.open(file.stream).convert("RGB")

        # Tahap 1: Anti-Noise & Smoothing
        img = img.filter(ImageFilter.SMOOTH_MORE)
        
        # Tahap 2: Ultra Sharpening (Efek HD)
        # Menggunakan UnsharpMask untuk detail mikro yang tajam
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=350, threshold=1))
        
        # Tahap 3: Final Enhancement
        img = ImageEnhance.Contrast(img).enhance(1.25)
        img = ImageEnhance.Color(img).enhance(1.15)
        img = ImageEnhance.Sharpness(img).enhance(2.0)

        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=100, subsampling=0)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        return f"Error: {str(e)}", 500


# --- 3. AI ANALYST (IDENTITAS CATOVISION AI) ---
@app.route("/chat", methods=["POST"])
def chat():
    user_query = request.form.get('query', '')
    lang = request.form.get('lang', 'id')
    image_file = request.files.get('image')
    
    if not GROQ_API_KEY:
        return jsonify({"reply": "Sistem CATOVISION AI sedang dalam pemeliharaan."})
    
    # Instruksi Sistem untuk Menghapus Jejak Model Pihak Ketiga
    system_instruction = (
        f"Anda adalah CATOVISION AI, asisten cerdas yang dikembangkan sepenuhnya oleh tim teknis CATOVISION. "
        f"Berikan jawaban dalam bahasa {lang}. "
        "\n\nATURAN MUTLAK:"
        "\n1. Dilarang menyebutkan nama model AI lain seperti Llama, Meta, Groq, atau OpenAI."
        "\n2. Identitas Anda hanya satu: CATOVISION AI."
        "\n3. Jawablah semua pertanyaan (umum, teknis, atau harian) dengan gaya profesional, membantu, dan cerdas."
        "\n4. Jika ditanya mengenai asal-usul, jawablah bahwa Anda adalah produk kecerdasan buatan dari ekosistem CATOVISION."
    )

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
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct", 
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": content_list}
                ],
                "temperature": 0.4 # Menjaga agar tetap patuh pada identitas sistem
            },
            timeout=25
        )
        return jsonify({"reply": response.json()['choices'][0]['message']['content']})
    except:
        return jsonify({"reply": "CATOVISION AI sedang melakukan sinkronisasi data."})

app = app


