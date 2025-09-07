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
    auth: bool = Depends(require_auth),
    db = Depends(get_database)
):
    """店舗一覧取得 - HTMLレスポンス"""
    
    try:
        # 実際のデータベースから取得
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
        
        # HTMLテンプレートをレンダリングして返す
        return templates.TemplateResponse(
            "components/stores_list.html", 
            {"request": request, "stores": stores}
        )
        
    except Exception as e:
        # フォールバック: 開発用ダミーデータ
        print(f"⚠️ DB取得エラー、ダミーデータを返します: {e}")
        
        # フォールバック用のデータ
        stores = [
            {
                "id": "1", 
                "name": "店舗A", 
                "prefecture": "東京都",
                "city": "新宿区",
                "area": "新宿", 
                "genre": "一般", 
                "status": "active",
                "last_updated": "2024-09-06",
                "util_today": 72.5,
                "util_yesterday": 65.3,
                "util_7d": 68.9,
                # カードテンプレート用のプロパティを追加
                "working_rate": 72.5,
                "previous_rate": 65.3,
                "weekly_rate": 68.9
            },
            {
                "id": "2", 
                "name": "店舗B", 
                "prefecture": "東京都",
                "city": "渋谷区", 
                "area": "渋谷", 
                "genre": "一般", 
                "status": "active",
                "last_updated": "2024-09-06",
                "util_today": 61.2,
                "util_yesterday": 55.8,
                "util_7d": 59.5,
                # カードテンプレート用のプロパティを追加
                "working_rate": 61.2,
                "previous_rate": 55.8,
                "weekly_rate": 59.5
            },
            {
                "id": "3", 
                "name": "店舗C", 
                "prefecture": "東京都",
                "city": "豊島区",
                "area": "池袋", 
                "genre": "一般", 
                "status": "active",
                "last_updated": "2024-09-06",
                "util_today": 48.8,
                "util_yesterday": 52.1,
                "util_7d": 50.3,
                # カードテンプレート用のプロパティを追加
                "working_rate": 48.8,
                "previous_rate": 52.1,
                "weekly_rate": 50.3
            },
        ]
        
        # HTMLテンプレートをレンダリング
        return templates.TemplateResponse(
            "components/stores_list.html", 
            {"request": request, "stores": stores}
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
