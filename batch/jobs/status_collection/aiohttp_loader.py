"""Phase 1改良版 aiohttp HTMLローダー
403エラー対策強化版：セッションローテーション、Cookieローテーション、ランダム間隔機能付き

元のaiohttp_loader.pyをPhase 1対策で強化
- 60分ベースのランダム間隔調整
- セッションローテーション機能
- Cookieローテーション機能
- 拡張User-Agentローテーション
- 403エラー対策の強化
"""

import asyncio
import aiohttp
import random
import logging
import time
import json
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from pathlib import Path
import sys
from datetime import datetime, timedelta

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
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ],
            'min_delay': 0.5,
            'max_delay': 2.0,
            'retry_attempts': 3,
            'retry_delay': 3.0,
            'session_rotation': True,
            'session_lifetime': 1800,
            'cookie_persistence': True,
            'random_intervals': True,
            'interval_base_minutes': 60,
            'interval_variance_percent': 50,
            'random_headers': True,
            'random_referer': True
        }

logger = logging.getLogger(__name__)

class ProxyManager:
    """プロキシ管理クラス - ローテーション機能付き"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.proxy_list = []
        self.current_proxy_index = 0
        self.failed_proxies = set()
        self.last_refresh_time = 0
        self.refresh_interval = config.get('proxy_refresh_interval', 3600)  # 1時間
        self.test_timeout = config.get('proxy_test_timeout', 10)
        
    async def get_proxy_list(self) -> List[Dict[str, Any]]:
        """プロキシリストを取得（必要に応じて更新）"""
        current_time = time.time()
        
        # 初回取得または更新間隔を過ぎた場合
        if not self.proxy_list or (current_time - self.last_refresh_time) > self.refresh_interval:
            await self._refresh_proxy_list()
            
        # 失敗したプロキシを除外
        available_proxies = [
            proxy for proxy in self.proxy_list 
            if proxy['url'] not in self.failed_proxies
        ]
        
        return available_proxies
        
    async def _refresh_proxy_list(self):
        """プロキシリストを更新"""
        logger.info("📡 プロキシリスト更新中...")
        
        try:
            # 複数のプロキシソースから取得
            new_proxies = []
            
            # 無料プロキシAPI 1: ProxyList
            try:
                proxies_1 = await self._fetch_from_proxylist_api()
                new_proxies.extend(proxies_1)
            except Exception as e:
                logger.warning(f"⚠️ ProxyList API エラー: {e}")
                
            # 無料プロキシAPI 2: Free Proxy List
            try:
                proxies_2 = await self._fetch_from_free_proxy_api()
                new_proxies.extend(proxies_2)
            except Exception as e:
                logger.warning(f"⚠️ Free Proxy API エラー: {e}")
                
            # 重複除去
            unique_proxies = {}
            for proxy in new_proxies:
                key = f"{proxy['host']}:{proxy['port']}"
                if key not in unique_proxies:
                    unique_proxies[key] = proxy
                    
            self.proxy_list = list(unique_proxies.values())
            self.last_refresh_time = time.time()
            
            logger.info(f"✅ プロキシリスト更新完了: {len(self.proxy_list)}個")
            
        except Exception as e:
            logger.error(f"❌ プロキシリスト更新エラー: {e}")
            # フォールバック: 基本的なプロキシリスト
            self.proxy_list = self._get_fallback_proxies()
            
    async def _fetch_from_proxylist_api(self) -> List[Dict[str, Any]]:
        """ProxyList APIからプロキシを取得"""
        url = "https://www.proxy-list.download/api/v1/get?type=http"
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    proxies = []
                    
                    for line in text.strip().split('\n'):
                        if ':' in line:
                            host, port = line.strip().split(':', 1)
                            proxies.append({
                                'host': host,
                                'port': int(port),
                                'type': 'http',
                                'url': f"http://{host}:{port}",
                                'source': 'proxylist'
                            })
                            
                    return proxies[:50]  # 最大50個
                    
        return []
        
    async def _fetch_from_free_proxy_api(self) -> List[Dict[str, Any]]:
        """Free Proxy APIからプロキシを取得"""
        url = "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    proxies = []
                    
                    for line in text.strip().split('\n'):
                        if ':' in line:
                            host, port = line.strip().split(':', 1)
                            try:
                                proxies.append({
                                    'host': host,
                                    'port': int(port),
                                    'type': 'http',
                                    'url': f"http://{host}:{port}",
                                    'source': 'proxyscrape'
                                })
                            except ValueError:
                                continue
                                
                    return proxies[:50]  # 最大50個
                    
        return []
        
    def _get_fallback_proxies(self) -> List[Dict[str, Any]]:
        """フォールバック用の基本プロキシリスト"""
        return [
            {'host': '8.210.83.33', 'port': 80, 'type': 'http', 'url': 'http://8.210.83.33:80', 'source': 'fallback'},
            {'host': '47.74.152.29', 'port': 8888, 'type': 'http', 'url': 'http://47.74.152.29:8888', 'source': 'fallback'},
            {'host': '20.111.54.16', 'port': 80, 'type': 'http', 'url': 'http://20.111.54.16:80', 'source': 'fallback'}
        ]
        
    async def get_next_proxy(self) -> Optional[Dict[str, Any]]:
        """次のプロキシを取得（ローテーション）"""
        available_proxies = await self.get_proxy_list()
        
        if not available_proxies:
            logger.warning("⚠️ 利用可能なプロキシがありません")
            return None
            
        # ローテーション
        if self.current_proxy_index >= len(available_proxies):
            self.current_proxy_index = 0
            
        proxy = available_proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(available_proxies)
        
        logger.debug(f"🔄 プロキシローテーション: {proxy['host']}:{proxy['port']}")
        return proxy
        
    def mark_proxy_failed(self, proxy_url: str):
        """プロキシを失敗としてマーク"""
        self.failed_proxies.add(proxy_url)
        logger.warning(f"❌ プロキシ失敗マーク: {proxy_url}")
        
    def reset_failed_proxies(self):
        """失敗プロキシリストをリセット"""
        self.failed_proxies.clear()
        logger.info("🔄 失敗プロキシリストをリセット")
        
    async def test_proxy(self, proxy: Dict[str, Any]) -> bool:
        """プロキシの動作テスト"""
        test_url = "http://httpbin.org/ip"
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.test_timeout)
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            ) as session:
                proxy_url = f"http://{proxy['host']}:{proxy['port']}"
                
                async with session.get(
                    test_url,
                    proxy=proxy_url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                ) as response:
                    if response.status == 200:
                        logger.debug(f"✅ プロキシテスト成功: {proxy['host']}:{proxy['port']}")
                        return True
                        
        except Exception as e:
            logger.debug(f"❌ プロキシテスト失敗: {proxy['host']}:{proxy['port']} - {e}")
            
        return False

class SessionManager:
    """セッション管理クラス - ローテーション機能付き"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sessions: List[aiohttp.ClientSession] = []
        self.session_created_times: List[datetime] = []
        self.current_session_index = 0
        self.session_lifetime = config.get('session_lifetime', 1800)  # 30分
        self.cookie_jar_storage = {}
        
        # プロキシ管理
        self.proxy_manager = None
        self.current_proxy = None
        if config.get('enable_proxy_rotation', False):
            self.proxy_manager = ProxyManager(config)
        
    async def get_session(self) -> aiohttp.ClientSession:
        """アクティブなセッションを取得（必要に応じてローテーション）"""
        await self._cleanup_expired_sessions()
        
        if not self.sessions:
            await self._create_new_session()
            
        # セッションローテーション
        if self.config.get('session_rotation', True):
            current_time = datetime.now()
            session_age = (current_time - self.session_created_times[self.current_session_index]).total_seconds()
            
            if session_age > self.session_lifetime:
                logger.info(f"🔄 セッションローテーション実行 (経過時間: {session_age:.0f}秒)")
                await self._rotate_session()
                
        return self.sessions[self.current_session_index]
        
    async def _create_new_session(self) -> aiohttp.ClientSession:
        """新しいセッションを作成"""
        timeout = aiohttp.ClientTimeout(total=self.config.get('timeout', 30))
        
        # Cookie Jar作成（永続化対応）
        cookie_jar = aiohttp.CookieJar()
        if self.config.get('cookie_persistence', True):
            # 既存のCookieを復元
            self._restore_cookies(cookie_jar)
            
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            ssl=False  # SSL検証を緩和
        )
        
        # プロキシ設定を取得
        proxy_url = None
        if self.proxy_manager:
            try:
                proxy = await self.proxy_manager.get_next_proxy()
                if proxy:
                    proxy_url = proxy['url']
                    self.current_proxy = proxy  # 現在のプロキシを保存
                    logger.debug(f"🔄 セッションにプロキシ設定: {proxy_url}")
            except Exception as e:
                logger.warning(f"⚠️ プロキシ取得エラー: {e}")
        
        session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            cookie_jar=cookie_jar,
            headers=self._get_base_headers()
        )
        
        # セッションにプロキシ情報を保存
        if proxy_url:
            session._proxy_url = proxy_url
        
        self.sessions.append(session)
        self.session_created_times.append(datetime.now())
        
        logger.info(f"🆕 新しいセッション作成 (総数: {len(self.sessions)}, プロキシ: {proxy_url or 'なし'})")
        return session
    
    def get_current_proxy(self):
        """現在のプロキシ情報を取得"""
        return self.current_proxy
        
    async def _rotate_session(self):
        """セッションをローテーション"""
        # 現在のセッションのCookieを保存
        if self.sessions and self.config.get('cookie_persistence', True):
            self._save_cookies(self.sessions[self.current_session_index].cookie_jar)
            
        # 古いセッションを閉じる
        if self.sessions:
            await self.sessions[self.current_session_index].close()
            
        # 新しいセッションを作成
        await self._create_new_session()
        self.current_session_index = len(self.sessions) - 1
        
    async def _cleanup_expired_sessions(self):
        """期限切れセッションをクリーンアップ"""
        current_time = datetime.now()
        expired_indices = []
        
        for i, created_time in enumerate(self.session_created_times):
            if (current_time - created_time).total_seconds() > self.session_lifetime * 2:
                expired_indices.append(i)
                
        for i in reversed(expired_indices):
            if i < len(self.sessions):
                await self.sessions[i].close()
                del self.sessions[i]
                del self.session_created_times[i]
                
        if expired_indices:
            logger.info(f"🧹 期限切れセッション削除: {len(expired_indices)}個")
            
    def _save_cookies(self, cookie_jar: aiohttp.CookieJar):
        """Cookieを保存"""
        try:
            cookies_data = []
            for cookie in cookie_jar:
                cookies_data.append({
                    'name': cookie.key,
                    'value': cookie.value,
                    'domain': cookie['domain'],
                    'path': cookie['path']
                })
            self.cookie_jar_storage['cookies'] = cookies_data
            logger.debug(f"🍪 Cookie保存: {len(cookies_data)}個")
        except Exception as e:
            logger.warning(f"⚠️ Cookie保存エラー: {e}")
            
    def _restore_cookies(self, cookie_jar: aiohttp.CookieJar):
        """Cookieを復元"""
        try:
            cookies_data = self.cookie_jar_storage.get('cookies', [])
            for cookie_data in cookies_data:
                cookie_jar.update_cookies({
                    cookie_data['name']: cookie_data['value']
                })
            if cookies_data:
                logger.debug(f"🍪 Cookie復元: {len(cookies_data)}個")
        except Exception as e:
            logger.warning(f"⚠️ Cookie復元エラー: {e}")
            
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
            
    async def close_all(self):
        """全セッションを閉じる"""
        for session in self.sessions:
            await session.close()
        self.sessions.clear()
        self.session_created_times.clear()
        
class AiohttpHTMLLoader:
    """Phase 1改良版 aiohttp HTMLローダー（既存クラス名維持）"""
    
    def __init__(self):
        self.config = get_scraping_config()
        self.session_manager = SessionManager(self.config)
        self.last_request_time = 0
        self.request_count = 0
        
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        await self.session_manager.close_all()
        
    def _get_random_user_agent(self) -> str:
        """ランダムなUser-Agentを取得（拡張版）"""
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
        
    def _get_random_headers(self, url: str = "") -> Dict[str, str]:
        """ランダム化されたHTTPヘッダーを取得（Phase 1強化版）"""
        headers = self._get_base_headers()
        headers['User-Agent'] = self._get_random_user_agent()
        
        # ランダムヘッダー追加
        if self.config.get('random_headers', True):
            if random.random() < 0.3:
                headers['X-Requested-With'] = 'XMLHttpRequest'
                
            if random.random() < 0.4:
                headers['Sec-CH-UA'] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
                headers['Sec-CH-UA-Mobile'] = '?0'
                headers['Sec-CH-UA-Platform'] = '"Windows"'
                
        # ランダムリファラー
        if self.config.get('random_referer', True) and random.random() < 0.6 and url:
            referers = [
                'https://www.google.com/',
                'https://www.yahoo.co.jp/',
                'https://www.bing.com/',
                f"https://{urlparse(url).netloc}/"
            ]
            headers['Referer'] = random.choice(referers)
            
        return headers
        
    async def _calculate_random_delay(self) -> float:
        """ランダム間隔を計算（Phase 1: 60分ベース±50%）"""
        if not self.config.get('random_intervals', True):
            return random.uniform(self.config.get('min_delay', 0.5), self.config.get('max_delay', 2.0))
            
        base_minutes = self.config.get('interval_base_minutes', 60)
        variance_percent = self.config.get('interval_variance_percent', 50)
        
        # ±50%の変動
        variance = base_minutes * (variance_percent / 100)
        random_minutes = random.uniform(base_minutes - variance, base_minutes + variance)
        
        # 最小1分、最大120分に制限
        random_minutes = max(1, min(120, random_minutes))
        
        return random_minutes * 60  # 秒に変換
        
    async def _random_delay(self):
        """スマート待機（リクエスト間隔の動的調整）"""
        import os
        
        # 強制即時実行モードのチェック
        force_immediate = os.getenv('FORCE_IMMEDIATE', 'false').lower() == 'true'
        if force_immediate:
            logger.info("⚡ 強制即時実行モード - 全ての待機時間をスキップ")
            self.last_request_time = time.time()
            return
            
        current_time = time.time()
        
        # 前回リクエストからの経過時間
        if self.last_request_time > 0:
            elapsed = current_time - self.last_request_time
            
            # 短時間での連続リクエストを検出
            if elapsed < 30:  # 30秒以内
                self.request_count += 1
                if self.request_count > 3:  # 3回以上連続
                    extra_delay = random.uniform(10, 30)  # 追加待機
                    logger.info(f"🛡️ 連続リクエスト検出 - 追加待機: {extra_delay:.1f}秒")
                    await asyncio.sleep(extra_delay)
                    self.request_count = 0
            else:
                self.request_count = 0
                
        # FORCE_IMMEDIATE環境変数が設定されている場合は待機をスキップ
        if os.getenv('FORCE_IMMEDIATE', 'false').lower() == 'true':
            logger.info("⚡ 強制即時実行モード - ランダム間隔待機をスキップ")
        elif self.config.get('random_intervals', True):
            # ランダム間隔待機
            delay = await self._calculate_random_delay()
            logger.info(f"⏰ ランダム間隔待機: {delay/60:.1f}分")
            await asyncio.sleep(delay)
        else:
            # 通常のランダム待機
            min_delay = self.config.get('min_delay', 0.5)
            max_delay = self.config.get('max_delay', 2.0)
            delay = random.uniform(min_delay, max_delay)
            logger.debug(f"⏰ 通常待機: {delay:.2f}秒")
            await asyncio.sleep(delay)
            
        self.last_request_time = current_time
        
    async def load_html(self, url: str, retries: Optional[int] = None) -> Optional[str]:
        """
        URLからHTMLを取得（Phase 1改良版）
        
        Args:
            url: 取得対象のURL
            retries: リトライ回数（Noneの場合は設定から取得）
            
        Returns:
            HTMLコンテンツまたはNone（エラー時）
        """
        if retries is None:
            retries = self.config.get('retry_attempts', 3)
            
        for attempt in range(retries + 1):
            try:
                # スマート待機
                if attempt > 0:
                    retry_delay = self.config.get('retry_delay', 3.0) * (attempt ** 2)  # 指数バックオフ
                    logger.info(f"🔄 リトライ待機: {retry_delay:.1f}秒")
                    await asyncio.sleep(retry_delay)
                else:
                    await self._random_delay()
                
                # セッション取得（ローテーション対応）
                session = await self.session_manager.get_session()
                
                # ランダム化されたヘッダーでリクエスト
                headers = self._get_random_headers(url)
                
                # プロキシ設定を取得
                proxy_url = getattr(session, '_proxy_url', None)
                
                logger.info(f"📡 HTML取得開始: {url} (試行 {attempt + 1}/{retries + 1})")
                logger.debug(f"🔧 User-Agent: {headers['User-Agent'][:50]}...")
                if proxy_url:
                    logger.debug(f"🔄 プロキシ使用: {proxy_url}")
                
                # プロキシを使用してリクエスト
                request_kwargs = {'headers': headers}
                if proxy_url:
                    request_kwargs['proxy'] = proxy_url
                
                async with session.get(url, **request_kwargs) as response:
                    if response.status == 200:
                        html_content = await response.text(encoding='utf-8')
                        
                        logger.info(f"✅ HTML取得成功: {url} ({len(html_content)}文字)")
                        return html_content
                        
                    elif response.status in [429, 503, 504]:  # レート制限・サーバー過負荷
                        logger.warning(f"🚫 レート制限検出: HTTP {response.status} - {url}")
                        if attempt < retries:
                            wait_time = (attempt + 1) * 10  # より長い待機
                            logger.info(f"⏰ {wait_time}秒待機してリトライ...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"❌ リトライ上限到達: {url}")
                            return None
                            
                    elif response.status in [403, 406]:  # アクセス拒否
                        logger.warning(f"🚫 アクセス拒否: HTTP {response.status} - {url}")
                        
                        # プロキシが原因の可能性がある場合、失敗マーク
                        if proxy_url and self.session_manager.proxy_manager:
                            self.session_manager.proxy_manager.mark_proxy_failed(proxy_url)
                            logger.info(f"❌ プロキシ失敗マーク: {proxy_url}")
                        
                        if attempt < retries:
                            # セッションローテーション強制実行
                            logger.info("🔄 403エラー対策: セッションローテーション実行")
                            await self.session_manager._rotate_session()
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
                
                # プロキシ接続エラーの可能性がある場合、失敗マーク
                session = await self.session_manager.get_session()
                proxy_url = getattr(session, '_proxy_url', None)
                if proxy_url and self.session_manager.proxy_manager:
                    self.session_manager.proxy_manager.mark_proxy_failed(proxy_url)
                    logger.info(f"❌ プロキシ接続エラーでマーク: {proxy_url}")
                
                if attempt < retries:
                    # セッションローテーション実行（新しいプロキシを取得）
                    await self.session_manager._rotate_session()
                    continue
                else:
                    logger.error(f"❌ 接続エラーが継続: {url}")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ 予期しないエラー: {e} - {url}")
                return None
                
        logger.error(f"❌ 全てのリトライが失敗: {url}")
        return None

# 便利関数（既存の関数名を維持）
async def load_html_with_aiohttp(url: str) -> Optional[str]:
    """
    Phase 1改良版 aiohttp を使用してHTMLを取得する便利関数
    
    Args:
        url: 取得対象のURL
        
    Returns:
        HTMLコンテンツまたはNone（エラー時）
    """
    async with AiohttpHTMLLoader() as loader:
        return await loader.load_html(url)

# 互換性関数（既存の関数名を維持）
async def load_html_compatible(url: str, use_aiohttp: bool = True) -> Optional[str]:
    """
    Phase 1改良版aiohttpを使用してHTMLを取得
    
    Args:
        url: 取得対象のURL
        use_aiohttp: 互換性のため残されているが、常にPhase1 aiohttpを使用
        
    Returns:
        HTMLコンテンツまたはNone（エラー時）
    """
    logger.info(f"🚀 Phase1 aiohttp使用: {url}")
    return await load_html_with_aiohttp(url)
