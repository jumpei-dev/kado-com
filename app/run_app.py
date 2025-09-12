import sys
import os
import signal
import socket
import subprocess
from pathlib import Path
import uvicorn
import time
import atexit
import json

# 設定
PORT = 8080
HOST = "127.0.0.1"

# データベース接続設定
DATABASE_URL = "postgresql://postgres.hnmbsqydlfemlmsyexrq:Ggzzmmb3@57.182.231.186:6543/postgres?sslmode=require"

# PIDファイル設定
PID_FILE = Path(os.path.expanduser("~")) / ".kado-com-app.pid"
LOCK_FILE = Path(os.path.expanduser("~")) / ".kado-com-app.lock"

# デバッグ情報の表示
print("Python バージョン:", sys.version)
print("実行パス:", sys.executable)
print("カレントディレクトリ:", os.getcwd())

def is_port_in_use(port, host='127.0.0.1'):
    """ポートが使用中かどうかを確認"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def save_pid_file(pid_file=PID_FILE, port=PORT):
    """現在のプロセスIDとポート情報をPIDファイルに保存"""
    try:
        data = {
            "pid": os.getpid(),
            "port": port,
            "timestamp": time.time(),
            "cwd": os.getcwd()
        }
        with open(pid_file, 'w') as f:
            json.dump(data, f)
        print(f"✅ PIDファイルを作成しました: {pid_file}")
        
        # プロセス終了時にPIDファイルを削除する処理を登録
        atexit.register(lambda: cleanup_pid_file(pid_file))
    except Exception as e:
        print(f"⚠️ PIDファイル作成エラー: {e}")

def cleanup_pid_file(pid_file=PID_FILE):
    """PIDファイルを削除"""
    try:
        if pid_file.exists():
            pid_file.unlink()
            print(f"✅ PIDファイルを削除しました: {pid_file}")
    except Exception as e:
        print(f"⚠️ PIDファイル削除エラー: {e}")

def read_pid_file(pid_file=PID_FILE):
    """PIDファイルから情報を読み取る"""
    try:
        if pid_file.exists():
            with open(pid_file, 'r') as f:
                data = json.load(f)
            return data
        return None
    except Exception as e:
        print(f"⚠️ PIDファイル読み取りエラー: {e}")
        return None

def kill_process_by_pid(pid, force=True):
    """指定したPIDのプロセスを終了する"""
    if not pid:
        return False
        
    try:
        if force:
            # 強制終了シグナル（SIGKILL）
            if sys.platform.startswith('win'):
                subprocess.run(f"taskkill /F /PID {pid}", shell=True)
            else:
                os.kill(int(pid), signal.SIGKILL)
        else:
            # 通常終了シグナル（SIGTERM）
            if sys.platform.startswith('win'):
                subprocess.run(f"taskkill /PID {pid}", shell=True)
            else:
                os.kill(int(pid), signal.SIGTERM)
        print(f"✅ PID {pid} のプロセスを停止しました")
        return True
    except ProcessLookupError:
        print(f"⚠️ PID {pid} のプロセスは存在しません")
        return False
    except Exception as e:
        print(f"⚠️ PID {pid} の停止中にエラー: {e}")
        return False

def kill_process_by_name(process_names):
    """指定した名前のプロセスを終了する"""
    print(f"🔍 プロセス {', '.join(process_names)} を検索中...")
    killed = False
    
    if sys.platform.startswith('win'):
        # Windowsの場合
        for name in process_names:
            try:
                result = subprocess.run(
                    f"tasklist /FI \"IMAGENAME eq {name}\" /NH",
                    shell=True, text=True, capture_output=True
                )
                if name in result.stdout:
                    subprocess.run(f"taskkill /F /IM {name}", shell=True)
                    print(f"✅ プロセス {name} を停止しました")
                    killed = True
            except Exception as e:
                print(f"⚠️ プロセス {name} の停止中にエラー: {e}")
    else:
        # macOS/Linuxの場合
        for name in process_names:
            try:
                # プロセスを検索して強制終了
                subprocess.run(f"pkill -f {name}", shell=True)
                print(f"✅ プロセス {name} を停止しました")
                killed = True
            except Exception as e:
                print(f"⚠️ プロセス {name} の停止中にエラー: {e}")
    
    return killed

def kill_process_on_port(port, force=True):
    """指定したポートで実行中のプロセスを終了する"""
    print(f"🔍 ポート{port}を使用しているプロセスを検索中...")
    killed = False
    
    # まずPIDファイルの情報を確認
    pid_data = read_pid_file()
    if pid_data and pid_data.get('port') == port:
        pid = pid_data.get('pid')
        if pid:
            print(f"🔍 PIDファイルからプロセスを検出: PID {pid}, ポート {port}")
            if kill_process_by_pid(pid, force=force):
                cleanup_pid_file()  # PIDファイルを削除
                killed = True

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
                        if kill_process_by_pid(pid, force=force):
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
            return killed
    else:
        # macOS/Linuxの場合
        try:
            # まずlsofを使用してPIDを取得
            result = subprocess.run(
                f"lsof -i :{port} -t", 
                shell=True, text=True, capture_output=True
            )
            
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        if kill_process_by_pid(pid, force=force):
                            killed = True
            
            # 追加: 直接kill -9コマンドを使用
            if force and not killed:
                try:
                    # lsofを使ってPIDを取得し、kill -9で強制終了
                    result = subprocess.run(
                        f"lsof -i :{port} -t | xargs -r kill -9",
                        shell=True
                    )
                    print(f"✅ 強制終了モード: ポート{port}のプロセスを直接kill -9で停止しました")
                    killed = True
                except Exception as e:
                    print(f"⚠️ 強制kill -9でのエラー: {e}")
            
            # pkillコマンドも試す (より広範囲に検索)
            if not killed:
                try:
                    # uvicornプロセスを検索して強制終了
                    subprocess.run(f"pkill -{9 if force else 15} -f 'uvicorn.*:{port}'", shell=True)
                    
                    # Pythonプロセスも検索
                    subprocess.run(f"pkill -{9 if force else 15} -f 'python.*:{port}'", shell=True)
                    print(f"✅ pkillでポート{port}のプロセスを停止しました")
                    killed = True
                except Exception as e:
                    print(f"⚠️ pkillでの停止エラー: {e}")
            
            # 強制終了モードの場合、追加の対策を試す
            if force and not killed:
                try:
                    # killall (最終手段)
                    subprocess.run(f"killall -{9 if force else 15} python3", shell=True, timeout=1)
                    subprocess.run(f"killall -{9 if force else 15} python", shell=True, timeout=1)
                    subprocess.run(f"killall -{9 if force else 15} uvicorn", shell=True, timeout=1)
                    print(f"✅ 強制終了モード: killallでプロセスを停止しました")
                    killed = True
                except Exception as e:
                    print(f"⚠️ 強制終了エラー: {e}")
            
            return killed
        except Exception as e:
            print(f"⚠️ プロセス停止エラー: {e}")
            return killed

# アプリケーションを実行
if __name__ == "__main__":
    import time
    
    print("🚀 アプリケーションを起動準備中...")
    
    # 起動前に既存の関連プロセスを終了
    print("🔄 既存のFastAPI/uvicornプロセスを確認中...")
    process_names = ['uvicorn', 'fastapi', 'python.*main.py']
    kill_process_by_name(process_names)
    
    # PIDファイルの確認と古いプロセスの終了
    pid_data = read_pid_file()
    if pid_data:
        print(f"🔍 前回のプロセス情報を検出: PID {pid_data.get('pid')}, ポート {pid_data.get('port')}")
        old_pid = pid_data.get('pid')
        if old_pid:
            # 前回のプロセスを強制終了
            kill_process_by_pid(old_pid, force=True)
            cleanup_pid_file()
    
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
                    print(f"   PORT={alt_port} python app/run_app.py")
                
                print(f"🔄 再度実行するか、別のポートを使用するか、手動でプロセスを停止してください。")
                sys.exit(1)
        else:
            # ポートが空いている場合は即座に実行
            break
    
    print(f"🚀 サーバーを起動します - http://{HOST}:{PORT}")
    try:
        # 現在のプロセス情報を保存
        save_pid_file(port=PORT)
        
        # アプリケーションの実行前に環境変数を設定
        project_root = str(Path(__file__).parent.parent.absolute())
        os.environ["PYTHONPATH"] = project_root
        os.environ["PYTHONUNBUFFERED"] = "1"
        os.environ["DATABASE_URL"] = DATABASE_URL
        
        # ダミーユーザーを作成
        print("👤 ダミーユーザーを作成しています...")
        try:
            from app.core.seed import create_dummy_users
            import asyncio
            asyncio.run(create_dummy_users())
            print("✅ ダミーユーザーの作成が完了しました")
        except Exception as e:
            print(f"⚠️ ダミーユーザー作成中にエラーが発生しました: {e}")
        
        # Tailwind CSSを一度ビルド
        print("🎨 Tailwind CSSをビルド中...")
        try:
            app_dir = Path(__file__).parent.absolute()
            subprocess.run(
                f"cd {app_dir} && npx tailwindcss -i ./tailwind.input.css -o ./static/css/tailwind.css", 
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
                print(f"   kill -9コマンドを使用して強制終了: lsof -i :{PORT} -t | xargs -r kill -9")
            
            # PIDファイルを削除して他のインスタンスが起動できるようにする
            cleanup_pid_file()
            sys.exit(1)
        else:
            print(f"❌ エラーが発生しました: {e}")
            # PIDファイルを削除して他のインスタンスが起動できるようにする
            cleanup_pid_file()
            raise
    finally:
        # 最終的にPIDファイルを確実に削除
        cleanup_pid_file()