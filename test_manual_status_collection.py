#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本番のステータス収集処理を手動実行するテストツール
"""

import asyncio
import sys
import os
from datetime import datetime

# バッチモジュールのパスを設定
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'batch'))

# 本番のコードをインポート
try:
    from core.database import DatabaseManager
    from jobs.status_collection.collector import run_status_collection, collect_all_working_status
    from utils.logging_utils import get_logger
    logger = get_logger(__name__)
except ImportError as e:
    print(f"Status collection インポートエラー: {e}")
    # フォールバック: 基本的なログ設定
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 代替手段でインポートを試行
    sys.path.append('./batch')
    try:
        from core.database import DatabaseManager
    except ImportError:
        print("❌ データベースモジュールのインポートに失敗しました")
        sys.exit(1)

logger = get_logger(__name__)

async def test_manual_status_collection():
    """手動でステータス収集を実行"""
    
    print("🎯 本番ステータス収集処理の手動実行テスト")
    print("="*100)
    
    try:
        # データベースから店舗情報を取得
        db = DatabaseManager()
        businesses_list = db.get_businesses()
        
        if not businesses_list:
            print("❌ Businessレコードが見つかりません")
            return False
            
        print(f"🏪 取得した店舗数: {len(businesses_list)}")
        
        # 店舗情報をcollectorが期待する形式に変換
        businesses = {}
        for i, business in enumerate(businesses_list):
            business_data = {
                "name": business.get("name", ""),
                "Business ID": business.get("id", ""),
                "schedule_url": business.get("URL", ""),
                "media": "cityhaven"  # デフォルト
            }
            businesses[i] = business_data
            
        print(f"🔧 変換済み店舗データ: {len(businesses)}件")
        
        # 最初の店舗の情報を表示
        first_business = list(businesses.values())[0]
        print(f"📋 テスト対象店舗:")
        print(f"   名前: {first_business['name']}")
        print(f"   ID: {first_business['Business ID']}")
        print(f"   URL: {first_business['schedule_url']}")
        
        # ステータス収集実行（ライブデータ取得）
        print(f"\n🌐 ステータス収集開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 本番のコレクター実行
        success = await run_status_collection(businesses)
        
        if success:
            print("✅ ステータス収集処理が正常に完了しました")
        else:
            print("❌ ステータス収集処理でエラーが発生しました")
            
        return success
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_collection_only():
    """データベース保存なしで収集のみテスト"""
    
    print("🎯 データ収集のみテスト（DB保存なし）")
    print("="*100)
    
    try:
        # データベースから店舗情報を取得
        db = DatabaseManager()
        businesses_list = db.get_businesses()
        
        if not businesses_list:
            print("❌ Businessレコードが見つかりません")
            return []
            
        # 店舗情報を変換
        businesses = {}
        for i, business in enumerate(businesses_list):
            business_data = {
                "name": business.get("name", ""),
                "Business ID": business.get("id", ""),
                "schedule_url": business.get("URL", ""),
                "media": "cityhaven"
            }
            businesses[i] = business_data
            
        print(f"🏪 対象店舗: {len(businesses)}件")
        
        # 収集のみ実行（DB保存なし）
        print(f"\n📊 データ収集開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        all_cast_data = await collect_all_working_status(businesses, use_local_html=False)
        
        # 結果サマリー
        print(f"\n🎯 収集結果サマリー")
        print("="*80)
        print(f"総キャスト数: {len(all_cast_data)}")
        
        working_count = sum(1 for cast in all_cast_data if cast.get('is_working', False))
        on_shift_count = sum(1 for cast in all_cast_data if cast.get('on_shift', False))
        
        print(f"出勤中キャスト: {on_shift_count} 人")
        print(f"稼働中キャスト: {working_count} 人")
        
        if working_count > 0:
            print(f"\n✅ 稼働中キャスト詳細（最大5件表示）:")
            working_casts = [cast for cast in all_cast_data if cast.get('is_working', False)]
            for i, cast in enumerate(working_casts[:5]):
                print(f"  {i+1}. ID: {cast.get('cast_id', 'N/A')} | 店舗: {cast.get('business_id', 'N/A')}")
            
            if len(working_casts) > 5:
                print(f"  ... 他 {len(working_casts) - 5}件")
        
        print(f"\n📊 データ収集完了！")
        return all_cast_data
        
    except Exception as e:
        print(f"❌ 収集テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """メイン関数"""
    import sys
    
    print(f"⏰ 実行開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "collect-only":
        # データ収集のみ
        cast_data = asyncio.run(test_collection_only())
        print(f"\n📈 収集データ件数: {len(cast_data)}")
    else:
        # フル実行（収集＋DB保存）
        success = asyncio.run(test_manual_status_collection())
        if success:
            print("\n🎉 テスト成功！")
        else:
            print("\n💥 テスト失敗")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 処理が中断されました")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
