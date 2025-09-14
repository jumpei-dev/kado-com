import sys
import os
import time
import traceback
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from app.api import stores
from app.core.database import get_database
from app.core.auth_utils import check_user_permissions
from app.utils.blurred_name_utils import get_store_display_info
from app.utils.business_type_utils import convert_business_type_to_japanese

from app.api import auth, stores, twitter, pages, config
from app.api.admin import router as admin_router
from app.core.config import config_manager

# デバッグ情報出力
print("\n" + "=" * 60)
print(" FastAPI アプリケーション初期化開始 ".center(60, "="))
print("=" * 60)
print(f"📂 main.pyファイルパス: {__file__}")
print(f"📂 main.pyの親ディレクトリ: {Path(__file__).parent}")
print(f"📂 プロジェクトルート: {Path(__file__).parent.parent.absolute()}")
print(f"🐍 Python実行パス: {sys.executable}")
print(f"🔍 現在のsys.path:")
for i, path in enumerate(sys.path):
    print(f"  {i+1}. {path}")

# プロジェクトルートをパスに追加
project_root = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, project_root)
print(f"✅ プロジェクトルートをsys.pathに追加: {project_root}")
print("=" * 60)

# インポート試行
try:
    print("🔄 APIモジュールをインポート中...")
    from app.api import auth, stores, twitter, pages
    from app.api.admin import router as admin_router
    print("✅ APIモジュールのインポート成功")
    
    print("🔄 コアモジュールをインポート中...")
    from app.core.database import get_database, DatabaseManager
    from app.core.seed import create_dummy_users
    print("✅ コアモジュールのインポート成功")
except Exception as e:
    print(f"❌ インポートエラー: {e}")
    traceback.print_exc()
    raise

# アプリケーション初期化
print("🔄 FastAPIアプリケーションを初期化中...")
app = FastAPI(
    title="稼働.com",
    description="店舗管理システム",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kado-com.pages.dev",   # Pages のデフォルトドメイン
        "http://localhost:5173",        # 開発中 (Vite などローカルフロント)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイルの設定
try:
    print("🔄 静的ファイルを設定中...")
    static_dir = Path(__file__).parent / "static"
    print(f"静的ファイルディレクトリの絶対パス: {static_dir.absolute()}")
    if static_dir.exists():
        print(f"✅ 静的ファイルディレクトリは存在します: {static_dir}")
        app.mount("/static", StaticFiles(directory=str(static_dir.absolute())), name="static")
        print("✅ 静的ファイルの設定成功")
    else:
        print(f"❌ 静的ファイルディレクトリが見つかりません: {static_dir}")
        os.makedirs(static_dir / "css", exist_ok=True)
        os.makedirs(static_dir / "js", exist_ok=True)
        print(f"✅ 静的ファイルディレクトリを作成しました: {static_dir}")
        app.mount("/static", StaticFiles(directory=str(static_dir.absolute())), name="static")
except Exception as e:
    print(f"❌ 静的ファイル設定エラー: {e}")
    traceback.print_exc()

# テンプレートの設定
try:
    print("🔄 テンプレートを設定中...")
    templates_dir = Path(__file__).parent / "templates"
    print(f"テンプレートディレクトリの絶対パス: {templates_dir.absolute()}")
    if templates_dir.exists():
        print(f"✅ テンプレートディレクトリは存在します: {templates_dir}")
        templates = Jinja2Templates(directory=str(templates_dir.absolute()))
        # デバッグモードを有効化（テンプレートの変更を自動検出）
        templates.env.auto_reload = True
        templates.env.cache_size = 0  # キャッシュを無効化
        print("✅ テンプレートの設定成功")
    else:
        print(f"❌ テンプレートディレクトリが見つかりません: {templates_dir}")
        raise RuntimeError(f"テンプレートディレクトリが見つかりません: {templates_dir}")
except Exception as e:
    print(f"❌ テンプレート設定エラー: {e}")
    traceback.print_exc()
    raise

# APIルーター登録
app.include_router(auth.router)
app.include_router(stores.router)
app.include_router(twitter.router)
app.include_router(admin_router)
app.include_router(pages.router)
app.include_router(config.router)

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db_client():
    """アプリ起動時のイベント処理"""
    try:
        print("🔄 データベース初期化を実行中...")
        # ダミーユーザーの作成
        await create_dummy_users()
        print("✅ データベース初期化が完了しました")
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        logger.error(f"データベース初期化エラー: {e}")

# ミドルウェア
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """リクエスト処理時間計測ミドルウェア"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/healthz")
async def health_check():
    """ヘルスチェック用エンドポイント"""
    return {"status": "healthy", "message": "Application is running"}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページを表示"""
    config_data = config_manager.config
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "title": "稼働.com", 
            "config": config_data,
            "page_type": "index"
        }
    )

# 店舗一覧ページ
@app.get("/stores", response_class=HTMLResponse)
async def stores_page(request: Request, db = Depends(get_database)):
    """店舗一覧ページ表示"""
    try:
        # ユーザー権限を確認
        user_permissions = await check_user_permissions(request)
        
        # APIから店舗一覧を取得
        store_data = await stores.get_stores(db=db)
        
        return templates.TemplateResponse(
            "components/stores_list.html", 
            {
                "request": request, 
                "stores": store_data["items"],
                "user_permissions": user_permissions,
                "page_type": "stores"
            }
        )
    except Exception as e:
        logger.error(f"店舗一覧取得エラー: {e}")
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "message": "店舗データの取得に失敗しました"}
        )

# 古い店舗詳細エンドポイントを削除（65%ハードコーディングの原因）
# 新しいエンドポイントは /app/api/stores.py で定義されています



# エラーハンドラー
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """404エラーハンドラー"""
    return templates.TemplateResponse(
        "error.html", 
        {"request": request, "message": "ページが見つかりません"}, 
        status_code=404
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """500エラーハンドラー"""
    logger.error(f"サーバーエラー: {exc}")
    return templates.TemplateResponse(
        "error.html", 
        {"request": request, "message": "サーバーエラーが発生しました"}, 
        status_code=500
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
