"""
稼働状況取得スケジューラー
30分ごとに InScope=True かつ営業時間中の店舗から稼働状況を取得
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from batch.core.database import DatabaseManager
from batch.jobs.status_collection.collector import collect_all_working_status
from batch.utils.logging_utils import get_logger
from batch.utils.config import Config
from batch.utils.datetime_utils import get_current_jst_datetime

logger = get_logger(__name__)


class StatusCollectionScheduler:
    """稼働状況取得専用スケジューラー"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone='Asia/Tokyo')
        self.database = Database()
        self.config = Config()
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
        
        # 30分間隔のジョブを追加
        status_collection_interval = self.config.get("scheduling.status_collection_interval", 30)
        self.scheduler.add_job(
            func=self._collect_status_data,
            trigger=IntervalTrigger(minutes=status_collection_interval),
            id='status_collection',
            name='稼働状況取得',
            max_instances=1,
            coalesce=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info("稼働状況取得スケジューラーが開始されました")
        logger.info(f"稼働状況取得: {status_collection_interval}分間隔で実行されます")
        
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
        try:
            logger.info("稼働状況収集ジョブを開始")
            
            # データベースから対象店舗情報を取得
            businesses_dict = await self._get_target_businesses()
            
            if not businesses_dict:
                logger.info("対象店舗がありません（InScope=True かつ営業時間中の店舗なし）")
                logger.info("次回の30分後に再チェックします")
                return
            
            logger.info(f"{len(businesses_dict)}店舗の稼働状況取得を開始")
            
            # 稼働状況取得実行
            success = await run_status_collection(businesses_dict)
            
            if success:
                logger.info("稼働状況取得処理が正常に完了しました")
            else:
                logger.error("稼働状況取得処理でエラーが発生しました")
            
        except Exception as e:
            logger.error(f"稼働状況取得が失敗: {str(e)}")
            logger.exception("稼働状況取得エラー")
    
    async def _get_target_businesses(self) -> Dict[int, Dict[str, Any]]:
        """営業時間内の対象店舗の情報を取得して新しいフォーマットで返す"""
        try:
            # データベースから店舗情報を取得（READMEのスキーマに合わせて修正）
            query = """
                SELECT business_id, name, schedule_url1 as url, 
                       'cityhaven' as media_type,  -- 仮のデフォルト値
                       'a' as cast_type, 'a' as working_type, 'a' as shift_type,
                       in_scope, open_hour, close_hour
                FROM businesses
                WHERE in_scope = true
            """
            
            businesses_data = self.database.fetch_all(query)
            current_time = get_current_jst_datetime()
            target_businesses = {}
            index = 1
            
            logger.info(f"取得した店舗数: {len(businesses_data)}店舗")
            
            for business_row in businesses_data:
                business_name = business_row.get('name', business_row['business_id'])
                open_hour = business_row.get('open_hour')
                close_hour = business_row.get('close_hour')
                
                # 営業時間チェック
                if self._is_business_hours(current_time, open_hour, close_hour):
                    target_businesses[index] = {
                        "Business ID": business_row['business_id'],
                        "URL": business_row['url'],
                        "media": business_row['media_type'],
                        "cast_type": business_row.get('cast_type', 'a'),
                        "working_type": business_row.get('working_type', 'a'), 
                        "shift_type": business_row.get('shift_type', 'a')
                    }
                    logger.info(f"営業時間内の対象店舗: {business_name} ({business_row['business_id']}) - {open_hour}時〜{close_hour}時")
                    index += 1
                else:
                    logger.debug(f"営業時間外でスキップ: {business_name} ({business_row['business_id']}) - {open_hour}時〜{close_hour}時 (現在{current_time.hour}時)")
            
            logger.info(f"営業時間内の対象店舗: {len(target_businesses)}店舗")
            return target_businesses
            
        except Exception as e:
            logger.error(f"対象店舗取得エラー: {str(e)}")
            return {}
    
    def _is_business_hours(self, current_time: datetime, open_hour, close_hour) -> bool:
        """営業時間かどうか判定"""
        try:
            # 営業時間が設定されていない場合は営業中とみなす
            if open_hour is None or close_hour is None:
                logger.debug("営業時間未設定 - 常に営業中とみなします")
                return True
            
            # 文字列の場合は整数に変換
            if isinstance(open_hour, str):
                open_hour = int(open_hour.split(':')[0])  # "09:00" -> 9
            if isinstance(close_hour, str):
                close_hour = int(close_hour.split(':')[0])  # "18:00" -> 18
                
            current_hour = current_time.hour
            
            if open_hour <= close_hour:
                # 通常のパターン (例: 9時〜18時)
                is_open = open_hour <= current_hour < close_hour
            else:
                # 夜中をまたぐパターン (例: 22時〜6時)
                is_open = current_hour >= open_hour or current_hour < close_hour
            
            logger.debug(f"営業時間判定: {open_hour}時〜{close_hour}時, 現在{current_hour}時 -> {'営業中' if is_open else '営業時間外'}")
            return is_open
            
        except Exception as e:
            logger.error(f"営業時間判定エラー: {str(e)} - デフォルトで営業中とみなします")
            return True
    
    def _log_scheduled_jobs(self):
        """スケジューラーのジョブ情報をログ出力"""
        jobs = self.scheduler.get_jobs()
        
        logger.info(f"稼働状況取得スケジューラー実行中 - {len(jobs)}個のジョブ:")
        for job in jobs:
            next_run = job.next_run_time
            logger.info(f"  - {job.name} (ID: {job.id}) - 次回実行: {next_run}")


async def run_status_collection_scheduler():
    """稼働状況取得スケジューラー（設定ファイル対応版）"""
    import pytz
    import aiocron
    from utils.config import get_scheduling_config
    
    # 設定読み込み
    config = get_scheduling_config()
    
    print("📊 稼働状況取得スケジューラーを開始中...")
    print(f"⏰ 実行間隔: {config['status_cron']}")
    print("停止するにはCtrl+Cを押してください")
    
    jst = pytz.timezone('Asia/Tokyo')
    
    @aiocron.crontab(config['status_cron'], tz=jst)
    async def scheduled_collection():
        try:
            print(f"\n🚀 稼働状況取得開始 ({datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')})")
            
            from core.database import DatabaseManager
            from jobs.status_collection.collector import collect_all_working_status
            
            db_manager = DatabaseManager()
            businesses = db_manager.get_businesses()
            
            target_businesses = {
                k: v for k, v in businesses.items() 
                if v.get('in_scope', False) == True
            }
            
            if not target_businesses:
                print("⚠️ in_scope=trueの店舗が見つかりません")
                return
            
            print(f"📊 処理対象: {len(target_businesses)}店舗")
            
            results = await collect_all_working_status(target_businesses, use_local_html=False)
            
            if results:
                saved_count = 0
                for result in results:
                    try:
                        success = db_manager.insert_status(
                            cast_id=result['cast_id'],
                            business_id=result.get('business_id', 1),
                            is_working=result['is_working'],
                            is_on_shift=result['is_on_shift'],
                            collected_at=result.get('collected_at')
                        )
                        if success:
                            saved_count += 1
                    except Exception as save_error:
                        print(f"保存エラー: {save_error}")
                
                print(f"✅ 完了: {saved_count}件のデータを保存しました")
            
        except Exception as e:
            print(f"❌ スケジューラーエラー: {e}")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ スケジューラーを停止しました")


if __name__ == "__main__":
    asyncio.run(run_status_collection_scheduler())
