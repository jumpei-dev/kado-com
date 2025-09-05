"""
稼働率計算関連のデータモデル

計算処理で使用するデータ構造の定義
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class StatusRecord:
    """Statusレコードのデータクラス"""
    business_id: str
    recorded_at: datetime
    cast_id: str
    is_working: bool
    is_on_shift: bool


@dataclass
class WorkingRateResult:
    """稼働率計算結果"""
    success: bool
    processed_count: int
    error_count: int
    errors: List[str]
    duration_seconds: float
    calculated_businesses: List[Dict[str, Any]]


@dataclass
class BusinessHours:
    """店舗営業時間"""
    business_id: str
    business_name: str
    open_time: datetime.time
    close_time: datetime.time
    is_overnight: bool  # 日跨ぎ営業かどうか
