"""
データ取得処理

店舗情報とステータスデータの取得
"""

from datetime import date, time, timedelta
from typing import List, Dict, Any, Tuple, Optional

from .models import StatusRecord

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class DataRetriever:
    """データ取得処理クラス"""
    
    def __init__(self, database):
        self.database = database
    
    async def get_target_businesses(self) -> List[Dict[str, Any]]:
        """計算対象の店舗を取得（InScope=Trueのみ）"""
        try:
            query = """
                SELECT business_id, name, open_hour, close_hour
                FROM business 
                WHERE in_scope = true 
                ORDER BY business_id
            """
            businesses_data = self.database.fetch_all(query)
            
            logger.info(f"計算対象店舗: {len(businesses_data)}店舗")
            return businesses_data
            
        except Exception as e:
            logger.error(f"店舗データ取得エラー: {e}")
            return []
    
    def get_business_hours(self, business: Dict[str, Any]) -> Tuple[Optional[time], Optional[time]]:
        """店舗の営業時間を取得"""
        try:
            open_time = None
            close_time = None
            
            # open_hourの変換
            open_hour = business.get('open_hour')
            if open_hour is not None:
                if isinstance(open_hour, int):
                    open_time = time(open_hour, 0)
                elif isinstance(open_hour, str):
                    if ':' in open_hour:
                        hour, minute = map(int, open_hour.split(':'))
                        open_time = time(hour, minute)
                    else:
                        open_time = time(int(open_hour), 0)
            
            # close_hourの変換
            close_hour = business.get('close_hour')
            if close_hour is not None:
                if isinstance(close_hour, int):
                    close_time = time(close_hour, 0)
                elif isinstance(close_hour, str):
                    if ':' in close_hour:
                        hour, minute = map(int, close_hour.split(':'))
                        close_time = time(hour, minute)
                    else:
                        close_time = time(int(close_hour), 0)
            
            return open_time, close_time
            
        except Exception as e:
            logger.error(f"営業時間取得エラー: {business.get('name', 'unknown')} - {e}")
            return None, None
    
    def get_business_status_data_in_hours(
        self, 
        business_id: str, 
        target_date: date, 
        business_hours: Tuple[Optional[time], Optional[time]]
    ) -> List[StatusRecord]:
        """指定店舗・日付の営業時間中のStatusデータを取得（SQLで高度な絞り込み）"""
        
        try:
            open_time, close_time = business_hours
            
            # 営業時間が未設定の場合は全データを取得
            if open_time is None or close_time is None:
                query = """
                    SELECT business_id, datetime as recorded_at, cast_id, is_working, is_on_shift
                    FROM status 
                    WHERE business_id = %s 
                    AND DATE(datetime) = %s
                    ORDER BY datetime
                """
                params = (business_id, target_date)
                logger.debug(f"店舗{business_id}: 営業時間未設定、全データを取得")
                
            else:
                # 営業時間の判定
                if open_time <= close_time:
                    # 通常営業（例: 9:00-18:00）
                    query = """
                        SELECT business_id, datetime as recorded_at, cast_id, is_working, is_on_shift
                        FROM status 
                        WHERE business_id = %s 
                        AND DATE(datetime) = %s
                        AND TIME(datetime) >= %s 
                        AND TIME(datetime) <= %s
                        ORDER BY datetime
                    """
                    params = (business_id, target_date, open_time, close_time)
                    logger.debug(f"店舗{business_id}: 通常営業時間 {open_time}-{close_time}")
                    
                else:
                    # 日跨ぎ営業（例: 22:00-6:00）
                    query = """
                        SELECT business_id, datetime as recorded_at, cast_id, is_working, is_on_shift
                        FROM status 
                        WHERE business_id = %s 
                        AND (
                            (DATE(datetime) = %s AND TIME(datetime) >= %s)
                            OR 
                            (DATE(datetime) = %s AND TIME(datetime) <= %s)
                        )
                        ORDER BY datetime
                    """
                    next_date = target_date + timedelta(days=1)
                    params = (business_id, target_date, open_time, next_date, close_time)
                    logger.debug(f"店舗{business_id}: 日跨ぎ営業時間 {open_time}-{close_time}")
            
            # データ取得
            raw_records = self.database.fetch_all(query, params)
            
            # StatusRecordオブジェクトに変換
            status_records = []
            for record in raw_records:
                status_records.append(StatusRecord(
                    business_id=record['business_id'],
                    recorded_at=record['recorded_at'],
                    cast_id=record['cast_id'],
                    is_working=bool(record['is_working']),
                    is_on_shift=bool(record['is_on_shift'])
                ))
            
            logger.debug(f"店舗{business_id}: 営業時間中のレコード{len(status_records)}件を取得")
            return status_records
            
        except Exception as e:
            logger.error(f"Statusデータ取得エラー: business_id={business_id}, date={target_date} - {e}")
            return []
