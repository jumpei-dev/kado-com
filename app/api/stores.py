from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Any, Optional
import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

from app.core.database import get_database
from app.core.auth_service import AuthService
from app.utils.blurred_name_utils import get_store_display_info
from app.utils.business_type_utils import convert_business_type_to_japanese

# AuthServiceのインスタンス化
auth_service = AuthService()

# テンプレートの設定
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir.absolute()))

router = APIRouter(prefix="/api/stores", tags=["stores"])
security = HTTPBearer(auto_error=False)

def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """認証チェック (開発版は常にOK)"""
    return True

async def check_user_permissions(request: Request) -> dict:
    """リクエストからユーザー権限を確認"""
    try:
        # auth_serviceを使用してユーザー情報を取得
        user_info = await auth_service.get_current_user(request)
        
        print(f"🔍 [DEBUG] check_user_permissions: user_info={'あり' if user_info else 'なし'}")
        
        if not user_info:
            print("🔍 [DEBUG] check_user_permissions: ユーザー情報なし - ログアウト状態")
            return {"logged_in": False, "can_see_contents": False}
        
        can_see_contents = user_info.get('can_see_contents', False)
        is_admin = user_info.get('is_admin', False)
        
        # 🔧 開発用: adminユーザーは強制的にcan_see_contents=Trueにする
        if is_admin:
            can_see_contents = True
            print(f"🔧 [DEBUG] admin強制設定: {user_info['username']} -> can_see_contents=True")
        
        result = {
            "logged_in": True,
            "can_see_contents": can_see_contents,
            "username": user_info['username'],
            "is_admin": is_admin
        }
        
        print(f"🔍 [DEBUG] check_user_permissions結果: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ [DEBUG] check_user_permissions エラー: {e}")
        return {"logged_in": False, "can_see_contents": False}

@router.get("", response_class=HTMLResponse)
async def get_stores(
    request: Request,
    sort: str = Query("util_today", description="ソート基準"),
    page: int = Query(1, description="ページ番号", ge=1),
    page_size: int = Query(30, description="1ページあたりの表示件数", ge=1, le=50),
    area: str = Query("all", description="エリアフィルター"),
    genre: str = Query("all", description="業種フィルター"),
    rank: str = Query("all", description="ランクフィルター"),
    period: str = Query("week", description="期間フィルター"),
    auth: bool = Depends(require_auth),
    db = Depends(get_database)
):
    """店舗一覧取得 - HTMLレスポンス (ページネーション対応)"""
    
    # ユーザー権限を確認
    user_permissions = await check_user_permissions(request)
    print(f"🔍 [DEBUG] 店舗一覧リクエスト: page={page}, user_permissions={user_permissions}")
    print(f"🔍 [DEBUG] リクエストヘッダー: {dict(request.headers)}")
    print(f"🔍 [DEBUG] クッキー: {dict(request.cookies)}")
    
    try:
        # 実際のデータベースから取得
        print("📊 [DEBUG] データベースから店舗データを取得中...")
        businesses = db.get_businesses()
        print(f"📊 [DEBUG] DB取得完了: {len(businesses)}件の店舗データ")
        
        # レスポンス形式に変換
        stores = []
        can_see_contents = user_permissions.get('can_see_contents', False)
        print(f"🔍 [DEBUG] blurred_name処理開始: can_see_contents={can_see_contents}")
        
        for key, business in businesses.items():
            if business.get('in_scope', False):  # 管理対象店舗のみ
                # blurred_name処理を適用
                store_display_info = get_store_display_info(business, can_see_contents)
                
                # DBのblurred_nameの値をログ出力
                original_name = business.get('name', '不明')
                db_blurred_name = business.get('blurred_name')
                display_name = store_display_info['display_name']
                
                print(f"📊 [DEBUG] 店舗ID {business.get('Business ID')}: {original_name} -> DB blurred_name: {db_blurred_name} -> 表示名: {display_name}")
                
                # 稼働率の値をカードテンプレートで使われる名前に合わせる
                util_today = 72.5  # TODO: 実際の稼働率を計算
                util_yesterday = 65.3
                util_7d = 68.9
                
                stores.append({
                    "id": str(business.get('Business ID')),
                    "name": display_name,  # blurred_name処理済みの表示名を使用
                    "original_name": original_name,
                    "blurred_name": store_display_info['blurred_name'],
                    "is_blurred": store_display_info['is_blurred'],
                    "prefecture": business.get('prefecture', '不明'),
                    "city": business.get('city', '不明'), 
                    "area": business.get('area', '不明'),
                    "genre": convert_business_type_to_japanese(business.get('type', '')),
                    "status": "active" if business.get('in_scope') else "inactive",
                    "last_updated": business.get('last_updated', '2024-01-01'),
                    "util_today": util_today,
                    "util_yesterday": util_yesterday,
                    "util_7d": util_7d,
                    # カードテンプレート用のプロパティを追加
                    "working_rate": util_today,
                    "previous_rate": util_yesterday,
                    "weekly_rate": util_7d
                })
        
        # ソート処理
        if sort == "util_today":
            stores.sort(key=lambda x: x.get("util_today", 0), reverse=True)
        elif sort == "name":
            stores.sort(key=lambda x: x.get("name", ""))
        
        # ページネーション処理
        total_items = len(stores)
        total_pages = (total_items + page_size - 1) // page_size  # 切り上げ計算
        
        # ページ番号の範囲チェック
        if page > total_pages and total_pages > 0:
            page = total_pages
            
        # スライスでページングデータを取得
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        paged_stores = stores[start_idx:end_idx]
        
        # HTMLテンプレートをレンダリングして返す
        return templates.TemplateResponse(
            "components/stores_list.html", 
            {
                "request": request, 
                "stores": paged_stores,
                "user_permissions": user_permissions,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_items,
                    "page_size": page_size,
                    "has_prev": page > 1,
                    "has_next": page < total_pages
                }
            }
        )
        
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail="データベースに接続できません。しばらく時間をおいてから再度お試しください。"
        )

@router.get("/{store_id}", response_class=HTMLResponse)
async def get_store_detail(
    request: Request,
    store_id: str,
    auth: bool = Depends(require_auth),
    db = Depends(get_database)
):
    """店舗詳細取得"""
    
    # Debug log for store_id
    print(f"🔍 [STORE_DETAIL] Received store_id: {store_id}")
    print(f"🔍 [STORE_DETAIL] Request URL: {request.url}")
    print(f"🔍 [STORE_DETAIL] Request method: {request.method}")
    
    # ユーザー権限を確認
    user_permissions = await check_user_permissions(request)
    
    try:
        # 実際のデータベースから店舗情報取得
        businesses = db.get_businesses()
        print(f"[DEBUG] Total businesses found: {len(businesses)}")
        business = None
        
        # データベースから店舗を検索
        print(f"🔍 DBから店舗ID {store_id} を検索中...")
        print(f"[DEBUG] Available businesses: {len(businesses)} items")
        
        for key, biz in businesses.items():
            biz_id = str(biz.get('Business ID'))
            print(f"[DEBUG] Checking business ID: {biz_id} against store_id: {store_id}")
            if biz_id == store_id:
                business = biz
                print(f"✅ DB店舗データ取得: {biz.get('name', biz.get('Name', 'Unknown'))}")
                break
        
        # 見つからない場合の詳細ログ
        if not business:
            print(f"❌ 店舗ID {store_id} が見つかりません")
            print(f"[DEBUG] Available Business IDs: {[str(biz.get('Business ID')) for key, biz in businesses.items()]}")
        
        if not business:
            # 店舗が見つからない場合はエラーを返す
            print(f"❌ 店舗ID {store_id} が見つかりません")
            raise HTTPException(
                status_code=404, 
                detail=f"店舗ID {store_id} が見つかりません。正しい店舗IDを指定してください。"
            )
        
        # データベースから店舗詳細データを取得
        store_details = db.get_store_details(int(store_id))
        if store_details:
            print(f"✅ DB詳細データ取得成功: {store_details['name']}")
            util_today = store_details['working_rate']
            util_yesterday = util_today - 5  # 簡易計算
            util_7d = util_today
            history_data = store_details['history']
        else:
            print(f"⚠️ DB詳細データ取得失敗、デフォルト値使用")
            util_today = 72.5
            util_yesterday = 65.3
            util_7d = 68.9
            history_data = [
                {"label": "今週", "rate": 72.5},
                {"label": "先週", "rate": 65.3},
                {"label": "2週間前", "rate": 68.9},
                {"label": "3週間前", "rate": 59.7},
                {"label": "4週間前", "rate": 63.2}
            ]
        
        # 24時間のタイムライン生成（TODO: 実際のstatus_historyから取得）
        timeline = []
        for hour in range(24):
            timeline.append({
                "slot": f"{hour:02d}:00",
                "active": hour % 3 != 0,
                "working_count": max(0, 5 - (hour % 4)),
                "total_count": 6
            })
        
        # 店舗名表示制御 - 店舗一覧と同じ仕組みを使用
        print(f"🔍 権限チェック: can_see_contents = {user_permissions['can_see_contents']}")
        name_display = get_store_display_info(business, user_permissions["can_see_contents"])
        print(f"📝 名前変換結果: {name_display}")
        
        store_data = {
            "id": store_id,
            "name": name_display["display_name"],
            "original_name": name_display["original_name"],
            "blurred_name": name_display["blurred_name"],
            "is_blurred": name_display["is_blurred"],
            "prefecture": business.get('Prefecture', business.get('prefecture', '不明')),
            "city": business.get('City', business.get('city', '不明')),
            "area": business.get('Area', business.get('area', '不明')),
            "genre": convert_business_type_to_japanese(business.get('Type', business.get('genre', ''))),
            "status": "active" if business.get('in_scope') else "inactive",
            "last_updated": business.get('last_updated', '2024-01-01'),
            "util_today": util_today,
            "util_yesterday": util_yesterday,
            "util_7d": util_7d,
            "timeline": timeline,
            # 期間ごとの稼働率履歴を追加
            "history": history_data,
            # テンプレート用のプロパティを追加
            "working_rate": util_today,
            "previous_rate": util_yesterday,
            "weekly_rate": util_7d
        }
        
        # HTMLテンプレートをレンダリング
        return templates.TemplateResponse(
            "store_detail.html", 
            {
                "request": request, 
                "store": store_data,
                "user_permissions": user_permissions
            }
        )
        
    except Exception as e:
        print(f"❌ 店舗詳細取得エラー: {e}")
        raise HTTPException(status_code=500, detail="店舗詳細の取得に失敗しました")



@router.get("/{store_id}/working_trend", response_class=JSONResponse)
async def get_working_trend(
    request: Request,
    store_id: str,
    auth: bool = Depends(require_auth)
):
    """店舗の稼働推移データ取得"""
    
    # ユーザー権限を確認
    user_permissions = await check_user_permissions(request)
    
    try:
        # 実際のデータベースから店舗情報取得
        businesses = db.get_businesses()
        business = None
        
        # ダミーデータ用IDの場合はダミーデータを返す
        if store_id.startswith("dummy_"):
            dummy_index = int(store_id.replace("dummy_", "")) - 1
            store_data_list = [
                {"name": "チュチュバナナ", "blurred_name": "〇〇〇〇ナナ"},
                {"name": "ハニービー", "blurred_name": "〇〇〇ビー"},
                {"name": "バンサー", "blurred_name": "〇〇サー"},
                {"name": "ウルトラグレース", "blurred_name": "〇〇〇〇〇レース"},
                {"name": "メルティキス", "blurred_name": "〇〇〇キス"},
                {"name": "ピュアハート", "blurred_name": "〇〇〇ハート"},
                {"name": "シャイニーガール", "blurred_name": "〇〇〇〇ガール"},
                {"name": "エンジェルフェザー", "blurred_name": "〇〇〇〇〇フェザー"},
                {"name": "プリンセスルーム", "blurred_name": "〇〇〇〇〇ルーム"},
                {"name": "ルビーパレス", "blurred_name": "〇〇〇パレス"},
            ]
            
            if 0 <= dummy_index < len(store_data_list):
                store_info = store_data_list[dummy_index]
                business = {
                    "name": store_info["name"],
                    "blurred_name": store_info["blurred_name"],
                    "area": "ダミー地区",
                    "prefecture": "東京都",
                    "city": "新宿区",
                    "genre": "ソープランド"
                }
            else:
                business = {"name": f"ダミー店舗{dummy_index + 1}", "blurred_name": f"〇〇店舗{dummy_index + 1}", "area": "ダミー地区"}
        else:
            # 実際のIDの場合はDBから検索
            for key, biz in businesses.items():
                if str(biz.get('Business ID')) == store_id:
                    business = biz
                    break
        
        if not business:
            # 店舗が見つからない場合はダミーデータ
            business = {"name": f"店舗{store_id}", "blurred_name": f"〇〇{store_id}", "area": "不明"}
        
        # ダミーの稼働推移データを生成
        trend_data = generate_dummy_working_trend_data(store_id)
        
        # レスポンスデータ
        response_data = {
            "store_id": store_id,
            "store_name": business.get("name", "不明"),
            "trend_data": trend_data
        }
        
        return response_data
    
    except Exception as e:
        print(f"⚠️ 稼働推移データ取得エラー: {e}")
        # エラー時は空のデータを返す
        return {
            "store_id": store_id,
            "store_name": f"店舗{store_id}",
            "trend_data": {
                "labels": [],
                "data": []
            }
        }

@router.get("/{store_id}/working-trend", response_class=JSONResponse)
async def get_store_working_trend(
    request: Request,
    store_id: str,
    auth: bool = Depends(require_auth),
    db = Depends(get_database)
):
    """店舗の稼働推移データを取得"""
    try:
        print(f"🔍 稼働推移データ取得: store_id={store_id}")
        
        # 実際のstatus_historyテーブルからデータ取得を試行
        if not store_id.startswith("dummy_"):
            # 実際のDBからデータ取得
            query = """
            SELECT 
                biz_date,
                working_rate,
                EXTRACT(DOW FROM biz_date) as day_of_week
            FROM status_history 
            WHERE business_id = %s
            AND biz_date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY biz_date ASC
            """
            
            try:
                results = db.fetch_all(query, (int(store_id),))
                
                if results:
                    # 曜日別データに変換
                    weekday_data = [0] * 7  # 日曜〜土曜
                    weekday_names = ['日', '月', '火', '水', '木', '金', '土']
                    
                    for row in results:
                        day_of_week = int(row['day_of_week'])  # 0=日曜, 6=土曜
                        weekday_data[day_of_week] = float(row['working_rate'])
                    
                    print(f"✅ 実際のDBデータを使用: {weekday_data}")
                    return JSONResponse(content={
                        "success": True,
                        "labels": weekday_names,
                        "data": weekday_data,
                        "store_id": store_id,
                        "data_source": "database"
                    })
            except Exception as db_error:
                print(f"⚠️ DBエラー、ダミーデータにフォールバック: {db_error}")
        
        # データが見つからない場合はエラーを返す
        print(f"❌ 稼働推移データが見つかりません: store_id={store_id}")
        raise HTTPException(status_code=404, detail="稼働推移データが見つかりません")
        
    except Exception as e:
        print(f"❌ 稼働推移データ取得エラー: {e}")
        raise HTTPException(status_code=500, detail="稼働推移データの取得に失敗しました")
