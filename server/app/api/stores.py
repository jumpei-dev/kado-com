from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
from ..core.database import get_database

router = APIRouter(prefix="/stores", tags=["stores"])
security = HTTPBearer()

def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """認証チェック (開発版は常にOK)"""
    return True

@router.get("")
async def get_stores(
    sort: str = Query("util_today", description="ソート基準"),
    auth: bool = Depends(require_auth),
    db = Depends(get_database)
) -> Dict[str, Any]:
    """店舗一覧取得"""
    
    try:
        # 実際のデータベースから取得
        businesses = db.get_businesses()
        
        # レスポンス形式に変換
        stores = []
        for key, business in businesses.items():
            if business.get('in_scope', False):  # 管理対象店舗のみ
                stores.append({
                    "id": str(business.get('Business ID')),
                    "name": business.get('name', '不明'),
                    "prefecture": business.get('prefecture', '不明'),
                    "city": business.get('city', '不明'), 
                    "area": business.get('area', '不明'),
                    "genre": business.get('genre', '一般'),
                    "status": "active" if business.get('in_scope') else "inactive",
                    "last_updated": business.get('last_updated', '2024-01-01'),
                    "util_today": 72.5,  # TODO: 実際の稼働率を計算
                    "util_yesterday": 65.3,
                    "util_7d": 68.9
                })
        
        # ソート処理
        if sort == "util_today":
            stores.sort(key=lambda x: x.get("util_today", 0), reverse=True)
        elif sort == "name":
            stores.sort(key=lambda x: x.get("name", ""))
        
        return {
            "items": stores,
            "total": len(stores)
        }
        
    except Exception as e:
        # フォールバック: 開発用ダミーデータ
        print(f"⚠️ DB取得エラー、ダミーデータを返します: {e}")
        
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
                "util_today": 72.5
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
                "util_today": 61.2
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
                "util_today": 48.8
            },
        ]
        
        return {"items": stores, "total": len(stores)}

@router.get("/{store_id}")
async def get_store_detail(
    store_id: str,
    auth: bool = Depends(require_auth),
    db = Depends(get_database)
) -> Dict[str, Any]:
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
        
        return {
            "id": store_id,
            "name": business.get('name', f"店舗{store_id}"),
            "prefecture": business.get('prefecture', '不明'),
            "city": business.get('city', '不明'),
            "area": business.get('area', '不明'),
            "genre": business.get('genre', '一般'),
            "status": "active" if business.get('in_scope') else "inactive",
            "last_updated": business.get('last_updated', '2024-01-01'),
            "util_today": 72.5,  # TODO: 実際の稼働率計算
            "util_yesterday": 65.3,
            "util_7d": 68.9,
            "timeline": timeline
        }
        
    except Exception as e:
        print(f"⚠️ 店舗詳細取得エラー: {e}")
        # フォールバック
        timeline = [{"slot": f"{h:02d}:00", "active": h % 3 != 0} for h in range(24)]
        return {
            "id": store_id,
            "name": f"店舗{store_id}",
            "prefecture": "不明",
            "city": "不明", 
            "area": "不明",
            "genre": "一般",
            "status": "active",
            "last_updated": "2024-01-01",
            "util_today": 72.5,
            "timeline": timeline
        }
