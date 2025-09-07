"""
サーバー起動テスト - 最小限のコードでFastAPIを起動
"""
import os
import sys
from pathlib import Path
import traceback

# 現在のディレクトリを表示
print(f"現在の作業ディレクトリ: {os.getcwd()}")

# パスを設定
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
print(f"プロジェクトルート: {project_root}")

try:
    print("\n1. FastAPIのインポート...")
    from fastapi import FastAPI
    print("✅ FastAPIのインポート成功")
    
    print("\n2. 最小限のアプリケーション作成...")
    app = FastAPI()
    
    @app.get("/")
    def read_root():
        return {"Hello": "World"}
    
    print("✅ 最小限のアプリケーション作成成功")
    
    print("\n3. uvicornの実行準備...")
    print("このスクリプトをuvicornから直接実行するには:")
    print(f"$ python -m uvicorn server_test:app --reload --port 8080")
    
    print("\n4. uvicornのインポート...")
    import uvicorn
    print("✅ uvicornのインポート成功")
    
    print("\n5. アプリケーション実行...")
    if __name__ == "__main__":
        print("🚀 サーバーを起動します...")
        uvicorn.run("server_test:app", host="127.0.0.1", port=8080, reload=True)

except Exception as e:
    print(f"\n❌ エラーが発生しました: {e}")
    traceback.print_exc()
