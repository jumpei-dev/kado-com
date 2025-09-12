"""
aiohttp を使用した高速・軽量HTMLローダー
ブロック対策とUser-Agentローテーション機能付き
"""

import asyncio
import aiohttp
import random
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from pathlib import Path
import sys

# 設定読み込み
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from utils.config import get_scraping_config
except ImportError:
    # フォールバック設定
    def get_scraping_config():
        return {
            'timeout': 30,
            'user_agents': [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ],
            'min_delay': 0.5,
            'max_delay': 2.0,
            'retry_attempts': 3,
            'retry_delay': 3.0
        }

logger = logging.getLogger(__name__)

class AiohttpHTMLLoader:
    """aiohttp を使用した高速HTMLローダー"""
    
    def __init__(self):
        self.config = get_scraping_config()
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        await self._create_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        await self._close_session()
        
    async def _create_session(self):
        """aiohttp セッションを作成"""
        timeout = aiohttp.ClientTimeout(total=self.config.get('timeout', 30))
        
        connector = aiohttp.TCPConnector(
            limit=100,  # 総接続数制限
            limit_per_host=10,  # ホスト別接続数制限
            keepalive_timeout=30,  # Keep-Alive タイムアウト
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._get_base_headers()
        )
        
    async def _close_session(self):
        """aiohttp セッションを閉じる"""
        if self.session:
            await self.session.close()
            self.session = None
            
    def _get_random_user_agent(self) -> str:
        """ランダムなUser-Agentを取得"""
        user_agents = self.config.get('user_agents', [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ])
        return random.choice(user_agents)
        
    def _get_base_headers(self) -> Dict[str, str]:
        """基本HTTPヘッダーを取得"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
    def _get_random_headers(self) -> Dict[str, str]:
        """ランダム化されたHTTPヘッダーを取得"""
        headers = self._get_base_headers()
        headers['User-Agent'] = self._get_random_user_agent()
        
        # ランダムな要素を追加してフィンガープリンティング対策
        if random.random() < 0.3:  # 30%の確率で追加ヘッダー
            headers['X-Requested-With'] = 'XMLHttpRequest'
            
        if random.random() < 0.2:  # 20%の確率でリファラー追加
            parsed_url = urlparse(headers.get('Referer', 'https://www.google.com/'))
            headers['Referer'] = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            
        return headers
        
    async def _random_delay(self):
        """ランダム待機でブロック対策"""
        min_delay = self.config.get('min_delay', 0.5)
        max_delay = self.config.get('max_delay', 2.0)
        delay = random.uniform(min_delay, max_delay)
        
        logger.debug(f"⏰ ランダム待機: {delay:.2f}秒")
        await asyncio.sleep(delay)
        
    async def load_html(self, url: str, retries: Optional[int] = None) -> Optional[str]:
        """
        URLからHTMLを取得
        
        Args:
            url: 取得対象のURL
            retries: リトライ回数（Noneの場合は設定から取得）
            
        Returns:
            HTMLコンテンツまたはNone（エラー時）
        """
        if retries is None:
            retries = self.config.get('retry_attempts', 3)
            
        if not self.session:
            await self._create_session()
            
        for attempt in range(retries + 1):
            try:
                # ブロック対策: ランダム待機
                if attempt > 0:
                    retry_delay = self.config.get('retry_delay', 3.0)
                    await asyncio.sleep(retry_delay * attempt)
                else:
                    await self._random_delay()
                
                # ランダム化されたヘッダーでリクエスト
                headers = self._get_random_headers()
                
                logger.debug(f"📡 HTML取得開始: {url} (試行 {attempt + 1}/{retries + 1})")
                logger.debug(f"🔧 User-Agent: {headers['User-Agent'][:50]}...")
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text(encoding='utf-8')
                        
                        logger.info(f"✅ HTML取得成功: {url} ({len(html_content)}文字)")
                        return html_content
                        
                    elif response.status in [429, 503, 504]:  # レート制限・サーバー過負荷
                        logger.warning(f"🚫 レート制限検出: HTTP {response.status} - {url}")
                        if attempt < retries:
                            wait_time = (attempt + 1) * 5  # 指数バックオフ
                            logger.info(f"⏰ {wait_time}秒待機してリトライ...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"❌ リトライ上限到達: {url}")
                            return None
                            
                    elif response.status in [403, 406]:  # アクセス拒否
                        logger.warning(f"🚫 アクセス拒否: HTTP {response.status} - {url}")
                        if attempt < retries:
                            # User-Agentを変更してリトライ
                            continue
                        else:
                            logger.error(f"❌ アクセス拒否が継続: {url}")
                            return None
                            
                    else:
                        logger.warning(f"⚠️ HTTP エラー: {response.status} - {url}")
                        if attempt < retries:
                            continue
                        else:
                            logger.error(f"❌ HTTP エラーが継続: {url}")
                            return None
                            
            except asyncio.TimeoutError:
                logger.warning(f"⏰ タイムアウト: {url} (試行 {attempt + 1}/{retries + 1})")
                if attempt < retries:
                    continue
                else:
                    logger.error(f"❌ タイムアウトが継続: {url}")
                    return None
                    
            except aiohttp.ClientError as e:
                logger.warning(f"🌐 接続エラー: {e} - {url} (試行 {attempt + 1}/{retries + 1})")
                if attempt < retries:
                    continue
                else:
                    logger.error(f"❌ 接続エラーが継続: {url}")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ 予期しないエラー: {e} - {url}")
                return None
                
        logger.error(f"❌ 全てのリトライが失敗: {url}")
        return None

# 便利関数
async def load_html_with_aiohttp(url: str) -> Optional[str]:
    """
    aiohttp を使用してHTMLを取得する便利関数
    
    Args:
        url: 取得対象のURL
        
    Returns:
        HTMLコンテンツまたはNone（エラー時）
    """
    async with AiohttpHTMLLoader() as loader:
        return await loader.load_html(url)

# aiohttp専用の互換性関数
async def load_html_compatible(url: str, use_aiohttp: bool = True) -> Optional[str]:
    """
    aiohttpを使用してHTMLを取得
    
    Args:
        url: 取得対象のURL
        use_aiohttp: 互換性のため残されているが、常にaiohttpを使用
        
    Returns:
        HTMLコンテンツまたはNone（エラー時）
    """
    logger.info(f"🚀 aiohttp使用: {url}")
    return await load_html_with_aiohttp(url)
