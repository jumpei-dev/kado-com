"""
ステータス収集のオーケストレーション

全店舗の並行処理、結果の集約、JSON出力などを管理
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# Strategy imports
try:
    from .cityheaven_strategy import CityheavenStrategy
    from .dto_strategy import DtoStrategy
    from .database_saver import save_working_status_to_database
except ImportError:
    try:
        from cityheaven_strategy import CityheavenStrategy
        from dto_strategy import DtoStrategy
        from database_saver import save_working_status_to_database
    except ImportError as e:
        print(f"Strategy imports failed: {e}")

# Utilities imports
try:
    from ..utils.datetime_utils import get_current_jst_datetime
except ImportError:
    try:
        from utils.datetime_utils import get_current_jst_datetime
    except ImportError:
        def get_current_jst_datetime():
            from datetime import datetime
            return datetime.now()

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    try:
        from utils.logging_utils import get_logger
    except ImportError:
        def get_logger(name):
            import logging
            return logging.getLogger(name)

logger = get_logger(__name__)


class ScrapingStrategyFactory:
    """スクレイピング戦略のファクトリークラス"""
    
    @staticmethod
    def create_strategy(media_type: str, use_local_html: bool = False, specific_file: Optional[str] = None):
        """メディアタイプに応じた戦略を作成"""
        if media_type in ["cityhaven", "cityheaven"]:  # typoも許容
            return CityheavenStrategy(use_local_html=use_local_html, specific_file=specific_file)
        elif media_type == "dto":
            return DtoStrategy(use_local_html=use_local_html)
        else:
            raise ValueError(f"未対応のメディアタイプ: {media_type}")


async def collect_status_for_business(session: aiohttp.ClientSession, business: Dict[str, Any], use_local_html: bool = False, dom_check_mode: bool = False, specific_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    単一の店舗のステータス収集を実行
    
    Args:
        dom_check_mode: 追加店舗DOM確認モード（HTML詳細出力）
    """
    try:
        media_type = business.get("media", "cityhaven")  # デフォルトはcityhaven
        business_name = business.get("name", "")
        business_id = business.get("Business ID", "")
        base_url = business.get("schedule_url", "")
        
        if not business_name:
            logger.warning(f"店舗名が指定されていません: {business}")
            return []
        
        strategy = ScrapingStrategyFactory.create_strategy(media_type, use_local_html, specific_file)
        cast_statuses = await strategy.scrape_working_status(
            business_name=business_name,
            business_id=str(business_id), 
            base_url=base_url,
            use_local=use_local_html,
            dom_check_mode=dom_check_mode  # DOM確認モードを戦略に渡す
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


async def collect_all_working_status(businesses: Dict[int, Dict[str, Any]], use_local_html: bool = False, dom_check_mode: bool = False, specific_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    全店舗のキャスト稼働ステータスを並行収集
    
    Args:
        businesses: 店舗データ
        use_local_html: ローカルHTML使用フラグ
        dom_check_mode: 追加店舗DOM確認モード（HTML詳細出力）
        specific_file: 指定するローカルHTMLファイル名
    """
    if dom_check_mode:
        mode_text = "追加店舗DOM確認モード"
        logger.info(f"🔍 {mode_text} - HTML詳細出力が有効です")
    else:
        mode_text = "ローカルHTML" if use_local_html else "ライブスクレイピング"
    
    logger.info(f"全店舗のキャスト稼働ステータス収集を開始 ({mode_text}モード)")
    
    # DOM確認モードでは1店舗のみ処理
    if dom_check_mode:
        businesses = dict(list(businesses.items())[:1])
        logger.info(f"DOM確認モード: {len(businesses)}店舗のみ処理")
    
    # 固定値でmax_concurrentを設定
    max_concurrent = 5  # デフォルト値
    
    # セマフォで並行数を制御
    semaphore = asyncio.Semaphore(max_concurrent)
    all_cast_data = []
    
    async def collect_with_semaphore(session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        async with semaphore:
            return await collect_status_for_business(session, business, use_local_html, dom_check_mode, specific_file)
    
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


async def collect_status_by_url(target_url: str, dom_check_mode: bool = False) -> List[Dict[str, Any]]:
    """
    URL直接指定による稼働状況収集（新店舗確認用）
    
    Args:
        target_url: 対象店舗のURL
        dom_check_mode: DOM確認モード
    """
    logger.info(f"URL直接指定による稼働状況収集開始: {target_url} (dom_check_mode={dom_check_mode})")
    
    # DOM確認モード時の特別処理
    if dom_check_mode:
        print(f"🔧 追加店舗DOM確認モード: URL直接指定")
        print(f"🌐 対象URL: {target_url}")
        print("=" * 80)
    
    try:
        # URLから店舗名を推測（URL解析）
        business_name = _extract_business_name_from_url(target_url)
        
        # 一時的なbusiness_idを生成（URLベース）
        temp_business_id = _generate_temp_business_id(target_url)
        
        logger.info(f"URL解析結果: 店舗名={business_name}, 一時ID={temp_business_id}")
        
        if dom_check_mode:
            print(f"🔍 URL解析結果:")
            print(f"   推定店舗名: {business_name}")
            print(f"   一時business_id: {temp_business_id}")
            print()
        
        # CityheavenStrategyでスクレイピング実行
        strategy = CityheavenStrategy(use_local_html=False)
        cast_statuses = await strategy.scrape_working_status(
            business_name=business_name,
            business_id=temp_business_id,
            base_url=target_url,
            use_local=False,  # URL直接指定時は強制的にリモート取得
            dom_check_mode=dom_check_mode
        )
        
        logger.info(f"URL直接指定スクレイピング完了: {len(cast_statuses)}件")
        
        # DOM確認モードでの詳細サマリー
        if dom_check_mode and cast_statuses:
            _display_url_debug_summary(cast_statuses, business_name, target_url)
        
        # DB保存は行わない（新店舗確認用のため）
        if dom_check_mode:
            print(f"\n💡 DOM確認モードのため、データベースには保存しません")
        
        return cast_statuses
        
    except Exception as e:
        logger.error(f"URL直接指定エラー: {e}")
        return []


def _extract_business_name_from_url(url: str) -> str:
    """URLから店舗名を推測"""
    try:
        import re
        from urllib.parse import urlparse
        
        # URLから店舗部分を抽出
        # 例: https://www.cityheaven.net/kanagawa/A1401/A140103/new-shop/attend/ → new-shop
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        # 通常、店舗名は最後から2番目または最後の部分
        if len(path_parts) >= 2 and path_parts[-1] in ['attend', 'girllist']:
            business_name = path_parts[-2]
        elif len(path_parts) >= 1:
            business_name = path_parts[-1]
        else:
            business_name = "unknown-shop"
        
        # URLエンコードを解除し、読みやすい形に
        import urllib.parse
        business_name = urllib.parse.unquote(business_name)
        
        return business_name or "URL解析店舗"
        
    except Exception as e:
        logger.warning(f"URL解析エラー: {e}")
        return "URL直接指定店舗"


def _generate_temp_business_id(url: str) -> str:
    """URLから一時的なbusiness_IDを生成"""
    try:
        import hashlib
        
        # URLのハッシュから短いIDを生成
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        temp_id = f"temp_{url_hash}"
        
        return temp_id
        
    except Exception as e:
        logger.warning(f"一時ID生成エラー: {e}")
        return "temp_unknown"


def _display_url_debug_summary(cast_statuses: List[Dict[str, Any]], business_name: str, target_url: str):
    """URL直接指定時の詳細サマリー表示"""
    working_count = sum(1 for cast in cast_statuses if cast.get('is_working', False))
    on_shift_count = sum(1 for cast in cast_statuses if cast.get('is_on_shift', False))
    
    print(f"\n" + "=" * 80)
    print(f"🌐 URL直接指定 - DOM確認結果")
    print("=" * 80)
    print(f"🏪 店舗名: {business_name}")
    print(f"🌐 URL: {target_url}")
    print(f"📊 スクレイピング結果:")
    print(f"   総キャスト数: {len(cast_statuses)}人")
    print(f"   出勤中: {on_shift_count}人")
    print(f"   稼働中: {working_count}人")
    print(f"   稼働率: {working_count/on_shift_count*100:.1f}%" if on_shift_count > 0 else "   稼働率: N/A")
    
    print(f"\n💡 新店舗追加時のチェックポイント:")
    print(f"   ✅ HTMLの構造が既存パーサーで解析可能か")
    print(f"   ✅ sugunavi_wrapper要素の存在: {len(cast_statuses) > 0}")
    print(f"   ✅ キャストデータの抽出精度")
    print(f"   ✅ 出勤時間・稼働状態の判定精度")
    print("=" * 80)
