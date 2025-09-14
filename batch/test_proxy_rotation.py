#!/usr/bin/env python3
"""
プロキシローテーション機能の詳細テストスクリプト
"""

import asyncio
import sys
from pathlib import Path

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'jobs' / 'status_collection'))

from jobs.status_collection.aiohttp_loader import AiohttpHTMLLoader
from utils.config import get_scraping_config

async def test_proxy_rotation_detailed():
    """プロキシローテーションの詳細テスト"""
    print("🚀 プロキシローテーション詳細テスト開始")
    
    # 設定を取得してプロキシを有効化
    config = get_scraping_config()
    config['enable_proxy_rotation'] = True
    config['timeout'] = 15  # タイムアウトを長めに設定
    
    print(f"📋 設定: プロキシローテーション={config['enable_proxy_rotation']}")
    
    # IPアドレス確認用URL
    ip_check_url = 'http://httpbin.org/ip'
    
    async with AiohttpHTMLLoader() as loader:
        # 設定を上書き
        loader.config = config
        loader.session_manager.config = config
        
        print("\n🔍 プロキシを使用したIPローテーションテスト")
        
        # 複数回リクエストしてIPの変化を確認
        ips_obtained = []
        
        for i in range(5):
            print(f"\n--- リクエスト {i+1} ---")
            
            try:
                # 現在のプロキシ情報を取得
                current_proxy = loader.session_manager.get_current_proxy()
                if current_proxy:
                    print(f"🔄 使用プロキシ: {current_proxy['host']}:{current_proxy['port']}")
                else:
                    print("🔄 プロキシなし（直接接続）")
                
                # HTMLを取得
                html = await loader.load_html(ip_check_url)
                
                if html:
                    # IPアドレスを抽出
                    import json
                    try:
                        ip_data = json.loads(html)
                        ip_address = ip_data.get('origin', 'unknown')
                        ips_obtained.append(ip_address)
                        print(f"✅ 取得IP: {ip_address}")
                    except:
                        print(f"✅ 取得成功: {html[:50]}...")
                        ips_obtained.append(html[:20])
                else:
                    print("❌ 取得失敗")
                    
            except Exception as e:
                print(f"❌ エラー: {e}")
                # エラー時はプロキシをローテーション
                if hasattr(loader.session_manager, 'proxy_manager'):
                    next_proxy = await loader.session_manager.proxy_manager.get_next_proxy()
                    if next_proxy:
                        print(f"🔄 次のプロキシに切り替え: {next_proxy['host']}:{next_proxy['port']}")
            
            # 少し待機
            await asyncio.sleep(3)
    
    # 結果の分析
    print("\n📊 テスト結果分析")
    print(f"取得したIP数: {len(ips_obtained)}")
    unique_ips = set(ips_obtained)
    print(f"ユニークIP数: {len(unique_ips)}")
    
    if len(unique_ips) > 1:
        print("✅ IPローテーションが正常に動作しています")
    else:
        print("⚠️ IPローテーションが検出されませんでした（プロキシが機能していない可能性）")
    
    for i, ip in enumerate(ips_obtained, 1):
        print(f"  {i}. {ip}")
    
    print("\n🏁 プロキシローテーション詳細テスト完了")

async def test_proxy_failure_handling():
    """プロキシ失敗時の処理テスト"""
    print("\n🔧 プロキシ失敗処理テスト開始")
    
    from jobs.status_collection.aiohttp_loader import ProxyManager
    
    config = {
        'proxy_refresh_interval': 3600,
        'proxy_test_timeout': 5
    }
    
    proxy_manager = ProxyManager(config)
    
    # プロキシリストを取得
    proxy_list = await proxy_manager.get_proxy_list()
    print(f"📡 利用可能プロキシ数: {len(proxy_list)}")
    
    if proxy_list:
        # 最初のプロキシを失敗としてマーク
        first_proxy = proxy_list[0]
        print(f"❌ プロキシ失敗をシミュレート: {first_proxy['host']}:{first_proxy['port']}")
        proxy_manager.mark_proxy_failed(first_proxy['url'])
        
        # 失敗後の利用可能プロキシを確認
        available_after_failure = await proxy_manager.get_proxy_list()
        print(f"📡 失敗後の利用可能プロキシ数: {len(available_after_failure)}")
        
        if len(available_after_failure) < len(proxy_list):
            print("✅ 失敗プロキシが正しく除外されました")
        else:
            print("⚠️ 失敗プロキシの除外が機能していません")
        
        # 失敗プロキシリストをリセット
        proxy_manager.reset_failed_proxies()
        reset_proxies = await proxy_manager.get_proxy_list()
        print(f"📡 リセット後の利用可能プロキシ数: {len(reset_proxies)}")
        
        if len(reset_proxies) == len(proxy_list):
            print("✅ プロキシリセットが正常に動作しました")
        else:
            print("⚠️ プロキシリセットに問題があります")
    
    print("🏁 プロキシ失敗処理テスト完了")

async def main():
    """メイン関数"""
    print("=" * 60)
    print("🌐 プロキシローテーション機能 詳細テスト")
    print("=" * 60)
    
    try:
        # プロキシ失敗処理のテスト
        await test_proxy_failure_handling()
        
        # プロキシローテーションの詳細テスト
        await test_proxy_rotation_detailed()
        
        print("\n" + "=" * 60)
        print("✅ 全ての詳細テストが完了しました")
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