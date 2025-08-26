"""
様々なサイトからキャストのステータスを抽出するためのウェブスクレイピングユーティリティ。
"""

import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import time

from .models import Cast, ScrapingResult

logger = logging.getLogger(__name__)

class BaseScraper:
    """サイト固有スクレイパーのベースクラス"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.session:
            await self.session.close()
    
    async def scrape_cast_status(self, cast: Cast) -> ScrapingResult:
        """単一キャストのステータスをスクレイピングする。サブクラスでオーバーライドする"""
        raise NotImplementedError("サブクラスで実装する必要があります")
    
    async def scrape_multiple_casts(self, casts: List[Cast]) -> List[ScrapingResult]:
        """複数キャストのステータスを並行してスクレイピングする"""
        tasks = [self.scrape_cast_status(cast) for cast in casts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"キャスト {casts[i].name} のスクレイピング例外: {result}")
                processed_results.append(ScrapingResult(
                    cast_id=casts[i].cast_id,
                    is_working=False,
                    is_on_shift=False,
                    recorded_at=datetime.now(),
                    success=False,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results

class CityHavenScraper(BaseScraper):
    """CityHeavenサイトのスクレイパー"""
    
    async def scrape_cast_status(self, cast: Cast) -> ScrapingResult:
        """CityHeavenプロファイルページからキャストステータスをスクレイピングする"""
        recorded_at = datetime.now()
        
        try:
            async with self.session.get(cast.profile_url) as response:
                if response.status != 200:
                    return ScrapingResult(
                        cast_id=cast.cast_id,
                        is_working=False,
                        is_on_shift=False,
                        recorded_at=recorded_at,
                        success=False,
                        error_message=f"HTTP {response.status}"
                    )
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # CityHeaven固有の解析ロジック
                is_working, is_on_shift = self._parse_working_status(soup, cast.name)
                
                return ScrapingResult(
                    cast_id=cast.cast_id,
                    is_working=is_working,
                    is_on_shift=is_on_shift,
                    recorded_at=recorded_at,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"キャスト {cast.name} のスクレイピングエラー: {e}")
            return ScrapingResult(
                cast_id=cast.cast_id,
                is_working=False,
                is_on_shift=False,
                recorded_at=recorded_at,
                success=False,
                error_message=str(e)
            )
    
    def _parse_working_status(self, soup: BeautifulSoup, cast_name: str) -> tuple[bool, bool]:
        """CityHeavenページ構造から稼働ステータスを解析する"""
        # 稼働ステータスの一般的な指標を探す
        
        is_working = False
        is_on_shift = False
        
        # 方法1: "出勤"（稼働中）指標をチェック
        working_indicators = soup.find_all(text=lambda x: x and '出勤' in x)
        if working_indicators:
            is_working = True
            is_on_shift = True
        
        # 方法2: スケジュール/空き状況セクションをチェック
        schedule_section = soup.find('div', class_=lambda x: x and 'schedule' in x.lower() if x else False)
        if schedule_section:
            today_indicator = schedule_section.find(text=lambda x: x and ('今日' in x or '本日' in x))
            if today_indicator:
                is_on_shift = True
        
        # 方法3: ステータスアイコンまたはクラスをチェック
        status_elements = soup.find_all(['span', 'div'], class_=lambda x: x and any(
            keyword in x.lower() for keyword in ['status', 'work', 'available', '出勤']
        ) if x else False)
        
        for element in status_elements:
            if element.text and any(keyword in element.text for keyword in ['出勤', '在籍']):
                is_working = True
                is_on_shift = True
            elif element.text and 'available' in element.text:
                is_on_shift = True
        
        return is_working, is_on_shift

class DeliherTownScraper(BaseScraper):
    """DeliherTownサイトのスクレイパー"""
    
    async def scrape_cast_status(self, cast: Cast) -> ScrapingResult:
        """DeliherTownプロファイルページからキャストステータスをスクレイピングする"""
        recorded_at = datetime.now()
        
        try:
            async with self.session.get(cast.profile_url) as response:
                if response.status != 200:
                    return ScrapingResult(
                        cast_id=cast.cast_id,
                        is_working=False,
                        is_on_shift=False,
                        recorded_at=recorded_at,
                        success=False,
                        error_message=f"HTTP {response.status}"
                    )
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # DeliherTown固有の解析ロジック
                is_working, is_on_shift = self._parse_working_status(soup, cast.name)
                
                return ScrapingResult(
                    cast_id=cast.cast_id,
                    is_working=is_working,
                    is_on_shift=is_on_shift,
                    recorded_at=recorded_at,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"キャスト {cast.name} のスクレイピングエラー: {e}")
            return ScrapingResult(
                cast_id=cast.cast_id,
                is_working=False,
                is_on_shift=False,
                recorded_at=recorded_at,
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"キャスト {cast.name} のスクレイピングエラー: {e}")
            return ScrapingResult(
                cast_id=cast.cast_id,
                is_working=False,
                is_on_shift=False,
                recorded_at=recorded_at,
                success=False,
                error_message=str(e)
            )
    
    def _parse_working_status(self, soup: BeautifulSoup, cast_name: str) -> tuple[bool, bool]:
        """DeliherTownページ構造から稼働ステータスを解析する"""
        # DeliherTown固有の解析ロジック
        # 実際のサイト構造に基づいてカスタマイズが必要
        
        is_working = False
        is_on_shift = False
        
        # スケジュール指標を探す
        schedule_indicators = soup.find_all(text=lambda x: x and any(
            keyword in x for keyword in ['出勤', '待機', 'スケジュール']
        ))
        
        if schedule_indicators:
            is_on_shift = True
            # より詳細な判定が必要に応じて追加
        
        return is_working, is_on_shift

class ScraperFactory:
    """サイト固有スクレイパーを作成するファクトリー"""
    
    SCRAPERS = {
        'cityhaven': CityHavenScraper,
        'deliher_town': DeliherTownScraper,
    }
    
    @classmethod
    def create_scraper(cls, site_type: str, **kwargs) -> BaseScraper:
        """指定したサイトタイプに適したスクレイパーを作成する"""
        scraper_class = cls.SCRAPERS.get(site_type.lower())
        if not scraper_class:
            raise ValueError(f"未知のサイトタイプ: {site_type}")
        
        return scraper_class(**kwargs)
    
    @classmethod
    def get_supported_sites(cls) -> List[str]:
        """サポートされているサイトタイプのリストを取得する"""
        return list(cls.SCRAPERS.keys())
