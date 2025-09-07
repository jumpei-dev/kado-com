from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
import logging
import time
import os
import json
import traceback

import sys
import os
from pathlib import Path

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
    from app.api import auth, stores, twitter
    print("✅ APIモジュールのインポート成功")
    
    print("🔄 コアモジュールをインポート中...")
    from app.core.database import get_database
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

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ミドルウェア
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """リクエスト処理時間計測ミドルウェア"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページを表示"""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "稼働.com"}
    )

# 店舗一覧ページ
@app.get("/stores", response_class=HTMLResponse)
async def stores_page(request: Request, db = Depends(get_database)):
    """店舗一覧ページ表示"""
    try:
        # APIから店舗一覧を取得
        store_data = await stores.get_stores(db=db)
        
        return templates.TemplateResponse(
            "components/stores_list.html", 
            {"request": request, "stores": store_data["items"]}
        )
    except Exception as e:
        logger.error(f"店舗一覧取得エラー: {e}")
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "message": "店舗データの取得に失敗しました"}
        )

# 店舗詳細ページ
@app.get("/stores/{store_id}", response_class=HTMLResponse)
async def store_detail(request: Request, store_id: str, db = Depends(get_database)):
    """店舗詳細ページ表示"""
    try:
        # APIから店舗詳細を取得
        store_detail = await stores.get_store_detail(store_id=store_id, db=db)
        
        return templates.TemplateResponse(
            "components/store_detail.html", 
            {"request": request, "store": store_detail}
        )
    except Exception as e:
        logger.error(f"店舗詳細取得エラー: {e}")
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "message": "店舗詳細の取得に失敗しました"}
        )

# HTMXコンポーネント: 店舗カード
@app.get("/components/store_card/{store_id}", response_class=HTMLResponse)
async def store_card(request: Request, store_id: str, db = Depends(get_database)):
    """店舗カードコンポーネント取得"""
    try:
        # APIから店舗詳細を取得
        store_detail = await stores.get_store_detail(store_id=store_id, db=db)
        
        return templates.TemplateResponse(
            "components/store_card.html", 
            {"request": request, "store": store_detail}
        )
    except Exception as e:
        logger.error(f"店舗カード取得エラー: {e}")
        return HTMLResponse(f"<div>店舗データ取得エラー</div>")

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
