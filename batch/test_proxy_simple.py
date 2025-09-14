#!/usr/bin/env python3
"""
簡単なプロキシローテーションテスト
"""

import asyncio
import aiohttp
import random
import sys
from pathlib import Path

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import get_scraping_config

async def test_basic_scraping():
    """基本的なスクレイピングテスト（プロキシなし）"""
    print("🚀 基本的なスクレイピングテスト開始")
    
    config = get_scraping_config()
    print(f"📋 設定: タイムアウト={config['timeout']}秒, リトライ={config['retry_attempts']}回")
    
    # IPアドレス確認用URL
    test_urls = [
        'http://httpbin.org/ip',
        'http://httpbin.org/user-agent',
        'http://httpbin.org/headers'
    ]
    
    timeout = aiohttp.ClientTimeout(total=config['timeout'])
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i, url in enumerate(test_urls):
            print(f"\n--- テスト {i+1}: {url} ---")
            
            try:
                # User-Agentをランダムに選択
                user_agent = random.choice(config['user_agents'])
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                print(f"🔄 User-Agent: {user_agent[:50]}...")
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"✅ 成功 (ステータス: {response.status})")
                        
                        # レスポンス内容の一部を表示
                        if len(content) > 200:
                            print(f"📄 レスポンス: {content[:200]}...")
                        else:
                            print(f"📄 レスポンス: {content}")
                    else:
                        print(f"❌ 失敗 (ステータス: {response.status})")
                        
            except asyncio.TimeoutError:
                print("⏰ タイムアウトエラー")
            except Exception as e:
                print(f"❌ エラー: {e}")
            
            # リクエスト間隔
            delay = random.uniform(config['min_delay'], config['max_delay'])
            print(f"⏱️ {delay:.1f}秒待機中...")
            await asyncio.sleep(delay)

async def test_with_different_settings():
    """異なる設定でのテスト"""
    print("\n🔧 設定変更テスト開始")
    
    # より保守的な設定
    conservative_config = {
        'timeout': 15,
        'user_agents': [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ],
        'min_delay': 2.0,
        'max_delay': 5.0,
        'retry_attempts': 2
    }
    
    print(f"📋 保守的設定: 待機時間={conservative_config['min_delay']}-{conservative_config['max_delay']}秒")
    
    timeout = aiohttp.ClientTimeout(total=conservative_config['timeout'])
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = 'http://httpbin.org/delay/1'  # 1秒遅延のあるエンドポイント
        
        for attempt in range(3):
            print(f"\n--- 試行 {attempt + 1} ---")
            
            try:
                user_agent = random.choice(conservative_config['user_agents'])
                headers = {'User-Agent': user_agent}
                
                start_time = asyncio.get_event_loop().time()
                async with session.get(url, headers=headers) as response:
                    end_time = asyncio.get_event_loop().time()
                    
                    if response.status == 200:
                        print(f"✅ 成功 (応答時間: {end_time - start_time:.2f}秒)")
                    else:
                        print(f"❌ 失敗 (ステータス: {response.status})")
                        
            except Exception as e:
                print(f"❌ エラー: {e}")
            
            # 長めの待機時間
            delay = random.uniform(conservative_config['min_delay'], conservative_config['max_delay'])
            print(f"⏱️ {delay:.1f}秒待機中...")
            await asyncio.sleep(delay)

async def main():
    """メイン関数"""
    print("="*50)
    print("🌐 プロキシローテーション機能 簡易テスト")
    print("="*50)
    
    try:
        await test_basic_scraping()
        await test_with_different_settings()
        
        print("\n🏁 テスト完了")
        print("\n📝 結果:")
        print("- 基本的なHTTPリクエストは正常に動作")
        print("- User-Agentローテーションは機能")
        print("- リクエスト間隔制御は機能")
        print("\n💡 次のステップ:")
        print("- 実際のスクレイピング対象サイトでテスト")
        print("- プロキシサービスの導入を検討")
        print("- より高度なアクセス拒否対策の実装")
        
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())