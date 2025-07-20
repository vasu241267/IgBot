from flask import Flask
import os
import time
import json
import logging
from instagrapi import Client
from yt_dlp import YoutubeDL

app = Flask(__name__)

# CONFIG
username = os.getenv("INSTA_USER", "your_username")
password = os.getenv("INSTA_PASS", "your_password")
playlist_url = os.getenv("YOUTUBE_PLAYLIST", "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID")
download_dir = "downloads"
cookie_json = "cookie.json"
cookie_txt = "cookies.txt"
log_file = "upload.log"
wait_seconds = 5 * 3600
caption = "Follow @yourpage for more 🔥\n.\n.\n.\n#reels #viral #trending"

os.makedirs(download_dir, exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format='[%(asctime)s] %(message)s')

# Convert JSON cookie to TXT
def convert_cookie():
    try:
        with open(cookie_json) as f:
            cookies = json.load(f)
        with open(cookie_txt, "w") as f:
            for c in cookies:
                f.write(f"{c['domain']}\tTRUE\t{c['path']}\t{str(c['secure']).upper()}\t0\t{c['name']}\t{c['value']}\n")
        logging.info("✅ cookies.txt generated from cookie.json")
    except Exception as e:
        logging.error(f"❌ Failed to convert cookie: {e}")

convert_cookie()

# Setup Instagram client
cl = Client()
cl.login(username, password)
logging.info("✅ Logged into Instagram")

# Store uploaded titles
uploaded_file = "uploaded.txt"
if not os.path.exists(uploaded_file):
    open(uploaded_file, 'w').close()

def get_uploaded_titles():
    with open(uploaded_file) as f:
        return set(line.strip() for line in f)

def mark_as_uploaded(title):
    with open(uploaded_file, "a") as f:
        f.write(title + "\n")

def download_video(video_url):
    ydl_opts = {
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
        'format': 'mp4[height<=720]',
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url)
        return info

def background_job():
    extract_opts = {'extract_flat': True, 'quiet': True, 'skip_download': True}

    while True:
        uploaded_titles = get_uploaded_titles()

        with YoutubeDL(extract_opts) as ydl:
            playlist = ydl.extract_info(playlist_url, download=False)
            videos = playlist.get('entries', [])

        for entry in videos:
            title = entry.get('title')
            video_id = entry.get('id')

            if not title or not video_id or title in uploaded_titles:
                continue

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            try:
                logging.info(f"📥 Downloading: {title}")
                info = download_video(video_url)

                video_path = os.path.join(download_dir, f"{info['title']}.{info['ext']}")

                try:
                    last_reel = cl.user_clips(cl.user_id)[0]
                    cl.clip_delete(last_reel.pk)
                    logging.info("🗑️ Previous reel deleted successfully.")
                except Exception as e:
                    logging.warning(f"⚠️ Couldn't delete previous reel: {e}")

                logging.info("🚀 Uploading to Instagram...")
                cl.clip_upload(video_path, caption=caption)
                logging.info(f"✅ Uploaded: {title}")

                mark_as_uploaded(title)
                break

            except Exception as e:
                logging.error(f"❌ Error uploading {title}: {e}")

        logging.info(f"⏳ Sleeping {wait_seconds // 3600}h...")
        time.sleep(wait_seconds)

import threading
threading.Thread(target=background_job, daemon=True).start()

@app.route("/")
def home():
    return "INSTAGRAM REEL AUTO-UPLOADER RUNNING"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
