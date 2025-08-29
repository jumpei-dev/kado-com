"""
HTMLコンテンツローダー（ローカル・リモート対応）

ローカルHTMLファイルの読み込みとSeleniumによるリモート取得を管理
"""

import asyncio
import concurrent.futures
from pathlib import Path
from typing import Optional

from .webdriver_manager import WebDriverManager

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class HTMLLoader:
    """HTMLコンテンツの読み込み処理"""
    
    def __init__(self, use_local_html: bool = False):
        self.use_local_html = use_local_html
    
    async def load_html_content(
        self, 
        business_name: str, 
        business_id: str, 
        url: Optional[str] = None
    ) -> str:
        """HTMLコンテンツを読み込む（ローカル・リモート対応）"""
        if self.use_local_html:
            return await self._load_local_html(business_name, business_id)
        else:
            if not url:
                raise ValueError("リモート取得にはURLが必要です")
            return await self._load_remote_html(url)
    
    async def _load_local_html(self, business_name: str, business_id: str) -> str:
        """ローカルHTMLファイルからコンテンツを読み込む（開発用）"""
        try:
            # data/raw_html/cityhaven/ ディレクトリを探索
            base_dir = Path(__file__).parent.parent.parent.parent / "data" / "raw_html" / "cityhaven"
            
            if not base_dir.exists():
                logger.warning(f"ローカルHTMLディレクトリが存在しません: {base_dir}")
                return ""
            
            # 店舗名またはbusiness_idでHTMLファイルを検索
            search_patterns = [
                f"人妻城*.html",  # 人妻城を優先
                f"{business_name}_*.html",
                f"*{business_name}*.html",
                f"{business_id}_*.html",
                f"*{business_id}*.html"
            ]
            
            html_file = None
            for pattern in search_patterns:
                matches = list(base_dir.glob(pattern))
                if matches:
                    html_file = matches[0]  # 最初のマッチを使用
                    logger.info(f"HTMLファイル発見: {pattern} -> {html_file.name}")
                    break
            
            if not html_file:
                # パターンマッチしない場合、全ファイルをリストして最新を選択
                html_files = list(base_dir.glob("*.html"))
                if html_files:
                    html_file = max(html_files, key=lambda x: x.stat().st_mtime)
                    logger.info(f"パターンマッチなし、最新ファイル使用: {html_file.name}")
                else:
                    logger.warning(f"ローカルHTMLファイルが見つかりません: {base_dir}")
                    return ""
            
            # HTMLファイルを読み込み
            logger.info(f"📁 HTMLファイル読み込み中: {html_file.name}")
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"✓ HTMLファイル読み込み完了: {len(content)} 文字")
            return content
            
        except Exception as e:
            logger.error(f"ローカルHTML読み込みエラー: {e}")
            return ""
    
    async def _load_remote_html(self, url: str) -> str:
        """Seleniumを使ってリモートHTMLを取得"""
        def _sync_scrape():
            """同期的なSeleniumスクレイピング処理"""
            webdriver_manager = None
            try:
                print("  🌐 WebDriverManagerを作成中...")
                webdriver_manager = WebDriverManager()
                print("  ✓ WebDriverManager作成完了")
                
                print("  📄 ページソースを取得中...")
                page_source = webdriver_manager.get_page_source(url)
                print("  ✓ ページソース取得処理完了")
                
                return page_source
            except Exception as e:
                print(f"  ❌ _sync_scrapeエラー: {e}")
                raise
            finally:
                print("  🔄 WebDriverManagerをクリーンアップ中...")
                if webdriver_manager:
                    webdriver_manager.close()
                print("  ✓ WebDriverManagerクリーンアップ完了")
        
        # 別スレッドでSeleniumを実行
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            page_source = await loop.run_in_executor(executor, _sync_scrape)
        
        return page_source
