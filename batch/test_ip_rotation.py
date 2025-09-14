#!/usr/bin/env python3
"""
IPローテーション機能のテストスクリプト
"""

import asyncio
import sys
from pathlib import Path

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'jobs' / 'status_collection'))

from jobs.status_collection.aiohttp_loader import AiohttpHTMLLoader
from utils.config import get_scraping_config

async def test_ip_rotation():
    """IPローテーション機能をテスト"""
    print("🚀 IPローテーション機能テスト開始")
    
    # 設定を取得してプロキシを有効化
    config = get_scraping_config()
    config['enable_proxy_rotation'] = True  # プロキシローテーションを有効化
    config['timeout'] = 10  # タイムアウトを短く設定
    
    print(f"📋 設定: プロキシローテーション={config['enable_proxy_rotation']}")
    
    # テスト用URL（IPアドレスを確認できるサービス）
    test_urls = [
        'http://httpbin.org/ip',
        'http://icanhazip.com',
        'http://ipinfo.io/ip'
    ]
    
    async with AiohttpHTMLLoader() as loader:
        # 設定を上書き
        loader.config = config
        loader.session_manager.config = config
        
        print("\n🔍 IPローテーションテスト実行中...")
        
        for i, url in enumerate(test_urls, 1):
            print(f"\n--- テスト {i}: {url} ---")
            
            try:
                # HTMLを取得
                html = await loader.load_html(url)
                
                if html:
                    # IPアドレスを抽出して表示
                    ip_info = html.strip()
                    print(f"✅ 取得成功: {ip_info[:100]}...")
                else:
                    print("❌ 取得失敗")
                    
            except Exception as e:
                print(f"❌ エラー: {e}")
            
            # 少し待機
            await asyncio.sleep(2)
    
    print("\n🏁 IPローテーション機能テスト完了")

async def test_proxy_manager():
    """ProxyManagerの単体テスト"""
    print("\n🔧 ProxyManager単体テスト開始")
    
    from jobs.status_collection.aiohttp_loader import ProxyManager
    
    config = {
        'proxy_refresh_interval': 3600,
        'proxy_test_timeout': 5
    }
    
    proxy_manager = ProxyManager(config)
    
    # プロキシリストを取得
    print("📡 プロキシリスト取得中...")
    proxy_list = await proxy_manager.get_proxy_list()
    
    print(f"✅ 取得したプロキシ数: {len(proxy_list)}")
    
    for i, proxy in enumerate(proxy_list[:3], 1):  # 最初の3個を表示
        print(f"  {i}. {proxy['host']}:{proxy['port']} ({proxy['type']})")
    
    # プロキシローテーションテスト
    if proxy_list:
        print("\n🔄 プロキシローテーションテスト")
        for i in range(3):
            proxy = await proxy_manager.get_next_proxy()
            if proxy:
                print(f"  ローテーション {i+1}: {proxy['host']}:{proxy['port']}")
            else:
                print(f"  ローテーション {i+1}: プロキシなし")
    
    print("🏁 ProxyManager単体テスト完了")

async def main():
    """メイン関数"""
    print("=" * 60)
    print("🌐 IPローテーション機能 総合テスト")
    print("=" * 60)
    
    try:
        # ProxyManagerの単体テスト
        await test_proxy_manager()
        
        # IPローテーション機能のテスト
        await test_ip_rotation()
        
        print("\n" + "=" * 60)
        print("✅ 全てのテストが完了しました")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 環境変数でテスト用の即時実行を有効化
    import os
    os.environ['FORCE_IMMEDIATE'] = 'true'
    
    asyncio.run(main())