"""
稼働率計算ジョブ - メインコントローラー

全店舗の稼働率計算処理のオーケストレーション
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Optional

from .calculator import WorkingRateCalculator
from .models import WorkingRateResult
from .history_summary import get_business_history_summary

# 後方互換性のため、旧クラス名でもアクセス可能にする
WorkingRateCalculationJob = WorkingRateCalculator

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


async def run_working_rate_calculation(target_date: Optional[date] = None, force: bool = False) -> WorkingRateResult:
    """
    稼働率計算のメイン関数 - 外部呼び出し用
    
    Args:
        target_date: 計算対象日付（省略時は前日）
        force: 強制実行フラグ（既存データを上書き）
    
    Returns:
        WorkingRateResult: 計算結果
    """
    calculator = WorkingRateCalculator()
    return await calculator.run_working_rate_calculation(target_date, force)


def run_status_history(business_id: int = None, target_date: str = None, force: bool = False):
    """
    ステータス履歴計算ジョブを実行する（status_history.py互換）
    
    Args:
        business_id: 処理する特定の店舗ID（全店舗の場合はNone）
        target_date: 計算する特定の日付（YYYY-MM-DD、自動検出の場合はNone）
        force: 適切な時間でなくても強制実行する
    
    Returns:
        実行詳細を含む結果辞書
    """
    # 日付文字列をdateオブジェクトに変換
    parsed_date = None
    if target_date:
        try:
            parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid date format: {target_date}. Expected YYYY-MM-DD")
            return {
                "success": False,
                "error": f"Invalid date format: {target_date}",
                "processed_count": 0,
                "error_count": 1
            }
    
    # 非同期関数を実行
    try:
        result = asyncio.run(run_working_rate_calculation(parsed_date, force))
        
        # BatchJobResult互換の形式で返す
        return {
            "success": result.success,
            "processed_count": result.processed_count,
            "error_count": result.error_count,
            "errors": result.errors,
            "duration_seconds": result.duration_seconds,
            "calculated_businesses": result.calculated_businesses
        }
    except Exception as e:
        logger.error(f"Status history execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "processed_count": 0,
            "error_count": 1
        }
