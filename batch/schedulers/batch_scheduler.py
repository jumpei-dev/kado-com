"""
統合バッチスケジューラー

全てのバッチジョブを統合管理するメインスケジューラー
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

from .status_collection_scheduler import StatusCollectionScheduler
from .working_rate_scheduler import WorkingRateScheduler

try:
    from ..core.database import DatabaseManager
    from ..core.models import Business
except ImportError:
    try:
        from batch.core.database import DatabaseManager
        from batch.core.models import Business
    except ImportError:
        DatabaseManager = None
        Business = None

try:
    from ..utils.logging_utils import setup_logging, get_job_logger, JobLoggerAdapter
    from ..utils.config import get_config
    from ..utils.datetime_utils import (
        now_jst_naive, is_business_hours,
        should_run_status_collection, should_run_history_calculation
    )
except ImportError:
    def setup_logging(): pass
    def get_job_logger(name): 
        import logging
        return logging.getLogger(name)
    def get_config(): 
        return {}
    def now_jst_naive(): 
        return datetime.now()
    def is_business_hours(): 
        return True
    def should_run_status_collection(): 
        return True
    def should_run_history_calculation(): 
        return True

logger = get_job_logger('batch_scheduler')


class BatchScheduler:
    """統合バッチスケジューラー - 全てのジョブを統合管理"""
    
    def __init__(self):
        """スケジューラーの初期化"""
        self.scheduler = AsyncIOScheduler()
        self.config = get_config()
        self.database = DatabaseManager() if DatabaseManager else None
        
        # 個別スケジューラーの初期化
        self.status_collection_scheduler = StatusCollectionScheduler()
        self.working_rate_scheduler = WorkingRateScheduler()
        
        # シャットダウンハンドラーを設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("統合バッチスケジューラーを初期化しました")
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー - 優雅なシャットダウン"""
        logger.info(f"シャットダウンシグナルを受信 (シグナル: {signum})")
        asyncio.create_task(self.stop())
    
    def setup_jobs(self):
        """全ジョブのスケジュール設定"""
        try:
            # ステータス収集ジョブ（2時間間隔、営業時間中のみ）
            self.scheduler.add_job(
                self._run_status_collection,
                IntervalTrigger(hours=2),
                id='status_collection',
                name='稼働ステータス収集',
                max_instances=1,
                coalesce=True
            )
            
            # 稼働率計算ジョブ（毎日12:00）
            self.scheduler.add_job(
                self._run_working_rate_calculation,
                CronTrigger(hour=12, minute=0),
                id='working_rate_calculation',
                name='稼働率計算',
                max_instances=1,
                coalesce=True
            )
            
            # ヘルスチェックジョブ（5分間隔）
            self.scheduler.add_job(
                self._health_check,
                IntervalTrigger(minutes=5),
                id='health_check',
                name='ヘルスチェック',
                max_instances=1,
                coalesce=True
            )
            
            logger.info("全ジョブのスケジュール設定が完了しました")
            
        except Exception as e:
            logger.error(f"ジョブ設定エラー: {e}")
            raise
    
    async def _run_status_collection(self):
        """ステータス収集ジョブの実行"""
        try:
            if not should_run_status_collection():
                logger.debug("ステータス収集: 実行条件を満たしていません")
                return
            
            logger.info("🔄 ステータス収集ジョブを開始")
            result = await self.status_collection_scheduler.run_status_collection()
            
            if result.get('success', False):
                logger.info(f"✅ ステータス収集完了: {result.get('processed_count', 0)}件処理")
            else:
                logger.error(f"❌ ステータス収集失敗: {result.get('errors', [])}")
                
        except Exception as e:
            logger.error(f"ステータス収集ジョブでエラー: {e}")
    
    async def _run_working_rate_calculation(self):
        """稼働率計算ジョブの実行"""
        try:
            if not should_run_history_calculation():
                logger.debug("稼働率計算: 実行条件を満たしていません")
                return
            
            logger.info("📊 稼働率計算ジョブを開始")
            result = await self.working_rate_scheduler.run_working_rate_calculation()
            
            if result.get('success', False):
                logger.info(f"✅ 稼働率計算完了: {result.get('processed_count', 0)}店舗処理")
            else:
                logger.error(f"❌ 稼働率計算失敗: {result.get('errors', [])}")
                
        except Exception as e:
            logger.error(f"稼働率計算ジョブでエラー: {e}")
    
    async def _health_check(self):
        """システムヘルスチェック"""
        try:
            # データベース接続確認
            if self.database:
                test_query = "SELECT 1"
                self.database.fetch_one(test_query)
            
            # スケジューラー状態確認
            running_jobs = len([job for job in self.scheduler.get_jobs() if job.next_run_time])
            
            logger.debug(f"💚 ヘルスチェックOK - アクティブジョブ: {running_jobs}個")
            
        except Exception as e:
            logger.error(f"💔 ヘルスチェック失敗: {e}")
    
    async def start(self):
        """スケジューラーの開始"""
        try:
            logger.info("🚀 統合バッチスケジューラーを開始します")
            
            # ジョブの設定
            self.setup_jobs()
            
            # スケジューラー開始
            self.scheduler.start()
            logger.info("✅ スケジューラー開始完了")
            
            # スケジュール表示
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                logger.info(f"📅 ジョブ: {job.name} - 次回実行: {job.next_run_time}")
            
            # メインループ
            while True:
                await asyncio.sleep(60)  # 1分間隔でループ
                
        except Exception as e:
            logger.error(f"スケジューラー開始エラー: {e}")
            raise
    
    async def stop(self):
        """スケジューラーの停止"""
        try:
            logger.info("🛑 統合バッチスケジューラーを停止します")
            
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("✅ スケジューラー停止完了")
            else:
                logger.info("ℹ️ スケジューラーは既に停止しています")
                
        except Exception as e:
            logger.error(f"スケジューラー停止エラー: {e}")
        finally:
            sys.exit(0)
    
    def get_job_status(self) -> Dict[str, Any]:
        """ジョブ状態の取得"""
        try:
            jobs = self.scheduler.get_jobs()
            return {
                "scheduler_running": self.scheduler.running,
                "total_jobs": len(jobs),
                "jobs": [
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run": str(job.next_run_time) if job.next_run_time else None,
                        "max_instances": job.max_instances
                    }
                    for job in jobs
                ]
            }
        except Exception as e:
            logger.error(f"ジョブ状態取得エラー: {e}")
            return {"error": str(e)}


async def run_batch_scheduler():
    """統合バッチスケジューラーのメイン実行関数"""
    setup_logging()
    
    scheduler = BatchScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("👋 キーボード割り込みを受信")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
    finally:
        await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(run_batch_scheduler())
