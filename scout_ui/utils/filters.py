from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from scout_ui.models.store import Business, StatusHistory, Cast, StoreView
from scout_ui.core.database import get_db_session
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def apply_filters(
    db: Session,
    filters: Dict[str, Any]
) -> List[StoreView]:
    """フィルターを適用してStoreViewオブジェクトのリストを返す"""
    try:
        # 基本クエリ: in_scope=trueの店舗のみ
        query = db.query(Business).filter(Business.in_scope == True)
        
        # エリアフィルター
        area = filters.get('area')
        if area and area != "all":
            query = query.filter(Business.area == area)
        
        # 業種フィルター
        business_type = filters.get('business_type')
        if business_type and business_type != "all":
            query = query.filter(Business.type == business_type)
        
        # 検索キーワードフィルター
        search = filters.get('search')
        if search:
            query = query.filter(
                or_(
                    Business.name.ilike(f'%{search}%'),
                    Business.area.ilike(f'%{search}%'),
                    Business.type.ilike(f'%{search}%')
                )
            )
        
        businesses = query.all()
        
        # StoreViewオブジェクトを作成
        store_views = []
        for business in businesses:
            # 最新の稼働率を取得
            latest_working_rate = None
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            
            if date_from or date_to:
                status_query = db.query(StatusHistory).filter(
                    StatusHistory.business_id == business.business_id
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
                
                latest_status = status_query.order_by(StatusHistory.biz_date.desc()).first()
                if latest_status:
                    latest_working_rate = float(latest_status.working_rate)
            else:
                # 日付フィルターがない場合は最新の稼働率を取得
                latest_status = db.query(StatusHistory).filter(
                    StatusHistory.business_id == business.business_id
                ).order_by(StatusHistory.biz_date.desc()).first()
                if latest_status:
                    latest_working_rate = float(latest_status.working_rate)
            
            # キャスト数を取得
            cast_count = db.query(Cast).filter(
                Cast.business_id == business.business_id
            ).count()
            
            active_cast_count = db.query(Cast).filter(
                and_(
                    Cast.business_id == business.business_id,
                    Cast.is_active == True
                )
            ).count()
            
            # 最終更新日を取得
            last_updated = business.updated_at
            
            store_view = StoreView(
                business=business,
                latest_working_rate=latest_working_rate,
                cast_count=cast_count,
                active_cast_count=active_cast_count,
                last_updated=last_updated
            )
            store_views.append(store_view)
        
        return store_views
        
    except Exception as e:
        logger.error(f"Error applying filters: {str(e)}")
        raise

def get_filter_options() -> Dict[str, List[str]]:
    """フィルターオプションを取得"""
    try:
        # モックデータを返す（実際のデータベース接続の代わり）
        return {
            "areas": ["銀座", "新宿", "渋谷", "六本木", "池袋", "赤坂", "青山"],
            "business_types": ["クラブ", "ラウンジ", "スナック", "キャバクラ"],
            "view_types": ["weekly", "daily"],
            "sort_options": [
                {"value": "working_rate", "label": "稼働率"},
                {"value": "name", "label": "店舗名"},
                {"value": "area", "label": "エリア"},
                {"value": "cast_count", "label": "キャスト数"},
                {"value": "last_updated", "label": "最終更新日"}
            ],
            "sort_orders": [
                {"value": "desc", "label": "降順"},
                {"value": "asc", "label": "昇順"}
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        raise

async def apply_sorting(
    stores: List[StoreView],
    sort_options: Dict[str, str]
) -> List[StoreView]:
    """ソートを適用"""
    try:
        sort_by = sort_options.get('sort_by', 'working_rate')
        sort_order = sort_options.get('sort_order', 'desc')
        reverse = sort_order == 'desc'
        
        # ソート関数を決定
        if sort_by == "working_rate":
            key_func = lambda x: x.working_rate or 0
        elif sort_by == "name":
            key_func = lambda x: x.name or ""
        elif sort_by == "area":
            key_func = lambda x: x.area or ""
        elif sort_by == "business_type":
            key_func = lambda x: x.business_type or ""
        elif sort_by == "updated_at":
            key_func = lambda x: x.updated_at or datetime.min
        else:
            key_func = lambda x: x.working_rate or 0
        
        # ソートを適用
        sorted_stores = sorted(stores, key=key_func, reverse=reverse)
        return sorted_stores
            
    except Exception as e:
        logger.error(f"Error applying sorting: {str(e)}")
        return stores

async def paginate_stores(
    stores: List[StoreView],
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """ページネーションを適用"""
    try:
        # 総件数を取得
        total_count = len(stores)
        total_pages = (total_count + page_size - 1) // page_size
        
        # オフセットを計算
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        # ページネーション適用
        paginated_stores = stores[start_index:end_index]
        
        return {
            "stores": paginated_stores,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "total_count": total_count
        }
        
    except Exception as e:
        logger.error(f"Error paginating stores: {str(e)}")
        raise

def get_date_range_options() -> List[Dict[str, Any]]:
    """日付範囲のプリセットオプションを取得"""
    today = datetime.now().date()
    
    return [
        {
            "label": "過去1週間",
            "value": "1week",
            "date_from": (today - timedelta(weeks=1)).isoformat(),
            "date_to": today.isoformat()
        },
        {
            "label": "過去2週間",
            "value": "2weeks",
            "date_from": (today - timedelta(weeks=2)).isoformat(),
            "date_to": today.isoformat()
        },
        {
            "label": "過去1ヶ月",
            "value": "1month",
            "date_from": (today - timedelta(days=30)).isoformat(),
            "date_to": today.isoformat()
        },
        {
            "label": "過去3ヶ月",
            "value": "3months",
            "date_from": (today - timedelta(days=90)).isoformat(),
            "date_to": today.isoformat()
        }
    ]