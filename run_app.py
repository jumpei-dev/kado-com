import sys
import os
import signal
import socket
import subprocess
from pathlib import Path
import uvicorn

# 設定
PORT = 8080
HOST = "127.0.0.1"

# デバッグ情報の表示
print("Python バージョン:", sys.version)
print("実行パス:", sys.executable)
print("カレントディレクトリ:", os.getcwd())

def is_port_in_use(port, host='127.0.0.1'):
    """ポートが使用中かどうかを確認"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def kill_process_on_port(port):
    """指定したポートで実行中のプロセスを終了する"""
    if sys.platform.startswith('win'):
        # Windowsの場合
        try:
            result = subprocess.run(
                f"netstat -ano | findstr :{port}",
                shell=True, text=True, capture_output=True
            )
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        pid = parts[-1]
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                        print(f"✅ ポート{port}のプロセス(PID: {pid})を停止しました")
                        return True
            return False
        except Exception as e:
            print(f"⚠️ プロセス停止エラー: {e}")
            return False
    else:
        # macOS/Linuxの場合
        try:
            # lsofコマンドでポートを使用しているプロセスを特定
            result = subprocess.run(
                f"lsof -i :{port} -t", 
                shell=True, text=True, capture_output=True
            )
            
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"✅ ポート{port}のプロセス(PID: {pid})を停止しました")
                return True
            return False
        except Exception as e:
            print(f"⚠️ プロセス停止エラー: {e}")
            return False

# アプリケーションを実行
if __name__ == "__main__":
    # ポートが使用中の場合はプロセスを停止
    if is_port_in_use(PORT):
        print(f"⚠️ ポート{PORT}は既に使用されています。実行中のプロセスを停止します...")
        if kill_process_on_port(PORT):
            print(f"✅ ポート{PORT}を解放しました")
        else:
            print(f"⚠️ ポート{PORT}のプロセスを停止できませんでした")
    
    print(f"🚀 サーバーを起動します - http://{HOST}:{PORT}")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True, log_level="info")