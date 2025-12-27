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
    mode = request.form.get('mode')
    
    if not url:
        return "URL wajib diisi", 400

    # Mengambil teks cookie dari settingan rahasia Vercel
    cookies_data = os.getenv("COOKIES_CONTENT")
    # Folder /tmp adalah satu-satunya tempat yang diizinkan Vercel untuk menulis file
    cookie_path = "/tmp/cookies.txt"

    if cookies_data:
        with open(cookie_path, "w") as f:
            f.write(cookies_data)
    
    ydl_opts = {
        # 'best' kadang gagal, 'bestvideo+bestaudio/best' lebih stabil
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookie_path,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
    }


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # download=False wajib agar tidak kena error Read-Only
            info = ydl.extract_info(url, download=False)
            
            # Mencari URL download yang bisa langsung diakses
            download_url = info.get('url')
            
            # Jika 'url' tidak ada di root, cari di daftar formats
            if not download_url and 'formats' in info:
                for f in info['formats']:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        download_url = f.get('url')
                        break

            if not download_url:
                return "Format video tidak ditemukan atau tidak didukung", 404
            
            # Kirim user langsung ke file videonya
            from flask import redirect
            return redirect(download_url)
            
    except Exception as e:
        return f"Gagal memproses video: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)



