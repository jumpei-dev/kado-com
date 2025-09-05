"""
HTMLコンテンツローダー（ローカル・リモート対応）

ローカルHTMLファイルの読み込みとSeleniumによるリモート取得を管理
"""

import asyncio
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from .webdriver_manager import WebDriverManager
except ImportError:
    try:
        from webdriver_manager import WebDriverManager
    except ImportError as e:
        print(f"WebDriverManager import failed: {e}")
        WebDriverManager = None

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


class HTMLLoader:
    """HTMLコンテンツの読み込み処理"""
    
    def __init__(self, use_local_html: bool = False, specific_file: Optional[str] = None):
        self.use_local_html = use_local_html
        self.specific_file = specific_file
    
    async def load_html_content(
        self, 
        business_name: str, 
        business_id: str, 
        url: Optional[str] = None,
        local_file: Optional[str] = None
    ) -> tuple[str, datetime]:
        """HTMLコンテンツを読み込む（ローカル・リモート対応）"""
        if self.use_local_html:
            # 優先順位: 1. local_file引数, 2. インスタンス設定, 3. 自動検索
            file_to_load = local_file or self.specific_file
            if file_to_load:
                return await self._load_specific_html_file(file_to_load)
            else:
                return await self._load_local_html_with_timestamp(business_name, business_id)
        else:
            if not url:
                raise ValueError("リモート取得にはURLが必要です")
            content = await self._load_remote_html(url)
            # リモート取得の場合は現在時刻を返す
            return content, datetime.now()
    
    async def _load_specific_html_file(self, filename: str) -> tuple[str, datetime]:
        """指定されたファイル名のHTMLファイルを読み込む"""
        try:
            # data/raw_html/cityhaven/ ディレクトリ内の指定ファイルを読み込み
            base_dir = Path(__file__).parent.parent.parent.parent / "data" / "raw_html" / "cityhaven"
            html_file = base_dir / filename
            
            if not html_file.exists():
                logger.error(f"指定されたHTMLファイルが存在しません: {html_file}")
                return "", datetime.now()
            
            logger.info(f"📁 指定されたHTMLファイル読み込み中: {filename}")
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ファイルの変更時刻を取得
            file_mtime = html_file.stat().st_mtime
            file_datetime = datetime.fromtimestamp(file_mtime)
            
            logger.info(f"✓ HTMLファイル読み込み完了: {len(content)} 文字, 取得時刻: {file_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            return content, file_datetime
            
        except Exception as e:
            logger.error(f"指定HTMLファイル読み込みエラー: {e}")
            return "", datetime.now()
    
    async def _load_local_html_with_timestamp(self, business_name: str, business_id: str) -> tuple[str, datetime]:
        """ローカルHTMLファイルからコンテンツと取得時刻を読み込む（開発用）"""
        try:
            # data/raw_html/cityhaven/ ディレクトリを探索
            base_dir = Path(__file__).parent.parent.parent.parent / "data" / "raw_html" / "cityhaven"
            
            if not base_dir.exists():
                logger.warning(f"ローカルHTMLディレクトリが存在しません: {base_dir}")
                return "", datetime.now()
            
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
                    return "", datetime.now()
            
            # HTMLファイルを読み込み
            logger.info(f"📁 HTMLファイル読み込み中: {html_file.name}")
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ファイルの変更時刻を取得（HTMLが実際に取得された時刻）
            file_mtime = html_file.stat().st_mtime
            file_datetime = datetime.fromtimestamp(file_mtime)
            
            logger.info(f"✓ HTMLファイル読み込み完了: {len(content)} 文字, 取得時刻: {file_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            return content, file_datetime
            
        except Exception as e:
            logger.error(f"ローカルHTML読み込みエラー: {e}")
            return "", datetime.now()
    
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
