"""
稼働率計算ジョブ
前日の稼働データから店舗ごとの稼働率を計算してStatusHistoryに保存
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

from core.database import DatabaseManager
from core.models import Business
from utils.logging_utils import JobLoggerAdapter

logger = logging.getLogger(__name__)

@dataclass
class WorkingRateResult:
    """稼働率計算結果"""
    success: bool
    processed_count: int
    error_count: int
    errors: List[str]
    duration_seconds: float
    calculated_businesses: List[Dict[str, Any]]

def run_working_rate_calculation(target_date: Optional[date] = None, force: bool = False) -> WorkingRateResult:
    """
    稼働率計算を実行
    
    Args:
        target_date: 計算対象日付（省略時は前日）
        force: 強制実行フラグ
    
    Returns:
        WorkingRateResult: 計算結果
    """
    start_time = datetime.now()
    job_logger = JobLoggerAdapter(logger, "稼働率計算")
    
    # 対象日付の決定
    if target_date is None:
        target_date = datetime.now().date() - timedelta(days=1)
    
    job_logger.info(f"稼働率計算開始: 対象日={target_date}")
    
    db_manager = DatabaseManager()
    processed_count = 0
    error_count = 0
    errors = []
    calculated_businesses = []
    
    try:
        # 全店舗を取得
        businesses_data = db_manager.get_businesses()
        businesses = [Business.from_dict(b) for b in businesses_data]
        
        job_logger.info(f"対象店舗数: {len(businesses)}店舗")
        
        for business in businesses:
            try:
                # 店舗ごとの稼働率を計算
                working_rate = calculate_business_working_rate(
                    db_manager, business, target_date
                )
                
                if working_rate is not None:
                    # StatusHistoryに保存
                    save_working_rate_to_history(
                        db_manager, business.business_id, target_date, working_rate
                    )
                    
                    calculated_businesses.append({
                        "business_id": business.business_id,
                        "business_name": business.name,
                        "working_rate": working_rate,
                        "date": target_date.isoformat()
                    })
                    
                    processed_count += 1
                    job_logger.debug(f"稼働率計算完了: {business.name} = {working_rate:.2%}")
                else:
                    job_logger.info(f"データなし: {business.name} (対象日にStatusデータがありません)")
                
            except Exception as e:
                error_msg = f"店舗 {business.name} (ID: {business.business_id}): {str(e)}"
                errors.append(error_msg)
                error_count += 1
                job_logger.error(error_msg)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        job_logger.info(
            f"稼働率計算完了: 処理済み={processed_count}, エラー={error_count}, "
            f"実行時間={duration:.2f}秒"
        )
        
        return WorkingRateResult(
            success=error_count == 0,
            processed_count=processed_count,
            error_count=error_count,
            errors=errors,
            duration_seconds=duration,
            calculated_businesses=calculated_businesses
        )
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        job_logger.error(f"稼働率計算が失敗: {e}")
        logger.exception("稼働率計算エラー")
        
        return WorkingRateResult(
            success=False,
            processed_count=processed_count,
            error_count=error_count + 1,
            errors=errors + [str(e)],
            duration_seconds=duration,
            calculated_businesses=calculated_businesses
        )

def calculate_business_working_rate(
    db_manager: DatabaseManager, 
    business: Business, 
    target_date: date
) -> Optional[float]:
    """
    単一店舗の稼働率を計算
    
    稼働率(%) = IsWorkingがTrueのレコード数 / IsOnShiftがTrueのレコード数
    
    Args:
        db_manager: データベースマネージャー
        business: 店舗情報
        target_date: 計算対象日付
    
    Returns:
        float: 稼働率（0.0-1.0）、データがない場合はNone
    """
    
    # 営業時間を算出
    open_time, close_time = calculate_business_hours(business, target_date)
    
    # 営業時間内のStatusレコードを取得
    status_records = get_status_records_for_period(
        db_manager,
        business_id=business.business_id,
        start_datetime=open_time,
        end_datetime=close_time
    )
    
    if not status_records:
        return None
    
    # IsOnShift=True のレコードのみを対象
    on_shift_records = [r for r in status_records if r.get('is_on_shift', False)]
    
    if not on_shift_records:
        return None
    
    # 稼働率計算
    working_records = [r for r in on_shift_records if r.get('is_working', False)]
    working_rate = len(working_records) / len(on_shift_records)
    
    return working_rate

def calculate_business_hours(business: Business, target_date: date) -> tuple[datetime, datetime]:
    """
    店舗の営業時間を算出
    
    Args:
        business: 店舗情報
        target_date: 対象日付
    
    Returns:
        tuple: (営業開始時刻, 営業終了時刻)
    """
    from datetime import time
    
    # OpenHour, CloseHour をパース（例: "10:00", "24:00"）
    open_hour_parts = business.open_hour.split(":")
    close_hour_parts = business.close_hour.split(":")
    
    open_hour = int(open_hour_parts[0])
    open_minute = int(open_hour_parts[1]) if len(open_hour_parts) > 1 else 0
    close_hour = int(close_hour_parts[0])
    close_minute = int(close_hour_parts[1]) if len(close_hour_parts) > 1 else 0
    
    # 営業開始時刻
    open_time = datetime.combine(target_date, time(open_hour, open_minute))
    
    # 営業終了時刻（24時を超える場合は翌日）
    if close_hour >= 24:
        close_date = target_date + timedelta(days=1)
        close_time = datetime.combine(close_date, time(close_hour - 24, close_minute))
    else:
        close_time = datetime.combine(target_date, time(close_hour, close_minute))
    
    return open_time, close_time

def get_status_records_for_period(
    db_manager: DatabaseManager,
    business_id: str,
    start_datetime: datetime,
    end_datetime: datetime
) -> List[Dict[str, Any]]:
    """
    指定期間のStatusレコードを取得
    
    Args:
        db_manager: データベースマネージャー
        business_id: 店舗ID
        start_datetime: 開始日時
        end_datetime: 終了日時
    
    Returns:
        List[Dict]: Statusレコードのリスト
    """
    query = """
        SELECT business_id, cast_id, datetime, is_working, is_on_shift
        FROM status
        WHERE business_id = %s 
        AND datetime >= %s 
        AND datetime <= %s
        ORDER BY datetime
    """
    
    try:
        records = db_manager.execute_query(query, (business_id, start_datetime, end_datetime))
        return [
            {
                'business_id': record[0],
                'cast_id': record[1],
                'datetime': record[2],
                'is_working': record[3],
                'is_on_shift': record[4]
            }
            for record in records
        ]
    except Exception as e:
        logger.error(f"Statusレコード取得エラー: {e}")
        return []

def save_working_rate_to_history(
    db_manager: DatabaseManager, 
    business_id: str, 
    target_date: date, 
    working_rate: float
) -> None:
    """
    稼働率をStatusHistoryテーブルに保存
    
    Args:
        db_manager: データベースマネージャー
        business_id: 店舗ID
        target_date: 対象日付
        working_rate: 稼働率
    """
    
    # 既存レコードがあるかチェック
    existing_query = """
        SELECT business_id FROM status_history 
        WHERE business_id = %s AND date = %s
    """
    
    existing_record = db_manager.execute_query(existing_query, (business_id, target_date))
    
    if existing_record:
        # 更新
        update_query = """
            UPDATE status_history 
            SET working_rate = %s, updated_at = NOW()
            WHERE business_id = %s AND date = %s
        """
        db_manager.execute_query(update_query, (working_rate, business_id, target_date))
        logger.debug(f"稼働率更新: {business_id} {target_date} = {working_rate:.2%}")
    else:
        # 新規挿入
        insert_query = """
            INSERT INTO status_history (business_id, date, working_rate, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
        """
        db_manager.execute_query(insert_query, (business_id, target_date, working_rate))
        logger.debug(f"稼働率新規保存: {business_id} {target_date} = {working_rate:.2%}")

if __name__ == "__main__":
    # テスト実行
    result = run_working_rate_calculation()
    print(f"稼働率計算結果: {result}")
