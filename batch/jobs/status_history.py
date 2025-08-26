"""
ステータス履歴計算ジョブ - 営業時間後に日別稼働率を計算する。
6時間ごとに実行して履歴の稼働率を計算する。
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from core.database import DatabaseManager
from core.models import Business, BatchJobResult
from utils.logging_utils import get_job_logger, JobLoggerAdapter
from utils.datetime_utils import (
    now_jst_naive, should_run_history_calculation, get_date_range_for_history_calculation
)

logger = get_job_logger('status_history')

class StatusHistoryJob:
    """日別ステータス履歴を計算するジョブ"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.name = "ステータス履歴計算"
    
    def run(self, business_id: int = None, target_date: str = None, force: bool = False) -> BatchJobResult:
        """
        ステータス履歴計算ジョブを実行する。
        
        Args:
            business_id: 処理する特定の店舗（全店舗の場合はNone）
            target_date: 計算する特定の日付（YYYY-MM-DD、自動検出の場合はNone）
            force: 適切な時間でなくても強制実行する
        """
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_logger = JobLoggerAdapter(logger, self.name, run_id)
        
        result = BatchJobResult(
            job_name=self.name,
            started_at=now_jst_naive()
        )
        
        job_logger.job_started()
        
        try:
            # 処理する店舗を取得
            if business_id:
                businesses_data = self.db_manager.execute_query(
                    "SELECT * FROM business WHERE business_id = %s AND in_scope = true",
                    (business_id,)
                )
            else:
                businesses_data = self.db_manager.get_businesses()
            
            if not businesses_data:
                job_logger.info("処理する店舗が見つかりません")
                result.finalize(success=True)
                return result
            
            businesses = [Business.from_dict(b) for b in businesses_data]
            
            for business in businesses:
                job_logger.processing_item("business", business.name)
                
                # Check if appropriate time to run (unless forced)
                current_time = now_jst_naive()
                if not force and not should_run_history_calculation(
                    current_time,
                    business.close_hour,
                    buffer_minutes=60
                ):
                    job_logger.info(f"店舗 {business.name} の履歴計算に適切な時間ではありません")
                    continue
                
                # Process history calculation for this business
                success = self._process_business_history(
                    business, target_date, job_logger
                )
                if success:
                    result.add_success()
                else:
                    result.add_error(f"店舗の処理に失敗しました: {business.name}")
            
            result.finalize()
            job_logger.job_completed(
                result.processed_count,
                result.error_count,
                result.duration_seconds
            )
            
        except Exception as e:
            error_msg = f"Job execution failed: {e}"
            result.add_error(error_msg)
            result.finalize(success=False)
            job_logger.job_failed(error_msg)
            logger.exception("Status history job failed")
        
        return result
    
    def _process_business_history(
        self,
        business: Business,
        target_date: str,
        job_logger: JobLoggerAdapter
    ) -> bool:
        """Process status history for a specific business."""
        try:
            if target_date:
                # Calculate for specific date
                dates_to_calculate = [target_date]
            else:
                # Get dates that need calculation
                dates_to_calculate = self.db_manager.get_status_history_dates_to_calculate(
                    business.business_id, days_back=30
                )
            
            if not dates_to_calculate:
                job_logger.info(f"店舗 {business.name} に計算が必要な日付がありません")
                return True
            
            job_logger.info(
                f"店舗 {business.name} の {len(dates_to_calculate)} 日間の履歴を計算中"
            )
            
            calculated_count = 0
            error_count = 0
            
            for calculation_date in dates_to_calculate:
                success = self.db_manager.calculate_and_insert_status_history(
                    business.business_id, calculation_date
                )
                
                if success:
                    calculated_count += 1
                    job_logger.debug(f"店舗 {business.name} の {calculation_date} の履歴を計算しました")
                else:
                    error_count += 1
                    job_logger.warning(
                        f"店舗 {business.name} の {calculation_date} の履歴計算に失敗しました"
                    )
            
            job_logger.item_success(
                f"業務 {business.name}",
                f"計算完了: {calculated_count}, エラー: {error_count}"
            )
            
            return error_count == 0
            
        except Exception as e:
            job_logger.item_error(f"business {business.name}", str(e))
            return False
    
    def get_history_summary(self, business_id: int, days: int = 7) -> Dict[str, Any]:
        """店舗の最近のステータス履歴サマリーを取得する"""
        try:
            query = """
            SELECT 
                biz_date,
                working_rate
            FROM status_history 
            WHERE business_id = %s 
            AND biz_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY biz_date DESC
            """
            
            results = self.db_manager.execute_query(query, (business_id, days))
            
            if not results:
                return {"business_id": business_id, "history": [], "summary": {}}
            
            # Calculate summary statistics
            rates = [r['working_rate'] for r in results if r['working_rate'] is not None]
            
            summary = {
                "business_id": business_id,
                "history": [
                    {
                        "date": r['biz_date'].isoformat() if hasattr(r['biz_date'], 'isoformat') else str(r['biz_date']),
                        "working_rate": float(r['working_rate']) if r['working_rate'] else 0.0
                    }
                    for r in results
                ],
                "summary": {
                    "days_calculated": len(results),
                    "average_rate": sum(rates) / len(rates) if rates else 0.0,
                    "max_rate": max(rates) if rates else 0.0,
                    "min_rate": min(rates) if rates else 0.0
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"店舗 {business_id} の履歴サマリー取得エラー: {e}")
            return {"business_id": business_id, "error": str(e)}

def run_status_history(
    business_id: int = None,
    target_date: str = None,
    force: bool = False
) -> BatchJobResult:
    """
    ステータス履歴計算ジョブを実行する。
    
    Args:
        business_id: 処理する特定の店舗ID（全店舗の場合はNone）
        target_date: 計算する特定の日付（YYYY-MM-DD、自動検出の場合はNone）
        force: 適切な時間でなくても強制実行する
    
    Returns:
        実行詳細を含むBatchJobResult
    """
    job = StatusHistoryJob()
    return job.run(business_id=business_id, target_date=target_date, force=force)

def get_business_history_summary(business_id: int, days: int = 7) -> Dict[str, Any]:
    """
    店舗のステータス履歴サマリーを取得する。
    
    Args:
        business_id: サマリーを取得する店舗ID
        days: 含める最近の日数
    
    Returns:
        履歴データとサマリー統計を含む辞書
    """
    job = StatusHistoryJob()
    return job.get_history_summary(business_id, days)

if __name__ == "__main__":
    # Allow running directly for testing
    import sys
    
    force_run = "--force" in sys.argv
    business_id = None
    target_date = None
    
    # Parse command line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--business-id" and i + 1 < len(sys.argv):
            business_id = int(sys.argv[i + 1])
        elif arg == "--date" and i + 1 < len(sys.argv):
            target_date = sys.argv[i + 1]
    
    # Run the job
    result = run_status_history(
        business_id=business_id,
        target_date=target_date,
        force=force_run
    )
    
    print(f"ステータス履歴ジョブ結果:")
    print(f"成功: {result.success}")
    print(f"処理済み: {result.processed_count}")
    print(f"エラー: {result.error_count}")
    if result.errors:
        print(f"エラーメッセージ: {result.errors}")
    if result.duration_seconds:
        print(f"実行時間: {result.duration_seconds:.2f}s")
