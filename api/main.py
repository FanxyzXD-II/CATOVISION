import os
import io
import yt_dlp
ydl_opts = {
    'format': 'best',
    'cookiefile': 'cookies.txt'
    'cookiefile': str(cookie_path), 
    'quiet': True,
    'no_warnings': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # Jika masih error, Anda harus menambahkan file cookies.txt
    # 'cookiefile': 'cookies.txt' 
}
from flask import Flask, render_template, request, send_file, Response
from PIL import Image, ImageEnhance

# Inisialisasi: '../' digunakan untuk keluar dari folder api/ mencari templates & static
app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route("/")
def index():
    # Data gallery kucing (Pastikan file gambar ada di /static/uploads/)
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
    
    # Logika Enhancer (Sharpen & Contrast)
    img = ImageEnhance.Sharpness(img).enhance(2.5)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    
    # Simpan ke memori (RAM) agar kompatibel dengan Vercel yang Read-Only
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
            
            # Memberikan link download langsung (Stream)
            return Response(download_url, headers={
                "Content-Disposition": f"attachment; filename={title}.{ext}"
            })
    except Exception as e:
        return f"Gagal memproses video: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)




