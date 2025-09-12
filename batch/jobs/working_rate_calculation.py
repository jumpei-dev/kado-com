"""
稼働率計算ジョブ

前日の営業時間中のデータから稼働率を計算し、status_historyに保存する
"""

from datetime import date, datetime, timedelta
from typing import Optional

from .working_rate_calculation.calculator import WorkingRateCalculator
from .working_rate_calculation.models import WorkingRateResult

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


async def run_working_rate_calculation(target_date: Optional[date] = None, force: bool = False) -> WorkingRateResult:
    """
    稼働率計算を実行
    
    Args:
        target_date: 計算対象日付（省略時は前日）
        force: 強制実行フラグ（既存データを上書き）
    
    Returns:
        WorkingRateResult: 計算結果
    """
    # 対象日の決定（前日）
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).date()
    
    logger.info(f"稼働率計算ジョブ開始: 対象日={target_date}, 強制実行={force}")
    
    try:
        # WorkingRateCalculatorインスタンスを作成
        calculator = WorkingRateCalculator()
        
        # 稼働率計算を実行
        result = await calculator.run_working_rate_calculation(target_date, force)
        
        logger.info(f"稼働率計算ジョブ完了: 成功={result.success}, 処理数={result.processed_count}")
        return result
        
    except Exception as e:
        error_msg = f"稼働率計算ジョブでエラー: {e}"
        logger.error(error_msg)
        
        return WorkingRateResult(
            success=False,
            processed_count=0,
            error_count=1,
            errors=[error_msg],
            duration_seconds=0.0,
            calculated_businesses=[]
        )