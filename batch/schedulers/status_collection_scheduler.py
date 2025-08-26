"""
稼働状況取得スケジューラー
30分ごとに InScope=True かつ営業時間中の店舗から稼働状況を取得
"""

import asyncio
import signal
import sys
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.database import DatabaseManager
from core.models import Business
from jobs.status_collection import run_status_collection
from utils.logging_utils import setup_logging, get_job_logger, JobLoggerAdapter
from utils.config import get_config
from utils.datetime_utils import now_jst_naive, is_business_hours

logger = get_job_logger('status_collection_scheduler')

class StatusCollectionScheduler:
    """稼働状況取得専用スケジューラー"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone='Asia/Tokyo')
        self.db_manager = DatabaseManager()
        self.config = get_config()
        self.is_running = False
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """正常なシャットダウンのためのシグナルハンドラー"""
        def signal_handler(signum, frame):
            logger.info(f"稼働状況取得: シグナル{signum}受信、シャットダウン中...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """スケジューラー開始"""
        if self.is_running:
            logger.warning("稼働状況取得スケジューラーは既に実行中です")
            return
        
        logger.info("稼働状況取得スケジューラーを開始中...")
        
        # ログ設定
        setup_logging(
            log_level=self.config.logging.level,
            log_dir=self.config.logging.log_dir,
            max_bytes=self.config.logging.max_file_size,
            backup_count=self.config.logging.backup_count
        )
        
        # 30分間隔のジョブを追加
        self.scheduler.add_job(
            func=self._collect_status_data,
            trigger=IntervalTrigger(minutes=self.config.scheduling.status_collection_interval),
            id='status_collection',
            name='稼働状況取得',
            max_instances=1,
            coalesce=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("稼働状況取得スケジューラーが開始されました")
        logger.info(f"稼働状況取得: {self.config.scheduling.status_collection_interval}分間隔で実行されます")
        
        # 現在のジョブ情報を出力
        self._log_scheduled_jobs()
    
    def stop(self):
        """スケジューラー停止"""
        if self.scheduler and self.is_running:
            logger.info("稼働状況取得スケジューラーを停止中...")
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("稼働状況取得スケジューラーが停止されました")
    
    async def _collect_status_data(self):
        """稼働状況データの収集実行"""
        job_logger = JobLoggerAdapter(logger, "稼働状況取得実行")
        
        try:
            # InScope=True かつ営業時間中の店舗を取得
            businesses_data = self.db_manager.get_businesses()
            businesses = [Business.from_dict(b) for b in businesses_data]
            
            current_time = now_jst_naive()
            target_businesses = []
            
            for business in businesses:
                # 新仕様: InScope=True かつ営業時間中
                if (hasattr(business, 'in_scope') and business.in_scope and 
                    is_business_hours(current_time, business.open_hour, business.close_hour)):
                    target_businesses.append(business)
                    job_logger.debug(f"対象店舗: {business.name} ({business.business_id})")
            
            if not target_businesses:
                job_logger.info("対象店舗がありません（InScope=True かつ営業時間中の店舗なし）")
                return
            
            job_logger.info(f"{len(target_businesses)}店舗の稼働状況取得を開始")
            
            # 稼働状況取得実行
            result = await run_status_collection(target_businesses=target_businesses)
            
            job_logger.info(
                f"稼働状況取得完了 - 成功: {result.success}, "
                f"処理済み: {result.processed_count}, エラー: {result.error_count}"
            )
            
            if result.error_count > 0:
                job_logger.warning(f"エラーが発生した店舗: {result.error_count}件")
                for error in result.errors[:5]:  # 最初の5件のエラーを表示
                    job_logger.error(f"  - {error}")
            
        except Exception as e:
            job_logger.error(f"稼働状況取得が失敗: {e}")
            logger.exception("稼働状況取得エラー")
    
    def _log_scheduled_jobs(self):
        """スケジューラーのジョブ情報をログ出力"""
        jobs = self.scheduler.get_jobs()
        
        logger.info(f"稼働状況取得スケジューラー実行中 - {len(jobs)}個のジョブ:")
        for job in jobs:
            next_run = job.next_run_time
            logger.info(f"  - {job.name} (ID: {job.id}) - 次回実行: {next_run}")

async def run_status_collection_scheduler():
    """稼働状況取得スケジューラーを実行"""
    scheduler = StatusCollectionScheduler()
    
    try:
        scheduler.start()
        
        # 無限ループで実行継続
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("稼働状況取得: 割り込み信号を受信、シャットダウン中...")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    asyncio.run(run_status_collection_scheduler())
