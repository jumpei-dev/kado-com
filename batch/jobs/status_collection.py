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

from batch.core.database import Database
from batch.utils.config import Config
from batch.utils.datetime_utils import get_current_jst_datetime
from batch.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ScrapingStrategy(ABC):
    """スクレイピング戦略の基底クラス"""
    
    @abstractmethod
    async def scrape_cast_status(self, session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        """キャストステータスを収集する抽象メソッド"""
        pass


class CityheavenStrategy(ScrapingStrategy):
    """Cityheavenサイト用のスクレイピング戦略"""
    
    async def scrape_cast_status(self, session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cityheavenからキャストステータスを収集"""
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
            # 名前の抽出
            name_element = element.select_one('.name, .cast-name, .girl-name, h3, h4')
            name = name_element.get_text(strip=True) if name_element else None
            
            if not name:
                return None
            
            # working_typeに応じた稼働状況の判定
            if working_type == "a":
                # 出勤アイコンやステータスから判定
                status_element = element.select_one('.status, .attendance, .working')
                is_working = bool(status_element and any(keyword in status_element.get_text() for keyword in ["出勤", "待機", "受付"]))
                
            elif working_type == "b":
                # 別のパターンで稼働状況を判定
                status_indicators = element.select('.icon, .badge, .label')
                is_working = any("出勤" in indicator.get_text() for indicator in status_indicators)
                
            else:
                is_working = False
            
            # shift_typeに応じた時間情報の抽出
            shift_info = await self._extract_shift_info(element, shift_type)
            
            return {
                "business_id": business_id,
                "cast_name": name,
                "is_working": is_working,
                "collected_at": current_time,
                "shift_info": shift_info,
                "media_type": "cityhaven"
            }
            
        except Exception as e:
            logger.error(f"Cityheavenキャスト情報抽出エラー: {str(e)}")
            return None

    async def _extract_shift_info(self, element, shift_type: str) -> Dict[str, Any]:
        """シフト情報を抽出する（Cityhaven用）"""
        return await _extract_shift_info(element, shift_type)


class DeliherTownStrategy(ScrapingStrategy):
    """Deliher Townサイト用のスクレイピング戦略"""
    
    async def scrape_cast_status(self, session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Deliher Townからキャストステータスを収集"""
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
            # 名前の抽出
            name_element = element.select_one('.lady-name, .girl-name, .cast-name, h2, h3')
            name = name_element.get_text(strip=True) if name_element else None
            
            if not name:
                return None
            
            # working_typeに応じた稼働状況の判定
            if working_type == "a":
                # 出勤ステータスから判定
                status_element = element.select_one('.status, .work-status, .attendance-status')
                is_working = bool(status_element and any(keyword in status_element.get_text() for keyword in ["出勤中", "待機中", "受付中"]))
                
            elif working_type == "b":
                # アイコンベースでの判定
                working_icons = element.select('.working-icon, .status-icon, .attendance-icon')
                is_working = len(working_icons) > 0
                
            else:
                is_working = False
            
            # shift_typeに応じた時間情報の抽出
            shift_info = await self._extract_shift_info(element, shift_type)
            
            return {
                "business_id": business_id,
                "cast_name": name,
                "is_working": is_working,
                "collected_at": current_time,
                "shift_info": shift_info,
                "media_type": "deliher_town"
            }
            
        except Exception as e:
            logger.error(f"Deliher Townキャスト情報抽出エラー: {str(e)}")
            return None

    async def _extract_shift_info(self, element, shift_type: str) -> Dict[str, Any]:
        """シフト情報を抽出する（Deliher Town用）"""
        return await _extract_shift_info(element, shift_type)


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


async def _extract_shift_info(element, shift_type: str) -> Dict[str, Any]:
    """シフト情報を抽出する共通メソッド"""
    shift_info = {"type": shift_type}
    
    try:
        if shift_type == "a":
            # 時間帯表示がある場合
            time_element = element.select_one('.time, .shift-time, .work-time')
            if time_element:
                shift_info["time_text"] = time_element.get_text(strip=True)
                
        elif shift_type == "b":
            # 出勤予定表示がある場合
            schedule_element = element.select_one('.schedule, .shift-schedule')
            if schedule_element:
                shift_info["schedule_text"] = schedule_element.get_text(strip=True)
    
    except Exception as e:
        logger.error(f"シフト情報抽出エラー: {str(e)}")
    
    return shift_info


async def collect_status_for_business(session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
    """単一の店舗のステータス収集を実行"""
    try:
        media_type = business.get("media")
        if not media_type:
            logger.warning(f"メディアタイプが指定されていません: {business}")
            return []
        
        strategy = ScrapingStrategyFactory.create_strategy(media_type)
        cast_list = await strategy.scrape_cast_status(session, business)
        
        return cast_list
        
    except Exception as e:
        business_id = business.get("Business ID", "unknown")
        logger.error(f"店舗 {business_id} のステータス収集エラー: {str(e)}")
        return []


async def collect_all_cast_status(businesses: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """全店舗のキャストステータスを並行収集"""
    logger.info("全店舗のキャストステータス収集を開始")
    
    config = Config()
    max_concurrent = config.get("concurrent.max_concurrent_businesses", 5)
    
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
    
    logger.info(f"全店舗のキャストステータス収集完了: 合計 {len(all_cast_data)} 件")
    return all_cast_data


async def save_cast_status_to_database(cast_data_list: List[Dict[str, Any]]) -> bool:
    """キャストステータスデータをデータベースに保存"""
    if not cast_data_list:
        logger.info("保存するデータがありません")
        return True
    
    try:
        database = Database()
        
        # バッチでデータを保存
        insert_query = """
            INSERT INTO cast_status 
            (business_id, cast_name, is_working, collected_at, shift_info, media_type) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        values = [
            (
                cast_data["business_id"],
                cast_data["cast_name"], 
                cast_data["is_working"],
                cast_data["collected_at"],
                json.dumps(cast_data["shift_info"]) if cast_data["shift_info"] else None,
                cast_data["media_type"]
            )
            for cast_data in cast_data_list
        ]
        
        database.execute_batch(insert_query, values)
        logger.info(f"キャストステータスをデータベースに保存しました: {len(values)} 件")
        return True
        
    except Exception as e:
        logger.error(f"データベース保存エラー: {str(e)}")
        return False


async def run_status_collection(businesses: Dict[int, Dict[str, Any]]) -> bool:
    """ステータス収集処理のメインエントリーポイント"""
    try:
        logger.info("ステータス収集処理を開始")
        
        # 全店舗のキャストステータスを収集
        all_cast_data = await collect_all_cast_status(businesses)
        
        # データベースに保存
        success = await save_cast_status_to_database(all_cast_data)
        
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
        "cast_name": "A124234", 
        "is_working": True,
        "collected_at": "2025-08-26 12:00",
        "shift_info": {"type": "a", "time_text": "12:00~19:00"},
        "media_type": "cityhaven"
    },
    {
        "business_id": "A01", 
        "cast_name": "B19834",
        "is_working": False,
        "collected_at": "2025-08-26 12:00", 
        "shift_info": {"type": "a"},
        "media_type": "cityhaven"
    }
]
"""
class DeliherTownStrategy(ScrapingStrategy):
    """Deliher Townサイト用のスクレイピング戦略"""
    
    async def scrape_cast_status(self, session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Deliher Townからキャストステータスを収集"""
        cast_list = []
        business_id = business.get("Business ID")
        url = business.get("URL")
        cast_type = business.get("cast_type", "a")
        working_type = business.get("working_type", "a")
        shift_type = business.get("shift_type", "a")
        "shift_type": "b"
    }
}

DB登録して欲しいjson:

STATUSES = {
    {
        “Business ID“: “A01”,
        “RecordedAt”: “2025-08-26 12:00”,
        “CastId: “A124234”,
        “IsWorking”: True,
        “IsOnShift”: true
    }
    {
        “Business ID“: “A01”,
        “RecordedAt”: “2025-08-26 12:00”,
        “CastId: “B19834”,
        “IsWorking”: False,
        “IsOnShift”: true
    }
}

上のjsonの例は保守の時のために書き残しておいて欲しい

データ整形関数
    jsonの空の枠を用意。1店舗分のjsonに対し、以下の情報を詰める
    Business IDを詰める
    RecordedAtを詰める

    スクレイピングの開始
    CastIDの取得関数を実行してキャストIDを取得、詰める
    IsWorkingの取得関数を実行して稼働中かどうかを判定、詰める
    IsOnShiftの取得関数を実行してシフト中かどうかを判定、詰める

DB登録関数
    データ整形関数で作成したデータをDBに登録する
    並行処理じゃなくてできたjsonの配列を一気に登録する

キャストIDの取得関数
    引数でurl, media, cast_typeを受け取る

    mediaがcityheavenでcast_typeがaのとき
        <div class="pcwidgets_shukkin">の後の<a href="/tokyo/A1304/A130401/ultragrace/girlid-58869431/">
        のようなaタグ以下の
        girlid-〇〇と書いてある部分の〇〇。この後の3つの情報もこのaブロックの下にある。

    mediaがdeliher_townでcast_typeがaのとき
        hogehoge (未調査なので未定義)
    
IsWorkingの取得関数
    引数でurl, media, working_typeを受け取る

    mediaがcityheavenでworking_typeがaのとき
        shukkin_detail_timeの次に出てくるTime型として解釈可能なコンテンツと、
        その後の「~」に続くTime型として解釈可能なコンテンツが、出勤時間帯を表現している。
        例えば「12:00~19:00」なら、12:00から19:00までが出勤時間帯。
        現在時刻がこの範囲内にあればTrue、そうでなければFalseを返す。
    
    mediaがdeliher_townでworking_typeがaのとき 
        hogehoge (未調査なので未定義)
    
IsOnShiftの取得関数
    引数でurl, media, shift_typeを受け取る

    mediaがcityheavenでshift_typeがaのとき
        Sugunaviboxとあるclassの次に出てくるコンテンツのうち、Time型として解釈できるものが、
        現在時刻よりも後のものがあればTrue、なければFalse
    
    mediaがdeliher_townでshift_typeがaのとき
        hogehoge (未調査なので未定義)


"""











