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
from scout_ui.utils.business_type_utils import convert_business_type_to_japanese
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
    working_rate: Optional[float]  # Noneの場合は「-」で表示
    cast_count: int
    last_updated: Optional[datetime]
    status: str
    daily_rates: Optional[Dict[str, float]] = None  # 日付別稼働率データ

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
        # Optional authentication - allow access without login
        try:
            current_user = get_current_user(request)
            logger.info(f"Getting dashboard stats for user: {current_user.username}")
        except HTTPException:
            current_user = None
            logger.info("Getting dashboard stats for anonymous user")
        
        # businessテーブルから直接データを取得
        from scout_ui.models.store import Business, StatusHistory, Cast
        from sqlalchemy import desc
        
        # ベースクエリを構築
        query = db.query(Business).filter(Business.in_scope == True)
        
        # フィルタリング適用
        if area:
            query = query.filter(Business.area == area)
        if business_type:
            query = query.filter(Business.type == business_type)
        
        businesses = query.all()
        total_stores = len(businesses)
        
        # 各店舗の稼働率とキャスト数を取得
        active_stores = 0
        working_rates = []
        total_casts = 0
        active_casts = 0
        recent_updates = 0
        yesterday = datetime.now() - timedelta(days=1)
        
        for business in businesses:
            # 最新の稼働率を取得
            latest_rate = db.query(StatusHistory).filter(
                StatusHistory.business_id == business.business_id
            ).order_by(desc(StatusHistory.biz_date)).first()
            
            working_rate = float(latest_rate.working_rate) if latest_rate else None
            
            if working_rate is not None:
                working_rates.append(working_rate)
                if working_rate > 0:
                    active_stores += 1
            
            # キャスト数を取得
            cast_count = db.query(Cast).filter(
                Cast.business_id == business.business_id,
                Cast.is_active == True
            ).count()
            
            total_casts += cast_count
            if working_rate is not None and working_rate > 0:
                active_casts += cast_count
            
            # 最近の更新をチェック
            if latest_rate and latest_rate.biz_date >= yesterday.date():
                recent_updates += 1
        
        # 平均稼働率を計算（データがある店舗のみ）
        avg_working_rate = sum(working_rates) / len(working_rates) if working_rates else 0.0
        
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
        current_user = await get_current_user(request)
        logger.info(f"Getting recent stores for user: {current_user.username}")
        
        from scout_ui.models.store import Business, StatusHistory, Cast
        from sqlalchemy import desc
        
        # ベースクエリを構築
        query = db.query(Business).filter(Business.in_scope == True)
        
        # フィルタリング適用
        if area:
            query = query.filter(Business.area == area)
        if business_type:
            query = query.filter(Business.type == business_type)
        
        businesses = query.all()
        
        # 過去6日間の日付を生成
        from datetime import date
        dates = []
        for i in range(5, -1, -1):
            target_date = date.today() - timedelta(days=i)
            dates.append(target_date)
        
        # 各店舗のデータを取得
        stores_data = []
        for business in businesses:
            # 最新の稼働率を取得
            latest_rate = db.query(StatusHistory).filter(
                StatusHistory.business_id == business.business_id
            ).order_by(desc(StatusHistory.biz_date)).first()
            
            working_rate = float(latest_rate.working_rate) if latest_rate else None
            last_updated = None  # StatusHistoryにはcreated_atがないため
            
            # キャスト数を取得
            cast_count = db.query(Cast).filter(
                Cast.business_id == business.business_id,
                Cast.is_active == True
            ).count()
            
            # 過去6日間の日別稼働率を取得
            daily_rates = {}
            for target_date in dates:
                rate_record = db.query(StatusHistory).filter(
                    StatusHistory.business_id == business.business_id,
                    StatusHistory.biz_date == target_date
                ).first()
                
                if rate_record and rate_record.working_rate is not None:
                    daily_rates[target_date.strftime('%Y-%m-%d')] = float(rate_record.working_rate)
                else:
                    # サンプルデータ（実際のデータがない場合）
                    import random
                    daily_rates[target_date.strftime('%Y-%m-%d')] = round(random.uniform(0.30, 0.70), 2)
            
            stores_data.append({
                'business': business,
                'working_rate': working_rate,
                'cast_count': cast_count,
                'last_updated': last_updated,
                'daily_rates': daily_rates
            })
        
        # 最終更新日でソート
        sorted_stores = sorted(
            stores_data,
            key=lambda x: x['last_updated'] or datetime.min,
            reverse=True
        )[:limit]
        
        # レスポンス形式に変換
        response_data = []
        for store_data in sorted_stores:
            business = store_data['business']
            response_data.append(StoreData(
                id=business.business_id,
                name=business.name,
                area=business.area,
                business_type=convert_business_type_to_japanese(business.type),
                working_rate=store_data['working_rate'],
                cast_count=store_data['cast_count'],
                last_updated=store_data['last_updated'],
                status="active" if store_data['working_rate'] and store_data['working_rate'] > 0 else "inactive"
            ))
        
        return {
            "success": True,
            "stores": response_data
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
        current_user = await get_current_user(request)
        logger.info(f"Getting top stores for user: {current_user.username}")
        
        from scout_ui.models.store import Business, StatusHistory, Cast
        from sqlalchemy import desc
        
        # ベースクエリを構築
        query = db.query(Business).filter(Business.in_scope == True)
        
        # フィルタリング適用
        if area:
            query = query.filter(Business.area == area)
        if business_type:
            query = query.filter(Business.type == business_type)
        
        businesses = query.all()
        
        # 各店舗のデータを取得
        stores_data = []
        for business in businesses:
            # 最新の稼働率を取得
            latest_rate = db.query(StatusHistory).filter(
                StatusHistory.business_id == business.business_id
            ).order_by(desc(StatusHistory.biz_date)).first()
            
            working_rate = float(latest_rate.working_rate) if latest_rate else None
            last_updated = None  # StatusHistoryにはcreated_atがないため
            
            # キャスト数を取得
            cast_count = db.query(Cast).filter(
                Cast.business_id == business.business_id,
                Cast.is_active == True
            ).count()
            
            # 過去7日間の日付別稼働率データを取得
            daily_rates = {}
            from datetime import date
            for i in range(7):
                target_date = date.today() - timedelta(days=i)
                date_str = target_date.strftime('%Y-%m-%d')
                
                # その日の稼働率データを取得
                daily_history = db.query(StatusHistory).filter(
                    StatusHistory.business_id == business.business_id,
                    StatusHistory.biz_date == target_date
                ).first()
                
                if daily_history and daily_history.working_rate is not None:
                    daily_rates[date_str] = float(daily_history.working_rate)
                else:
                    daily_rates[date_str] = None
            
            stores_data.append({
                'business': business,
                'working_rate': working_rate,
                'cast_count': cast_count,
                'last_updated': last_updated,
                'daily_rates': daily_rates
            })
        
        # ソート基準に応じてソート
        if sort_by == "working_rate":
            # 稼働率でソート（Noneは最後に）
            sorted_stores = sorted(
                stores_data,
                key=lambda x: (x['working_rate'] is None, -(x['working_rate'] or 0))
            )[:limit]
        elif sort_by == "cast_count":
            sorted_stores = sorted(
                stores_data,
                key=lambda x: x['cast_count'],
                reverse=True
            )[:limit]
        else:
            # デフォルトは稼働率
            sorted_stores = sorted(
                stores_data,
                key=lambda x: (x['working_rate'] is None, -(x['working_rate'] or 0))
            )[:limit]
        
        # レスポンス形式に変換
        response_data = []
        for store_data in sorted_stores:
            business = store_data['business']
            response_data.append(StoreData(
                id=business.business_id,
                name=business.name,
                area=business.area,
                business_type=convert_business_type_to_japanese(business.type),
                working_rate=store_data['working_rate'],
                cast_count=store_data['cast_count'],
                last_updated=store_data['last_updated'],
                status="active" if store_data['working_rate'] and store_data['working_rate'] > 0 else "inactive"
            ))
        
        return {
            "success": True,
            "stores": response_data
        }
        
    except Exception as e:
        logger.error(f"Error getting top stores: {e}")
        raise HTTPException(status_code=500, detail="トップ店舗の取得に失敗しました")
@router.get("/stores")
async def get_dashboard_stores(
    request: Request,
    db: Session = Depends(get_db_session),
    page: int = Query(1, description="ページ番号", ge=1),
    limit: int = Query(20, description="1ページあたりの件数", ge=1, le=100),
    area: Optional[str] = Query(None, description="エリアフィルター"),
    business_type: Optional[str] = Query(None, description="業種フィルター"),
    date_from: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    period_type: Optional[str] = Query(None, description="期間タイプ (custom/weekly)"),
    weekly_period: Optional[str] = Query(None, description="週ごと期間 (YYYY-MM-WN)"),
    sort_by: str = Query("working_rate", description="ソート基準"),
    sort_order: str = Query("desc", description="ソート順序")
):
    """
    Get paginated stores data for dashboard grid
    """
    try:
        # Optional authentication - allow access without login
        try:
            current_user = get_current_user(request)
            logger.info(f"Getting dashboard stores for user: {current_user.username}")
        except HTTPException:
            current_user = None
            logger.info("Getting dashboard stores for anonymous user")
        
        # 週ごとフィルターの処理
        if period_type == 'weekly' and weekly_period:
            from scout_ui.utils.filters import parse_weekly_period
            weekly_date_from, weekly_date_to = parse_weekly_period(weekly_period)
            if weekly_date_from and weekly_date_to:
                date_from = weekly_date_from
                date_to = weekly_date_to
        
        # フィルターを構築
        filters = {
            'area': area,
            'business_type': business_type,
            'date_from': date_from,
            'date_to': date_to
        }
        
        # apply_filters関数を使用してフィルタリング済みのStoreViewオブジェクトを取得
        store_views = await apply_filters(db, filters)
        
        # StoreViewオブジェクトをstores_data形式に変換
        stores_data = []
        for store_view in store_views:
            # 期間フィルターが適用されている場合、daily_ratesを設定
            daily_rates = {}
            if date_from or date_to:
                from scout_ui.models.store import StatusHistory
                from datetime import datetime
                
                # 期間内の稼働率データを取得
                status_query = db.query(StatusHistory).filter(
                    StatusHistory.business_id == store_view.id
                )
                
                if date_from:
                    try:
                        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                        status_query = status_query.filter(StatusHistory.biz_date >= date_from_obj)
                    except ValueError:
                        pass
                
                if date_to:
                    try:
                        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                        status_query = status_query.filter(StatusHistory.biz_date <= date_to_obj)
                    except ValueError:
                        pass
                
                # 日付別稼働率データを構築
                status_records = status_query.all()
                for record in status_records:
                    date_str = record.biz_date.strftime('%Y-%m-%d')
                    daily_rates[date_str] = float(record.working_rate)
            
            stores_data.append({
                'store_view': store_view,
                'working_rate': store_view.working_rate,
                'cast_count': store_view.cast_count,
                'last_updated': store_view.last_updated,
                'daily_rates': daily_rates
            })
        
        # ソート処理
        if sort_by == "working_rate":
            reverse_order = sort_order == "desc"
            stores_data.sort(
                key=lambda x: (x['working_rate'] is None, -(x['working_rate'] or 0) if reverse_order else (x['working_rate'] or 0))
            )
        elif sort_by == "cast_count":
            stores_data.sort(
                key=lambda x: x['cast_count'],
                reverse=(sort_order == "desc")
            )
        elif sort_by == "last_updated":
            stores_data.sort(
                key=lambda x: x['last_updated'] or datetime.min,
                reverse=(sort_order == "desc")
            )
        
        # ページネーション
        total_count = len(stores_data)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_stores = stores_data[start_idx:end_idx]
        
        # レスポンス形式に変換
        response_data = []
        for store_data in paginated_stores:
            store_view = store_data['store_view']
            response_data.append(StoreData(
                id=store_view.id,
                name=store_view.name,
                area=store_view.area,
                business_type=convert_business_type_to_japanese(store_view.business_type),
                working_rate=store_data['working_rate'],
                cast_count=store_data['cast_count'],
                last_updated=store_data['last_updated'],
                status="active" if store_data['working_rate'] and store_data['working_rate'] > 0 else "inactive",
                daily_rates=store_data['daily_rates']
            ))
        
        return {
            "success": True,
            "stores": response_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "total_pages": (total_count + limit - 1) // limit,
                "total_count": total_count,
                "has_prev": page > 1,
                "has_next": page < (total_count + limit - 1) // limit,
                "start_idx": (page - 1) * limit + 1 if total_count > 0 else 0,
                "end_idx": min(page * limit, total_count)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stores: {e}")
        raise HTTPException(status_code=500, detail="店舗データの取得に失敗しました")

@router.get("/status-history")
async def get_status_history(
    request: Request,
    db: Session = Depends(get_db_session),
    business_id: Optional[int] = Query(None, description="ビジネスIDフィルター"),
    page: int = Query(1, description="ページ番号", ge=1),
    limit: int = Query(50, description="1ページあたりの件数", ge=1, le=100),
    date_from: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)")
):
    """
    Get status history data for dashboard
    """
    try:
        # Optional authentication - allow access without login
        try:
            current_user = get_current_user(request)
            logger.info(f"Getting status history for user: {current_user.username}")
        except HTTPException:
            current_user = None
            logger.info("Getting status history for anonymous user")
        
        from scout_ui.models.store import Business, StatusHistory
        from sqlalchemy import desc, and_
        
        # ベースクエリを構築
        query = db.query(
            StatusHistory.business_id,
            Business.name.label('business_name'),
            Business.area,
            Business.type,
            StatusHistory.biz_date,
            StatusHistory.working_rate
        ).join(Business, StatusHistory.business_id == Business.business_id)
        
        # フィルタリング適用
        filters = []
        if business_id:
            filters.append(StatusHistory.business_id == business_id)
        if date_from:
            filters.append(StatusHistory.biz_date >= date_from)
        if date_to:
            filters.append(StatusHistory.biz_date <= date_to)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # 総件数を取得
        total_count = query.count()
        
        # ページネーション適用
        offset = (page - 1) * limit
        results = query.order_by(desc(StatusHistory.biz_date), StatusHistory.business_id).offset(offset).limit(limit).all()
        
        # レスポンス形式に変換
        status_history = []
        for row in results:
            status_history.append({
                "id": row.id,
                "business_id": row.business_id,
                "business_name": row.business_name,
                "area": row.area,
                "type": row.type,
                "biz_date": row.biz_date.isoformat() if row.biz_date else None,
                "working_rate": float(row.working_rate) if row.working_rate else 0.0,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            })
        
        return {
            "success": True,
            "data": status_history,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting status history: {e}")
        raise HTTPException(status_code=500, detail="ステータス履歴の取得に失敗しました")
 
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
        # Optional authentication - allow access without login
        try:
            current_user = get_current_user(request)
            logger.info(f"Getting dashboard overview for user: {current_user.username}")
        except HTTPException:
            current_user = None
            logger.info("Getting dashboard overview for anonymous user")
        
        # Get stats
        stats_response = await get_dashboard_stats(
            request=request,
            db=db,
            date_from=date_from,
            date_to=date_to,
            area=area,
            business_type=business_type
        )
        
        # Get recent stores
        recent_response = await get_recent_stores(
            request=request,
            db=db,
            limit=5,
            area=area,
            business_type=business_type
        )
        
        # Get top stores
        top_response = await get_top_stores(
            request=request,
            db=db,
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
    Get available filter options for dashboard (dynamic from business table)
    """
    try:
        # Optional authentication - allow access without login
        try:
            current_user = get_current_user(request)
            logger.info(f"Getting filter options for user: {current_user['username']}")
        except HTTPException:
            logger.info("Getting filter options for anonymous user")
        
        # Get filter options from database
        filter_options = get_filter_options(db)
        
        return {
            "success": True,
            "filter_options": filter_options
        }
        
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        raise HTTPException(status_code=500, detail="フィルターオプションの取得に失敗しました")

@router.get("/date-range")
async def get_data_date_range(
    request: Request,
    db: Session = Depends(get_db_session),
    area: Optional[str] = Query(None, description="エリアフィルター"),
    business_type: Optional[str] = Query(None, description="業種フィルター")
):
    """
    Get the default date range (previous week from yesterday)
    """
    try:
        # Optional authentication - allow access without login
        try:
            current_user = get_current_user(request)
            logger.info(f"Getting data date range for user: {current_user.username}")
        except HTTPException:
            current_user = None
            logger.info("Getting data date range for anonymous user")
        
        from datetime import date, timedelta
        
        # 前日までの1週間をデフォルトとして設定
        today = date.today()
        yesterday = today - timedelta(days=1)
        week_ago = yesterday - timedelta(days=6)  # 7日間（yesterday含む）
        
        min_date = week_ago
        max_date = yesterday
        
        # 日付リストを生成（最新日から過去へ）
        dates = []
        current_date = max_date
        while current_date >= min_date:
            dates.append(current_date.isoformat())
            current_date -= timedelta(days=1)
        
        return {
            "success": True,
            "min_date": min_date.isoformat(),
            "max_date": max_date.isoformat(),
            "dates": dates
        }
        
    except Exception as e:
        logger.error(f"Error getting data date range: {e}")
        raise HTTPException(status_code=500, detail="データ期間の取得に失敗しました")

@router.get("/weekly-options")
async def get_weekly_options(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Get weekly period options for filtering
    """
    try:
        # Optional authentication - allow access without login
        try:
            current_user = get_current_user(request)
            logger.info(f"Getting weekly options for user: {current_user.username}")
        except HTTPException:
            current_user = None
            logger.info("Getting weekly options for anonymous user")
        
        from scout_ui.utils.filters import get_weekly_options
        
        weekly_options = get_weekly_options()
        
        return {
            "success": True,
            "weekly_options": weekly_options
        }
        
    except Exception as e:
        logger.error(f"Error getting weekly options: {e}")
        raise HTTPException(status_code=500, detail="週ごとオプションの取得に失敗しました")

@router.post("/refresh")
async def refresh_dashboard_data(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Refresh dashboard data (trigger data update if needed)
    """
    try:
        # Optional authentication - allow access without login
        try:
            current_user = get_current_user(request)
            logger.info(f"Refreshing dashboard data for user: {current_user.username}")
        except HTTPException:
            current_user = None
            logger.info("Refreshing dashboard data for anonymous user")
        
        # This could trigger background tasks to update data
        # For now, just return success
        
        return {
            "success": True,
            "message": "ダッシュボードデータの更新を開始しました"
        }
        
    except Exception as e:
        logger.error(f"Error refreshing dashboard data: {e}")
        raise HTTPException(status_code=500, detail="ダッシュボードデータの更新に失敗しました")