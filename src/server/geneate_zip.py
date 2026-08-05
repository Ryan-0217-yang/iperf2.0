import zipfile
import os
import version  # 引入同目錄下的 version.py
import urllib.request
import urllib.error

def build_update_zip():
    zip_filename = f"{version.version}.zip"
    files_to_pack = version.need_package_files

    print(f"[*] 準備建立壓縮檔: {zip_filename}")

    # 建立 zip 檔案
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_pack:
            # 檢查檔案是否存在，避免程式報錯中斷
            if os.path.exists(file):
                zipf.write(file)
                print(f"  [+] 成功加入檔案: {file}")
            else:
                print(f"  [!] 警告: 找不到檔案 {file}，已跳過！")

    print(f"[*] 打包完成！已產生: {zip_filename}")


    print("[*] 正在通知 Flask 伺服器進行版本熱更新...")
    try:
        req = urllib.request.Request("http://127.0.0.1:7999/reload_version", method="POST")
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print(f"  [+] 伺服器回應: {result}")
    except urllib.error.URLError as e:
        print(f"  [!] 無法連線到 Flask 伺服器 (伺服器可能未啟動): {e}")

if __name__ == "__main__":
    build_update_zip()
