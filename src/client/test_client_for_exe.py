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



def cleanup_old_exe():

    if getattr(sys, 'frozen', False):  
        old_backup = sys.executable + ".old"
        if os.path.exists(old_backup):
            try:
                os.remove(old_backup)
                print("已清除上次更新殘留的備份檔")
            except OSError as e:
                print("清除備份檔失敗（可忽略）：", e)



def download(url, extract_to="."):
    old_exe = None
    backup_exe = None

    if getattr(sys, 'frozen', False): 
        old_exe = sys.executable
        backup_exe = old_exe + ".old"


        if os.path.exists(backup_exe):
            try:
                os.remove(backup_exe)
            except OSError:
                pass 

        try:
            os.rename(old_exe, backup_exe)
            print(f"已將現有 exe 改名為 {backup_exe}，準備解壓新版本")
        except OSError as e:
            print("rename 舊 exe 失敗：", e)
            return False


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


        if old_exe and backup_exe and os.path.exists(backup_exe):
            try:
                os.rename(backup_exe, old_exe)
                print("解壓失敗，已還原舊版本 exe")
            except OSError as restore_err:
                print("還原舊版本 exe 失敗：", restore_err)


        return False


if __name__ == "__main__":
    cleanup_old_exe() 

    result = check_version()

    if result == "Need update":
        print("Client needs to update")
        download(f"{SERVER_BASE_URL}/download", extract_to=BASE_DIR)
    elif result == "OK":
        print(f"Client is up-to-date. this version is {CLIENT_VERSION}")
        run_client(HOST_IP, 8000, 1)
    else:
        print(f"Unknown response or error: {result}")
