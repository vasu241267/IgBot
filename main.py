import os
import json
import time
import subprocess
import threading
from flask import Flask
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from moviepy.editor import VideoFileClip

app = Flask(__name__)

USERNAME = "cricko.fun"
PASSWORD = "@Vasu2412"
YOUTUBE_PLAYLIST_URL = "https://youtube.com/playlist?list=PLzlOHuvgTpSY4_88tPkqV9BKMt-J2Ivnm&si=JoeqJg4oODfAmZCX"
UPLOAD_INTERVAL = 60 * 60 * 5  # 5 hours

def convert_cookies():
    print("🔄 Converting cookie.json to cookies.txt...")
    if not os.path.exists("cookie.json"):
        print("❌ cookie.json not found")
        return
    try:
        with open("cookie.json", "r") as f:
            cookies = json.load(f)

        with open("cookies.txt", "w") as f:
            for cookie in cookies:
                if cookie.get("domain", "").startswith("."):
                    cookie["domain"] = cookie["domain"][1:]
                line = "\t".join([
                    cookie.get("domain", ""),
                    "TRUE" if cookie.get("hostOnly") == False else "FALSE",
                    cookie.get("path", "/"),
                    "TRUE" if cookie.get("secure") else "FALSE",
                    str(int(cookie.get("expirationDate", 0))),
                    cookie.get("name", ""),
                    cookie.get("value", "")
                ])
                f.write(line + "\n")
        print("✅ cookies.txt generated from cookie.json")
    except Exception as e:
        print("❌ Failed to convert cookies:", e)

def login_instagram():
    print("🔐 Logging into Instagram...")
    cl = Client()
    if os.path.exists("session.json"):
        print("📂 Found session.json, attempting to load...")
        cl.load_settings("session.json")
        try:
            cl.get_timeline_feed()
            print("✅ Session loaded and valid")
            return cl
        except Exception as e:
            print("⚠️ Session invalid, logging in fresh:", e)

    try:
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings("session.json")
        print("✅ Logged in and session saved to session.json")
    except Exception as e:
        print("❌ Login failed:", e)
    return cl

def get_uploaded_titles():
    if not os.path.exists("uploaded_titles.txt"):
        return set()
    with open("uploaded_titles.txt", "r") as f:
        return set(title.strip() for title in f.readlines())

def mark_as_uploaded(title):
    with open("uploaded_titles.txt", "a") as f:
        f.write(title + "\n")

def get_playlist_video_urls():
    print("🎞️ Fetching playlist video URLs using yt-dlp...")
    result = subprocess.run([
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--cookies", "cookies.txt",
        YOUTUBE_PLAYLIST_URL
    ], capture_output=True, text=True)

    urls = []
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            for entry in data.get("entries", []):
                video_id = entry.get("id")
                if video_id:
                    urls.append((video_id, f"https://www.youtube.com/watch?v={video_id}"))
        except Exception as e:
            print("❌ Failed to parse playlist data:", e)
    else:
        print("❌ Failed to fetch playlist videos:", result.stderr)
    print(f"📼 Found {len(urls)} videos in playlist")
    return urls

def download_first_unuploaded_video():
    convert_cookies()
    uploaded_titles = get_uploaded_titles()
    urls = get_playlist_video_urls()
    os.makedirs("downloads", exist_ok=True)

    for video_id, url in urls:
        title = f"video_{video_id}"
        if title not in uploaded_titles:
            print(f"⬇️ Downloading: {title} from {url}")
            output_path = os.path.join("downloads", f"{title}.mp4")
            try:
                subprocess.run([
                    "yt-dlp",
                    url,
                    "-o", output_path,
                    "--cookies", "cookies.txt"
                ], check=True)
                print(f"✅ Downloaded: {title}")
                return output_path, title
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to download {title}:", e)
    print("⚠️ No unuploaded videos found.")
    return None, None

def delete_last_reel(cl):
    print("🗑️ Checking for previous reels to delete...")
    try:
        reels = cl.user_clips(cl.user_id)
        if reels:
            cl.clip_delete(reels[0].pk)
            print("🗑️ Deleted previous reel")
        else:
            print("📭 No previous reels found")
    except Exception as e:
        print("❌ Failed to delete last reel:", e)

def upload_video_to_instagram(cl, video_path, caption):
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()

        print(f"🎬 Video duration: {duration} seconds")
        if duration > 90:
            print("⚠️ Video is longer than 90 seconds. Skipping.")
            return

        delete_last_reel(cl)
        cl.clip_upload(video_path, caption)
        print("🚀 Uploaded to Instagram")
    except Exception as e:
        print("❌ Upload failed:", e)

def worker():
    while True:
        print("🧠 Starting new upload cycle...")
        cl = login_instagram()
        video_path, title = download_first_unuploaded_video()
        if video_path and title:
            upload_video_to_instagram(cl, video_path, title)
            mark_as_uploaded(title)
        else:
            print("⏳ Waiting until next cycle...")
        time.sleep(UPLOAD_INTERVAL)

@app.route("/")
def index():
    return "✅ YouTube to Instagram Reel bot is running!"

if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
