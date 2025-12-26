import os
import uuid
from flask import Flask, render_template, request, send_file, abort
from PIL import Image, ImageEnhance

app = Flask(__name__)

# Konfigurasi folder
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def index():
    # Simulasi data koleksi kucing (Gunakan file yang Anda upload)
    koleksi_kucing = [
        {"id": 1, "name": "Classic Sketch", "img": "1000037411.jpg"},
        {"id": 2, "name": "Meme King", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    if 'photo' not in request.files:
        return "No photo", 400
    
    file = request.files['photo']
    uid = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, uid + "_in.jpg")
    output_path = os.path.join(UPLOAD_FOLDER, uid + "_out.jpg")
    
    file.save(input_path)
    
    # Proses "Penjernih" Sederhana (Sharpen & Contrast)
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        img.save(output_path, quality=95)
    
    return send_file(output_path, as_attachment=True, download_name="cleared_cat.jpg")

if __name__ == "__main__":
    app.run(debug=True)
