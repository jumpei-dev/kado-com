"""
Selenium WebDriverの管理

Selenium WebDriverの初期化、設定、ページ取得、クリーンアップを管理
"""

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError as e:
    print(f"Selenium import failed: {e}")
    SELENIUM_AVAILABLE = False

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class WebDriverManager:
    """Selenium WebDriverの管理クラス"""
    
    def __init__(self):
        """WebDriverManagerを初期化"""
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Chrome WebDriverを設定"""
        try:
            print("  🔧 Chrome WebDriver初期化中...")
            logger.info("Chrome WebDriver初期化開始")
            
            print("  ⏳ Chrome オプションを設定中...")
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # ヘッドレスモード
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            print("  ✓ Chrome オプション設定完了")
            
            # より人間らしいUser-Agentを設定
            print("  ⏳ User-Agent設定中...")
            chrome_options.add_argument(
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            print("  ✓ User-Agent設定完了")
            
            # その他のbot検出回避オプション
            print("  ⏳ Bot検出回避オプション設定中...")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            print("  ✓ Bot検出回避オプション設定完了")
            
            # ChromeDriverを自動ダウンロード・セットアップ
            print("  ⏳ ChromeDriverを自動ダウンロード中...")
            service = Service(ChromeDriverManager().install())
            print("  ✓ ChromeDriver取得完了")
            
            print("  ⏳ Chrome WebDriverを起動中...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("  ✓ Chrome WebDriver起動完了")
            
            # bot検出回避のためのJavaScriptを実行
            print("  ⏳ Bot検出回避スクリプト実行中...")
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("  ✓ Bot検出回避スクリプト実行完了")
            
            print("  🎉 Chrome WebDriver初期化成功")
            logger.info("Chrome WebDriver初期化成功")
            
        except Exception as e:
            print(f"  ❌ WebDriver初期化エラー: {e}")
            logger.error(f"WebDriver初期化エラー: {e}")
            self.driver = None
    
    def get_page_source(self, url: str, wait_timeout: int = 10) -> str:
        """指定URLのページソースを取得"""
        if not self.driver:
            raise RuntimeError("WebDriverが初期化されていません")
        
        try:
            print(f"  📱 Seleniumでページ取得開始: {url}")
            logger.info(f"Seleniumでページ取得開始: {url}")
            
            print("  ⏳ ページにアクセス中...")
            self.driver.get(url)
            print("  ✓ ページアクセス完了")
            
            print("  ⏳ ページの読み込み完了を待機中...")
            # ページの読み込み完了を待機
            WebDriverWait(self.driver, wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("  ✓ ページ読み込み完了")
            
            # 少し待機してJavaScriptの動的コンテンツを読み込む
            print("  ⏳ JavaScript動的コンテンツ読み込み中...")
            import time
            time.sleep(2)
            print("  ✓ 動的コンテンツ読み込み完了")
            
            print("  ⏳ ページソースを取得中...")
            page_source = self.driver.page_source
            print(f"  ✓ ページソース取得完了: {len(page_source)} 文字")
            logger.info(f"ページソース取得完了: {len(page_source)} 文字")
            
            return page_source
            
        except Exception as e:
            print(f"  ❌ ページソース取得エラー: {e}")
            logger.error(f"ページソース取得エラー: {e}")
            raise
    
    def close(self):
        """WebDriverを閉じる"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver正常終了")
            except Exception as e:
                logger.error(f"WebDriver終了エラー: {e}")
            finally:
                self.driver = None
