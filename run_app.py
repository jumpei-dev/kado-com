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

def kill_process_on_port(port, force=True):
    """指定したポートで実行中のプロセスを終了する"""
    print(f"🔍 ポート{port}を使用しているプロセスを検索中...")
    killed = False

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
                        killed = True
            
            # 強制終了モードの場合、追加の対策を試す
            if force and not killed:
                try:
                    subprocess.run(f"for /f \"tokens=5\" %a in ('netstat -aon ^| find \":{port}\" ^| find \"LISTENING\"') do taskkill /F /PID %a", shell=True)
                    print(f"✅ 強制終了モード: ポート{port}のプロセスを停止しました")
                    killed = True
                except Exception as e:
                    print(f"⚠️ 強制終了エラー: {e}")
            
            return killed
        except Exception as e:
            print(f"⚠️ プロセス停止エラー: {e}")
            return False
    else:
        # macOS/Linuxの場合
        try:
            # まずlsofを使用
            result = subprocess.run(
                f"lsof -i :{port} -t", 
                shell=True, text=True, capture_output=True
            )
            
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            # 強制終了シグナルを送信
                            os.kill(int(pid), signal.SIGKILL)
                            print(f"✅ ポート{port}のプロセス(PID: {pid})を停止しました")
                            killed = True
                        except ProcessLookupError:
                            print(f"⚠️ プロセス(PID: {pid})は既に存在しません")
            
            # pkillコマンドも試す (より広範囲に検索)
            try:
                # uvicornプロセスを検索して強制終了
                subprocess.run(f"pkill -9 -f 'uvicorn.*:{port}'", shell=True)
                
                # Pythonプロセスも検索
                subprocess.run(f"pkill -9 -f 'python.*:{port}'", shell=True)
                print(f"✅ pkillでポート{port}のプロセスを停止しました")
                killed = True
            except Exception as e:
                print(f"⚠️ pkillでの停止エラー: {e}")
            
            # 強制終了モードの場合、追加の対策を試す
            if force and not killed:
                try:
                    # sudo killall (sudoパスワードが必要な場合は動作しない)
                    subprocess.run(f"killall -9 python", shell=True, timeout=1)
                    subprocess.run(f"killall -9 uvicorn", shell=True, timeout=1)
                    print(f"✅ 強制終了モード: killallでプロセスを停止しました")
                    killed = True
                except Exception as e:
                    print(f"⚠️ 強制終了エラー: {e}")
            
            return killed
        except Exception as e:
            print(f"⚠️ プロセス停止エラー: {e}")
            return False

# アプリケーションを実行
if __name__ == "__main__":
    import time
    
    # 最大再試行回数
    MAX_RETRIES = 3
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        # ポートが使用中の場合はプロセスを停止
        if is_port_in_use(PORT):
            print(f"⚠️ ポート{PORT}は既に使用されています。実行中のプロセスを停止します... (試行: {retry_count + 1}/{MAX_RETRIES})")
            
            # 強制モードでプロセス停止を試みる
            force_mode = retry_count > 0  # 2回目以降は強制モードを使用
            if kill_process_on_port(PORT, force=force_mode):
                print(f"✅ ポート{PORT}を解放しました")
            else:
                print(f"⚠️ ポート{PORT}のプロセスを停止できませんでした")
            
            # 停止後に再度確認（少し待機）
            wait_time = 2 * (retry_count + 1)  # 待機時間を徐々に増やす
            print(f"⏳ {wait_time}秒待機します...")
            time.sleep(wait_time)
            
            # ポートが解放されたか確認
            if not is_port_in_use(PORT):
                print(f"✅ ポート{PORT}が解放されました！")
                break
            
            retry_count += 1
            
            # 最大試行回数に達した場合
            if retry_count >= MAX_RETRIES:
                print(f"❌ {MAX_RETRIES}回試行しましたが、ポート{PORT}を解放できませんでした。")
                
                # 代替ポートを提案
                alt_port = PORT + 1
                while is_port_in_use(alt_port) and alt_port < PORT + 10:
                    alt_port += 1
                
                if not is_port_in_use(alt_port):
                    print(f"💡 代わりにポート{alt_port}を使用してみますか？使用するには次のように実行してください：")
                    print(f"   PORT={alt_port} python run_app.py")
                
                print(f"🔄 再度実行するか、別のポートを使用するか、手動でプロセスを停止してください。")
                sys.exit(1)
        else:
            # ポートが空いている場合は即座に実行
            break
    
    print(f"🚀 サーバーを起動します - http://{HOST}:{PORT}")
    try:
        # アプリケーションの実行前に環境変数を設定
        os.environ["PYTHONPATH"] = os.getcwd()
        os.environ["PYTHONUNBUFFERED"] = "1"
        
        # ダミーユーザーを作成
        print("👤 ダミーユーザーを作成しています...")
        try:
            import asyncio
            from app.core.seed import create_dummy_users
            asyncio.run(create_dummy_users())
            print("✅ ダミーユーザーの作成が完了しました")
        except Exception as e:
            print(f"⚠️ ダミーユーザー作成中にエラーが発生しました: {e}")
        
        # Tailwind CSSを一度ビルド
        print("🎨 Tailwind CSSをビルド中...")
        try:
            subprocess.run(
                "cd app && npx tailwindcss -i ./tailwind.input.css -o ./static/css/tailwind.css", 
                shell=True, 
                timeout=10
            )
            print("✅ Tailwind CSSのビルド完了")
        except Exception as e:
            print(f"⚠️ Tailwind CSSのビルドに失敗しました: {e}")
        
        # サーバーを起動
        print(f"🚀 Uvicornサーバーを起動中... http://{HOST}:{PORT}")
        uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True, log_level="info")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ 予期せぬエラー: ポート{PORT}は他のプロセスで使用中です。")
            print(f"💡 次のコマンドを試して実行中のプロセスを確認できます：")
            
            if sys.platform.startswith('win'):
                print(f"   netstat -ano | findstr :{PORT}")
            else:
                print(f"   lsof -i :{PORT}")
                print(f"   または: sudo lsof -i :{PORT}")
            
            sys.exit(1)
        else:
            print(f"❌ エラーが発生しました: {e}")
            raise