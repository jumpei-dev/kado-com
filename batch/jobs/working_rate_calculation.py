

"""

毎日1回走るバッチ(初期設定値が12時)

可能であればSQLでのやや高度な絞り込みをしたい。

店舗DBを見に行って、business idごとに異なる「前日の営業時間」を取得し、
business idごとの、前日の営業時間中にrecorded_atがあるレコードを取得し、
以下のstatusesを得る。

STATUSES = {
    {
        “Business ID“: “A01”,
        “RecordedAt”: “2025-08-26 13:00”,
        “CastId: “A124234”,
        “IsWorking”: True,
        “IsOnShift”: true
    }
    {
        “Business ID“: “A01”,
        “RecordedAt”: “2025-08-26 13:45”,
        “CastId: “B19834”,
        “IsWorking”: False,
        “IsOnShift”: true
    }
}



その中から、店舗IDごとに

稼働率(%) =IsWorkingがTrueのレコードの数/ IsOnshiftがTrueのレコード

を算出する

そして、

前日の営業時間のOpen HourのDateをDateとして、以下として整形しDBに記録する

STATUS_HISTORIES = {
    {
        “Business ID“: “A01”,
        “Date”: “2025-08-26”,
        “WorkingRate: 0.45
    }
}
"""

from datetime import datetime, date, timedelta, time
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.database import DatabaseManager
from utils.logging_utils import get_logger
from utils.datetime_utils import get_current_jst_datetime

logger = get_logger(__name__)

@dataclass
class StatusRecord:
    """Statusレコードのデータクラス"""
    business_id: str
    recorded_at: datetime
    cast_id: str
    is_working: bool
    is_on_shift: bool

@dataclass
class WorkingRateResult:
    """稼働率計算結果"""
    success: bool
    processed_count: int
    error_count: int
    errors: List[str]
    duration_seconds: float
    calculated_businesses: List[Dict[str, Any]]


class WorkingRateCalculationJob:
    """稼働率計算ジョブ - 前日の営業時間中のデータから稼働率を計算"""
    
    def __init__(self):
        self.database = DatabaseManager()
        self.config = Config()
    
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
            businesses = await self._get_target_businesses()
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
    
    async def _get_target_businesses(self) -> List[Dict[str, Any]]:
        """計算対象の店舗を取得（InScope=Trueのみ）"""
        try:
            query = """
                SELECT business_id, name, open_hour, close_hour
                FROM business 
                WHERE in_scope = true 
                ORDER BY business_id
            """
            businesses_data = self.database.fetch_all(query)
            
            logger.info(f"計算対象店舗: {len(businesses_data)}店舗")
            return businesses_data
            
        except Exception as e:
            logger.error(f"店舗データ取得エラー: {e}")
            return []
    
    async def _calculate_working_rates_for_all_businesses(
        self, 
        businesses: List[Dict[str, Any]], 
        target_date: date
    ) -> Dict[str, Dict[str, Any]]:
        """全店舗の稼働率を並行計算"""
        
        max_workers = self.config.get("concurrent.max_concurrent_working_rate", 10)
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
    
    def _calculate_single_business_working_rate(
        self, 
        business: Dict[str, Any], 
        target_date: date
    ) -> Dict[str, Any]:
        """単一店舗の稼働率計算"""
        
        try:
            business_id = business['business_id']
            business_name = business.get('name', business_id)
            
            # 店舗の前日の営業時間を取得
            business_hours = self._get_business_hours(business)
            
            # 前日の営業時間中のStatusデータを取得（SQLで高度な絞り込み）
            status_records = self._get_business_status_data_in_hours(
                business_id, 
                target_date, 
                business_hours
            )
            
            if not status_records:
                logger.warning(f"店舗{business_name}: 営業時間中のStatusデータが見つかりません")
                # データがない場合でも0%として記録
                working_rate_percentage = 0.0
            else:
                # 稼働率計算: IsWorkingがTrue / IsOnShiftがTrue
                working_rate = self._calculate_working_rate_from_records(status_records)
                # パーセンテージに変換（0.45 → 45.00）
                working_rate_percentage = working_rate * 100.0
            
            # status_historyに保存するデータを作成
            history_data = {
                "business_id": business_id,
                "biz_date": target_date,
                "working_rate": working_rate_percentage
            }
            
            # status_historyテーブルに保存
            self._save_to_status_history(history_data)
            
            logger.info(
                f"店舗{business_name}: 稼働率={working_rate_percentage:.2f}% "
                f"(レコード数:{len(status_records)}件)"
            )
            return history_data
            
        except Exception as e:
            logger.error(f"店舗{business.get('name', business_id)}の稼働率計算エラー: {e}")
            raise
    
    def _get_business_hours(self, business: Dict[str, Any]) -> Tuple[Optional[time], Optional[time]]:
        """店舗の営業時間を取得"""
        try:
            open_time = None
            close_time = None
            
            # open_hourの変換
            open_hour = business.get('open_hour')
            if open_hour is not None:
                if isinstance(open_hour, int):
                    open_time = time(open_hour, 0)
                elif isinstance(open_hour, str):
                    if ':' in open_hour:
                        hour, minute = map(int, open_hour.split(':'))
                        open_time = time(hour, minute)
                    else:
                        open_time = time(int(open_hour), 0)
            
            # close_hourの変換
            close_hour = business.get('close_hour')
            if close_hour is not None:
                if isinstance(close_hour, int):
                    close_time = time(close_hour, 0)
                elif isinstance(close_hour, str):
                    if ':' in close_hour:
                        hour, minute = map(int, close_hour.split(':'))
                        close_time = time(hour, minute)
                    else:
                        close_time = time(int(close_hour), 0)
            
            return open_time, close_time
            
        except Exception as e:
            logger.error(f"営業時間取得エラー: {business.get('name', 'unknown')} - {e}")
            return None, None
    
    def _get_business_status_data_in_hours(
        self, 
        business_id: str, 
        target_date: date, 
        business_hours: Tuple[Optional[time], Optional[time]]
    ) -> List[StatusRecord]:
        """指定店舗・日付の営業時間中のStatusデータを取得（SQLで高度な絞り込み）"""
        
        try:
            open_time, close_time = business_hours
            
            # 営業時間が未設定の場合は全データを取得
            if open_time is None or close_time is None:
                query = """
                    SELECT business_id, datetime as recorded_at, cast_id, is_working, is_on_shift
                    FROM status 
                    WHERE business_id = %s 
                    AND DATE(datetime) = %s
                    ORDER BY datetime
                """
                params = (business_id, target_date)
                logger.debug(f"店舗{business_id}: 営業時間未設定、全データを取得")
                
            else:
                # 営業時間の判定
                if open_time <= close_time:
                    # 通常営業（例: 9:00-18:00）
                    query = """
                        SELECT business_id, datetime as recorded_at, cast_id, is_working, is_on_shift
                        FROM status 
                        WHERE business_id = %s 
                        AND DATE(datetime) = %s
                        AND TIME(datetime) >= %s 
                        AND TIME(datetime) <= %s
                        ORDER BY datetime
                    """
                    params = (business_id, target_date, open_time, close_time)
                    logger.debug(f"店舗{business_id}: 通常営業時間 {open_time}-{close_time}")
                    
                else:
                    # 日跨ぎ営業（例: 22:00-6:00）
                    query = """
                        SELECT business_id, datetime as recorded_at, cast_id, is_working, is_on_shift
                        FROM status 
                        WHERE business_id = %s 
                        AND (
                            (DATE(datetime) = %s AND TIME(datetime) >= %s)
                            OR 
                            (DATE(datetime) = %s AND TIME(datetime) <= %s)
                        )
                        ORDER BY datetime
                    """
                    next_date = target_date + timedelta(days=1)
                    params = (business_id, target_date, open_time, next_date, close_time)
                    logger.debug(f"店舗{business_id}: 日跨ぎ営業時間 {open_time}-{close_time}")
            
            # データ取得
            raw_records = self.database.fetch_all(query, params)
            
            # StatusRecordオブジェクトに変換
            status_records = []
            for record in raw_records:
                status_records.append(StatusRecord(
                    business_id=record['business_id'],
                    recorded_at=record['recorded_at'],
                    cast_id=record['cast_id'],
                    is_working=bool(record['is_working']),
                    is_on_shift=bool(record['is_on_shift'])
                ))
            
            logger.debug(f"店舗{business_id}: 営業時間中のレコード{len(status_records)}件を取得")
            return status_records
            
        except Exception as e:
            logger.error(f"Statusデータ取得エラー: business_id={business_id}, date={target_date} - {e}")
            return []
    
    def _calculate_working_rate_from_records(self, status_records: List[StatusRecord]) -> float:
        """StatusRecordから稼働率を計算: IsWorkingがTrue / IsOnShiftがTrue"""
        
        if not status_records:
            return 0.0
        
        # IsOnShiftがTrueのレコード数（分母）
        on_shift_records = [r for r in status_records if r.is_on_shift]
        on_shift_count = len(on_shift_records)
        
        if on_shift_count == 0:
            return 0.0
        
        # IsWorkingがTrueかつIsOnShiftがTrueのレコード数（分子）
        working_count = sum(1 for r in status_records if r.is_working and r.is_on_shift)
        
        # 稼働率計算（0.0-1.0の範囲）
        working_rate = working_count / on_shift_count
        
        logger.debug(f"稼働率計算: 稼働中={working_count}, 出勤中={on_shift_count}, 稼働率={working_rate:.3f}")
        return working_rate
    
    def _save_to_status_history(self, history_data: Dict[str, Any]):
        """status_historyテーブルに稼働率データを保存"""
        try:
            # 既存データを削除（重複回避）
            delete_query = """
                DELETE FROM status_history 
                WHERE business_id = %s AND biz_date = %s
            """
            self.database.execute(
                delete_query, 
                (history_data["business_id"], history_data["biz_date"])
            )
            
            # 新しいデータを挿入
            insert_query = """
                INSERT INTO status_history 
                (business_id, biz_date, working_rate)
                VALUES (%s, %s, %s)
            """
            self.database.execute(insert_query, (
                history_data["business_id"],
                history_data["biz_date"],
                history_data["working_rate"]
            ))
            
            logger.debug(f"status_history保存成功: {history_data['business_id']} - {history_data['working_rate']:.2f}%")
            
        except Exception as e:
            logger.error(f"status_history保存エラー: {e}")
            raise


# 外部から呼び出される関数（後方互換性のため）
async def run_working_rate_calculation(target_date: Optional[date] = None, force: bool = False) -> WorkingRateResult:
    """稼働率計算のメイン関数 - 外部呼び出し用"""
    job = WorkingRateCalculationJob()
    return await job.run_working_rate_calculation(target_date, force)


# status_history.pyとの統合のための互換関数
def run_status_history(
    business_id: int = None,
    target_date: str = None,
    force: bool = False
) -> Dict[str, Any]:
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


def get_business_history_summary(business_id: int, days: int = 7) -> Dict[str, Any]:
    """
    店舗のステータス履歴サマリーを取得する（status_history.py互換）
    
    Args:
        business_id: サマリーを取得する店舗ID
        days: 含める最近の日数
    
    Returns:
        履歴データとサマリー統計を含む辞書
    """
    try:
        database = Database()
        
        query = """
            SELECT 
                biz_date,
                working_rate
            FROM status_history 
            WHERE business_id = %s 
            AND biz_date >= CURRENT_DATE - INTERVAL %s DAY
            ORDER BY biz_date DESC
        """
        
        results = database.fetch_all(query, (business_id, days))
        
        if not results:
            return {"business_id": business_id, "history": [], "summary": {}}
        
        # サマリー統計を計算
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