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

from app.api import auth, stores, twitter, pages, config
from app.api.admin import router as admin_router

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
async def get_store_detail(request: Request, store_id: str):
    """店舗詳細ページを表示"""
    
    try:
        # ユーザー権限を確認
        user_permissions = await check_user_permissions(request)
        
        # 実際のデータベースでは店舗IDを使って詳細情報を取得
        # ここではデモ用のダミーデータを返す
        store = generate_dummy_store(store_id)
        related_stores = generate_dummy_related_stores(store_id, store["area"], store["genre"])
        
        # 店舗名表示制御
        store_info = {"name": store["name"], "blurred_name": store.get("blurred_name", f"〇〇{store_id}")}
        name_display = get_store_display_info(store_info, user_permissions["can_see_contents"])
        
        store["original_name"] = name_display["original_name"]
        store["blurred_name"] = name_display["blurred_name"]
        store["is_blurred"] = name_display["is_blurred"]
        
        # 関連店舗の名前も同様に処理
        for related_store in related_stores:
            related_info = {
                "name": related_store["name"],
                "blurred_name": related_store.get("blurred_name", f"〇〇{related_store['id']}")
            }
            related_display = get_store_display_info(related_info, user_permissions["can_see_contents"])
            related_store["original_name"] = related_display["original_name"]
            related_store["blurred_name"] = related_display["blurred_name"]
            related_store["is_blurred"] = related_display["is_blurred"]
        
        return templates.TemplateResponse(
            "store_detail.html",
            {
                "request": request,
                "store": store,
                "related_stores": related_stores,
                "user_permissions": user_permissions
            }
        )
    except Exception as e:
        logger.error(f"店舗詳細表示エラー: {e}")
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "message": "店舗情報の取得に失敗しました"}
        )

def generate_dummy_store(store_id: str) -> dict:
    """指定されたIDの店舗の詳細情報（ダミー）を生成"""
    import random
    from datetime import datetime, timedelta
    
    # 店舗名は ID によって決定（安定したデモ用）
    names = ["エンジェルハート", "エレガンス", "クラブ美人館", "ベストパートナー", "ブルーハート", "ドレス倶楽部",
             "ウルトラグレース", "プレミアムクラブ", "ロイヤルVIP", "人妻城", "セレブクイーン"]
    
    areas = ["新宿", "池袋", "渋谷", "銀座", "六本木", "上野", "横浜", "大阪", "名古屋", "福岡"]
    genres = ["ソープランド", "ヘルス", "デリヘル", "キャバクラ", "ピンサロ"]
    
    # IDに基づいて安定したデータを生成
    id_num = int(store_id) if store_id.isdigit() else hash(store_id) % 100
    name_index = id_num % len(names)
    area_index = (id_num // 10) % len(areas)
    genre_index = (id_num // 3) % len(genres)
    
    # 稼働率データの生成
    working_rate = 30 + (id_num % 70)  # 30-99%の範囲
    previous_rate = max(20, working_rate - 10 + (id_num % 20))
    weekly_rate = max(25, working_rate - 5 + (id_num % 15))
    
    # エリア平均と業種平均
    area_avg_rate = working_rate - 15 + random.randint(-10, 10)
    area_avg_rate = max(20, min(95, area_avg_rate))
    
    genre_avg_rate = working_rate - 10 + random.randint(-10, 10)
    genre_avg_rate = max(20, min(95, genre_avg_rate))
    
    # 履歴データの生成
    history = []
    for i in range(7):
        day = datetime.now() - timedelta(days=6-i)
        day_of_week = ["月", "火", "水", "木", "金", "土", "日"][day.weekday()]
        rate = max(20, min(95, working_rate - 15 + random.randint(-20, 20)))
        
        history.append({
            "date": day.strftime("%Y/%m/%d"),
            "label": day_of_week,
            "rate": rate
        })
    
    return {
        "id": store_id,
        "name": names[name_index],
        "area": areas[area_index],
        "genre": genres[genre_index],
        "working_rate": working_rate,
        "previous_rate": previous_rate,
        "weekly_rate": weekly_rate,
        "area_avg_rate": area_avg_rate,
        "genre_avg_rate": genre_avg_rate,
        "cast_count": 15 + (id_num % 30),
        "website": f"https://example.com/shop/{store_id}",
        "history": history
    }

def generate_dummy_related_stores(current_id: str, area: str, genre: str) -> list:
    """関連店舗（同エリア・同業種）のダミーデータを生成"""
    related_stores = []
    
    # 同エリア・同業種の店舗をIDベースで生成（現在の店舗を除く）
    for i in range(1, 11):
        store_id = str(i)
        if store_id == current_id:
            continue
            
        store = generate_dummy_store(store_id)
        
        # 一部の店舗だけを関連店舗として選択（同エリアまたは同業種）
        if store["area"] == area or store["genre"] == genre:
            related_stores.append(store)
    
    # 最大3件まで
    return related_stores[:3]

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
