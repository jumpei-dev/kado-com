#!/usr/bin/env python3
"""
プロキシローテーション統合テスト
実装されたProxyManagerとSessionManagerの統合動作をテスト
"""

import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from batch.jobs.status_collection.aiohttp_loader import AiohttpHTMLLoader, ProxyManager
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_proxy_manager():
    """ProxyManagerの基本機能テスト"""
    logger.info("=== ProxyManager基本機能テスト ===")
    
    config = {
        'use_proxy_rotation': True,
        'proxy_refresh_interval': 60,  # テスト用に短縮
        'proxy_test_timeout': 5
    }
    
    proxy_manager = ProxyManager(config)
    
    # プロキシリスト取得テスト
    logger.info("📡 プロキシリスト取得テスト...")
    proxy_list = await proxy_manager.get_proxy_list()
    logger.info(f"✅ 取得したプロキシ数: {len(proxy_list)}")
    
    if proxy_list:
        # 最初の3つのプロキシをテスト
        for i, proxy in enumerate(proxy_list[:3]):
            logger.info(f"🔍 プロキシテスト {i+1}: {proxy['host']}:{proxy['port']}")
            is_working = await proxy_manager.test_proxy(proxy)
            logger.info(f"{'✅' if is_working else '❌'} テスト結果: {proxy['url']}")
    
    # プロキシローテーションテスト
    logger.info("\n🔄 プロキシローテーションテスト...")
    for i in range(5):
        proxy = await proxy_manager.get_next_proxy()
        if proxy:
            logger.info(f"  {i+1}. {proxy['host']}:{proxy['port']} (source: {proxy.get('source', 'unknown')})")
        else:
            logger.warning(f"  {i+1}. プロキシ取得失敗")
    
    return proxy_manager

async def test_integrated_scraping():
    """統合スクレイピングテスト"""
    logger.info("\n=== 統合スクレイピングテスト ===")
    
    # プロキシローテーション有効化設定
    os.environ['FORCE_IMMEDIATE'] = 'true'  # テスト用に待機時間をスキップ
    
    test_urls = [
        'http://httpbin.org/ip',  # IPアドレス確認
        'http://httpbin.org/user-agent',  # User-Agent確認
        'http://httpbin.org/headers',  # ヘッダー確認
    ]
    
    async with AiohttpHTMLLoader() as loader:
        # プロキシローテーション有効化
        loader.session_manager.proxy_manager = ProxyManager({
            'use_proxy_rotation': True,
            'proxy_refresh_interval': 60,
            'proxy_test_timeout': 5
        })
        
        for i, url in enumerate(test_urls):
            logger.info(f"\n📡 テスト {i+1}: {url}")
            
            try:
                html = await loader.load_html(url)
                if html:
                    logger.info(f"✅ 取得成功: {len(html)}文字")
                    # IPアドレス情報を抽出
                    if 'httpbin.org/ip' in url:
                        import json
                        try:
                            ip_data = json.loads(html)
                            logger.info(f"🌐 使用IP: {ip_data.get('origin', 'unknown')}")
                        except:
                            logger.info(f"📄 レスポンス: {html[:200]}...")
                    else:
                        logger.info(f"📄 レスポンス: {html[:200]}...")
                else:
                    logger.warning(f"❌ 取得失敗: {url}")
                    
            except Exception as e:
                logger.error(f"❌ エラー: {e}")

async def test_proxy_failure_handling():
    """プロキシ失敗処理テスト"""
    logger.info("\n=== プロキシ失敗処理テスト ===")
    
    config = {
        'use_proxy_rotation': True,
        'proxy_refresh_interval': 60,
        'proxy_test_timeout': 2  # 短いタイムアウトで失敗を誘発
    }
    
    proxy_manager = ProxyManager(config)
    
    # 無効なプロキシを手動で追加
    invalid_proxy = {
        'host': '192.168.1.999',
        'port': 8080,
        'type': 'http',
        'url': 'http://192.168.1.999:8080',
        'source': 'test'
    }
    
    proxy_manager.proxy_list.append(invalid_proxy)
    logger.info(f"🧪 無効プロキシ追加: {invalid_proxy['url']}")
    
    # 失敗マークテスト
    proxy_manager.mark_proxy_failed(invalid_proxy['url'])
    logger.info(f"❌ プロキシ失敗マーク: {invalid_proxy['url']}")
    
    # 利用可能プロキシリスト確認
    available_proxies = await proxy_manager.get_proxy_list()
    logger.info(f"✅ 利用可能プロキシ数: {len(available_proxies)}")
    
    # 失敗したプロキシが除外されているか確認
    failed_urls = [p['url'] for p in available_proxies if p['url'] == invalid_proxy['url']]
    if not failed_urls:
        logger.info("✅ 失敗プロキシが正常に除外されました")
    else:
        logger.warning("⚠️ 失敗プロキシが除外されていません")

async def main():
    """メインテスト実行"""
    logger.info("🚀 プロキシローテーション統合テスト開始")
    
    try:
        # 1. ProxyManager基本機能テスト
        await test_proxy_manager()
        
        # 2. 統合スクレイピングテスト
        await test_integrated_scraping()
        
        # 3. プロキシ失敗処理テスト
        await test_proxy_failure_handling()
        
        logger.info("\n🎉 全テスト完了")
        
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 環境変数クリーンアップ
        if 'FORCE_IMMEDIATE' in os.environ:
            del os.environ['FORCE_IMMEDIATE']

if __name__ == "__main__":
    asyncio.run(main())