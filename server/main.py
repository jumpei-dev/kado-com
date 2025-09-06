import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.core.config import settings
    from app.api import auth, stores
    print("✅ 統合設定を使用してサーバーを起動します")
except ImportError as e:
    print(f"⚠️ インポートエラー: {e}")
    print("デフォルト設定を使用します")
    
    # フォールバック設定
    class DefaultSettings:
        api_host = "localhost"
        api_port = 8000
        debug = True
        allowed_origins = ["http://localhost:5173"]
    
    settings = DefaultSettings()
    auth = None
    stores = None

# FastAPIアプリケーション作成
app = FastAPI(
    title="稼働.com API",
    description="風俗店稼働率管理システムのAPI",
    version="1.0.0",
    debug=settings.debug
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
if auth and stores:
    app.include_router(auth.router)
    app.include_router(stores.router)
    print("✅ 認証・店舗APIルーターを登録しました")
else:
    print("⚠️ APIルーターが利用できません（デフォルトモード）")

# ヘルスチェック
@app.get("/")
async def root():
    return {
        "message": "稼働.com API サーバー",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
