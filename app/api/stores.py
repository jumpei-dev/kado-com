from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Any, Optional
import sys
import os

from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

from app.core.database import get_database
from app.core.auth_service import AuthService
from app.utils.blurred_name_utils import get_store_display_info
from app.utils.business_type_utils import convert_business_type_to_japanese

def get_working_rate(db, business_id: int, period: str) -> float:
    """指定された期間の稼働率を取得"""
    try:
        if period == 'today':
            query = """
            SELECT working_rate 
            FROM status_history 
            WHERE business_id = %s AND biz_date = CURRENT_DATE
            ORDER BY biz_date DESC LIMIT 1
            """
        elif period == 'yesterday':
            query = """
            SELECT working_rate 
            FROM status_history 
            WHERE business_id = %s AND biz_date = CURRENT_DATE - INTERVAL '1 day'
            ORDER BY biz_date DESC LIMIT 1
            """
        elif period == 'month':
            query = """
            SELECT CEIL(AVG(working_rate)) as working_rate
            FROM status_history 
            WHERE business_id = %s AND biz_date >= DATE_TRUNC('month', CURRENT_DATE)
            AND biz_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            """
        elif period == 'last_month':
            query = """
            SELECT AVG(working_rate) as working_rate
            FROM status_history 
            WHERE business_id = %s AND biz_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
            AND biz_date < DATE_TRUNC('month', CURRENT_DATE)
            """
        elif period == 'week':
            query = """
            SELECT AVG(working_rate) as working_rate
            FROM status_history 
            WHERE business_id = %s AND biz_date >= CURRENT_DATE - INTERVAL '7 days'
            """
        elif period == 'last_week':
            query = """
            SELECT AVG(working_rate) as working_rate
            FROM status_history 
            WHERE business_id = %s AND biz_date >= CURRENT_DATE - INTERVAL '14 days'
            AND biz_date < CURRENT_DATE - INTERVAL '7 days'
            """
        elif period == '2weeks_ago':
            query = """
            SELECT AVG(working_rate) as working_rate
            FROM status_history 
            WHERE business_id = %s AND biz_date >= CURRENT_DATE - INTERVAL '21 days'
            AND biz_date < CURRENT_DATE - INTERVAL '14 days'
            """
        elif period == '3weeks_ago':
            query = """
            SELECT AVG(working_rate) as working_rate
            FROM status_history 
            WHERE business_id = %s AND biz_date >= CURRENT_DATE - INTERVAL '28 days'
            AND biz_date < CURRENT_DATE - INTERVAL '21 days'
            """
        elif period == '4weeks_ago':
            query = """
            SELECT AVG(working_rate) as working_rate
            FROM status_history 
            WHERE business_id = %s AND biz_date >= CURRENT_DATE - INTERVAL '35 days'
            AND biz_date < CURRENT_DATE - INTERVAL '28 days'
            """
        else:
            return 0.0
            
        result = db.fetch_one(query, (business_id,))
        if result and result['working_rate'] is not None:
            return float(result['working_rate'])
        else:
            # データがない場合はnullを返す
            return None
            
    except Exception as e:
        print(f"❌ get_working_rate エラー: {e}")
        # エラー時はnullを返す
        return None

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
        print(f"❌ ユーザー権限確認エラー: {e}")
        return {
            "logged_in": False,
            "can_see_contents": False,
            "username": None,
            "is_admin": False
        }


@router.get("/ranking", response_class=JSONResponse)
async def get_store_ranking(
    request: Request,
    area: str = Query("all", description="エリアフィルター"),
    business_type: str = Query("all", description="業種フィルター"),
    spec: str = Query("all", description="仕様フィルター"),
    period: str = Query("month", description="期間フィルター"),
    limit: int = Query(20, description="取得件数", ge=1, le=100),
    offset: int = Query(0, description="オフセット", ge=0),
    auth: bool = Depends(require_auth),
    db = Depends(get_database)
):
    """店舗ランキングAPIエンドポイント"""
    try:
        # ユーザー権限を確認
        user_permissions = await check_user_permissions(request)
        can_see_contents = user_permissions.get('can_see_contents', False)
        
        # データベースからランキングデータを取得
        ranking_data = db.get_store_ranking(
            area=area,
            business_type=business_type,
            spec=spec,
            period=period,
            limit=limit,
            offset=offset
        )
        
        # 権限に応じて店舗名を処理
        processed_ranking = []
        for store in ranking_data:
            # blurred_name処理を適用
            store_info = {
                'name': store['name'],
                'blurred_name': store.get('blurred_name', store['name'])
            }
            display_info = get_store_display_info(store_info, can_see_contents)
            
            processed_store = {
                "business_id": store["business_id"],
                "name": display_info['display_name'],
                "blurred_name": display_info['blurred_name'],
                "is_blurred": display_info['is_blurred'],
                "area": store["area"],
                "prefecture": store["prefecture"],
                "type": convert_business_type_to_japanese(store["type"]),
                "cast_type": store["cast_type"],
                "avg_working_rate": store["avg_working_rate"]
            }
            processed_ranking.append(processed_store)
        
        return {
            "ranking": processed_ranking,
            "total": len(processed_ranking),
            "period": period,
            "filters": {
                "area": area,
                "business_type": business_type,
                "spec": spec
            }
        }
        
    except Exception as e:
        print(f"❌ ランキングデータ取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ランキングデータの取得に失敗しました")
        


@router.get("")
async def get_stores(
    request: Request,
    sort: str = Query("util_today", description="ソート基準"),
    page: int = Query(1, description="ページ番号", ge=1),
    page_size: int = Query(30, description="1ページあたりの表示件数", ge=1, le=50),
    area: str = Query("all", description="エリアフィルター"),
    genre: str = Query("all", description="業種フィルター"),
    period: str = Query("month", description="期間フィルター"),
    chart_period: str = Query("7days", description="グラフ期間フィルター (7days, 2months)"),
    include_chart_data: bool = Query(False, description="全体稼働推移データを含めるか"),
    auth: bool = Depends(require_auth),
    db = Depends(get_database)
):
    """店舗一覧取得 - HTMLレスポンス (ページネーション対応) + 全体稼働推移データ"""
    
    # ユーザー権限を確認
    user_permissions = await check_user_permissions(request)
    print(f"🔍 [DEBUG] 店舗一覧リクエスト: page={page}, area={area}, genre={genre}, period={period}, user_permissions={user_permissions}")
    print(f"🔍 [DEBUG] リクエストヘッダー: {dict(request.headers)}")
    print(f"🔍 [DEBUG] クッキー: {dict(request.cookies)}")
    
    try:
        # ランキングAPIを使用してデータを取得
        print("📊 [DEBUG] ランキングAPIから店舗データを取得中...")
        ranking_data = db.get_store_ranking(
            area=area,
            business_type=genre,
            spec="all",
            period=period,
            limit=100,  # 十分な数を取得してからページング
            offset=0
        )
        print(f"📊 [DEBUG] ランキングデータ取得完了: {len(ranking_data)}件")
        
        # レスポンス形式に変換
        stores = []
        can_see_contents = user_permissions.get('can_see_contents', False)
        print(f"🔍 [DEBUG] blurred_name処理開始: can_see_contents={can_see_contents}")
        
        for idx, store_data in enumerate(ranking_data):
            # blurred_name処理を適用
            store_info = {
                'name': store_data['name'],
                'blurred_name': store_data.get('blurred_name', store_data['name'])
            }
            display_info = get_store_display_info(store_info, can_see_contents)
            
            # 期間に応じた稼働率を取得
            avg_working_rate = store_data['avg_working_rate']
            
            # 期間が「今月」の場合は先月データを取得、それ以外は同じ値を使用
            if period == "month":
                last_month_rate = get_working_rate(db, store_data['business_id'], 'last_month')
                previous_rate = last_month_rate if last_month_rate is not None else avg_working_rate
            else:
                previous_rate = avg_working_rate
            
            stores.append({
                "id": str(store_data['business_id']),
                "name": display_info['display_name'],
                "original_name": store_data['name'],
                "blurred_name": display_info['blurred_name'],
                "is_blurred": display_info['is_blurred'],
                "prefecture": store_data['prefecture'],
                "city": store_data.get('city', '不明'),
                "area": store_data['area'],
                "genre": convert_business_type_to_japanese(store_data['type']),
                "status": "active",
                "last_updated": "2024-01-01",
                "util_today": avg_working_rate,
                "util_yesterday": avg_working_rate,
                "util_7d": avg_working_rate,
                # カードテンプレート用のプロパティを追加
                "working_rate": avg_working_rate,
                "previous_rate": previous_rate,
                "weekly_rate": previous_rate,  # テンプレートとの互換性のため
                "rank": idx + 1,
                "current_period": period  # 現在の期間フィルターを追加
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
        
        # 全体稼働推移データを取得（include_chart_dataがTrueの場合）
        chart_data = None
        if include_chart_data:
            try:
                print(f"🔍 全体稼働推移データ取得: chart_period={chart_period}, area={area}, genre={genre}")
                
                # フィルター条件を構築
                where_conditions = ["b.in_scope = true"]
                params = []
                
                if area != "all":
                    where_conditions.append("b.area = %s")
                    params.append(area)
                    
                if genre != "all":
                    where_conditions.append("b.type = %s")
                    params.append(genre)
                
                where_clause = " AND ".join(where_conditions)
                
                # 期間に応じてクエリを変更
                if chart_period == "2months":
                    # 2ヶ月間の週次データ
                    query = f"""
                    SELECT 
                        DATE_TRUNC('week', sh.biz_date) as week_start,
                        AVG(sh.working_rate) as working_rate
                    FROM status_history sh
                    JOIN business b ON sh.business_id = b.business_id
                    WHERE {where_clause}
                    AND sh.biz_date >= CURRENT_DATE - INTERVAL '8 weeks'
                    AND sh.biz_date < CURRENT_DATE
                    GROUP BY DATE_TRUNC('week', sh.biz_date)
                    ORDER BY week_start ASC
                    """
                else:
                    # 7日間の日次データ（デフォルト）
                    query = f"""
                    SELECT 
                        sh.biz_date,
                        AVG(sh.working_rate) as working_rate
                    FROM status_history sh
                    JOIN business b ON sh.business_id = b.business_id
                    WHERE {where_clause}
                    AND sh.biz_date >= CURRENT_DATE - INTERVAL '7 days'
                    AND sh.biz_date < CURRENT_DATE
                    GROUP BY sh.biz_date
                    ORDER BY sh.biz_date ASC
                    """
                
                results = db.execute_query(query, params)
                
                if results:
                    # データを整形
                    labels = []
                    data = []
                    
                    for row in results:
                        if chart_period == "2months":
                            # 週次データの場合
                            week_start = row["week_start"]
                            week_end = week_start + timedelta(days=6)
                            labels.append(f"{week_start.strftime('%m/%d')}-{week_end.strftime('%m/%d')}")
                        else:
                            # 日次データの場合
                            labels.append(row["biz_date"].strftime("%m/%d"))
                        
                        working_rate = float(row["working_rate"]) if row["working_rate"] else 0
                        data.append(round(working_rate, 1))
                    
                    chart_data = {
                        "success": True,
                        "labels": labels,
                        "data": data,
                        "period": chart_period,
                        "filters": {"area": area, "genre": genre}
                    }
                    print(f"✅ 全体稼働推移データ取得完了: {len(results)}件")
                else:
                    chart_data = {
                        "success": True,
                        "labels": [],
                        "data": [],
                        "message": "データが見つかりません"
                    }
                    
            except Exception as e:
                print(f"❌ 全体稼働推移データ取得エラー: {e}")
                chart_data = {
                    "success": False,
                    "error": "全体稼働推移データの取得に失敗しました",
                    "details": str(e)
                }
        
        # HTMLテンプレートをレンダリングして返す
        template_context = {
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
            },
            "filters": {
                "area": area,
                "genre": genre,
                "period": period,
                "sort": sort,
                "chart_period": chart_period
            }
        }
        
        # 全体稼働推移データが含まれる場合は追加
        if chart_data:
            template_context["chart_data"] = chart_data
        
        # Acceptヘッダーをチェックしてレスポンス形式を決定
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header:
            # JSONレスポンスを返す
            response_data = {
                "stores": [{
                    "id": store["id"],
                    "name": store["name"],
                    "area": store["area"],
                    "genre": store["genre"],
                    "working_rate": store["working_rate"],
                    "weekly_rate": store["weekly_rate"],
                    "util_today": store["util_today"]
                } for store in paged_stores],
                "pagination": template_context["pagination"],
                "filters": template_context["filters"]
            }
            
            if chart_data:
                response_data["chart_data"] = chart_data
                
            return JSONResponse(content=response_data)
        else:
            # HTMLレスポンスを返す
            return templates.TemplateResponse(
                "components/stores_list.html", 
                template_context
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
    """店舗詳細ページを表示"""
    try:
        # ユーザー権限を確認
        user_permissions = await check_user_permissions(request)
        
        # 新しいロジック: database.pyのget_store_detailsメソッドを使用
        try:
            print(f"🔍 [NEW_LOGIC] 新しいロジックで店舗ID {store_id} の詳細を取得中...")
            store_details = await db.get_store_details(int(store_id))
            print(f"🔍 [NEW_LOGIC] 取得結果: {store_details}")
            
            if store_details:
                print(f"🔍 [NEW_LOGIC] area_avg_rate: {store_details.get('area_avg_rate')}")
                print(f"🔍 [NEW_LOGIC] genre_avg_rate: {store_details.get('genre_avg_rate')}")
                
                # 店舗名表示制御
                name_display = get_store_display_info(store_details, user_permissions["can_see_contents"])
                
                store_data = {
                    "id": store_id,
                    "name": name_display["display_name"],
                    "original_name": name_display["original_name"],
                    "blurred_name": name_display["blurred_name"],
                    "is_blurred": name_display["is_blurred"],
                    "prefecture": store_details.get('prefecture', '不明'),
                    "city": store_details.get('city', '不明'),
                    "area": store_details.get('area', '不明'),
                    "genre": convert_business_type_to_japanese(store_details.get('type', '')),
                    "status": "active" if store_details.get('in_scope') else "inactive",
                    "last_updated": store_details.get('updated_at', '2024-01-01'),
                    "util_today": store_details.get('working_rate', 0),
                    "util_yesterday": store_details.get('working_rate', 0),
                    "util_7d": store_details.get('working_rate', 0),
                    "timeline": store_details.get('timeline', []),
                    "history": store_details.get('history', []),
                    "working_rate": store_details.get('working_rate', 0),
                    "previous_rate": store_details.get('working_rate', 0),
                    "weekly_rate": store_details.get('working_rate', 0),
                    "area_average": store_details.get('area_avg_rate', 0),
                    "industry_average": store_details.get('genre_avg_rate', 0)
                }
                
                print(f"🔍 [NEW_LOGIC] 最終的なstore_data.area_average: {store_data['area_average']}")
                print(f"🔍 [NEW_LOGIC] 最終的なstore_data.industry_average: {store_data['industry_average']}")
                
                # HTMLテンプレートをレンダリング
                return templates.TemplateResponse(
                    "store_detail.html", 
                    {
                        "request": request, 
                        "store": store_data,
                        "user_permissions": user_permissions
                    }
                )
        except Exception as new_logic_error:
            print(f"⚠️ 新しいロジックでエラー発生、古いロジックにフォールバック: {new_logic_error}")
            import traceback
            print(f"⚠️ エラー詳細: {traceback.format_exc()}")
        
        # 古いロジック（フォールバック）: 既存の実装を維持
        # Debug log for store_id
        print(f"🔍 [STORE_DETAIL] Received store_id: {store_id}")
        print(f"🔍 [STORE_DETAIL] Request URL: {request.url}")
        print(f"🔍 [STORE_DETAIL] Request method: {request.method}")
        
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
                print(f"[DEBUG] Business type data: {biz.get('type')}, Type: {biz.get('Type')}, genre: {biz.get('genre')}")
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
        
        # 実際の稼働率データを取得
        business_id = int(store_id)
        util_today = get_working_rate(db, business_id, 'today')
        util_yesterday = get_working_rate(db, business_id, 'yesterday')
        util_7d = get_working_rate(db, business_id, 'week')
        util_month = get_working_rate(db, business_id, 'month')
        
        # 履歴データも実際のデータから生成
        history_data = [
            {"label": "今週", "rate": util_7d},
            {"label": "先週", "rate": get_working_rate(db, business_id, 'last_week')},
            {"label": "2週間前", "rate": get_working_rate(db, business_id, '2weeks_ago')},
            {"label": "3週間前", "rate": get_working_rate(db, business_id, '3weeks_ago')},
            {"label": "4週間前", "rate": get_working_rate(db, business_id, '4weeks_ago')}
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
            "genre": convert_business_type_to_japanese(business.get('type', business.get('Type', business.get('genre', '')))),
            "status": "active" if business.get('in_scope') else "inactive",
            "last_updated": business.get('last_updated', '2024-01-01'),
            "util_today": util_today,
            "util_yesterday": util_yesterday,
            "util_7d": util_7d,
            "timeline": timeline,
            # 期間ごとの稼働率履歴を追加
            "history": history_data,
            # テンプレート用のプロパティを追加
            "working_rate": util_month,
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



# 古い重複エンドポイントを削除しました
# 新しい /{store_id}/working-trend エンドポイントを使用してください

# 専用の /overall-working-trend エンドポイントは削除されました
# 全体稼働推移データは統合された /api/stores エンドポイントから取得してください
# include_chart_data=true パラメータを使用することで、チャートデータが含まれます


@router.get("/{store_id}/working-trend", response_class=JSONResponse)
async def get_store_working_trend(
    request: Request,
    store_id: str,
    period: str = Query("7days", description="期間フィルター (7days, 2months)"),
    auth: bool = Depends(require_auth),
    db = Depends(get_database)
):
    """店舗の稼働推移データを取得"""
    try:
        print(f"🔍 稼働推移データ取得: store_id={store_id}, period={period}")
        
        # 実際のstatus_historyテーブルからデータ取得を試行
        if not store_id.startswith("dummy_"):
            # 期間に応じてクエリを変更
            if period == "2months":
                # 2ヶ月間の週次データ - 前日まで
                query = """
                SELECT 
                    DATE_TRUNC('week', biz_date) as week_start,
                    AVG(working_rate) as working_rate
                FROM status_history 
                WHERE business_id = %s
                AND biz_date >= CURRENT_DATE - INTERVAL '8 weeks'
                AND biz_date < CURRENT_DATE
                GROUP BY DATE_TRUNC('week', biz_date)
                ORDER BY week_start ASC
                """
            else:
                # 7日間の日次データ（デフォルト）- 前日まで
                query = """
                SELECT 
                    biz_date,
                    working_rate,
                    EXTRACT(DOW FROM biz_date) as day_of_week
                FROM status_history 
                WHERE business_id = %s
                AND biz_date >= CURRENT_DATE - INTERVAL '7 days'
                AND biz_date < CURRENT_DATE
                ORDER BY biz_date ASC
                """
            
            try:
                results = db.fetch_all(query, (int(store_id),))
                
                if period == "2months":
                    # 2ヶ月間の週次データ処理 - 8週間分のラベルを生成
                    labels = []
                    data = []
                    
                    # 8週間分のラベルを生成（最新の週が右端、前日まで）
                    end_date = datetime.now().date() - timedelta(days=1)  # 前日まで
                    for i in range(7, -1, -1):  # 8週間前から今日まで
                        week_start = end_date - timedelta(weeks=i, days=end_date.weekday())
                        week_end = week_start + timedelta(days=6)
                        # 週の終了日が今日を超えないように制限
                        if week_end > end_date:
                            week_end = end_date
                        labels.append(f"{week_start.strftime('%m/%d')}-{week_end.strftime('%m/%d')}")
                        data.append(None)  # 初期値はnull
                    
                    # 実際のデータがあれば対応する週に配置
                    if results:
                        for row in results:
                            week_start = row['week_start']
                            if hasattr(week_start, 'date'):
                                week_start_date = week_start.date()
                            else:
                                week_start_date = week_start
                            
                            # 該当する週のインデックスを見つける
                            for i, label in enumerate(labels):
                                label_start_str = label.split('-')[0]
                                # 年を正しく設定
                                current_year = datetime.now().year
                                label_start = datetime.strptime(f"{current_year}/{label_start_str}", '%Y/%m/%d').date()
                                
                                if label_start == week_start_date:
                                    data[i] = float(row['working_rate']) if row['working_rate'] else None
                                    break
                    
                    data_count = sum(1 for x in data if x is not None)
                    
                    return JSONResponse(content={
                        "success": True,
                        "labels": labels,
                        "data": data,
                        "store_id": store_id,
                        "data_source": "database",
                        "data_count": data_count,
                        "total_days": len(labels),
                        "period": period
                    })
                else:
                    # 7日間の日次データ処理 - 7日分のラベルを生成
                    labels = []
                    data = []
                    
                    # 7日分のラベルを生成（最新の日が右端、前日まで）
                    end_date = datetime.now().date() - timedelta(days=1)  # 前日まで
                    for i in range(6, -1, -1):  # 7日前から前日まで
                        date = end_date - timedelta(days=i)
                        labels.append(date.strftime('%m/%d'))
                        data.append(None)  # 初期値はnull
                    
                    # 実際のデータがあれば対応する日に配置
                    if results:
                        for row in results:
                            biz_date = row['biz_date']
                            # 該当する日のインデックスを見つける
                            for i, label in enumerate(labels):
                                label_date = datetime.strptime(f"{datetime.now().year}/{label}", '%Y/%m/%d').date()
                                if label_date == biz_date:
                                    data[i] = float(row['working_rate']) if row['working_rate'] else None
                                    break
                    
                    data_count = sum(1 for x in data if x is not None)
                    print(f"✅ 7日間データ: labels={labels}, data={data}")
                
                return JSONResponse(content={
                    "success": True,
                    "labels": labels,
                    "data": data,
                    "store_id": store_id,
                    "data_source": "database",
                    "data_count": data_count,
                    "total_days": len(labels),
                    "period": period
                })
                
            except Exception as db_error:
                print(f"⚠️ DBエラー、空データを返す: {db_error}")
                # エラー時は空のデータを返す
                labels = []
                data = []
                
                return JSONResponse(content={
                    "success": True,
                    "labels": labels,
                    "data": data,
                    "store_id": store_id,
                    "data_source": "error_fallback",
                    "data_count": len(data),
                    "total_days": len(data),
                    "period": period,
                    "error": "データ取得エラーが発生しました"
                })
        
        # データが見つからない場合は空のレスポンスを返す
        print(f"⚠️ データが見つかりません: store_id={store_id}, period={period}")
        
        return JSONResponse(content={
            "success": False,
            "labels": [],
            "data": [],
            "store_id": store_id,
            "data_source": "no_data",
            "data_count": 0,
            "total_days": 0,
            "period": period,
            "message": "データが見つかりませんでした"
        })
        
    except Exception as e:
        print(f"❌ 稼働推移データ取得エラー: {e}")
        
        return JSONResponse(content={
            "success": False,
            "labels": [],
            "data": [],
            "store_id": store_id,
            "data_source": "error",
            "data_count": 0,
            "total_days": 0,
            "period": period,
            "error": "稼働推移データの取得に失敗しました"
        })
