import os
import json
import time
import subprocess
import threading
import shutil
import gc
import psutil
from flask import Flask, Response
from instagrapi import Client
from moviepy.editor import VideoFileClip

app = Flask(__name__)
FIXED_CAPTION_SUFFIX = "\n\n✨🤏 This Reel Uploaded By Automation If You Wanna Do Something Like This Then Dm Me 💫#shorts #reels #cricko #foryou #bikelover"

USERNAME = "cricko.fun"
PASSWORD = "@Vasu2412"
YOUTUBE_PLAYLIST_URL = "https://youtube.com/playlist?list=PLzlOHuvgTpSY4_88tPkqV9BKMt-J2Ivnm&si=JoeqJg4oODfAmZCX"
UPLOAD_INTERVAL = 60 * 3  # Every 5 minutes

def login_instagram():
    print("🔐 Logging into Instagram...")
    cl = Client()
    if os.path.exists("session.json"):
        try:
            cl.load_settings("session.json")
            cl.get_timeline_feed()
            print("✅ Session loaded from session.json")
            return cl
        except Exception as e:
            print("⚠️ Session invalid, logging in fresh:", e)
    cl.login(USERNAME, PASSWORD)
    cl.dump_settings("session.json")
    print("✅ Logged in and session saved to session.json")
    return cl

def get_uploaded_titles():
    if not os.path.exists("uploaded_titles.txt"):
        return set()
    with open("uploaded_titles.txt", "r") as f:
        return set(title.strip() for title in f.readlines())

def mark_as_uploaded(title):
    with open("uploaded_titles.txt", "a") as f:
        f.write(title + "\n")

def download_first_unuploaded_video():
    if not os.path.exists("cookies.txt"):
        print("❌ cookies.txt not found")
        return None, None

    uploaded_titles = get_uploaded_titles()
    print("🎞️ Fetching playlist video URLs using yt-dlp...")

    try:
        result = subprocess.run([
            "yt-dlp",
            "--flat-playlist",
            "--cookies", "cookies.txt",
            "--print", "%(title)s|||%(id)s",
            YOUTUBE_PLAYLIST_URL
        ], capture_output=True, text=True, check=True)

        entries = result.stdout.strip().split("\n")
        print(f"📼 Found {len(entries)} videos in playlist")

        for entry in entries:
            try:
                title, video_id = entry.split("|||")
            except:
                print("⚠️ Failed to parse:", entry)
                continue

            if title in uploaded_titles:
                continue

            output_path = os.path.join("downloads", f"{video_id}.mp4")
            os.makedirs("downloads", exist_ok=True)

            try:
                print(f"⬇️ Downloading: {title}")
                subprocess.run([
                    "yt-dlp",
                    f"https://www.youtube.com/watch?v={video_id}",
                    "-o", output_path,
                    "--cookies", "cookies.txt"
                ], check=True)
                print(f"✅ Downloaded: {title}")
                return output_path, title
            except subprocess.CalledProcessError as e:
                print(f"❌ Download failed: {e}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to fetch playlist videos: {e.stderr}")
    return None, None

def clean_download_folder():
    print("🧹 Full cleanup: deleting everything in downloads folder...")
    folder = "downloads"
    try:
        shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
        print("✅ Downloads folder cleaned.")
    except Exception as e:
        print(f"❌ Failed to clean downloads folder: {e}")

def upload_video_to_instagram(cl, video_path, caption):
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        del clip
        gc.collect()

        if duration > 90:
            print("⚠️ Video is longer than 90 seconds. Skipping.")
            return

        # Ensure login is valid
        try:
            cl.get_timeline_feed()
        except:
            print("⚠️ Session expired. Logging in again...")
            cl.login(USERNAME, PASSWORD)
            cl.dump_settings("session.json")

        # 🔳 Use fixed thumbnail
        thumbnail_path = "fix-thumbnail.jpg"
        if not os.path.exists(thumbnail_path):
            print(f"❌ Thumbnail file '{thumbnail_path}' not found.")
            return

        print("📤 Uploading to Instagram with fixed thumbnail...")
        cl.clip_upload(video_path, caption + FIXED_CAPTION_SUFFIX, thumbnail=thumbnail_path)
        print("🚀 Uploaded successfully")

        if os.path.exists(video_path):
            os.remove(video_path)
        clean_download_folder()

    except Exception as e:
        print("❌ Upload failed:", e)



def worker():
    print("🕒 Delaying worker for 3 minutes to let Flask health pass...")
    time.sleep(180)

    while True:
        print("\n🧠 Starting new upload cycle...")
        cl = login_instagram()
        video_path, title = download_first_unuploaded_video()
        if video_path and title:
            upload_video_to_instagram(cl, video_path, title)
            mark_as_uploaded(title)
        else:
            print("⚠️ No new video to upload.")

        print(f"🧠 RAM usage: {psutil.virtual_memory().percent}%")
        del cl
        gc.collect()
        print("⏳ Waiting until next cycle...\n")
        time.sleep(UPLOAD_INTERVAL)

@app.route("/")
def index():
    print("✅ Health check received")
    return Response("✅ YouTube to Instagram Reel bot is running!", status=200, mimetype="text/plain")

if __name__ == "__main__":
    print("⏳ Waiting 7 sec for Koyeb health check to pass...")
    time.sleep(7)
    threading.Thread(target=worker, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
