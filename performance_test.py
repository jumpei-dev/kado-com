#!/usr/bin/env python3
"""
パフォーマンステストスクリプト
最適化前後の性能を測定し、効果を評価する
"""

import time
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import DatabaseManager
from app.core.cache import cache

class PerformanceTest:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.db = DatabaseManager()
        
    def measure_time(self, func, *args, **kwargs):
        """関数の実行時間を測定"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time, result
    
    def test_database_queries(self, iterations=10):
        """データベースクエリのパフォーマンステスト"""
        print("\n🔍 データベースクエリパフォーマンステスト")
        print("=" * 50)
        
        # キャッシュをクリア
        cache.clear()
        
        # 店舗一覧取得テスト
        print("\n📊 店舗一覧取得テスト")
        times = []
        for i in range(iterations):
            if i == 5:  # 5回目でキャッシュをクリア
                cache.clear()
                print("  💾 キャッシュをクリアしました")
            
            exec_time, result = self.measure_time(
                self.db.get_businesses,
                area="関東",
                business_type="delivery_health",
                page=1,
                per_page=20
            )
            times.append(exec_time)
            print(f"  実行 {i+1:2d}: {exec_time:.4f}秒 ({len(result)}件取得)")
        
        print(f"\n  平均実行時間: {statistics.mean(times):.4f}秒")
        print(f"  最小実行時間: {min(times):.4f}秒")
        print(f"  最大実行時間: {max(times):.4f}秒")
        
        # ランキング取得テスト
        print("\n🏆 ランキング取得テスト")
        cache.clear()
        times = []
        for i in range(iterations):
            if i == 5:
                cache.clear()
                print("  💾 キャッシュをクリアしました")
            
            exec_time, result = self.measure_time(
                self.db.get_store_ranking,
                area="関東",
                business_type="delivery_health",
                period="week",
                limit=20
            )
            times.append(exec_time)
            print(f"  実行 {i+1:2d}: {exec_time:.4f}秒 ({len(result)}件取得)")
        
        print(f"\n  平均実行時間: {statistics.mean(times):.4f}秒")
        print(f"  最小実行時間: {min(times):.4f}秒")
        print(f"  最大実行時間: {max(times):.4f}秒")
    
    def test_api_endpoints(self, iterations=5):
        """APIエンドポイントのパフォーマンステスト"""
        print("\n🌐 APIエンドポイントパフォーマンステスト")
        print("=" * 50)
        
        endpoints = [
            "/api/stores?area=関東&business_type=delivery_health&page=1",
            "/api/stores/ranking?area=関東&business_type=delivery_health&period=week"
        ]
        
        for endpoint in endpoints:
            print(f"\n📡 テスト対象: {endpoint}")
            times = []
            
            for i in range(iterations):
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}{endpoint}")
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        exec_time = end_time - start_time
                        times.append(exec_time)
                        print(f"  実行 {i+1}: {exec_time:.4f}秒 (ステータス: {response.status_code})")
                    else:
                        print(f"  実行 {i+1}: エラー (ステータス: {response.status_code})")
                except Exception as e:
                    print(f"  実行 {i+1}: 接続エラー - {str(e)}")
            
            if times:
                print(f"\n  平均レスポンス時間: {statistics.mean(times):.4f}秒")
                print(f"  最小レスポンス時間: {min(times):.4f}秒")
                print(f"  最大レスポンス時間: {max(times):.4f}秒")
    
    def test_concurrent_requests(self, concurrent_users=5, requests_per_user=3):
        """同時リクエストのパフォーマンステスト"""
        print(f"\n👥 同時リクエストテスト ({concurrent_users}ユーザー × {requests_per_user}リクエスト)")
        print("=" * 50)
        
        def make_request(user_id, request_id):
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/stores?area=関東&page=1")
                end_time = time.time()
                return {
                    'user_id': user_id,
                    'request_id': request_id,
                    'time': end_time - start_time,
                    'status': response.status_code,
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'user_id': user_id,
                    'request_id': request_id,
                    'time': None,
                    'status': None,
                    'success': False,
                    'error': str(e)
                }
        
        # 同時リクエストを実行
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for user_id in range(concurrent_users):
                for request_id in range(requests_per_user):
                    future = executor.submit(make_request, user_id, request_id)
                    futures.append(future)
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        # 結果を分析
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        print(f"\n📈 結果サマリー:")
        print(f"  成功リクエスト: {len(successful_requests)}/{len(results)}")
        print(f"  失敗リクエスト: {len(failed_requests)}/{len(results)}")
        
        if successful_requests:
            times = [r['time'] for r in successful_requests]
            print(f"  平均レスポンス時間: {statistics.mean(times):.4f}秒")
            print(f"  最小レスポンス時間: {min(times):.4f}秒")
            print(f"  最大レスポンス時間: {max(times):.4f}秒")
    
    def run_full_test(self):
        """全てのパフォーマンステストを実行"""
        print("🚀 パフォーマンステスト開始")
        print("=" * 60)
        
        # データベーステスト
        self.test_database_queries()
        
        # APIテスト（サーバーが起動している場合のみ）
        try:
            response = requests.get(f"{self.base_url}/api/stores?area=関東&business_type=delivery_health&page=1", timeout=2)
            if response.status_code in [200, 404]:  # サーバーが応答すればOK
                self.test_api_endpoints()
                self.test_concurrent_requests()
            else:
                print("\n⚠️  サーバーが起動していないため、APIテストをスキップします")
        except:
            print("\n⚠️  サーバーに接続できないため、APIテストをスキップします")
        
        print("\n✅ パフォーマンステスト完了")
        print("=" * 60)

if __name__ == "__main__":
    test = PerformanceTest()
    test.run_full_test()