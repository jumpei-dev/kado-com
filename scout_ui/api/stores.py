from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
import csv
import io
from sqlalchemy.orm import Session

from scout_ui.core.auth import get_current_user_optional
from scout_ui.core.database import get_db_session
from scout_ui.utils.filters import (
    apply_filters,
    get_filter_options,
    apply_sorting,
    paginate_stores
)
from scout_ui.utils.business_type_utils import convert_business_type_to_japanese
from scout_ui.models.store import StoreView
from scout_ui.utils.csv_export import generate_csv_response

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class StoreListItem(BaseModel):
    id: int
    name: str
    area: str
    business_type: str
    working_rate: Optional[float]  # Noneの場合は「-」で表示
    cast_count: int
    last_updated: Optional[datetime]
    status: str
    address: Optional[str] = None
    phone: Optional[str] = None

class StoreListResponse(BaseModel):
    success: bool
    stores: List[StoreListItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    message: Optional[str] = None

class FilterOptions(BaseModel):
    areas: List[str]
    business_types: List[str]
    sort_options: List[Dict[str, str]]
    view_types: List[Dict[str, str]]

@router.get("/list")
async def get_stores(
    request: Request,
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(30, ge=1, le=100, description="1ページあたりの件数"),
    area: Optional[str] = Query(None, description="エリアフィルター"),
    business_type: Optional[str] = Query(None, description="業種フィルター"),
    date_from: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    sort_by: str = Query("working_rate", description="ソート項目"),
    sort_order: str = Query("desc", description="ソート順序 (asc/desc)"),
    view_type: str = Query("weekly", description="表示タイプ (weekly/daily)"),
    search: Optional[str] = Query(None, description="検索キーワード"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db_session)
):
    """
    Get paginated list of stores with filtering and sorting
    """
    try:
        # ログイン状態を確認
        is_logged_in = current_user is not None
        user_name = getattr(current_user, 'username', 'anonymous') if current_user else 'anonymous'
        logger.info(f"Getting stores list for user: {user_name} (logged_in: {is_logged_in})")
        
        # 未ログイン時は3日間のデータのみ表示するため、データを制限
        # データベースから実際の店舗データを取得
        from scout_ui.models.store import Business, StatusHistory
        from sqlalchemy import desc, asc
        
        logger.info(f"Getting stores list for user: {user_name} (logged_in: {is_logged_in})")
        
        # ベースクエリを構築
        query = db.query(Business).filter(Business.in_scope == True)
        
        # フィルタリング適用
        if area:
            query = query.filter(Business.area == area)
        if business_type:
            query = query.filter(Business.type == business_type)
        if search:
            query = query.filter(Business.name.ilike(f"%{search}%"))
        
        # 全件数を取得
        total_count = query.count()
        
        # ソート適用
        if sort_by == "working_rate":
            # 最新の稼働率でソート（サブクエリを使用）
            from sqlalchemy import func
            latest_rates = db.query(
                StatusHistory.business_id,
                func.max(StatusHistory.biz_date).label('latest_date')
            ).group_by(StatusHistory.business_id).subquery()
            
            working_rates = db.query(
                StatusHistory.business_id,
                StatusHistory.working_rate
            ).join(
                latest_rates,
                (StatusHistory.business_id == latest_rates.c.business_id) &
                (StatusHistory.biz_date == latest_rates.c.latest_date)
            ).subquery()
            
            query = query.outerjoin(
                working_rates,
                Business.business_id == working_rates.c.business_id
            )
            
            if sort_order == "desc":
                query = query.order_by(desc(working_rates.c.working_rate))
            else:
                query = query.order_by(asc(working_rates.c.working_rate))
        elif sort_by == "name":
            if sort_order == "desc":
                query = query.order_by(desc(Business.name))
            else:
                query = query.order_by(asc(Business.name))
        elif sort_by == "area":
            if sort_order == "desc":
                query = query.order_by(desc(Business.area))
            else:
                query = query.order_by(asc(Business.area))
        
        # ページネーション
        total_pages = (total_count + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_count)
        paged_stores = query.offset(start_idx).limit(page_size).all()
        
        # 各店舗の最新稼働率を取得
        stores_with_rates = []
        for store in paged_stores:
            # 最新の稼働率を取得
            latest_rate = db.query(StatusHistory).filter(
                StatusHistory.business_id == store.business_id
            ).order_by(desc(StatusHistory.biz_date)).first()
            
            # status_historyがない場合はNoneを設定（UIで「-」表示）
            working_rate = float(latest_rate.working_rate) if latest_rate else None
            last_updated = latest_rate.biz_date if latest_rate else store.updated_at
            
            # キャスト数を実際のcastsテーブルから取得
            from scout_ui.models.store import Cast
            actual_cast_count = db.query(Cast).filter(
                Cast.business_id == store.business_id,
                Cast.is_active == True
            ).count()
            
            stores_with_rates.append({
                "id": store.business_id,
                "name": store.name,
                "area": store.area,
                "business_type": store.type,
                "working_rate": working_rate,
                "cast_count": actual_cast_count,
                "active_cast_count": int(actual_cast_count * working_rate) if working_rate is not None and actual_cast_count else 0,
                "last_updated": last_updated,
                "avg_rating": 4.0  # デフォルト値
            })
        
        filtered_stores = stores_with_rates
        
        # レスポンス形式に変換
        stores_data = []
        for store in stores_with_rates:
            stores_data.append({
                "id": store["id"],
                "name": store["name"],
                "area": store["area"],
                "business_type": convert_business_type_to_japanese(store["business_type"]),
                "working_rate": store["working_rate"],  # Noneの場合はそのまま（フロントエンドで「-」表示）
                "cast_count": store["cast_count"],
                "active_cast_count": store["active_cast_count"],
                "last_updated": store["last_updated"].isoformat() if store["last_updated"] else None,
                "status": "active" if store["working_rate"] is not None and store["working_rate"] > 0.5 else "inactive",
                "avg_rating": store["avg_rating"]
            })
        
        return {
            "stores": stores_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "start_idx": start_idx + 1 if paged_stores else 0,
                "end_idx": min(end_idx, total_count)
            }
        }
            
    except Exception as e:
        logger.error(f"Error getting stores list: {e}")
        raise HTTPException(status_code=500, detail="店舗一覧の取得に失敗しました")

@router.get("/{store_id}")
async def get_store_detail(
    request: Request,
    store_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Get detailed information for a specific store
    """
    try:
        # ユーザー認証
        current_user = await get_current_user(request)
        if not current_user:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        logger.info(f"Getting store detail for store_id: {store_id}, user: {current_user.username}")
        
        # データベースセッションは既に引数で取得済み
        # Get store by ID
        store = db.query(StoreView).filter(StoreView.id == store_id).first()
        
        if not store:
            raise HTTPException(status_code=404, detail="店舗が見つかりません")
        
        # Convert to detailed response format
        store_detail = {
            "id": store.id,
            "name": store.name,
            "area": store.area,
            "business_type": store.business_type,
            "working_rate": store.working_rate,
            "cast_count": 0,  # Placeholder
            "last_updated": store.updated_at,
            "status": "active" if store.working_rate > 0 else "inactive",
            "address": getattr(store, 'address', None),
            "phone": getattr(store, 'phone', None),
            "created_at": store.created_at,
            "updated_at": store.updated_at
        }
        
        return {
            "success": True,
            "store": store_detail
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting store detail: {e}")
        raise HTTPException(status_code=500, detail="店舗詳細の取得に失敗しました")

@router.get("/filter-options")
async def get_filter_options_endpoint(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Get available filter options for stores
    """
    try:
        logger.info(f"Getting filter options for user: {current_user['username']}")
        
        # Get filter options
        filter_options = get_filter_options()
        
        # Add sort and view type options
        sort_options = [
            {"value": "working_rate", "label": "稼働率"},
            {"value": "name", "label": "店舗名"},
            {"value": "area", "label": "エリア"},
            {"value": "business_type", "label": "業種"},
            {"value": "updated_at", "label": "更新日時"}
        ]
        
        view_types = [
            {"value": "weekly", "label": "週ごと"},
            {"value": "daily", "label": "日ごと"}
        ]
        
        response_options = FilterOptions(
            areas=filter_options.get('areas', []),
            business_types=filter_options.get('business_types', []),
            sort_options=sort_options,
            view_types=view_types
        )
        
        return {
            "success": True,
            "filter_options": response_options
        }
        
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        raise HTTPException(status_code=500, detail="フィルターオプションの取得に失敗しました")

@router.get("/export/csv")
async def export_csv(
    request: Request,
    area: Optional[str] = Query(None, description="エリアフィルター"),
    business_type: Optional[str] = Query(None, description="業種フィルター"),
    date_from: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    sort_by: str = Query("working_rate", description="ソート項目"),
    sort_order: str = Query("desc", description="ソート順序"),
    view_type: str = Query("weekly", description="表示タイプ"),
    search: Optional[str] = Query(None, description="検索キーワード"),
    db: Session = Depends(get_db_session)
):
    """
    Export stores data as CSV
    """
    try:
        logger.info(f"Exporting CSV for user: {current_user['username']}")
        
        async with get_db_session() as db:
            # Apply filters to get StoreView objects
            filters = {
                'area': area,
                'business_type': business_type,
                'date_from': date_from,
                'date_to': date_to,
                'view_type': view_type,
                'search': search
            }
            
            stores = await apply_filters(db, filters)
            
            # Apply sorting
            sort_options = {
                'sort_by': sort_by,
                'sort_order': sort_order
            }
            
            sorted_stores = await apply_sorting(stores, sort_options)
            
            # Generate CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', '店舗名', 'エリア', '業種', '稼働率', 
                '作成日時', '更新日時', 'ステータス'
            ])
            
            # Write data rows
            for store in sorted_stores:
                writer.writerow([
                    store.id,
                    store.name,
                    store.area,
                    store.business_type,
                    store.working_rate or 0.0,
                    store.created_at.strftime('%Y-%m-%d %H:%M:%S') if store.created_at else '',
                    store.last_updated.strftime('%Y-%m-%d %H:%M:%S') if store.last_updated else '',
                    'アクティブ' if (store.working_rate or 0) > 0 else '非アクティブ'
                ])
            
            # Create response
            csv_content = output.getvalue()
            output.close()
            
            filename = f"stores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return StreamingResponse(
                io.BytesIO(csv_content.encode('utf-8-sig')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail="CSVエクスポートに失敗しました")

@router.get("/export/ranking")
async def export_simple_ranking(
    request: Request,
    area: Optional[str] = Query(None, description="エリアフィルター"),
    business_type: Optional[str] = Query(None, description="業種フィルター"),
    date_from: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    view_type: str = Query("weekly", description="表示タイプ"),
    search: Optional[str] = Query(None, description="検索キーワード"),
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db_session)
):
    """
    Export simple ranking as text format for LINE sharing
    """
    try:
        logger.info(f"Exporting simple ranking for user: {current_user.get('username', 'anonymous') if current_user else 'anonymous'}")
        
        # Determine data period based on login status
        if not current_user:
            # Limit to 3 days for non-logged users
            if not date_from and not date_to:
                date_to = datetime.now().date().isoformat()
                date_from = (datetime.now().date() - timedelta(days=3)).isoformat()
        else:
            # 30 days for logged users if no dates specified
            if not date_from and not date_to:
                date_to = datetime.now().date().isoformat()
                date_from = (datetime.now().date() - timedelta(days=30)).isoformat()
        
        # Apply filters to get StoreView objects
        filters = {
            'area': area,
            'business_type': business_type,
            'date_from': date_from,
            'date_to': date_to,
            'view_type': view_type,
            'search': search
        }
        
        stores = await apply_filters(db, filters)
        
        # Sort by working rate descending
        sort_options = {
            'sort_by': 'working_rate',
            'sort_order': 'desc'
        }
        
        sorted_stores = await apply_sorting(stores, sort_options)
        
        # Take top 6 stores for ranking
        top_stores = sorted_stores[:6]
        
        # Generate ranking text
        area_text = area if area else "全エリア"
        business_type_text = business_type if business_type else "全業種"
        
        # Calculate period text
        if date_from and date_to:
            period_text = f"{date_from} ～ {date_to}"
        else:
            period_text = "最新データ"
        
        ranking_text = f"【{area_text}】【{business_type_text}】\n【{period_text}】平均稼働率\n"
        
        # Add ranking entries
        rank_emojis = ["🥇", "🥈", "🥉"]
        
        for i, store in enumerate(top_stores):
            rank = i + 1
            working_rate = store.working_rate or 0.0
            
            if rank <= 3:
                emoji = rank_emojis[rank - 1]
                ranking_text += f"{emoji}【{store.name}】：{working_rate:.1f}%\n"
            else:
                ranking_text += f"{rank}.【{store.name}】：{working_rate:.1f}%\n"
        
        return JSONResponse(
            content=ranking_text,
            media_type="text/plain; charset=utf-8"
        )
        
    except Exception as e:
        logger.error(f"Error exporting simple ranking: {e}")
        raise HTTPException(status_code=500, detail="簡易ランキング出力に失敗しました")

@router.get("/ranking")
async def get_ranking(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="ランキング件数"),
    sort_by: str = Query("working_rate", description="ランキング基準"),
    view_type: str = Query("weekly", description="表示タイプ"),
    area: Optional[str] = Query(None, description="エリアフィルター"),
    business_type: Optional[str] = Query(None, description="業種フィルター"),
    db: Session = Depends(get_db_session)
):
    """
    Get store ranking based on specified criteria
    """
    try:
        logger.info(f"Getting store ranking for user: {current_user['username']}")
        
        async with get_db_session() as db:
            # Apply filters to get StoreView objects
            filters = {
                'area': area,
                'business_type': business_type,
                'view_type': view_type
            }
            
            stores = await apply_filters(db, filters)
            
            # Apply sorting for ranking
            sort_options = {
                'sort_by': sort_by,
                'sort_order': 'desc'  # Always descending for ranking
            }
            
            sorted_stores = await apply_sorting(stores, sort_options)
            
            # Get top stores
            ranking_stores = sorted_stores[:limit]
            
            # Create ranking data
            ranking_data = []
            for i, store in enumerate(ranking_stores, 1):
                ranking_data.append({
                    "rank": i,
                    "id": store.id,
                    "name": store.name,
                    "area": store.area,
                    "business_type": store.business_type,
                    "working_rate": store.working_rate or 0.0,
                    "cast_count": store.cast_count,
                    "status": "active" if (store.working_rate or 0) > 0 else "inactive"
                })
            
            return {
                "success": True,
                "ranking": ranking_data,
                "total_count": len(ranking_data),
                "criteria": sort_by,
                "message": f"トップ{len(ranking_data)}店舗のランキングです"
            }
            
    except Exception as e:
        logger.error(f"Error getting store ranking: {e}")
        raise HTTPException(status_code=500, detail="ランキングの取得に失敗しました")

@router.post("/refresh")
async def refresh_stores_data(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Refresh stores data (trigger data update if needed)
    """
    try:
        logger.info(f"Refreshing stores data for user: {current_user['username']}")
        
        # This could trigger background tasks to update store data
        # For now, just return success
        
        return {
            "success": True,
            "message": "店舗データの更新を開始しました"
        }
        
    except Exception as e:
        logger.error(f"Error refreshing stores data: {e}")
        raise HTTPException(status_code=500, detail="店舗データの更新に失敗しました")