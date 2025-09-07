"""
アプリケーション起動前のデバッグ情報収集スクリプト
"""
import sys
import os
import importlib
import traceback

def log_separator(title=""):
    """区切り線をログに出力"""
    print("\n" + "=" * 60)
    if title:
        print(f" {title} ".center(60, "="))
    print("=" * 60)

def check_module_importable(module_name):
    """モジュールがインポート可能かチェック"""
    try:
        importlib.import_module(module_name)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    """メイン関数"""
    log_separator("アプリケーション起動前診断")
    
    # 1. システム情報
    print("📊 システム情報:")
    print(f"  - Python バージョン: {sys.version}")
    print(f"  - 実行パス: {sys.executable}")
    print(f"  - カレントディレクトリ: {os.getcwd()}")
    
    # 2. 環境変数
    log_separator("環境変数")
    for key, value in sorted(os.environ.items()):
        if key.startswith("PYTHON") or key in ["PATH", "VIRTUAL_ENV"]:
            print(f"  - {key}: {value}")
    
    # 3. sys.path
    log_separator("Python パス (sys.path)")
    for i, path in enumerate(sys.path):
        print(f"  {i+1}. {path}")
        if os.path.exists(path):
            print(f"     ✅ パスは存在します")
        else:
            print(f"     ❌ パスは存在しません")
    
    # 4. 重要なモジュールのチェック
    log_separator("重要なモジュールのインポートテスト")
    modules_to_check = [
        "fastapi", 
        "uvicorn", 
        "jinja2",
        "app",
        "app.api",
        "app.api.stores",
        "app.api.auth",
        "app.api.twitter",
        "app.core",
        "app.core.database"
    ]
    
    for module in modules_to_check:
        success, error = check_module_importable(module)
        if success:
            print(f"✅ {module}: インポート成功")
        else:
            print(f"❌ {module}: インポート失敗")
            print(f"   エラー: {error}")
    
    # 5. アプリケーションのファイル構造チェック
    log_separator("アプリケーションファイル構造")
    app_files = [
        "app/main.py",
        "app/api/stores.py",
        "app/api/auth.py",
        "app/api/twitter.py",
        "app/core/database.py",
        "app/core/config.py"
    ]
    
    for file in app_files:
        if os.path.exists(file):
            print(f"✅ {file}: 存在します")
        else:
            print(f"❌ {file}: 存在しません")
    
    log_separator("診断完了")
    print("🚀 uvicorn起動を試みます...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_separator("エラー発生")
        print(f"❌ 診断中にエラーが発生しました: {e}")
        traceback.print_exc()
