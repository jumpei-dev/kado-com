"""
バッチ処理のための日付と時刻のユーティリティ。
"""

from datetime import datetime, time, timedelta, date
from typing import List, Tuple, Optional
import pytz

# 日本のタイムゾーン
JST = pytz.timezone('Asia/Tokyo')

def now_jst() -> datetime:
    """JSTタイムゾーンで現在の日時を取得する"""
    return datetime.now(JST)

def now_jst_naive() -> datetime:
    """JSTタイムゾーンでナイーブな日時として現在の日時を取得する"""
    return now_jst().replace(tzinfo=None)

def to_jst(dt: datetime) -> datetime:
    """日時をJSTタイムゾーンに変換する"""
    if dt.tzinfo is None:
        # ナイーブな場合はUTCと仮定
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(JST)

def is_business_hours(
    current_time: datetime,
    start_time: time,
    end_time: time,
    buffer_minutes: int = 0
) -> bool:
    """
    現在時刻が営業時間内かどうかをチェックする。
    
    Args:
        current_time: チェックする時刻
        start_time: 営業開始時刻
        end_time: 営業終了時刻
        buffer_minutes: 営業時間を延長するバッファ分数
    
    Returns:
        営業時間内（バッファ含む）の場合True
    """
    current_time_only = current_time.time()
    
    # バッファを適用
    if buffer_minutes > 0:
        buffer_delta = timedelta(minutes=buffer_minutes)
        start_datetime = datetime.combine(current_time.date(), start_time) - buffer_delta
        end_datetime = datetime.combine(current_time.date(), end_time) + buffer_delta
        
        start_time = start_datetime.time()
        end_time = end_datetime.time()
    
    # 営業時間が深夜をまたぐ場合の処理
    if start_time <= end_time:
        # 通常の場合: 9:00 - 18:00
        return start_time <= current_time_only <= end_time
    else:
        # Midnight spanning: 22:00 - 06:00
        return current_time_only >= start_time or current_time_only <= end_time

def get_next_business_day(reference_date: date = None) -> date:
    """Get the next business day (excluding weekends)."""
    if reference_date is None:
        reference_date = now_jst().date()
    
    next_day = reference_date + timedelta(days=1)
    
    # Skip weekends (Saturday=5, Sunday=6)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    
    return next_day

def get_business_days_in_range(start_date: date, end_date: date) -> List[date]:
    """Get all business days within a date range."""
    business_days = []
    current_date = start_date
    
    while current_date <= end_date:
        # Monday=0, ..., Friday=4, Saturday=5, Sunday=6
        if current_date.weekday() < 5:
            business_days.append(current_date)
        current_date += timedelta(days=1)
    
    return business_days

def get_collection_times_for_day(
    business_date: date,
    start_time: time,
    end_time: time,
    interval_minutes: int = 30
) -> List[datetime]:
    """
    Get all collection times for a business day.
    
    Args:
        business_date: The business day
        start_time: Business hours start time
        end_time: Business hours end time
        interval_minutes: Collection interval in minutes
    
    Returns:
        List of datetime objects for collection times
    """
    collection_times = []
    
    # Start from business start time
    current_datetime = datetime.combine(business_date, start_time)
    end_datetime = datetime.combine(business_date, end_time)
    
    # Handle midnight spanning business hours
    if end_time < start_time:
        end_datetime += timedelta(days=1)
    
    while current_datetime <= end_datetime:
        collection_times.append(current_datetime)
        current_datetime += timedelta(minutes=interval_minutes)
    
    return collection_times

def get_time_until_next_collection(
    current_time: datetime,
    start_time: time,
    end_time: time,
    interval_minutes: int = 30,
    buffer_minutes: int = 30
) -> Optional[timedelta]:
    """
    Calculate time until next collection should occur.
    
    Returns None if not within business hours (including buffer).
    """
    if not is_business_hours(current_time, start_time, end_time, buffer_minutes):
        return None
    
    # Find next collection time
    current_date = current_time.date()
    collection_times = get_collection_times_for_day(
        current_date, start_time, end_time, interval_minutes
    )
    
    # Find the next collection time after current time
    for collection_time in collection_times:
        if collection_time > current_time:
            return collection_time - current_time
    
    # If no more collections today, check next business day
    next_business_day = get_next_business_day(current_date)
    next_day_collections = get_collection_times_for_day(
        next_business_day, start_time, end_time, interval_minutes
    )
    
    if next_day_collections:
        return next_day_collections[0] - current_time
    
    return None

def format_duration(duration: timedelta) -> str:
    """Format a timedelta as a human-readable string."""
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def get_date_range_for_history_calculation(
    days_back: int = 30,
    reference_date: date = None
) -> Tuple[date, date]:
    """
    Get date range for status history calculation.
    
    Args:
        days_back: Number of days to go back from reference date
        reference_date: Reference date (defaults to yesterday)
    
    Returns:
        Tuple of (start_date, end_date) for calculation
    """
    if reference_date is None:
        # Default to yesterday (we don't calculate today's history until after business hours)
        reference_date = now_jst().date() - timedelta(days=1)
    
    start_date = reference_date - timedelta(days=days_back - 1)
    
    return start_date, reference_date

def should_run_status_collection(
    current_time: datetime,
    start_time: time,
    end_time: time,
    buffer_minutes: int = 30
) -> bool:
    """Check if status collection should run at current time."""
    return is_business_hours(current_time, start_time, end_time, buffer_minutes)

def should_run_history_calculation(
    current_time: datetime,
    end_time: time,
    buffer_minutes: int = 60
) -> bool:
    """
    Check if history calculation should run.
    
    Should run after business hours with some buffer.
    """
    current_time_only = current_time.time()
    
    # Calculate time after business hours + buffer
    end_datetime = datetime.combine(current_time.date(), end_time)
    calculation_time = (end_datetime + timedelta(minutes=buffer_minutes)).time()
    
    # Should run after the calculation time
    return current_time_only >= calculation_time

def get_rounded_datetime(dt: datetime, round_minutes: int = 30) -> datetime:
    """Round datetime to nearest specified minutes."""
    minutes = (dt.minute // round_minutes) * round_minutes
    return dt.replace(minute=minutes, second=0, microsecond=0)
