#!/usr/bin/env python
"""
稼働.com 開発環境起動スクリプト
サーバーとフロントエンドを同時に起動します
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from threading import Thread

# プロジェクトルートディレクトリ
ROOT_DIR = Path(__file__).parent.absolute()
SERVER_DIR = ROOT_DIR / "server"
FRONTEND_DIR = ROOT_DIR / "frontend"

def run_server():
    """FastAPIサーバーを起動"""
    os.chdir(SERVER_DIR)
    print("🚀 バックエンドサーバーを起動します...")
    subprocess.run(
        ["python", "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        check=True,
    )

def run_frontend():
    """フロントエンドを起動"""
    os.chdir(FRONTEND_DIR)
    print("🚀 フロントエンドを起動します...")
    # Windowsの場合はnpm.cmdを使用
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    subprocess.run([npm_cmd, "run", "dev"], check=True)

if __name__ == "__main__":
    # サーバーを別スレッドで起動
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # サーバーの起動を少し待ってからフロントエンドを起動
    time.sleep(2)
    
    try:
        # フロントエンドを起動（メインスレッド）
        run_frontend()
    except KeyboardInterrupt:
        print("\n👋 アプリケーションを終了します...")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    
    # Ctrl+Cが押されたらプログラムが終了
