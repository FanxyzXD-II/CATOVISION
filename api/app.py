import os
import io
import uuid
import yt_dlp
from flask import Flask, render_template, request, send_file, Response
from PIL import Image, ImageEnhance

# Vercel mencari template di root jika app.py ada di folder api/
app = Flask(__name__, template_folder='../', static_folder='../static')

@app.route("/")
def index():
    # Sesuaikan nama file img dengan yang ada di folder static/uploads Anda
    koleksi_kucing = [
        {"id": 1, "name": "Classic Sketch", "img": "1000037411.jpg"},
        {"id": 2, "name": "Meme King", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    if 'photo' not in request.files:
        return "Tidak ada foto yang diunggah", 400
    
    file = request.files['photo']
    img = Image.open(file.stream).convert("RGB")
    
    # Logika Enhancer (Sharpening & Contrast)
    img = ImageEnhance.Sharpness(img).enhance(2.5)
    img = ImageEnhance.Contrast(img).enhance(1.3)
    
    # Simpan ke memori (buffer) bukan ke disk
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="cleared_cat.jpg")

@app.route("/download", methods=["POST"])
def download_media():
    url = request.form.get('url')
    mode = request.form.get('mode') # 'video' atau 'audio'
    
    if not url:
        return "URL wajib diisi", 400

    ydl_opts = {
        'format': 'best' if mode == 'video' else 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            download_url = info['url']
            title = info.get('title', 'video')
            ext = 'mp4' if mode == 'video' else 'mp3'
            
            # Memberikan link download langsung ke user
            return Response(download_url, headers={
                "Content-Disposition": f"attachment; filename={title}.{ext}"
            })
    except Exception as e:
        return f"Gagal memproses video: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
