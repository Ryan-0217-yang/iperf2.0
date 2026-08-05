import asyncio
import subprocess
import json
import time
from datetime import datetime
import sqlite3
import os
import config
import logging

# ==========================================
# Logging 設定區塊
# ==========================================
# 確保 logs 目錄存在
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger("iperf2_worker_logger")
logger.setLevel(logging.DEBUG)

# 將 info 日誌寫入 iperf2_worker.log
info_handler = logging.FileHandler(os.path.join(log_dir, "iperf2_worker.log"), encoding='utf-8')
info_handler.setLevel(logging.INFO)
info_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
info_handler.setFormatter(info_formatter)

# 將 error 日誌寫入 iperf2_worker_error.log
error_handler = logging.FileHandler(os.path.join(log_dir, "iperf2_worker_error.log"), encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
error_handler.setFormatter(error_formatter)

logger.addHandler(info_handler)
logger.addHandler(error_handler)

# 若想在終端機也看到輸出，可解除下方註解
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(info_formatter)
# logger.addHandler(console_handler)
# ==========================================

DB_PATH = os.path.expanduser("../../data/iperf2.db")

start_port, count = config.port_num
work_port = [start_port + i for i in range(count)]

def write_to_db(ip, upload_bps=0, download_bps=0):
    upload_kbps = int(upload_bps / 1000)
    download_kbps = int(download_bps / 1000)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Bandwidth (ipv4_addr, upload_bandwidth, download_bandwidth)
            VALUES (?, ?, ?)
        """, (ip, upload_kbps, download_kbps))
        conn.commit()
        conn.close()
        logger.info(f"寫入 DB | IP={ip} | Up={upload_kbps} Kbps | Down={download_kbps} Kbps")

    except sqlite3.Error as e:
        logger.error(f"DB 寫入失敗: {e}")


async def worker_task(port):
    while True:
        cmd = ["iperf3", "-s", "-p", str(port), "-J", "-1"]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        stdout, _ = await proc.communicate()
        output_str = stdout.decode('utf-8', errors='ignore')

        try:
            data = json.loads(output_str)
            if "error" not in data:
                client_ip = data['start']['connected'][0]['remote_host']
                upload_bps = 0
                download_bps = 0
                if 'streams' in data['end']:
                    for stream in data['end']['streams']:
                        if 'receiver' in stream:
                            upload_bps += stream['receiver'].get('bits_per_second', 0)
                        if 'sender' in stream:
                            download_bps += stream['sender'].get('bits_per_second', 0)

                write_to_db(client_ip, upload_bps, download_bps)

            else:
                logger.error(f"Port {port} 測速錯誤 : {data.get('error')}")

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Port {port} JSON 解析失敗: {e}")

        await asyncio.sleep(0.5)


async def main():
    logger.info(f"啟動 {count} 個 server，管理 Port: {work_port}")
    tasks = [worker_task(port) for port in work_port]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("server 正常關閉")
