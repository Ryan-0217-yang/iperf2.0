from flask import Flask, send_file, request
import os
import logging
from logging import FileHandler, Formatter
import version
import importlib  # 新增這個標準函式庫

app = Flask(__name__)

# ==========================================
# Logging 設定區塊 (保持不變)
# ==========================================
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
os.makedirs(log_dir, exist_ok=True)

info_log_path = os.path.join(log_dir, 'iperf2_flask.log')
error_log_path = os.path.join(log_dir, 'iperf2_flask_error.log')

formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')

info_handler = FileHandler(info_log_path, encoding='utf-8')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)

error_handler = FileHandler(error_log_path, encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

app.logger.handlers.clear()
app.logger.setLevel(logging.INFO)
app.logger.addHandler(info_handler)
app.logger.addHandler(error_handler)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addHandler(info_handler)
werkzeug_logger.addHandler(error_handler)
# ==========================================

# 初始讀取
latest_version = version.version
update_ips = None
UPDATE_FILE = f"{latest_version}.zip"

def parse_version(v_str):
    return tuple(map(int, v_str.strip().split('.')))

# ==========================================
# 新增：熱更新 API (只允許本機觸發)
# ==========================================
@app.route("/reload_version", methods=["POST"])
def reload_version():
    # 安全檢查：只允許伺服器自己 (本機) 呼叫這個 API
    if request.remote_addr != '127.0.0.1':
        app.logger.warning(f"阻擋了來自 {request.remote_addr} 的熱更新請求")
        return "Forbidden", 403

    global latest_version, UPDATE_FILE

    try:
        # 重新載入 version.py 的內容
        importlib.reload(version)

        # 更新全域變數
        latest_version = version.version
        UPDATE_FILE = f"{latest_version}.zip"

        app.logger.info(f"版本已成功熱更新至: {latest_version}")
        return f"Success! Reloaded to version {latest_version}", 200
    except Exception as e:
        app.logger.error(f"熱更新失敗: {e}")
        return "Internal Server Error", 500

# ==========================================
# 原本的 API
# ==========================================
@app.route("/check_version", methods=["POST"])
def check_version():
    ip = request.remote_addr
    app.logger.info(f"Connection from {ip}")

    try:
        data = request.get_data(as_text=True).strip()
        if not data:
            return "No data received", 400

        client_version = data
        need_check = (update_ips is None) or (ip in update_ips)

        # 這裡會使用到熱更新後最新的 latest_version
        if need_check and parse_version(client_version) < parse_version(latest_version):
            response_text = "Need update"
        else:
            response_text = "OK"

        return response_text

    except ValueError:
        return "Invalid version format", 400
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return "Server Error", 500

@app.route("/download", methods=["GET"])
def download():
    # 這裡會使用到熱更新後最新的 UPDATE_FILE
    if not os.path.exists(UPDATE_FILE):
        app.logger.error(f"找不到更新檔: {UPDATE_FILE}")
        return f"File {UPDATE_FILE} not found", 404

    return send_file(UPDATE_FILE, as_attachment=True, download_name="update.zip")


if __name__ == "__main__":
    app.logger.info("啟動 Flask 更新伺服器")
    app.run(host="0.0.0.0", port=7999)
