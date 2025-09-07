"""
アプリケーションのインポート検証スクリプト
"""
import sys
import os
from pathlib import Path
import traceback

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

print(f"カレントディレクトリ: {os.getcwd()}")
print(f"プロジェクトルート: {project_root}")
print("Python Path:")
for p in sys.path:
    print(f"  - {p}")

print("\n======== モジュールインポートテスト ========")

try:
    print("FastAPIとその依存関係をテスト中...")
    import fastapi
    import uvicorn
    import jinja2
    print("✅ 基本ライブラリのインポート成功")
except Exception as e:
    print(f"❌ 基本ライブラリのインポートに失敗: {e}")
    traceback.print_exc()

# app.apiモジュールのテスト
try:
    print("\napp.apiモジュールをテスト中...")
    # インポートを試みる前に__init__.pyファイルの存在を確認
    api_init = Path("app/api/__init__.py")
    if api_init.exists():
        print(f"✅ {api_init} は存在します")
    else:
        print(f"❌ {api_init} が見つかりません")
        # 作成する
        api_init.parent.mkdir(parents=True, exist_ok=True)
        with open(api_init, "w") as f:
            f.write("# API package\n")
        print(f"✅ {api_init} を作成しました")
    
    # 各APIモジュールのパスを確認
    for module in ["stores", "auth", "twitter"]:
        module_path = Path(f"app/api/{module}.py")
        if module_path.exists():
            print(f"✅ {module_path} は存在します")
        else:
            print(f"❌ {module_path} が見つかりません")
    
    # インポート試行
    print("\napp.apiモジュールをインポート中...")
    sys.path.insert(0, str(project_root))
    from app.api import stores, auth, twitter
    print("✅ app.apiモジュールのインポート成功")
except Exception as e:
    print(f"❌ app.apiモジュールのインポートに失敗: {e}")
    traceback.print_exc()

# app.coreモジュールのテスト
try:
    print("\napp.coreモジュールをテスト中...")
    # インポートを試みる前に__init__.pyファイルの存在を確認
    core_init = Path("app/core/__init__.py")
    if core_init.exists():
        print(f"✅ {core_init} は存在します")
    else:
        print(f"❌ {core_init} が見つかりません")
        # 作成する
        core_init.parent.mkdir(parents=True, exist_ok=True)
        with open(core_init, "w") as f:
            f.write("# Core package\n")
        print(f"✅ {core_init} を作成しました")
    
    # coreモジュールのパスを確認
    for module in ["database", "config"]:
        module_path = Path(f"app/core/{module}.py")
        if module_path.exists():
            print(f"✅ {module_path} は存在します")
        else:
            print(f"❌ {module_path} が見つかりません")
    
    # インポート試行
    print("\napp.coreモジュールをインポート中...")
    from app.core import database
    print("✅ app.coreモジュールのインポート成功")
except Exception as e:
    print(f"❌ app.coreモジュールのインポートに失敗: {e}")
    traceback.print_exc()

# FastAPIアプリケーション作成テスト
try:
    print("\nFastAPIアプリケーション作成テスト...")
    from fastapi import FastAPI
    app = FastAPI()
    print("✅ FastAPIアプリケーション作成成功")
    
    # 静的ファイルの設定テスト
    try:
        from fastapi.staticfiles import StaticFiles
        static_path = Path("app/static")
        if static_path.exists():
            print(f"✅ 静的ファイルディレクトリ {static_path} は存在します")
            app.mount("/static", StaticFiles(directory="app/static"), name="static")
            print("✅ 静的ファイルのマウント成功")
        else:
            print(f"❌ 静的ファイルディレクトリ {static_path} が見つかりません")
    except Exception as e:
        print(f"❌ 静的ファイルのマウントに失敗: {e}")
        traceback.print_exc()
    
    # テンプレートの設定テスト
    try:
        from fastapi.templating import Jinja2Templates
        templates_path = Path("app/templates")
        if templates_path.exists():
            print(f"✅ テンプレートディレクトリ {templates_path} は存在します")
            templates = Jinja2Templates(directory="app/templates")
            print("✅ テンプレートの設定成功")
        else:
            print(f"❌ テンプレートディレクトリ {templates_path} が見つかりません")
    except Exception as e:
        print(f"❌ テンプレートの設定に失敗: {e}")
        traceback.print_exc()
except Exception as e:
    print(f"❌ FastAPIアプリケーション作成テストに失敗: {e}")
    traceback.print_exc()

print("\n======== テスト完了 ========")
print("上記の結果を確認して、具体的な問題点を特定してください。")
