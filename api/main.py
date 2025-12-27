import os
import io
import yt_dlp
from flask import Flask, render_template, request, jsonify, send_file, redirect
from PIL import Image, ImageEnhance

# Inisialisasi Flask: Pastikan path template & static sesuai struktur folder Anda
app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route("/")
def index():
    # Data gallery tetap dipertahankan sesuai tampilan asli
    koleksi_kucing = [
        {"id": 1, "name": "green cat", "img": "1000037411.jpg"},
        {"id": 2, "name": "turquoise cat", "img": "1000037421.jpg"},
    ]
    return render_template("index.html", cats=koleksi_kucing)

# --- FITUR PHOTO ENHANCER (Tampilan Screenshot 1000050114.jpg) ---
@app.route("/enhance", methods=["POST"])
def enhance_photo():
    if 'photo' not in request.files:
        return "Tidak ada foto", 400
    
    file = request.files['photo']
    img = Image.open(file.stream).convert("RGB")
    
    # Logika Enhancer asli Anda
    img = ImageEnhance.Sharpness(img).enhance(2.5)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name="CATO_HD.jpg")

# --- FITUR DOWNLOADER (Fix Format Error 1000050260.jpg) ---
@app.route("/get-info", methods=["POST"])
def get_info():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL wajib diisi"}), 400

    # Mengambil cookie dari Environment Variable (Aman & mendukung Vercel)
    cookies_content = os.getenv("COOKIES_CONTENT")
    cookie_path = "/tmp/cookies.txt"
    if cookies_content:
        with open(cookie_path, "w") as f:
            f.write(cookies_content)

    ydl_opts = {
        'cookiefile': cookie_path if cookies_content else None,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Ekstrak info tanpa download untuk mendapatkan daftar format tersedia
            info = ydl.extract_info(url, download=False)
            formats_list = []
            
            for f in info.get('formats', []):
                # Filter format yang memiliki video dan audio (siap download langsung)
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    res = f.get('height')
                    ext = f.get('ext')
                    filesize = f.get('filesize')
                    size_text = f"{round(filesize / (1024*1024), 1)} MB" if filesize else "Unknown Size"
                    
                    formats_list.append({
                        'resolution': f"{res}p" if res else "N/A",
                        'ext': ext,
                        'size': size_text,
                        'url': f.get('url')
                    })
            
            # Ambil satu stream audio saja untuk opsi MP3
            audio_url = None
            for f in reversed(info.get('formats', [])):
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    audio_url = f.get('url')
                    break

            # Urutkan resolusi dari tinggi ke rendah
            formats_list.sort(key=lambda x: int(x['resolution'].replace('p','')) if 'p' in x['resolution'] else 0, reverse=True)

            return jsonify({
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats_list[:6], 
                "audio_url": audio_url
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
