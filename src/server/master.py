import socket
import threading
import heapq
import time
import config
import logging
import os

host = ''
PORT = 8000

log_dir = "../../logs"

logger = logging.getLogger("iperf2_logger")
logger.setLevel(logging.DEBUG)

# 將 info 日誌寫入 iperf2_master.log
info_handler = logging.FileHandler(os.path.join(log_dir, "iperf2_master.log"), encoding='utf-8')
info_handler.setLevel(logging.INFO)
info_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
info_handler.setFormatter(info_formatter)

# 將 error 日誌寫入 iperf2_master_error.log
error_handler = logging.FileHandler(os.path.join(log_dir, "iperf2_master_error.log"), encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
error_handler.setFormatter(error_formatter)

logger.addHandler(info_handler)
logger.addHandler(error_handler)

# 如果想在終端機也看到輸出，可以加上這個
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(info_formatter)
# logger.addHandler(console_handler)

start_port, count = config.port_num
work_port = [start_port + i for i in range(count)]

client_queue = []
queue_lock = threading.Lock()
port_status = {port: False for port in work_port}

def accept_clients():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, PORT))
    server.listen(70)
    logger.info(f"啟動 listen，管理 Port: {work_port}")

    counter = 0
    while True:
        client_sock, addr = server.accept()
        try:
            client_sock.settimeout(2.0)
            data = client_sock.recv(1024).decode().strip()
            client_sock.settimeout(None)
            priority = int(data) if data in ['0', '1'] else 1
        except Exception:
            priority = 1

        logger.info(f"Client {addr} 加入隊列")

        with queue_lock:
            heapq.heappush(client_queue, (priority, time.time(), counter, client_sock))
            counter += 1

def dispatcher():
    while True:
        free_port = None
        target_client = None

        with queue_lock:
            if client_queue:
                for port in work_port:
                    if not port_status[port]:
                        free_port = port
                        break

                if free_port:
                    _, _, _, target_client = heapq.heappop(client_queue)
                    port_status[free_port] = True

        if target_client and free_port:
            threading.Thread(
                target=handle_assignment,
                args=(target_client, free_port),
                daemon=True
            ).start()
        else:
            time.sleep(0.5)

def handle_assignment(client_sock, port):
    try:
        logger.info(f"Client 指派往 Port {port}")
        client_sock.send(str(port).encode())
        client_sock.close()
        time.sleep(15)

    except Exception as e:
        logger.error(f"dispatcher error: {e}")

    finally:
        port_status[port] = False
        logger.info(f"Port {port} 任務完成，釋放資源")

if __name__ == "__main__":
    threading.Thread(target=accept_clients, daemon=True).start()
    threading.Thread(target=dispatcher, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("listen 正常關閉")
