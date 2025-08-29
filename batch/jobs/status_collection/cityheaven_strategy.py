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
    async def scrape_working_status(self, session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
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
    
    async def scrape_working_status(self, session: aiohttp.ClientSession, business: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cityheavenから稼働ステータスを収集（指示書準拠）"""
        cast_list = []
        
        # DBから各種情報を取得（両方のキー名に対応）
        business_id = business.get("business_id") or business.get("Business ID")
        url = business.get("URL")
        business_name = business.get("name") or business.get("Name", business_id)
        media = business.get("media", "cityhaven")
        cast_type = business.get("cast_type", "a")
        working_type = business.get("working_type", "a")
        shift_type = business.get("shift_type", "a")
        
        if not url or not business_id:
            logger.warning(f"必要な情報が不足しています: business_id={business_id}, url={url}")
            return cast_list
        
        try:
            logger.info(f"🎯 Cityheavenデータ収集開始: {business_id} (media={media}, cast={cast_type}, working={working_type}, shift={shift_type})")
            
            # HTMLコンテンツを取得
            page_source = await self.html_loader.load_html_content(business_name, business_id, url)
            if not page_source:
                logger.warning(f"HTMLコンテンツの取得に失敗: {business_name}")
                return cast_list
            
            collection_method = "ローカルHTML" if self.use_local_html else "Selenium"
            logger.info(f"📁 {collection_method}でのHTML取得成功: {business_name} ({len(page_source)} 文字)")
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 指示書準拠のtype別パース処理
            cast_list = await self._parse_cityhaven_data(soup, business_id, cast_type, working_type, shift_type)
            
            logger.info(f"🎯 {collection_method}での収集完了: {business_name}, {len(cast_list)}件")
                
        except Exception as e:
            collection_method = "ローカルHTML" if self.use_local_html else "Selenium"
            logger.error(f"❌ {collection_method}データ収集エラー {business_id}: {str(e)}")
            import traceback
            logger.error(f"詳細エラー: {traceback.format_exc()}")
            
        return cast_list
    
    async def _parse_cityhaven_data(self, soup: BeautifulSoup, business_id: str, cast_type: str, working_type: str, shift_type: str) -> List[Dict[str, Any]]:
        """
        指示書準拠のCityheavenデータ解析
        
        指示書の条件:
        - mediaがcityheaven、cast_type、shift_type、working_typeがそれぞれaのとき
        - Class名が"sugunavi_wrapper"のdiv要素でsugunaviboxを含むものが対象
        """
        cast_list = []
        current_time = get_current_jst_datetime()
        
        try:
            logger.info(f"指示書準拠解析開始: business_id={business_id}, cast_type={cast_type}, working_type={working_type}, shift_type={shift_type}")
            
            # デバッグ: HTMLの内容を少し確認
            title = soup.find('title')
            if title:
                logger.info(f"ページタイトル: {title.get_text().strip()}")
            
            # パーサーファクトリーを使用
            parser = CityheavenParserFactory.get_parser(cast_type, working_type, shift_type)
            cast_list = await parser.parse_cast_data(soup, business_id, current_time)
                
        except Exception as e:
            logger.error(f"Cityheaven解析エラー {business_id}: {str(e)}")
            
        return cast_list
