import os
import io
import yt_dlp
from pathlib import Path
from flask import Flask, render_template, request, send_file, Response, redirect

# Inisialisasi: Sesuaikan folder jika main.py berada di dalam subfolder (seperti api/)
# Jika main.py di root, cukup gunakan app = Flask(__name__)
app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route("/")
def index():
    koleksi_kucing = [
        {"id": 1, "name": "green cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "turquoise cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

@app.route("/enhance", methods=["POST"])
def enhance_photo():
    if 'photo' not in request.files:
        return "Tidak ada foto", 400
    
    file = request.files['photo']
    img = Image.open(file.stream).convert("RGB")
    
    img = ImageEnhance.Sharpness(img).enhance(2.5)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="CATO_HD.jpg")

@app.route("/download", methods=["POST"])
def download_media():
    url = request.form.get('url')
    mode = request.form.get('mode') # 'video' atau 'audio'
    
    if not url:
        return "URL wajib diisi", 400

    # FIX: Path absolut yang dinamis untuk Vercel
    base_path = Path(__file__).parent.resolve()
    cookie_path = str(base_path / "cookies.txt")

    ydl_opts = {
        'format': 'best' if mode == 'video' else 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookie_path,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'nocheckcertificate': True, # Tambahan agar tidak error SSL di server
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # download=False sangat penting untuk Vercel (Read-Only)
            info = ydl.extract_info(url, download=False)
            
            # Ambil URL direct stream dari YouTube/Provider
            download_url = info.get('url') or info.get('formats')[0].get('url')
            
            if not download_url:
                return "Gagal mendapatkan URL stream", 500

            # FIX: Gunakan redirect agar browser langsung mengunduh dari sumbernya
            return redirect(download_url)
            
    except Exception as e:
        return f"Gagal memproses video: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
