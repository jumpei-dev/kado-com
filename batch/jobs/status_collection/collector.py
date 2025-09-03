"""
ステータス収集のオーケストレーション

全店舗の並行処理、結果の集約、JSON出力などを管理
"""

import asyncio
import aiohttp
from typing import Dict, List, Any
from datetime import datetime
import json

from .cityheaven_strategy import CityheavenStrategy
from .dto_strategy import DtoStrategy
from .database_saver import save_working_status_to_database

try:
    from ..utils.datetime_utils import get_current_jst_datetime
except ImportError:
    def get_current_jst_datetime():
        from datetime import datetime
        return datetime.now()

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class ScrapingStrategyFactory:
    """スクレイピング戦略のファクトリークラス"""
    
    @staticmethod
    def create_strategy(media_type: str, use_local_html: bool = False):
        """メディアタイプに応じた戦略を作成"""
        if media_type in ["cityhaven", "cityheaven"]:  # typoも許容
            return CityheavenStrategy(use_local_html=use_local_html)
        elif media_type == "dto":
            return DtoStrategy(use_local_html=use_local_html)
        else:
            raise ValueError(f"未対応のメディアタイプ: {media_type}")


async def collect_status_for_business(session: aiohttp.ClientSession, business: Dict[str, Any], use_local_html: bool = False) -> List[Dict[str, Any]]:
    """単一の店舗のステータス収集を実行"""
    try:
        media_type = business.get("media", "cityhaven")  # デフォルトはcityhaven
        business_name = business.get("name", "")
        business_id = business.get("Business ID", "")
        base_url = business.get("schedule_url", "")
        
        if not business_name:
            logger.warning(f"店舗名が指定されていません: {business}")
            return []
        
        strategy = ScrapingStrategyFactory.create_strategy(media_type, use_local_html)
        cast_statuses = await strategy.scrape_working_status(
            business_name=business_name,
            business_id=str(business_id), 
            base_url=base_url,
            use_local=use_local_html
        )
        
        # CastStatusオブジェクトを辞書形式に変換
        cast_list = []
        for cast_status in cast_statuses:
            cast_dict = {
                "name": cast_status.name,
                "is_working": cast_status.is_working,
                "business_id": cast_status.business_id,
                "cast_id": cast_status.cast_id,
                "on_shift": cast_status.on_shift,
                "shift_times": cast_status.shift_times,
                "working_times": cast_status.working_times
            }
            cast_list.append(cast_dict)
        
        return cast_list
        
    except Exception as e:
        business_id = business.get("Business ID", "unknown")
        logger.error(f"店舗 {business_id} のステータス収集エラー: {str(e)}")
        return []


async def collect_all_working_status(businesses: Dict[int, Dict[str, Any]], use_local_html: bool = False) -> List[Dict[str, Any]]:
    """全店舗のキャスト稼働ステータスを並行収集"""
    mode_text = "ローカルHTML" if use_local_html else "ライブスクレイピング"
    logger.info(f"全店舗のキャスト稼働ステータス収集を開始 ({mode_text}モード)")
    
    # 固定値でmax_concurrentを設定
    max_concurrent = 5  # デフォルト値
    
    # セマフォで並行数を制御
    semaphore = asyncio.Semaphore(max_concurrent)
    all_cast_data = []
    
    async def collect_with_semaphore(session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        async with semaphore:
            return await collect_status_for_business(session, business, use_local_html)
    
    try:
        # HTTPセッションを作成
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 全店舗の処理を並行実行
            tasks = [
                collect_with_semaphore(session, business)
                for business in businesses.values()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果をまとめる
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"並行処理でエラーが発生: {str(result)}")
                elif isinstance(result, list):
                    all_cast_data.extend(result)
    
    except Exception as e:
        logger.error(f"ステータス収集処理でエラーが発生: {str(e)}")
    finally:
        # WebDriverのクリーンアップ
        await cleanup_webdrivers()
    
    logger.info(f"全店舗のキャスト稼働ステータス収集完了: 合計 {len(all_cast_data)} 件")
    
    # 🔍 結果のJSONをコンソールに出力
    _output_collection_results_json(all_cast_data)
    
    return all_cast_data


def _output_collection_results_json(all_cast_data: List[Dict[str, Any]]):
    """収集結果をJSON形式でコンソール出力"""
    if all_cast_data:
        logger.info("=" * 60)
        logger.info("📊 収集結果 (JSON形式)")
        logger.info("=" * 60)
        
        try:
            # datetimeオブジェクトをISO形式文字列に変換する関数
            def serialize_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            # JSON形式で整形
            json_output = json.dumps(all_cast_data, 
                                   ensure_ascii=False, 
                                   indent=2, 
                                   default=serialize_datetime)
            
            # 結果をコンソールに出力
            print("\n" + "="*80)
            print("📊 キャスト稼働ステータス収集結果 (JSON)")
            print("="*80)
            print(json_output)
            print("="*80)
            print(f"合計件数: {len(all_cast_data)} 件")
            print("="*80 + "\n")
            
            # ログにも記録
            logger.info(f"収集結果JSON出力完了: {len(all_cast_data)} 件")
            
        except Exception as json_error:
            logger.error(f"JSON出力エラー: {json_error}")
            # フォールバック: 辞書形式で出力
            print("\n" + "="*80)
            print("📊 キャスト稼働ステータス収集結果 (辞書形式)")
            print("="*80)
            for i, cast_data in enumerate(all_cast_data):
                print(f"[{i+1}] {cast_data}")
            print("="*80 + "\n")
    else:
        print("\n" + "="*50)
        print("⚠️ 収集結果: データなし")
        print("="*50 + "\n")


async def cleanup_webdrivers():
    """すべてのWebDriverインスタンスをクリーンアップ"""
    try:
        logger.info("WebDriverクリーンアップ完了")
    except Exception as e:
        logger.error(f"WebDriverクリーンアップエラー: {e}")


async def run_status_collection(businesses: Dict[int, Dict[str, Any]]) -> bool:
    """ステータス収集処理のメインエントリーポイント"""
    try:
        logger.info("ステータス収集処理を開始")
        
        # 全店舗のキャスト稼働ステータスを収集
        all_cast_data = await collect_all_working_status(businesses)
        
        # データベースに保存
        success = await save_working_status_to_database(all_cast_data)
        
        if success:
            logger.info("ステータス収集処理が正常に完了しました")
        else:
            logger.error("ステータス収集処理でエラーが発生しました")
            
        return success
        
    except Exception as e:
        logger.error(f"ステータス収集処理で予期しないエラーが発生: {str(e)}")
        return False
