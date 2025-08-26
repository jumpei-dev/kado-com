"""
ステータス収集ジョブ - 営業時間中にキャストの稼働状況を収集する
営業時間中に30分間隔で実行される
"""

import asyncio
import logging
from datetime import datetime, time
from typing import List, Dict, Any

from core.database import DatabaseManager
from core.models import Business, Cast, ScrapingResult, BatchJobResult
from core.scraper import ScraperFactory
from utils.logging_utils import get_job_logger, JobLoggerAdapter
from utils.datetime_utils import now_jst_naive, is_business_hours, should_run_status_collection

logger = get_job_logger('status_collection')

class StatusCollectionJob:
    """キャスト稼働状況収集ジョブ"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.name = "Status Collection"
    
    async def run(self, business_id: int = None, force: bool = False) -> BatchJobResult:
        """
        ステータス収集ジョブを実行する
        
        Args:
            business_id: 処理対象の特定店舗ID（Noneの場合は全店舗）
            force: 営業時間外でも強制実行するかどうか
        """
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_logger = JobLoggerAdapter(logger, self.name, run_id)
        
        result = BatchJobResult(
            job_name=self.name,
            started_at=now_jst_naive()
        )
        
        job_logger.job_started()
        
        try:
            # 処理対象の店舗を取得
            if business_id:
                businesses_data = self.db_manager.execute_query(
                    "SELECT * FROM business WHERE id = %s AND is_active = true",
                    (business_id,)
                )
            else:
                businesses_data = self.db_manager.get_businesses()
            
            if not businesses_data:
                job_logger.info("処理対象の店舗が見つかりませんでした")
                result.finalize(success=True)
                return result
            
            businesses = [Business.from_dict(b) for b in businesses_data]
            
            for business in businesses:
                job_logger.processing_item("business", business.name)
                
                # 営業時間内かチェック（強制実行でない場合）
                current_time = now_jst_naive()
                if not force and not is_business_hours(
                    current_time,
                    business.business_hours_start,
                    business.business_hours_end,
                    buffer_minutes=30
                ):
                    job_logger.info(f"{business.name}は営業時間外のためスキップします")
                    continue
                
                # この店舗のキャストを処理
                success = await self._process_business_casts(business, job_logger)
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
            error_msg = f"ジョブ実行に失敗しました: {e}"
            result.add_error(error_msg)
            result.finalize(success=False)
            job_logger.job_failed(error_msg)
            logger.exception("ステータス収集ジョブが失敗しました")
        
        return result
    
    async def _process_business_casts(
        self,
        business: Business,
        job_logger: JobLoggerAdapter
    ) -> bool:
        """特定の店舗のキャストを処理する"""
        try:
            # この店舗のキャストを取得
            casts_data = self.db_manager.get_casts_by_business(business.id)
            if not casts_data:
                job_logger.info(f"店舗{business.name}にキャストが見つかりませんでした")
                return True
            
            casts = [Cast.from_dict(c) for c in casts_data]
            job_logger.info(f"{business.name}の{len(casts)}人のキャストを処理中")
            
            # この店舗に適したスクレイパーを作成
            scraper = ScraperFactory.create_scraper(business.site_type)
            
            # キャストの状況をスクレイピング
            async with scraper:
                scraping_results = await scraper.scrape_multiple_casts(casts)
            
            # 結果をデータベースに保存
            saved_count = 0
            error_count = 0
            
            for scraping_result in scraping_results:
                if scraping_result.success:
                    success = self.db_manager.insert_status(
                        scraping_result.cast_id,
                        scraping_result.is_working,
                        scraping_result.collected_at.isoformat()
                    )
                    if success:
                        saved_count += 1
                        job_logger.debug(f"キャストID {scraping_result.cast_id}のステータスを保存しました")
                    else:
                        error_count += 1
                        job_logger.warning(f"キャストID {scraping_result.cast_id}のステータス保存に失敗しました")
                else:
                    error_count += 1
                    job_logger.warning(
                        f"キャストID {scraping_result.cast_id}のスクレイピングに失敗しました: "
                        f"{scraping_result.error_message}"
                    )
            
            job_logger.item_success(
                f"店舗 {business.name}",
                f"保存: {saved_count}, エラー: {error_count}"
            )
            
            return error_count == 0
            
        except Exception as e:
            job_logger.item_error(f"店舗 {business.name}", str(e))
            return False

async def run_status_collection(business_id: int = None, force: bool = False) -> BatchJobResult:
    """
    ステータス収集ジョブを実行する
    
    Args:
        business_id: 処理対象の特定店舗ID（Noneの場合は全店舗）
        force: 営業時間外でも強制実行するかどうか
    
    Returns:
        実行詳細を含むBatchJobResult
    """
    job = StatusCollectionJob()
    return await job.run(business_id=business_id, force=force)

if __name__ == "__main__":
    # テスト用に直接実行可能
    import sys
    
    force_run = "--force" in sys.argv
    business_id = None
    
    # business_id引数をチェック
    for i, arg in enumerate(sys.argv):
        if arg == "--business-id" and i + 1 < len(sys.argv):
            business_id = int(sys.argv[i + 1])
            break
    
    # ジョブを実行
    result = asyncio.run(run_status_collection(business_id=business_id, force=force_run))
    
    print(f"ステータス収集ジョブ結果:")
    print(f"成功: {result.success}")
    print(f"処理件数: {result.processed_count}")
    print(f"エラー件数: {result.error_count}")
    if result.errors:
        print(f"エラーメッセージ: {result.errors}")
    if result.duration_seconds:
        print(f"実行時間: {result.duration_seconds:.2f}s")
