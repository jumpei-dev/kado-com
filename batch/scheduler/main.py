"""
自動バッチ処理のためのジョブスケジューラー。
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.database import DatabaseManager
from core.models import Business
from jobs.status_collection import run_status_collection
from jobs.working_rate_calculation import run_status_history
from utils.logging_utils import (
    setup_logging, get_job_logger, JobLoggerAdapter
)
from utils.config import get_config
from utils.datetime_utils import (
    now_jst_naive, is_business_hours,
    should_run_status_collection, should_run_history_calculation
)

logger = get_job_logger('scheduler')

class BatchScheduler:
    """バッチ処理ジョブのメインスケジューラー"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone='Asia/Tokyo')
        self.db_manager = DatabaseManager()
        self.config = get_config()
        self.is_running = False
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """正常なシャットダウンのためのシグナルハンドラーを設定する"""
        def signal_handler(signum, frame):
            logger.info(f"シグナル{signum}を受信、正常にシャットダウン中...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """スケジューラーを開始する"""
        if self.is_running:
            logger.warning("スケジューラーは既に実行中です")
            return
        
        logger.info("バッチスケジューラーを開始中...")
        
        # ログ設定
        setup_logging(
            log_level=self.config.logging.level,
            log_dir=self.config.logging.log_dir,
            max_bytes=self.config.logging.max_file_size,
            backup_count=self.config.logging.backup_count
        )
        
        # スケジューラーにジョブを追加
        self._add_scheduled_jobs()
        
        # スケジューラー開始
        self.scheduler.start()
        self.is_running = True
        
        logger.info("バッチスケジューラーが正常に開始されました")
        
        # 現在のジョブ情報を出力
        self._log_scheduled_jobs()
    
    def stop(self):
        """スケジューラーを停止"""
        if self.scheduler and self.is_running:
            logger.info("バッチスケジューラーを停止中...")
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("バッチスケジューラーが正常に停止されました")
    
    def _add_scheduled_jobs(self):
        """スケジューラーにスケジュールされたジョブを追加"""
        
        # ステータス収集ジョブ - 営業時間中に30分間隔で実行
        self.scheduler.add_job(
            func=self._run_status_collection_wrapper,
            trigger=IntervalTrigger(
                minutes=self.config.scheduling.status_collection_interval
            ),
            id='status_collection',
            name='ステータス収集',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300  # 5分
        )
        
        # ステータス履歴計算 - 6時間間隔で実行
        self.scheduler.add_job(
            func=self._run_status_history_wrapper,
            trigger=IntervalTrigger(
                hours=self.config.scheduling.history_calculation_interval // 60
            ),
            id='status_history',
            name='ステータス履歴計算',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600  # 10分
        )
        
        # 日次クリーンアップジョブ - 午前2時に実行
        self.scheduler.add_job(
            func=self._cleanup_old_logs,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_logs',
            name='ログクリーンアップ',
            max_instances=1
        )
        
        # ヘルスチェックジョブ - 15分間隔で実行
        self.scheduler.add_job(
            func=self._health_check,
            trigger=IntervalTrigger(minutes=15),
            id='health_check',
            name='システムヘルスチェック',
            max_instances=1
        )
    
    async def _run_status_collection_wrapper(self):
        """営業時間チェック付きのステータス収集ジョブのラッパー"""
        job_logger = JobLoggerAdapter(logger, "Status Collection Scheduler")
        
        try:
            # 全ての店舗を取得し、営業時間内の店舗があるかチェック
            businesses_data = self.db_manager.get_businesses()
            businesses = [Business.from_dict(b) for b in businesses_data]
            
            current_time = now_jst_naive()
            businesses_to_process = []
            
            for business in businesses:
                if should_run_status_collection(
                    current_time,
                    business.open_hour,
                    business.close_hour,
                    self.config.scheduling.business_hours_buffer
                ):
                    businesses_to_process.append(business)
            
            if not businesses_to_process:
                job_logger.info("No businesses in operating hours, skipping status collection")
                return
            
            job_logger.info(f"Running status collection for {len(businesses_to_process)} businesses")
            
            # Run status collection
            result = await run_status_collection()
            
            job_logger.info(
                f"Status collection completed - Success: {result.success}, "
                f"Processed: {result.processed_count}, Errors: {result.error_count}"
            )
            
        except Exception as e:
            job_logger.error(f"Status collection wrapper failed: {e}")
            logger.exception("Status collection wrapper error")
    
    def _run_status_history_wrapper(self):
        """Wrapper for status history calculation job."""
        job_logger = JobLoggerAdapter(logger, "Status History Scheduler")
        
        try:
            # Get all businesses and check if appropriate time for history calculation
            businesses_data = self.db_manager.get_businesses()
            businesses = [Business.from_dict(b) for b in businesses_data]
            
            current_time = now_jst_naive()
            businesses_to_process = []
            
            for business in businesses:
                if should_run_history_calculation(
                    current_time,
                    business.close_hour,
                    buffer_minutes=60
                ):
                    businesses_to_process.append(business)
            
            if not businesses_to_process:
                job_logger.info("Not appropriate time for history calculation")
                return
            
            job_logger.info(f"Running status history calculation for {len(businesses_to_process)} businesses")
            
            # Run status history calculation
            result = run_status_history()
            
            job_logger.info(
                f"Status history calculation completed - Success: {result.success}, "
                f"Processed: {result.processed_count}, Errors: {result.error_count}"
            )
            
        except Exception as e:
            job_logger.error(f"Status history wrapper failed: {e}")
            logger.exception("Status history wrapper error")
    
    def _cleanup_old_logs(self):
        """Clean up old log files."""
        job_logger = JobLoggerAdapter(logger, "Log Cleanup")
        
        try:
            import os
            import glob
            from pathlib import Path
            
            log_dir = Path(self.config.logging.log_dir)
            if not log_dir.exists():
                return
            
            # Remove log files older than 30 days
            cutoff_time = datetime.now() - timedelta(days=30)
            
            removed_count = 0
            for log_file in log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time.timestamp():
                    log_file.unlink()
                    removed_count += 1
            
            job_logger.info(f"Cleaned up {removed_count} old log files")
            
        except Exception as e:
            job_logger.error(f"Log cleanup failed: {e}")
    
    def _health_check(self):
        """Perform system health check."""
        job_logger = JobLoggerAdapter(logger, "Health Check")
        
        try:
            # Check database connection
            businesses = self.db_manager.get_businesses()
            
            job_logger.info(f"Health check passed - {len(businesses)} businesses active")
            
        except Exception as e:
            job_logger.error(f"Health check failed: {e}")
            logger.exception("Health check error")
    
    def _log_scheduled_jobs(self):
        """Log information about scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        
        logger.info(f"Scheduler running with {len(jobs)} jobs:")
        for job in jobs:
            next_run = job.next_run_time
            logger.info(f"  - {job.name} (ID: {job.id}) - Next run: {next_run}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get current status of all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        
        return {
            "scheduler_running": self.is_running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                }
                for job in jobs
            ]
        }
    
    async def run_job_manually(self, job_id: str, **kwargs) -> Dict[str, Any]:
        """Run a specific job manually."""
        job_logger = JobLoggerAdapter(logger, f"Manual {job_id}")
        
        try:
            if job_id == 'status_collection':
                result = await run_status_collection(force=True, **kwargs)
            elif job_id == 'status_history':
                result = run_status_history(force=True, **kwargs)
            else:
                raise ValueError(f"Unknown job ID: {job_id}")
            
            job_logger.info(f"Manual job execution completed - Success: {result.success}")
            
            return {
                "success": result.success,
                "processed_count": result.processed_count,
                "error_count": result.error_count,
                "errors": result.errors,
                "duration_seconds": result.duration_seconds
            }
            
        except Exception as e:
            job_logger.error(f"Manual job execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

async def run_scheduler():
    """Run the batch scheduler."""
    scheduler = BatchScheduler()
    
    try:
        scheduler.start()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    # Run the scheduler
    asyncio.run(run_scheduler())
