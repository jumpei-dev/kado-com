"""
ステータス収集ジョブ - 営業時間中にキャストの稼働状況を収集する
営業時間中に30分間隔で実行される

Strategy Pattern を使用して異なるメディアサイトとタイプに対応
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json

try:
    from ..core.database import DatabaseManager
except ImportError as e:
    print(f"DatabaseManager インポート失敗: {e}")
    DatabaseManager = None

try:
    from ..utils.datetime_utils import get_current_jst_datetime
except ImportError as e:
    print(f"datetime_utils インポート失敗: {e}")
    def get_current_jst_datetime():
        from datetime import datetime
        return datetime.now()

try:
    from ..utils.logging_utils import get_logger
except ImportError as e:
    print(f"logging_utils インポート失敗: {e}")
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class ScrapingStrategy(ABC):
    """スクレイピング戦略の基底クラス"""
    
    @abstractmethod
    async def scrape_working_status(self, session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        """稼働ステータスを収集する抽象メソッド"""
        pass


class CityheavenStrategy(ScrapingStrategy):
    """Cityheavenサイト用のスクレイピング戦略"""
    
    async def scrape_working_status(self, session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cityheavenから稼働ステータスを収集"""
        cast_list = []
        business_id = business.get("Business ID")
        url = business.get("URL")
        cast_type = business.get("cast_type", "a")
        working_type = business.get("working_type", "a")
        shift_type = business.get("shift_type", "a")
        
        if not url or not business_id:
            logger.warning(f"必要な情報が不足しています: business_id={business_id}, url={url}")
            return cast_list
            
        try:
            logger.info(f"Cityheavenからデータ収集開始: {business_id} - {url}")
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"HTTP error {response.status} for {business_id}: {url}")
                    return cast_list
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Cityheavenのcast_type別パース処理
                cast_list = await self._parse_cityhaven_data(soup, business_id, cast_type, working_type, shift_type)
                
                logger.info(f"Cityheavenからのデータ収集完了: {business_id}, {len(cast_list)}件")
                
        except Exception as e:
            logger.error(f"Cityheavenスクレイピングエラー {business_id}: {str(e)}")
            
        return cast_list
    
    async def _parse_cityhaven_data(self, soup: BeautifulSoup, business_id: str, cast_type: str, working_type: str, shift_type: str) -> List[Dict[str, Any]]:
        """Cityheavenのデータをパースしてキャスト情報を抽出"""
        cast_list = []
        current_time = get_current_jst_datetime()
        
        try:
            if cast_type == "a":
                # cast_type "a" の処理
                cast_elements = soup.select('.cast-item, .girl-item, .cast-profile')
                
            elif cast_type == "b":
                # cast_type "b" の処理
                cast_elements = soup.select('.profile-card, .cast-card')
                
            elif cast_type == "c":
                # cast_type "c" の処理
                cast_elements = soup.select('.member-info, .cast-info')
                
            else:
                logger.warning(f"未対応のcast_type: {cast_type} for business {business_id}")
                return cast_list
            
            for element in cast_elements:
                cast_info = await self._extract_cityhaven_cast_info(element, business_id, working_type, shift_type, current_time)
                if cast_info:
                    cast_list.append(cast_info)
                    
        except Exception as e:
            logger.error(f"Cityheavenデータパースエラー {business_id}: {str(e)}")
            
        return cast_list
    
    async def _extract_cityhaven_cast_info(self, element, business_id: str, working_type: str, shift_type: str, current_time: datetime) -> Optional[Dict[str, Any]]:
        """Cityheavenの個別キャスト情報を抽出"""
        try:
            # キャストIDの抽出
            cast_id = await self._extract_cast_id(element, "cityhaven", business_id)
            if not cast_id:
                return None
            
            # 稼働状況の判定
            is_working = await self._extract_is_working(element, "cityhaven", working_type)
            
            # シフト状況の判定
            is_on_shift = await self._extract_is_on_shift(element, "cityhaven", shift_type)
            
            return {
                "business_id": business_id,
                "cast_id": cast_id,
                "is_working": is_working,
                "is_on_shift": is_on_shift,
                "collected_at": current_time,
                "media_type": "cityhaven"
            }
            
        except Exception as e:
            logger.error(f"Cityheavenキャスト情報抽出エラー: {str(e)}")
            return None

    async def _extract_cast_id(self, element, media_type: str, cast_type: str) -> Optional[str]:
        """キャストIDを抽出する（Cityhaven用）"""
        try:
            if media_type == "cityhaven" and cast_type == "a":
                # pcwidgets_shukkin内のgirlid-xxxパターンを抽出
                shukkin_div = element.select_one('.pcwidgets_shukkin')
                if shukkin_div:
                    girl_link = shukkin_div.select_one('a[href*="girlid-"]')
                    if girl_link:
                        href = girl_link.get('href', '')
                        # girlid-58869431のような形式から数字部分を抽出
                        import re
                        match = re.search(r'girlid-(\d+)', href)
                        if match:
                            return match.group(1)
                
                # フォールバック: 他のパターンでキャスト名/IDを取得
                name_element = element.select_one('.name, .cast-name, .girl-name, h3, h4')
                if name_element:
                    return name_element.get_text(strip=True)
                    
            else:
                # その他のパターン（拡張用）
                name_element = element.select_one('.name, .cast-name, .girl-name, h3, h4')
                if name_element:
                    return name_element.get_text(strip=True)
                    
        except Exception as e:
            logger.error(f"キャストID抽出エラー ({media_type}): {str(e)}")
        
        return None

    async def _extract_is_working(self, element, media_type: str, working_type: str) -> bool:
        """稼働状況を判定する（Cityhaven用）"""
        try:
            if media_type == "cityhaven" and working_type == "a":
                # shukkin_detail_timeから時間帯を抽出して現在時刻と比較
                time_element = element.select_one('.shukkin_detail_time')
                if time_element:
                    time_text = time_element.get_text(strip=True)
                    return await self._is_current_time_in_range(time_text)
                
            elif media_type == "cityhaven" and working_type == "b":
                # 別のパターンで稼働状況を判定
                status_indicators = element.select('.icon, .badge, .label')
                return any("出勤" in indicator.get_text() for indicator in status_indicators)
                
            # デフォルトパターン
            status_element = element.select_one('.status, .attendance, .working')
            return bool(status_element and any(keyword in status_element.get_text() for keyword in ["出勤", "待機", "受付"]))
                
        except Exception as e:
            logger.error(f"稼働状況判定エラー ({media_type}): {str(e)}")
        
        return False

    async def _extract_is_on_shift(self, element, media_type: str, shift_type: str) -> bool:
        """シフト状況を判定する（Cityhaven用）"""
        try:
            if media_type == "cityhaven" and shift_type == "a":
                # Sugunaviboxから将来の時間を取得
                suguna_box = element.select_one('.Sugunavibox')
                if suguna_box:
                    return await self._has_future_time_in_element(suguna_box)
                    
            elif media_type == "cityhaven" and shift_type == "b":
                # 出勤予定表示がある場合
                schedule_element = element.select_one('.schedule, .shift-schedule')
                return bool(schedule_element and schedule_element.get_text(strip=True))
                
            # デフォルトパターン  
            time_element = element.select_one('.time, .shift-time, .work-time')
            return bool(time_element and time_element.get_text(strip=True))
                
        except Exception as e:
            logger.error(f"シフト状況判定エラー ({media_type}): {str(e)}")
        
        return False

    async def _is_current_time_in_range(self, time_text: str) -> bool:
        """時間テキストから範囲を解析して現在時刻が含まれるかチェック"""
        try:
            import re
            from datetime import datetime
            
            # "12:00~19:00"のようなパターンを抽出
            time_pattern = r'(\d{1,2}):(\d{2}).*?(\d{1,2}):(\d{2})'
            match = re.search(time_pattern, time_text)
            
            if match:
                start_hour, start_min, end_hour, end_min = map(int, match.groups())
                current_time = get_current_jst_datetime()
                current_minutes = current_time.hour * 60 + current_time.minute
                start_minutes = start_hour * 60 + start_min
                end_minutes = end_hour * 60 + end_min
                
                # 日跨ぎのケースを考慮
                if start_minutes <= end_minutes:
                    return start_minutes <= current_minutes <= end_minutes
                else:
                    return current_minutes >= start_minutes or current_minutes <= end_minutes
                    
        except Exception as e:
            logger.error(f"時間範囲判定エラー: {str(e)}")
        
        return False

    async def _has_future_time_in_element(self, element) -> bool:
        """要素内に現在時刻より後の時間があるかチェック"""
        try:
            import re
            
            text_content = element.get_text()
            current_time = get_current_jst_datetime()
            current_minutes = current_time.hour * 60 + current_time.minute
            
            # 時間パターンを検索
            time_patterns = re.findall(r'(\d{1,2}):(\d{2})', text_content)
            
            for hour_str, min_str in time_patterns:
                hour, minute = int(hour_str), int(min_str)
                time_minutes = hour * 60 + minute
                
                # 現在時刻より後の時間が見つかった場合
                if time_minutes > current_minutes:
                    return True
                    
        except Exception as e:
            logger.error(f"将来時間判定エラー: {str(e)}")
        
        return False


class DeliherTownStrategy(ScrapingStrategy):
    """Deliher Townサイト用のスクレイピング戦略"""
    
    async def scrape_working_status(self, session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Deliher Townから稼働ステータスを収集"""
        cast_list = []
        business_id = business.get("Business ID")
        url = business.get("URL")
        cast_type = business.get("cast_type", "a")
        working_type = business.get("working_type", "a")
        shift_type = business.get("shift_type", "a")
        
        if not url or not business_id:
            logger.warning(f"必要な情報が不足しています: business_id={business_id}, url={url}")
            return cast_list
            
        try:
            logger.info(f"Deliher Townからデータ収集開始: {business_id} - {url}")
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"HTTP error {response.status} for {business_id}: {url}")
                    return cast_list
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Deliher Townのcast_type別パース処理
                cast_list = await self._parse_deliher_town_data(soup, business_id, cast_type, working_type, shift_type)
                
                logger.info(f"Deliher Townからのデータ収集完了: {business_id}, {len(cast_list)}件")
                
        except Exception as e:
            logger.error(f"Deliher Townスクレイピングエラー {business_id}: {str(e)}")
            
        return cast_list
    
    async def _parse_deliher_town_data(self, soup: BeautifulSoup, business_id: str, cast_type: str, working_type: str, shift_type: str) -> List[Dict[str, Any]]:
        """Deliher Townのデータをパースしてキャスト情報を抽出"""
        cast_list = []
        current_time = get_current_jst_datetime()
        
        try:
            if cast_type == "a":
                # cast_type "a" の処理
                cast_elements = soup.select('.lady-item, .girl-profile, .cast-box')
                
            elif cast_type == "b":
                # cast_type "b" の処理  
                cast_elements = soup.select('.profile-box, .member-card')
                
            elif cast_type == "c":
                # cast_type "c" の処理
                cast_elements = soup.select('.cast-data, .girl-data')
                
            else:
                logger.warning(f"未対応のcast_type: {cast_type} for business {business_id}")
                return cast_list
            
            for element in cast_elements:
                cast_info = await self._extract_deliher_town_cast_info(element, business_id, working_type, shift_type, current_time)
                if cast_info:
                    cast_list.append(cast_info)
                    
        except Exception as e:
            logger.error(f"Deliher Townデータパースエラー {business_id}: {str(e)}")
            
        return cast_list
    
    async def _extract_deliher_town_cast_info(self, element, business_id: str, working_type: str, shift_type: str, current_time: datetime) -> Optional[Dict[str, Any]]:
        """Deliher Townの個別キャスト情報を抽出"""
        try:
            # キャストIDの抽出
            cast_id = await self._extract_cast_id(element, "deliher_town", working_type)
            if not cast_id:
                return None
            
            # 稼働状況の判定
            is_working = await self._extract_is_working(element, "deliher_town", working_type)
            
            # シフト状況の判定
            is_on_shift = await self._extract_is_on_shift(element, "deliher_town", shift_type)
            
            return {
                "business_id": business_id,
                "cast_id": cast_id,
                "is_working": is_working,
                "is_on_shift": is_on_shift,
                "collected_at": current_time,
                "media_type": "deliher_town"
            }
            
        except Exception as e:
            logger.error(f"Deliher Townキャスト情報抽出エラー: {str(e)}")
            return None

    async def _extract_cast_id(self, element, media_type: str, cast_type: str) -> Optional[str]:
        """キャストIDを抽出する（Deliher Town用）"""
        try:
            if media_type == "deliher_town" and cast_type == "a":
                # TODO: deliher_town用の具体的な実装が必要
                # 現在は名前を取得（将来的に実際のIDパターンを実装）
                name_element = element.select_one('.lady-name, .girl-name, .cast-name, h2, h3')
                if name_element:
                    return name_element.get_text(strip=True)
                    
            else:
                # その他のパターン
                name_element = element.select_one('.lady-name, .girl-name, .cast-name, h2, h3')
                if name_element:
                    return name_element.get_text(strip=True)
                    
        except Exception as e:
            logger.error(f"キャストID抽出エラー ({media_type}): {str(e)}")
        
        return None

    async def _extract_is_working(self, element, media_type: str, working_type: str) -> bool:
        """稼働状況を判定する（Deliher Town用）"""
        try:
            if media_type == "deliher_town" and working_type == "a":
                # TODO: deliher_town用の具体的な実装が必要
                status_element = element.select_one('.status, .work-status, .attendance-status')
                return bool(status_element and any(keyword in status_element.get_text() for keyword in ["出勤中", "待機中", "受付中"]))
                
            elif media_type == "deliher_town" and working_type == "b":
                # アイコンベースでの判定
                working_icons = element.select('.working-icon, .status-icon, .attendance-icon')
                return len(working_icons) > 0
                
            # デフォルトパターン
            status_element = element.select_one('.status, .work-status, .attendance-status')
            return bool(status_element and any(keyword in status_element.get_text() for keyword in ["出勤中", "待機中", "受付中"]))
                
        except Exception as e:
            logger.error(f"稼働状況判定エラー ({media_type}): {str(e)}")
        
        return False

    async def _extract_is_on_shift(self, element, media_type: str, shift_type: str) -> bool:
        """シフト状況を判定する（Deliher Town用）"""
        try:
            if media_type == "deliher_town" and shift_type == "a":
                # TODO: deliher_town用の具体的な実装が必要
                schedule_element = element.select_one('.schedule, .shift-schedule')
                return bool(schedule_element and schedule_element.get_text(strip=True))
                
            elif media_type == "deliher_town" and shift_type == "b":
                # 出勤予定表示がある場合
                schedule_element = element.select_one('.schedule, .shift-schedule')
                return bool(schedule_element and schedule_element.get_text(strip=True))
                
            # デフォルトパターン
            time_element = element.select_one('.time, .shift-time, .work-time')
            return bool(time_element and time_element.get_text(strip=True))
                
        except Exception as e:
            logger.error(f"シフト状況判定エラー ({media_type}): {str(e)}")
        
        return False


class ScrapingStrategyFactory:
    """スクレイピング戦略のファクトリークラス"""
    
    @staticmethod
    def create_strategy(media_type: str) -> ScrapingStrategy:
        """メディアタイプに応じた戦略を作成"""
        if media_type == "cityhaven":
            return CityheavenStrategy()
        elif media_type == "deliher_town":
            return DeliherTownStrategy()
        else:
            raise ValueError(f"未対応のメディアタイプ: {media_type}")



async def collect_status_for_business(session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
    """単一の店舗のステータス収集を実行"""
    try:
        media_type = business.get("media")
        if not media_type:
            logger.warning(f"メディアタイプが指定されていません: {business}")
            return []
        
        strategy = ScrapingStrategyFactory.create_strategy(media_type)
        cast_list = await strategy.scrape_working_status(session, business)
        
        return cast_list
        
    except Exception as e:
        business_id = business.get("Business ID", "unknown")
        logger.error(f"店舗 {business_id} のステータス収集エラー: {str(e)}")
        return []


async def collect_all_working_status(businesses: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """全店舗のキャスト稼働ステータスを並行収集"""
    logger.info("全店舗のキャスト稼働ステータス収集を開始")
    
    # 固定値でmax_concurrentを設定
    max_concurrent = 5  # デフォルト値
    
    # セマフォで並行数を制御
    semaphore = asyncio.Semaphore(max_concurrent)
    all_cast_data = []
    
    async def collect_with_semaphore(session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        async with semaphore:
            return await collect_status_for_business(session, business)
    
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
    
    logger.info(f"全店舗のキャスト稼働ステータス収集完了: 合計 {len(all_cast_data)} 件")
    return all_cast_data


async def save_working_status_to_database(cast_data_list: List[Dict[str, Any]]) -> bool:
    """稼働ステータスデータをデータベースに保存"""
    if not cast_data_list:
        logger.info("保存するデータがありません")
        return True
    
    try:
        if DatabaseManager:
            database = DatabaseManager()
        else:
            logger.error("DatabaseManagerが利用できません")
            return False
        
        # バッチでデータを保存（テーブル名をstatusに変更）
        insert_query = """
            INSERT INTO status 
            (business_id, cast_id, is_working, is_on_shift, datetime) 
            VALUES (%s, %s, %s, %s, %s)
        """
        
        # 個別にデータを保存
        saved_count = 0
        for cast_data in cast_data_list:
            try:
                database.execute_command(insert_query, (
                    cast_data["business_id"],
                    cast_data["cast_id"], 
                    cast_data["is_working"],
                    cast_data["is_on_shift"],
                    cast_data["collected_at"]
                ))
                saved_count += 1
            except Exception as save_error:
                logger.error(f"個別保存エラー: {save_error}")
        
        logger.info(f"稼働ステータスをデータベースに保存しました: {saved_count} 件")
        return True
        
    except Exception as e:
        logger.error(f"データベース保存エラー: {str(e)}")
        return False


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


"""
保守用メモ: 期待されるデータフォーマット

入力データ形式 (BUSINESSES):
{
    1: {
        "Business ID": "A01",
        "URL": "https://example.com/business/a01", 
        "media": "cityhaven",
        "cast_type": "a",
        "working_type": "a", 
        "shift_type": "a"
    },
    2: {
        "Business ID": "B02",
        "URL": "https://example.com/business/b02",
        "media": "deliher_town", 
        "cast_type": "b",
        "working_type": "b",
        "shift_type": "b"
    }
}

出力データ形式 (STATUSES):
[
    {
        "business_id": "A01",
        "cast_id": "A124234", 
        "is_working": True,
        "is_on_shift": True,
        "collected_at": "2025-08-26 12:00:00",
        "media_type": "cityhaven"
    },
    {
        "business_id": "A01", 
        "cast_id": "B19834",
        "is_working": False,
        "is_on_shift": True,
        "collected_at": "2025-08-26 12:00:00", 
        "media_type": "cityhaven"
    }
]

関数の役割分担:
- _extract_cast_id: キャストIDを抽出（girlid-XXXパターンなど）
- _extract_is_working: 現在の稼働状況を判定（出勤時間帯チェックなど）
- _extract_is_on_shift: シフト予定を判定（将来の予定時間チェックなど）
"""

# サンプルデータ構造（保守用）
STATUSES_SAMPLE = [
    {
        "Business_ID": "A01",
        "RecordedAt": "2025-08-26 12:00",
        "CastId": "A124234",
        "IsWorking": True,
        "IsOnShift": True
    },
    {
        "Business_ID": "A01", 
        "RecordedAt": "2025-08-26 12:00",
        "CastId": "B19834",
        "IsWorking": False,
        "IsOnShift": True
    }
]

# 上のjsonの例は保守の時のために書き残しておいて欲しい











