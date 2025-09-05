"""
稼働率計算処理

StatusRecordから稼働率を算出
"""

from typing import List

from .models import StatusRecord

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class RateCalculator:
    """稼働率計算クラス"""
    
    def calculate_working_rate_from_records(self, status_records: List[StatusRecord]) -> float:
        """StatusRecordから稼働率を計算: IsWorkingがTrue / IsOnShiftがTrue"""
        
        if not status_records:
            return 0.0
        
        # IsOnShiftがTrueのレコード数（分母）
        on_shift_records = [r for r in status_records if r.is_on_shift]
        on_shift_count = len(on_shift_records)
        
        if on_shift_count == 0:
            return 0.0
        
        # IsWorkingがTrueかつIsOnShiftがTrueのレコード数（分子）
        working_count = sum(1 for r in status_records if r.is_working and r.is_on_shift)
        
        # 稼働率計算（0.0-1.0の範囲）
        working_rate = working_count / on_shift_count
        
        logger.debug(f"稼働率計算: 稼働中={working_count}, 出勤中={on_shift_count}, 稼働率={working_rate:.3f}")
        return working_rate
