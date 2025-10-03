from fastapi import APIRouter, Request, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from scout_ui.core.auth import get_current_user
from scout_ui.core.database import get_db_session
from scout_ui.utils.filters import (
    apply_filters,
    get_filter_options,
    apply_sorting,
    paginate_stores
)
from scout_ui.models.store import StoreView

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class DashboardStats(BaseModel):
    total_stores: int
    active_stores: int
    avg_working_rate: float
    total_casts: int
    active_casts: int
    recent_updates: int

class StoreData(BaseModel):
    id: int
    name: str
    area: str
    business_type: str
    working_rate: float
    cast_count: int
    last_updated: Optional[datetime]
    status: str

class DashboardResponse(BaseModel):
    success: bool
    stats: DashboardStats
    recent_stores: List[StoreData]
    top_stores: List[StoreData]
    message: Optional[str] = None

@router.get("/stats")
async def get_dashboard_stats(
    request: Request,
    db: Session = Depends(get_db_session),
    date_from: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    area: Optional[str] = Query(None, description="エリアフィルター"),
    business_type: Optional[str] = Query(None, description="業種フィルター")
):
    """
    Get dashboard statistics
    """
    try:
        # Authenticate user
        current_user = get_current_user(request, db)
        if not current_user:
            raise HTTPException(status_code=401, detail="認証が必要です")
            
        logger.info(f"Getting dashboard stats for user: {current_user.username}")
        
        # Apply filters
        filters = {
            'area': area,
            'business_type': business_type,
            'date_from': date_from,
            'date_to': date_to
        }
        
        filtered_stores = await apply_filters(db, filters)
        
        # Get total stores count
        total_stores = len(filtered_stores)
        
        # Get active stores (working_rate > 0)
        active_stores = len([store for store in filtered_stores if (store.working_rate or 0) > 0])
        
        # Calculate average working rate
        avg_working_rate = 0.0
        if total_stores > 0:
            working_rates = [store.working_rate or 0.0 for store in filtered_stores]
            avg_working_rate = sum(working_rates) / len(working_rates) if working_rates else 0.0
        
        # Get cast statistics
        total_casts = sum(store.cast_count for store in filtered_stores)
        active_casts = sum(store.cast_count for store in filtered_stores if (store.working_rate or 0) > 0)
        
        # Get recent updates count (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_updates = len([store for store in filtered_stores if store.last_updated and store.last_updated >= yesterday])
        
        stats = DashboardStats(
            total_stores=total_stores,
            active_stores=active_stores,
            avg_working_rate=round(avg_working_rate, 2),
            total_casts=total_casts,
            active_casts=active_casts,
            recent_updates=recent_updates
        )
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="統計情報の取得に失敗しました")

@router.get("/recent-stores")
async def get_recent_stores(
    request: Request,
    db: Session = Depends(get_db_session),
    limit: int = Query(10, description="取得件数"),
    area: Optional[str] = Query(None, description="エリアフィルター"),
    business_type: Optional[str] = Query(None, description="業種フィルター")
):
    """
    Get recently updated stores
    """
    try:
        logger.info(f"Getting recent stores for user: {current_user['username']}")
        
        async with get_db_session() as db:
            # Apply filters
            filters = {
                'area': area,
                'business_type': business_type
            }
            
            filtered_stores = await apply_filters(db, filters)
            
            # Sort by last_updated descending and limit
            sorted_stores = sorted(
                filtered_stores,
                key=lambda x: x.last_updated or datetime.min,
                reverse=True
            )[:limit]
            
            # Convert to response format
            stores_data = []
            for store in sorted_stores:
                stores_data.append(StoreData(
                    id=store.id,
                    name=store.name,
                    area=store.area,
                    business_type=store.business_type,
                    working_rate=store.working_rate or 0.0,
                    cast_count=store.cast_count,
                    last_updated=store.last_updated,
                    status="active" if (store.working_rate or 0) > 0 else "inactive"
                ))
            
            return {
                "success": True,
                "stores": stores_data
            }
            
    except Exception as e:
        logger.error(f"Error getting recent stores: {e}")
        raise HTTPException(status_code=500, detail="最近更新された店舗の取得に失敗しました")

@router.get("/top-stores")
async def get_top_stores(
    request: Request,
    db: Session = Depends(get_db_session),
    limit: int = Query(10, description="取得件数"),
    sort_by: str = Query("working_rate", description="ソート基準"),
    area: Optional[str] = Query(None, description="エリアフィルター"),
    business_type: Optional[str] = Query(None, description="業種フィルター")
):
    """
    Get top performing stores
    """
    try:
        logger.info(f"Getting top stores for user: {current_user['username']}")
        
        async with get_db_session() as db:
            # Apply filters
            filters = {
                'area': area,
                'business_type': business_type
            }
            
            filtered_stores = await apply_filters(db, filters)
            
            # Apply sorting
            sort_options = {
                'sort_by': sort_by,
                'sort_order': 'desc'
            }
            
            sorted_stores = await apply_sorting(filtered_stores, sort_options)
            
            # Get top stores
            top_stores = sorted_stores[:limit]
            
            # Convert to response format
            stores_data = []
            for store in top_stores:
                stores_data.append(StoreData(
                    id=store.id,
                    name=store.name,
                    area=store.area,
                    business_type=store.business_type,
                    working_rate=store.working_rate or 0.0,
                    cast_count=store.cast_count,
                    last_updated=store.last_updated,
                    status="active" if (store.working_rate or 0) > 0 else "inactive"
                ))
            
            return {
                "success": True,
                "stores": stores_data
            }
            
    except Exception as e:
        logger.error(f"Error getting top stores: {e}")
        raise HTTPException(status_code=500, detail="トップ店舗の取得に失敗しました")
@router.get("/overview")
async def get_dashboard_overview(
    request: Request,
    db: Session = Depends(get_db_session),
    date_from: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    area: Optional[str] = Query(None, description="エリアフィルター"),
    business_type: Optional[str] = Query(None, description="業種フィルター")
):
    """
    Get complete dashboard overview data
    """
    try:
        logger.info(f"Getting dashboard overview for user: {current_user['username']}")
        
        # Get stats
        stats_response = await get_dashboard_stats(
            current_user=current_user,
            date_from=date_from,
            date_to=date_to,
            area=area,
            business_type=business_type
        )
        
        # Get recent stores
        recent_response = await get_recent_stores(
            current_user=current_user,
            limit=5,
            area=area,
            business_type=business_type
        )
        
        # Get top stores
        top_response = await get_top_stores(
            current_user=current_user,
            limit=5,
            sort_by="working_rate",
            area=area,
            business_type=business_type
        )
        
        return DashboardResponse(
            success=True,
            stats=stats_response["stats"],
            recent_stores=recent_response["stores"],
            top_stores=top_response["stores"],
            message="ダッシュボードデータを正常に取得しました"
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="ダッシュボード概要の取得に失敗しました")

@router.get("/filter-options")
async def get_dashboard_filter_options(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Get available filter options for dashboard
    """
    try:
        logger.info(f"Getting filter options for user: {current_user['username']}")
        
        # Get filter options
        filter_options = get_filter_options()
        
        return {
            "success": True,
            "filter_options": filter_options
        }
        
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        raise HTTPException(status_code=500, detail="フィルターオプションの取得に失敗しました")

@router.post("/refresh")
async def refresh_dashboard_data(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Refresh dashboard data (trigger data update if needed)
    """
    try:
        logger.info(f"Refreshing dashboard data for user: {current_user['username']}")
        
        # This could trigger background tasks to update data
        # For now, just return success
        
        return {
            "success": True,
            "message": "ダッシュボードデータの更新を開始しました"
        }
        
    except Exception as e:
        logger.error(f"Error refreshing dashboard data: {e}")
        raise HTTPException(status_code=500, detail="ダッシュボードデータの更新に失敗しました")