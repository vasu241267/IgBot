# main.py (API with auto JSON to cookies.txt conversion)
import os
import yt_dlp
import logging
import json
from flask import Flask, request
from instagrapi import Client

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

# ========== Config ==========
output_folder = "downloads"
os.makedirs(output_folder, exist_ok=True)
video_path = os.path.join(output_folder, "reel.mp4")
cookies_file = "cookies.txt"
cookie_json_file = "cookie.json"  # your saved format
session_file = "insta_session.json"
caption = "Follow For Such Amazing Content 😋 #Viral #Like #Follow #Meme... This Reel Is Uploaded Via Automation"

username = os.getenv("INSTA_USERNAME", "cricko.fun")
password = os.getenv("INSTA_PASSWORD", "@Vasu2412")

cl = Client()

if os.path.exists(session_file):
    cl.load_settings(session_file)
    try:
        cl.login(username, password)
        logging.info("✅ Session restored.")
    except:
        cl.login(username, password)
        cl.dump_settings(session_file)
else:
    cl.login(username, password)
    cl.dump_settings(session_file)

# ========== Convert JSON cookies to cookies.txt ==========
def convert_json_to_cookies_txt(json_file, txt_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)

        with open(txt_file, 'w', encoding='utf-8') as f:
            for c in cookies:
                f.write(f"{c['domain']}	"
                        f"{str(not c.get('hostOnly', False)).upper()}	"
                        f"{c['path']}	"
                        f"{'TRUE' if c['secure'] else 'FALSE'}	"
                        f"{int(c['expirationDate']) if 'expirationDate' in c else 0}	"
                        f"{c['name']}	"
                        f"{c['value']}\n")
        logging.info("✅ cookies.txt generated from cookie.json")
    except Exception as e:
        logging.error(f"❌ Failed to convert cookie: {e}")

# Always run conversion at startup
if os.path.exists(cookie_json_file):
    convert_json_to_cookies_txt(cookie_json_file, cookies_file)
else:
    logging.warning("⚠️ cookie.json not found — using last cookies.txt")

# ========== Helpers ==========
def download_video(url):
    if os.path.exists(video_path):
        os.remove(video_path)
    if os.path.exists("reel.mp4.jpg"):
        os.remove("reel.mp4.jpg")

    ydl_opts = {
        'outtmpl': video_path,
        'quiet': True,
        'format': 'mp4/best',
        'noplaylist': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'headers': {
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'retries': 3,
    }

    if os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)

# ========== Routes ==========
@app.route("/")
def home():
    return "🤖 YouTube to Instagram API is Running!"

@app.route("/set-cookies", methods=["POST"])
def set_cookies():
    content = request.data.decode("utf-8")
    with open(cookie_json_file, "w", encoding="utf-8") as f:
        f.write(content)
    convert_json_to_cookies_txt(cookie_json_file, cookies_file)
    return {"status": "✅ cookie.json saved and converted"}

@app.route("/upload", methods=["POST"])
def upload():
    data = request.json
    url = data.get("url")

    if not url:
        return {"error": "Missing 'url'"}, 400

    try:
        info = download_video(url)
        cl.clip_upload(video_path, caption=caption)
        return {"status": "✅ Uploaded", "title": info.get("title")}
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        return {"error": str(e)}, 500

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
