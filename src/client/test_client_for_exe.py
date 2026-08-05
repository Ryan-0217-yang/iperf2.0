import sys, os


BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import version  # 改為引入同目錄下的 version.py
import requests
import zipfile
from io import BytesIO
import os
from speed_test import run_client
from config import HOST_IP

SERVER_PORT = 7999
SERVER_BASE_URL = f"http://{HOST_IP}:{SERVER_PORT}"

CLIENT_VERSION = version.version


def check_version():
    try:
        url = f"{SERVER_BASE_URL}/check_version"
        response = requests.post(url, data=str(CLIENT_VERSION), timeout=5)
        response.raise_for_status() 
        return response.text.strip()
    except requests.exceptions.RequestException as e:
        print("Connection error:", e)
        return None

def download(url, extract_to="."):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        zip_data = BytesIO(r.content)

        with zipfile.ZipFile(zip_data, "r") as zip_ref:
            zip_ref.extractall(extract_to)

        print("Download and extract completed")
        return True

    except Exception as e:
        print("Error:", e)
        return False

if __name__ == "__main__":
    result = check_version()

    if result == "Need update":
        print("Client needs to update")
        download(f"{SERVER_BASE_URL}/download")
    elif result == "OK":
        print("Client is up-to-date")
        run_client(HOST_IP, 8000, 1)
    else:
        print(f"Unknown response or error: {result}")
