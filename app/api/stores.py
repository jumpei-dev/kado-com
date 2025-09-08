from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any, Optional
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

from app.core.database import get_database

# テンプレートの設定
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir.absolute()))

router = APIRouter(prefix="/api/stores", tags=["stores"])
security = HTTPBearer(auto_error=False)

def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """認証チェック (開発版は常にOK)"""
    return True

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
    
    try:
        # ランキング表示の開発用にDBエラーを強制発生させる
        if True:  # 常にダミーデータを使用するためのフラグ
            print("🔧 ランキング表示開発中: ダミーデータを使用します")
            raise Exception("開発用にダミーデータを表示")
            
        # 実際のデータベースから取得（上記エラーのため実行されない）
        businesses = db.get_businesses()
        
        # レスポンス形式に変換
        stores = []
        for key, business in businesses.items():
            if business.get('in_scope', False):  # 管理対象店舗のみ
                # 稼働率の値をカードテンプレートで使われる名前に合わせる
                util_today = 72.5  # TODO: 実際の稼働率を計算
                util_yesterday = 65.3
                util_7d = 68.9
                
                stores.append({
                    "id": str(business.get('Business ID')),
                    "name": business.get('name', '不明'),
                    "prefecture": business.get('prefecture', '不明'),
                    "city": business.get('city', '不明'), 
                    "area": business.get('area', '不明'),
                    "genre": business.get('genre', '一般'),
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
        # フォールバック: 開発用ダミーデータ
        print(f"⚠️ DB取得エラー、ダミーデータを返します: {e}")
        
        # フォールバック用のデータ - 50店舗のダミーデータ
        import random
        
        # 店舗名リスト
        store_names = [
            "チュチュバナナ", "ハニービー", "バンサー", "ウルトラグレース", "メルティキス", 
            "ピュアハート", "シャイニーガール", "エンジェルフェザー", "プリンセスルーム", "ルビーパレス",
            "シルクロード", "ゴールデンタイム", "ダイヤモンドクイーン", "パラダイスガーデン", "エターナルラブ",
            "パッションフルーツ", "スターダスト", "ミルキーウェイ", "サンシャイン", "ムーンライト",
            "フェアリーテイル", "クリスタルパレス", "サクラ", "ロイヤルハウス", "ドリームキャッスル",
            "人妻城", "プラチナガール", "セレブリティ", "ゴージャスタイム", "ラグジュアリー",
            "エレガントローズ", "スウィートハート", "アロマテラス", "ブロッサム", "オーシャンビュー",
            "カルネーション", "ホワイトリリー", "ブルーローズ", "レッドチェリー", "ゴールドラッシュ",
            "シルバームーン", "プラチナスター", "サファイアブルー", "ルビーレッド", "エメラルドグリーン",
            "パールホワイト", "オニキスブラック", "アンバーオレンジ", "アクアマリン", "トパーズイエロー"
        ]
        
        # エリア情報 (フィルターの選択肢に合わせる)
        areas = [
            # 関東エリア
            {"prefecture": "東京都", "city": "新宿区", "area": "新宿", "region": "関東"},
            {"prefecture": "東京都", "city": "渋谷区", "area": "渋谷", "region": "関東"},
            {"prefecture": "東京都", "city": "豊島区", "area": "池袋", "region": "関東"},
            {"prefecture": "東京都", "city": "台東区", "area": "上野", "region": "関東"},
            {"prefecture": "東京都", "city": "千代田区", "area": "秋葉原", "region": "関東"},
            {"prefecture": "東京都", "city": "港区", "area": "六本木", "region": "関東"},
            {"prefecture": "神奈川県", "city": "横浜市", "area": "横浜", "region": "関東"},
            {"prefecture": "埼玉県", "city": "さいたま市", "area": "大宮", "region": "関東"},
            {"prefecture": "千葉県", "city": "千葉市", "area": "千葉", "region": "関東"},
            
            # 関西エリア
            {"prefecture": "大阪府", "city": "大阪市中央区", "area": "難波", "region": "関西"},
            {"prefecture": "大阪府", "city": "大阪市北区", "area": "梅田", "region": "関西"},
            {"prefecture": "大阪府", "city": "大阪市浪速区", "area": "新世界", "region": "関西"},
            {"prefecture": "京都府", "city": "京都市", "area": "祇園", "region": "関西"},
            {"prefecture": "兵庫県", "city": "神戸市", "area": "三宮", "region": "関西"},
            {"prefecture": "奈良県", "city": "奈良市", "area": "奈良", "region": "関西"},
            
            # 中部エリア
            {"prefecture": "愛知県", "city": "名古屋市中区", "area": "栄", "region": "中部"},
            {"prefecture": "愛知県", "city": "名古屋市中村区", "area": "名駅", "region": "中部"},
            {"prefecture": "静岡県", "city": "静岡市", "area": "静岡", "region": "中部"},
            {"prefecture": "新潟県", "city": "新潟市", "area": "新潟", "region": "中部"},
            
            # 北海道・東北エリア
            {"prefecture": "北海道", "city": "札幌市中央区", "area": "すすきの", "region": "北海道・東北"},
            {"prefecture": "宮城県", "city": "仙台市青葉区", "area": "国分町", "region": "北海道・東北"},
            {"prefecture": "青森県", "city": "青森市", "area": "青森", "region": "北海道・東北"},
            {"prefecture": "岩手県", "city": "盛岡市", "area": "盛岡", "region": "北海道・東北"},
            
            # 中国・四国エリア
            {"prefecture": "広島県", "city": "広島市中区", "area": "流川", "region": "中国・四国"},
            {"prefecture": "岡山県", "city": "岡山市", "area": "岡山", "region": "中国・四国"},
            {"prefecture": "香川県", "city": "高松市", "area": "中央町", "region": "中国・四国"},
            {"prefecture": "愛媛県", "city": "松山市", "area": "松山", "region": "中国・四国"},
            
            # 九州・沖縄エリア
            {"prefecture": "福岡県", "city": "福岡市博多区", "area": "博多", "region": "九州・沖縄"},
            {"prefecture": "福岡県", "city": "福岡市中央区", "area": "天神", "region": "九州・沖縄"},
            {"prefecture": "長崎県", "city": "長崎市", "area": "長崎", "region": "九州・沖縄"},
            {"prefecture": "沖縄県", "city": "那覇市", "area": "那覇", "region": "九州・沖縄"}
        ]
        
        # 業種リスト
        genres = ["ソープランド", "ヘルス", "デリヘル", "キャバクラ", "ピンサロ"]
        
        # ダミーデータ生成
        stores = []
        for i in range(50):
            # 基本となる稼働率をランダムに設定（40%〜95%）
            base_rate = round(random.uniform(40, 95), 1)
            
            # 期間に応じた稼働率を生成
            daily_rate = round(base_rate + random.uniform(-10, 10), 1)
            weekly_rate = round(base_rate + random.uniform(-5, 5), 1)
            monthly_rate = round(base_rate + random.uniform(-3, 3), 1)
            three_month_rate = round(base_rate + random.uniform(-2, 2), 1)
            six_month_rate = base_rate
            
            # 使用する稼働率を期間に応じて選択
            if period == "day":
                working_rate = daily_rate
            elif period == "week":
                working_rate = weekly_rate
            elif period == "month":
                working_rate = monthly_rate
            elif period == "three_months":
                working_rate = three_month_rate
            elif period == "six_months":
                working_rate = six_month_rate
            else:
                working_rate = base_rate
                
            # 前日比のための値
            previous_rate = round(working_rate + random.uniform(-8, 8), 1)
            
            # エリア情報をランダムに選択
            area_info = random.choice(areas)
            
            stores.append({
                "id": str(i + 1),
                "name": store_names[i] if i < len(store_names) else f"店舗{i + 1}",
                "prefecture": area_info["prefecture"],
                "city": area_info["city"],
                "area": area_info["area"],
                "region": area_info["region"],
                "genre": random.choice(genres),
                "status": "active",
                "last_updated": "2025-09-08",
                "util_today": daily_rate,
                "util_yesterday": previous_rate,
                "util_7d": weekly_rate,
                # カードテンプレート用のプロパティを追加
                "working_rate": working_rate,
                "previous_rate": previous_rate,
                "weekly_rate": weekly_rate
            })
            
        # 稼働率で降順ソート
        stores.sort(key=lambda x: x["working_rate"], reverse=True)
        
        # エリアでフィルタリング
        if area and area != "all":
            stores = [store for store in stores if store["region"] == area]
            
        # ジャンルでフィルタリング
        if genre and genre != "all":
            stores = [store for store in stores if store["genre"] == genre]
            
        # ランクでフィルタリング
        if rank and rank != "all":
            if rank == "under100":
                stores = [store for store in stores if store["working_rate"] < 100]
            elif rank == "over100":
                stores = [store for store in stores if store["working_rate"] >= 100]
        
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
        
        # ランク情報を追加
        for i, store in enumerate(paged_stores):
            store["rank"] = start_idx + i + 1
        
        # HTMLテンプレートをレンダリング
        return templates.TemplateResponse(
            "components/stores_list.html", 
            {
                "request": request, 
                "stores": paged_stores,
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

@router.get("/{store_id}", response_class=HTMLResponse)
async def get_store_detail(
    request: Request,
    store_id: str,
    auth: bool = Depends(require_auth),
    db = Depends(get_database)
):
    """店舗詳細取得"""
    
    try:
        # 実際のデータベースから店舗情報取得
        businesses = db.get_businesses()
        business = None
        
        for key, biz in businesses.items():
            if str(biz.get('Business ID')) == store_id:
                business = biz
                break
        
        if not business:
            # 店舗が見つからない場合はダミーデータ
            business = {"name": f"店舗{store_id}", "area": "不明"}
        
        # 24時間のタイムライン生成（TODO: 実際のstatus_historyから取得）
        timeline = []
        for hour in range(24):
            timeline.append({
                "slot": f"{hour:02d}:00",
                "active": hour % 3 != 0,
                "working_count": max(0, 5 - (hour % 4)),
                "total_count": 6
            })
        
        # 稼働率の値
        util_today = 72.5  # TODO: 実際の稼働率を計算
        util_yesterday = 65.3
        util_7d = 68.9
        
        # 店舗情報をまとめる
        store_data = {
            "id": store_id,
            "name": business.get('name', f"店舗{store_id}"),
            "prefecture": business.get('prefecture', '不明'),
            "city": business.get('city', '不明'),
            "area": business.get('area', '不明'),
            "genre": business.get('genre', '一般'),
            "status": "active" if business.get('in_scope') else "inactive",
            "last_updated": business.get('last_updated', '2024-01-01'),
            "util_today": util_today,
            "util_yesterday": util_yesterday,
            "util_7d": util_7d,
            "timeline": timeline,
            # 期間ごとの稼働率履歴を追加
            "history": [
                {"label": "今週", "rate": 72.5},
                {"label": "先週", "rate": 65.3},
                {"label": "2週間前", "rate": 68.9},
                {"label": "3週間前", "rate": 59.7},
                {"label": "4週間前", "rate": 63.2}
            ],
            # テンプレート用のプロパティを追加
            "working_rate": util_today,
            "previous_rate": util_yesterday,
            "weekly_rate": util_7d
        }
        
        # HTMLテンプレートをレンダリング
        return templates.TemplateResponse(
            "components/store_detail.html", 
            {"request": request, "store": store_data}
        )
        
    except Exception as e:
        print(f"⚠️ 店舗詳細取得エラー: {e}")
        # フォールバック
        timeline = [{"slot": f"{h:02d}:00", "active": h % 3 != 0} for h in range(24)]
        # 稼働率の値
        util_today = 72.5
        util_yesterday = 65.3
        util_7d = 68.9
        
        # フォールバック用の店舗データ
        store_data = {
            "id": store_id,
            "name": f"店舗{store_id}",
            "prefecture": "不明",
            "city": "不明", 
            "area": "不明",
            "genre": "一般",
            "status": "active",
            "last_updated": "2024-01-01",
            "util_today": util_today,
            "util_yesterday": util_yesterday,
            "util_7d": util_7d,
            "timeline": timeline,
            # 期間ごとの稼働率履歴を追加
            "history": [
                {"label": "今週", "rate": 72.5},
                {"label": "先週", "rate": 65.3},
                {"label": "2週間前", "rate": 68.9},
                {"label": "3週間前", "rate": 59.7},
                {"label": "4週間前", "rate": 63.2}
            ],
            # テンプレート用のプロパティを追加
            "working_rate": util_today,
            "previous_rate": util_yesterday,
            "weekly_rate": util_7d
        }
        
        # HTMLテンプレートをレンダリング
        return templates.TemplateResponse(
            "components/store_detail.html", 
            {"request": request, "store": store_data}
        )
