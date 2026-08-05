import socket
import subprocess
from config import HOST_IP

def run_client(SERVER_IP, MASTER_PORT, priority=1):
    try:
        print(f"[*] 正在連線至 listen 伺服器 {SERVER_IP}:{MASTER_PORT}")
        master_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        master_sock.settimeout(250)
        master_sock.connect((SERVER_IP, MASTER_PORT))
        master_sock.sendall(str(priority).encode())
        data = master_sock.recv(1024)
        assigned_port = data.decode().strip()
        master_sock.close()
        if not assigned_port:
            print("[!] 未收到 Server 分配的 Port。")
            return

        print(f"[*] 啟動測速")
        print("-" * 50)
        cmd = ["iperf3", "-c", SERVER_IP, "-p", assigned_port, "-t", "10", "--bidir"]
        subprocess.run(cmd)
        print("-" * 50)
        print("[*] 測速完成！")

    except ConnectionRefusedError:
        print("[!] 連線被拒絕：請確認 Master 伺服器是否已啟動，以及 IP 是否正確。")
    except socket.timeout:
        print("[!] 連線超時：伺服器無回應。")
    except Exception as e:
        print(f"[!] 發生未預期錯誤: {e}")

if __name__ == "__main__":
    run_client(HOST_IP, 8000, 1)
