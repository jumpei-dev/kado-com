#!/usr/bin/env python3

import asyncio
import logging
from jobs.status_collection.aiohttp_loader import ProxyManager, AiohttpHTMLLoader
from utils.config import get_scraping_config

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_improved_proxy_system():
    """改善されたプロキシシステムのテスト"""
    logger.info("🚀 改善されたプロキシシステムのテストを開始")
    
    # AiohttpHTMLLoaderを初期化
    loader = AiohttpHTMLLoader()
    
    # 設定を取得してプロキシローテーション有効化
    config = loader.config
    config['enable_proxy_rotation'] = True
    config['proxy_rotation_interval'] = 1  # 1リクエストごとにローテーション
    config['force_immediate_execution'] = True  # 強制即時実行モード
    config['interval_base_minutes'] = 0.1  # デバッグ用に短縮（6秒）
    
    # プロキシマネージャーを再初期化
    loader.session_manager.proxy_manager = ProxyManager(config)
    loader.session_manager.current_proxy = None
    
    try:
        # 1. プロキシマネージャーの状態確認
        logger.info("\n=== プロキシマネージャーの状態確認 ===")
        logger.info(f"SessionManager: {loader.session_manager}")
        logger.info(f"SessionManager.proxy_manager: {loader.session_manager.proxy_manager}")
        logger.info(f"SessionManager.current_proxy: {loader.session_manager.current_proxy}")
        
        # 2. プロキシリストの取得テスト
        logger.info("\n=== プロキシリスト取得テスト ===")
        proxy_manager = loader.session_manager.proxy_manager
        if proxy_manager:
            proxy_list = await proxy_manager.get_proxy_list()
            logger.info(f"取得したプロキシ数: {len(proxy_list)}")
            
            # プロキシソース別の統計を表示
            source_stats = {}
            for proxy in proxy_list:
                source = proxy.get('source', 'unknown')
                source_stats[source] = source_stats.get(source, 0) + 1
            
            logger.info("プロキシソース別統計:")
            for source, count in source_stats.items():
                logger.info(f"  {source}: {count}個")
            
            # 取得したプロキシの最初の5個を表示
            logger.info("\n取得したプロキシ（最初の5個）:")
            for i, proxy in enumerate(proxy_list[:5], 1):
                source = proxy.get('source', 'unknown')
                logger.info(f"  {i}. {proxy['host']}:{proxy['port']} ({source})")
        
        # 3. プロキシの基本テスト
        logger.info("\n=== プロキシ基本テスト ===")
        if proxy_manager and proxy_list:
            test_proxy = proxy_list[0]
            logger.info(f"テスト対象プロキシ: {test_proxy['host']}:{test_proxy['port']}")
            
            try:
                test_result = await proxy_manager.test_proxy(test_proxy)
                logger.info(f"テスト結果: {'✅ 成功' if test_result else '❌ 失敗'}")
            except Exception as e:
                logger.error(f"テスト中にエラーが発生: {e}")
        
        # 4. 実際のHTMLローダーテスト
        logger.info("\n=== 実際のHTMLローダーテスト ===")
        
        test_urls = [
            "http://httpbin.org/ip",
            "http://httpbin.org/user-agent",
            "http://httpbin.org/headers"
        ]
        
        for i, url in enumerate(test_urls, 1):
            logger.info(f"\nテスト {i}: {url}")
            
            try:
                # 現在のプロキシを確認
                current_proxy = loader.session_manager.current_proxy
                logger.info(f"使用予定プロキシ: {current_proxy['host']}:{current_proxy['port']} ({current_proxy.get('source', 'unknown')})" if current_proxy else "プロキシなし")
                
                # HTMLを取得
                html_content = await loader.load_html(url)
                if html_content:
                    logger.info(f"✅ 成功: {len(html_content)}文字のHTMLを取得")
                    # レスポンスの一部を表示（IPアドレス情報など）
                    if "origin" in html_content:
                        import json
                        try:
                            response_data = json.loads(html_content)
                            logger.info(f"  取得したIP: {response_data.get('origin', 'N/A')}")
                        except:
                            pass
                else:
                    logger.warning("⚠️ HTMLの取得に失敗")
                    
            except Exception as e:
                logger.error(f"❌ エラー: {e}")
            
            # 少し待機
            await asyncio.sleep(1)
        
        # 5. プロキシローテーションテスト
        logger.info("\n=== プロキシローテーションテスト ===")
        
        for i in range(3):
            logger.info(f"\nローテーション {i+1}:")
            current_proxy = loader.session_manager.current_proxy
            if current_proxy:
                logger.info(f"現在のプロキシ: {current_proxy['host']}:{current_proxy['port']}")
            else:
                logger.info("現在のプロキシ: なし")
            
            # 次のプロキシに切り替え
            if proxy_manager:
                next_proxy = await proxy_manager.get_next_proxy()
                if next_proxy:
                    logger.info(f"次のプロキシ: {next_proxy['host']}:{next_proxy['port']}")
                else:
                    logger.info("次のプロキシ: なし")
    
    except Exception as e:
        logger.error(f"テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # クリーンアップ
        await loader.__aexit__(None, None, None)
        logger.info("\n🏁 テスト完了")

if __name__ == "__main__":
    asyncio.run(test_improved_proxy_system())