# config_manager.py
import os
import json

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "yt-audio-downloader")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)

def save_config(download_path):
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump({"download_path": download_path}, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("download_path", "")
        except Exception:
            return ""
    return ""
