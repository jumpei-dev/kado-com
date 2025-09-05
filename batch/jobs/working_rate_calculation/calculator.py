"""
稼働率計算処理

前日の営業時間中のデータから稼働率を計算
"""

from datetime import datetime, date, timedelta, time
from typing import Optional, List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import StatusRecord, WorkingRateResult
from .data_retriever import DataRetriever
from .rate_calculator import RateCalculator
from .history_saver import HistorySaver

try:
    from ..core.database import DatabaseManager
except ImportError:
    from core.database import DatabaseManager

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class WorkingRateCalculator:
    """稼働率計算のメインクラス"""
    
    def __init__(self):
        self.database = DatabaseManager()
        self.data_retriever = DataRetriever(self.database)
        self.rate_calculator = RateCalculator()
        self.history_saver = HistorySaver(self.database)
        self.max_concurrent = 10  # デフォルト値
    
    async def run_working_rate_calculation(self, target_date: Optional[date] = None, force: bool = False) -> WorkingRateResult:
        """
        稼働率計算を実行
        
        Args:
            target_date: 計算対象日付（省略時は前日）
            force: 強制実行フラグ（既存データを上書き）
        
        Returns:
            WorkingRateResult: 計算結果
        """
        start_time = datetime.now()
        
        # 対象日の決定（前日）
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).date()
        
        logger.info(f"稼働率計算開始: 対象日={target_date}, 強制実行={force}")
        
        try:
            # 既存データチェック（強制実行でない場合）
            if not force and await self._has_existing_data(target_date):
                logger.info(f"対象日{target_date}の稼働率データは既に存在します（強制実行=False）")
                return WorkingRateResult(
                    success=True,
                    processed_count=0,
                    error_count=0,
                    errors=[],
                    duration_seconds=0.0,
                    calculated_businesses=[]
                )
            
            # 店舗一覧を取得（InScope=Trueのみ）
            businesses = await self.data_retriever.get_target_businesses()
            if not businesses:
                logger.warning("計算対象店舗が見つかりません")
                return WorkingRateResult(
                    success=False,
                    processed_count=0,
                    error_count=1,
                    errors=["計算対象店舗が見つかりません"],
                    duration_seconds=(datetime.now() - start_time).total_seconds(),
                    calculated_businesses=[]
                )
            
            # 並行処理で各店舗の稼働率計算
            results = await self._calculate_working_rates_for_all_businesses(businesses, target_date)
            
            # 結果集計
            successful_businesses = []
            errors = []
            
            for business_id, result in results.items():
                if result["success"]:
                    successful_businesses.append(result["data"])
                else:
                    errors.append(f"店舗{business_id}: {result['error']}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"稼働率計算完了: 成功={len(successful_businesses)}, "
                f"エラー={len(errors)}, 実行時間={duration:.2f}秒"
            )
            
            return WorkingRateResult(
                success=len(errors) == 0,
                processed_count=len(successful_businesses),
                error_count=len(errors),
                errors=errors,
                duration_seconds=duration,
                calculated_businesses=successful_businesses
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"稼働率計算で予期しないエラー: {e}"
            logger.error(error_msg)
            
            return WorkingRateResult(
                success=False,
                processed_count=0,
                error_count=1,
                errors=[error_msg],
                duration_seconds=duration,
                calculated_businesses=[]
            )
    
    async def _has_existing_data(self, target_date: date) -> bool:
        """指定日のstatus_historyデータが既に存在するかチェック"""
        try:
            query = """
                SELECT COUNT(*) as count 
                FROM status_history 
                WHERE biz_date = %s
            """
            result = self.database.fetch_one(query, (target_date,))
            existing_count = result['count'] if result else 0
            
            logger.debug(f"既存データ件数: {existing_count}件")
            return existing_count > 0
            
        except Exception as e:
            logger.error(f"既存データチェックエラー: {e}")
            return False
    
    async def _calculate_working_rates_for_all_businesses(
        self, 
        businesses: List[Dict[str, Any]], 
        target_date: date
    ) -> Dict[str, Dict[str, Any]]:
        """全店舗の稼働率を並行計算"""
        
        max_workers = self.max_concurrent
        results = {}
        
        logger.info(f"並行処理開始: {len(businesses)}店舗, 最大{max_workers}並行")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 各店舗の計算タスクを作成
            future_to_business = {
                executor.submit(
                    self._calculate_single_business_working_rate, 
                    business, 
                    target_date
                ): business
                for business in businesses
            }
            
            # 完了した順に結果を処理
            for future in as_completed(future_to_business):
                business = future_to_business[future]
                
                try:
                    result = future.result()
                    results[business['business_id']] = {
                        "success": True,
                        "data": result,
                        "error": None
                    }
                    logger.debug(f"店舗{business.get('name', business['business_id'])}の稼働率計算完了")
                    
                except Exception as e:
                    results[business['business_id']] = {
                        "success": False,
                        "data": None,
                        "error": str(e)
                    }
                    logger.error(f"店舗{business.get('name', business['business_id'])}の稼働率計算エラー: {e}")
        
        return results
    
    def _calculate_single_business_working_rate(self, business: Dict[str, Any], target_date: date) -> Dict[str, Any]:
        """単一店舗の稼働率計算"""
        
        try:
            business_id = business['business_id']
            business_name = business.get('name', business_id)
            
            # 店舗の前日の営業時間を取得
            business_hours = self.data_retriever.get_business_hours(business)
            
            # 前日の営業時間中のStatusデータを取得（SQLで高度な絞り込み）
            status_records = self.data_retriever.get_business_status_data_in_hours(
                business_id, 
                target_date, 
                business_hours
            )
            
            if not status_records:
                logger.warning(f"店舗{business_name}: 営業時間中のStatusデータが見つかりません")
                working_rate_percentage = 0.0
            else:
                # 稼働率計算（capacity補正適用）
                working_rate = self.rate_calculator.calculate_working_rate_from_records(status_records, business)
                working_rate_percentage = working_rate * 100.0
            
            # status_historyに保存するデータを作成
            history_data = {
                "business_id": business_id,
                "biz_date": target_date,
                "working_rate": working_rate_percentage
            }
            
            # status_historyテーブルに保存
            self.history_saver.save_to_status_history(history_data)
            
            logger.info(
                f"店舗{business_name}: 稼働率={working_rate_percentage:.2f}% "
                f"(レコード数:{len(status_records)}件)"
            )
            return history_data
            
        except Exception as e:
            logger.error(f"店舗{business.get('name', business_id)}の稼働率計算エラー: {e}")
            raise
