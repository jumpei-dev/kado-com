from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from scout_ui.models.store import Business, StatusHistory, Cast, StoreView
from scout_ui.core.database import get_db_session
from scout_ui.utils.business_type_utils import convert_business_type_to_japanese
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
                
                # 期間内の平均稼働率を計算
                status_records = status_query.all()
                if status_records:
                    working_rates = [float(record.working_rate) for record in status_records]
                    latest_working_rate = sum(working_rates) / len(working_rates)
                else:
                    # 期間内にデータがない場合はNoneを設定（店舗は表示する）
                    latest_working_rate = None
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

def get_filter_options(db: Session = None) -> Dict[str, List[str]]:
    """フィルターオプションを取得（businessテーブルから動的に取得）"""
    try:
        if db is None:
            db = get_db_session()
        
        # businessテーブルからDISTINCT値を取得
        areas_query = db.query(Business.area).filter(Business.in_scope == True).distinct().order_by(Business.area)
        areas_raw = [area[0] for area in areas_query.all() if area[0]]
        # エリアもvalue/label形式に統一
        areas = [{
            "value": area,
            "label": area
        } for area in areas_raw]
        
        types_query = db.query(Business.type).filter(Business.in_scope == True).distinct().order_by(Business.type)
        business_types_raw = [btype[0] for btype in types_query.all() if btype[0]]
        # 業種を日本語に変換
        business_types = [{
            "value": btype,
            "label": convert_business_type_to_japanese(btype)
        } for btype in business_types_raw]
        
        return {
            "areas": areas,
            "business_types": business_types,
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
        # エラー時はフォールバック値を返す
        return {
            "areas": [],
            "business_types": [],
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


def get_weekly_options():
    """Get weekly period options for filtering (10月W1, W2, W3 format)"""
    today = datetime.now().date()
    options = []
    
    # Generate options for the past 12 weeks
    for i in range(12):
        # Calculate the start of the week (Monday)
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday + (i * 7))
        week_end = week_start + timedelta(days=6)
        
        # Get the month and week number within that month
        month = week_start.month
        year = week_start.year
        
        # Calculate week number within the month
        first_day_of_month = week_start.replace(day=1)
        first_monday = first_day_of_month + timedelta(days=(7 - first_day_of_month.weekday()) % 7)
        if first_monday > week_start:
            first_monday -= timedelta(days=7)
        
        week_num = ((week_start - first_monday).days // 7) + 1
        
        # Format label as "10月W1" style
        label = f"{month}月W{week_num}"
        
        # If week spans across months, use the month of the majority of days
        if week_start.month != week_end.month:
            # Use the month that has more days in this week
            mid_week = week_start + timedelta(days=3)
            month = mid_week.month
            
            # Recalculate week number for the correct month
            first_day_of_month = mid_week.replace(day=1)
            first_monday = first_day_of_month + timedelta(days=(7 - first_day_of_month.weekday()) % 7)
            if first_monday > mid_week:
                first_monday -= timedelta(days=7)
            
            week_num = ((mid_week - first_monday).days // 7) + 1
            label = f"{month}月W{week_num}"
        
        options.append({
            'label': label,
            'value': f"{year}-{month:02d}-W{week_num}",
            'date_from': week_start.isoformat(),
            'date_to': week_end.isoformat(),
            'year': year,
            'month': month,
            'week': week_num
        })
    
    return options


def parse_weekly_period(weekly_period):
    """Parse weekly period value and return date_from and date_to"""
    if not weekly_period:
        return None, None
    
    try:
        # Parse format: "2024-10-W1"
        parts = weekly_period.split('-')
        if len(parts) != 3 or not parts[2].startswith('W'):
            return None, None
        
        year = int(parts[0])
        month = int(parts[1])
        week_num = int(parts[2][1:])  # Remove 'W' prefix
        
        # Calculate the first Monday of the month
        first_day_of_month = datetime(year, month, 1).date()
        first_monday = first_day_of_month + timedelta(days=(7 - first_day_of_month.weekday()) % 7)
        if first_monday > first_day_of_month:
            first_monday -= timedelta(days=7)
        
        # Calculate the start and end of the specified week
        week_start = first_monday + timedelta(days=(week_num - 1) * 7)
        week_end = week_start + timedelta(days=6)
        
        return week_start.isoformat(), week_end.isoformat()
        
    except (ValueError, IndexError):
        return None, None