"""
Cityheaven専用スクレイピング戦略

Cityheavenサイトの指示書準拠スクレイピング処理
"""

import aiohttp
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ...core.models import CastStatus
from .html_loader import HTMLLoader
from .cityheaven_parsers import CityheavenParserFactory

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


class ScrapingStrategy(ABC):
    """スクレイピング戦略の基底クラス"""
    
    @abstractmethod
    async def scrape_working_status(self, business_name: str, business_id: str, base_url: str, use_local: bool = True) -> List[CastStatus]:
        """稼働ステータスを収集する抽象メソッド"""
        pass


class CityheavenStrategy(ScrapingStrategy):
    """Cityheavenサイト用のスクレイピング戦略（Selenium使用）"""
    
    def __init__(self, use_local_html: bool = False):
        """
        初期化
        
        Args:
            use_local_html: ローカルHTMLファイルを使用するかどうか（開発用）
        """
        self.use_local_html = use_local_html
        self.html_loader = HTMLLoader(use_local_html)
        
        if use_local_html:
            logger.info("🔧 開発モード: ローカルHTMLファイルを使用します")
        else:
            logger.info("🌐 本番モード: Seleniumでライブスクレイピングを実行します")
    
    async def scrape_working_status(self, business_name: str, business_id: str, base_url: str, use_local: bool = True) -> list[CastStatus]:
        """働き状況のスクレイピングを実行（時間判定修正版）"""
        logger.info(f"� Cityheaven状況スクレイピング開始: {business_name}")
        
        # HTMLコンテンツと取得時刻を読み込み（修正版）
        html_content, html_acquisition_time = await self.html_loader.load_html_content(
            business_name, business_id, base_url if not use_local else None
        )
        
        if not html_content:
            logger.error(f"HTMLコンテンツが取得できませんでした: {business_name}")
            return []
        
        # CityheavenParsersでデータをパース（HTML取得時刻を使用）
        parser = CityheavenParserFactory.get_parser(business_id)
        cast_statuses = parser.parse_cast_list(html_content, html_acquisition_time)
        
        logger.info(f"✓ Cityheaven状況スクレイピング完了: {business_name}, {len(cast_statuses)} 件")
        return cast_statuses

