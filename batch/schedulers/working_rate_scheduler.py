"""
稼働率計算スケジューラー
毎日12時に前日の稼働率を計算してStatusHistoryに保存
"""

import asyncio
import signal
import sys
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.database import DatabaseManager
from jobs.working_rate_calculation import run_working_rate_calculation
from utils.logging_utils import setup_logging, get_job_logger, JobLoggerAdapter
from utils.config import get_config

logger = get_job_logger('working_rate_scheduler')

class WorkingRateScheduler:
    """稼働率計算専用スケジューラー"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone='Asia/Tokyo')
        self.db_manager = DatabaseManager()
        self.config = get_config()
        self.is_running = False
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """正常なシャットダウンのためのシグナルハンドラー"""
        def signal_handler(signum, frame):
            logger.info(f"稼働率計算: シグナル{signum}受信、シャットダウン中...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """スケジューラー開始"""
        if self.is_running:
            logger.warning("稼働率計算スケジューラーは既に実行中です")
            return
        
        logger.info("稼働率計算スケジューラーを開始中...")
        
        # ログ設定
        setup_logging(
            log_level=self.config.logging.level,
            log_dir=self.config.logging.log_dir,
            max_bytes=self.config.logging.max_file_size,
            backup_count=self.config.logging.backup_count
        )
        
        # 毎日12時の日次ジョブを追加
        self.scheduler.add_job(
            func=self._calculate_working_rates,
            trigger=CronTrigger(
                hour=self.config.scheduling.history_calculation_hour,
                minute=self.config.scheduling.history_calculation_minute
            ),
            id='working_rate_calculation',
            name='稼働率計算',
            max_instances=1
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("稼働率計算スケジューラーが開始されました")
        logger.info(f"稼働率計算: 毎日{self.config.scheduling.history_calculation_hour}:{self.config.scheduling.history_calculation_minute:02d}に実行されます")
        
        # 現在のジョブ情報を出力
        self._log_scheduled_jobs()
    
    def stop(self):
        """スケジューラー停止"""
        if self.scheduler and self.is_running:
            logger.info("稼働率計算スケジューラーを停止中...")
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("稼働率計算スケジューラーが停止されました")
    
    def _calculate_working_rates(self):
        """稼働率の計算実行"""
        job_logger = JobLoggerAdapter(logger, "稼働率計算実行")
        
        try:
            # 前日の日付を算出
            yesterday = datetime.now().date() - timedelta(days=1)
            
            job_logger.info(f"{yesterday}の稼働率計算を開始")
            
            # 稼働率計算実行
            result = run_working_rate_calculation(target_date=yesterday)
            
            job_logger.info(
                f"稼働率計算完了 - 成功: {result.success}, "
                f"処理済み店舗数: {result.processed_count}, エラー: {result.error_count}"
            )
            
            if result.error_count > 0:
                job_logger.warning(f"エラーが発生した店舗: {result.error_count}件")
                for error in result.errors[:3]:  # 最初の3件のエラーを表示
                    job_logger.error(f"  - {error}")
            
            # 成功した店舗の概要を表示
            if result.calculated_businesses:
                job_logger.info(f"稼働率計算結果（抜粋）:")
                for business in result.calculated_businesses[:5]:  # 最初の5店舗を表示
                    job_logger.info(f"  - {business['business_name']}: {business['working_rate']:.1%}")
            
        except Exception as e:
            job_logger.error(f"稼働率計算が失敗: {e}")
            logger.exception("稼働率計算エラー")
    
    def _log_scheduled_jobs(self):
        """スケジューラーのジョブ情報をログ出力"""
        jobs = self.scheduler.get_jobs()
        
        logger.info(f"稼働率計算スケジューラー実行中 - {len(jobs)}個のジョブ:")
        for job in jobs:
            next_run = job.next_run_time
            logger.info(f"  - {job.name} (ID: {job.id}) - 次回実行: {next_run}")

async def run_working_rate_scheduler():
    """稼働率計算スケジューラーを実行"""
    scheduler = WorkingRateScheduler()
    
    try:
        scheduler.start()
        
        # 無限ループで実行継続
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("稼働率計算: 割り込み信号を受信、シャットダウン中...")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    asyncio.run(run_working_rate_scheduler())
