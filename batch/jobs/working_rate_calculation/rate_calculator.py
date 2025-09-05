"""
稼働率計算処理

StatusRecordから稼働率を算出
"""

from typing import List, Optional

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
    
    def calculate_working_rate_from_records(self, status_records: List[StatusRecord], business_info: Optional[dict] = None) -> float:
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
        
        # 🔧 ソープランドのcapacity補正を適用
        working_count = self._apply_capacity_limit(working_count, business_info)
        
        # 稼働率計算（0.0-1.0の範囲）
        working_rate = working_count / on_shift_count
        
        logger.debug(f"稼働率計算: 稼働中={working_count}, 出勤中={on_shift_count}, 稼働率={working_rate:.3f}")
        return working_rate
    
    def _apply_capacity_limit(self, working_count: int, business_info: Optional[dict]) -> int:
        """
        ソープランドのcapacity制限を適用
        
        Args:
            working_count: 検出された稼働数
            business_info: 店舗情報（type, capacityを含む）
        
        Returns:
            補正後の稼働数
        """
        try:
            if not business_info:
                return working_count
            
            business_type = business_info.get('type')
            capacity = business_info.get('capacity')
            
            # ソープランド以外は補正なし
            if business_type != 'soapland':
                return working_count
            
            # capacityが設定されていない場合は補正なし
            if not capacity or capacity <= 0:
                return working_count
            
            # capacity制限を適用
            original_count = working_count
            corrected_count = min(working_count, capacity)
            
            if corrected_count < original_count:
                logger.info(f"🔧 ソープランドcapacity補正: {original_count} → {corrected_count} (上限: {capacity})")
            
            return corrected_count
            
        except Exception as e:
            logger.error(f"❌ capacity補正エラー: {e}")
            return working_count  # エラー時は元の値を返す
