# app.py
import yt_dlp
import time
import os
import logging
from instagrapi import Client
from flask import Flask
import threading

# ========== Configuration ==========
playlist_url = "https://youtube.com/playlist?list=PLzlOHuvgTpSY4_88tPkqV9BKMt-J2Ivnm&si=zXefeH20MrI7dN6f"
wait_seconds = 5 * 60 * 60
output_folder = "downloads"
video_path = os.path.join(output_folder, "reel.mp4")
uploaded_file = "uploaded_titles.txt"
session_file = "insta_session.json"
caption = "Follow For Such Amazing Content 😋 #Viral #Like #Follow #Meme... This Reel Is Uploaded Via Automation If You Wanna Learn Then Dm Me Asap"

# ========== Setup ==========
app = Flask(__name__)
os.makedirs(output_folder, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')

username = "cricko.fun"
password = "@Vasu2412"


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

def get_uploaded_titles():
    if not os.path.exists(uploaded_file):
        return set()
    with open(uploaded_file, "r", encoding='utf-8') as f:
        return set(line.strip() for line in f)

def mark_as_uploaded(title):
    with open(uploaded_file, "a", encoding='utf-8') as f:
        f.write(title + "\n")

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
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)

def background_job():
    extract_opts = {'extract_flat': True, 'quiet': True, 'skip_download': True}

    while True:
        uploaded_titles = get_uploaded_titles()

        with yt_dlp.YoutubeDL(extract_opts) as ydl:
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

                logging.info("🚀 Uploading to Instagram...")
                cl.clip_upload(video_path, caption=caption)
                logging.info(f"✅ Uploaded: {title}")

                mark_as_uploaded(title)
                break  # only upload 1 at a time, then wait

            except Exception as e:
                logging.error(f"❌ Error uploading {title}: {e}")

        logging.info(f"⏳ Sleeping {wait_seconds // 3600}h...")
        time.sleep(wait_seconds)

@app.route("/")
def home():
    return "🤖 Instagram Auto Upload Bot Running!"

if __name__ == "__main__":
    threading.Thread(target=background_job, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)