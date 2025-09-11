#!/usr/bin/env python3
"""
テスト用稼働推移データ作成スクリプト
status_historyテーブルにダミーデータを挿入
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.absolute()))

try:
    from app.core.database import DatabaseManager
except ImportError:
    print("❌ DatabaseManagerをインポートできません")
    print("ディレクトリ構造を確認してください")
    sys.exit(1)

def create_test_working_trend_data():
    """テスト用の稼働推移データを挿入"""
    print("🔧 テスト用稼働推移データの作成を開始...")
    
    try:
        db = DatabaseManager()
        
        # 過去7日間のデータを生成
        base_date = datetime.now().date()
        print(f"📅 基準日: {base_date}")
        
        # 店舗ID 1-6 のデータを作成
        for store_id in range(1, 7):
            print(f"📊 店舗ID {store_id} のデータを作成中...")
            
            for i in range(7):  # 過去7日間
                biz_date = base_date - timedelta(days=i)
                
                # 曜日に基づく基本稼働率
                weekday = biz_date.weekday()  # 0=月曜, 6=日曜
                
                # 曜日別基本稼働率 (月〜日)
                base_rates = [65, 70, 75, 85, 95, 90, 45]  # 月〜日
                base_rate = base_rates[weekday]
                
                # ランダムな変動を追加
                working_rate = max(0, min(100, base_rate + random.randint(-15, 15)))
                
                print(f"  📈 {biz_date} (曜日:{weekday}): 稼働率 {working_rate}%")
                
                # データ挿入
                query = """
                INSERT INTO status_history (business_id, biz_date, working_rate)
                VALUES (%s, %s, %s)
                ON CONFLICT (business_id, biz_date) DO UPDATE SET
                working_rate = EXCLUDED.working_rate
                """
                
                try:
                    db.execute_command(query, (store_id, biz_date, working_rate))
                except Exception as insert_error:
                    print(f"❌ データ挿入エラー: {insert_error}")
                    # テーブルが存在しない場合は作成
                    create_table_query = """
                    CREATE TABLE IF NOT EXISTS status_history (
                        business_id INTEGER NOT NULL,
                        biz_date DATE NOT NULL,
                        working_rate NUMERIC(5,2) DEFAULT 0.00,
                        PRIMARY KEY (business_id, biz_date)
                    );
                    """
                    print("🔧 status_historyテーブルを作成中...")
                    db.execute_command(create_table_query)
                    
                    # 再度データ挿入を試行
                    db.execute_command(query, (store_id, biz_date, working_rate))
        
        print("✅ テスト用稼働推移データの挿入完了")
        
        # 作成されたデータを確認
        print("\n📋 作成されたデータのサンプル:")
        check_query = """
        SELECT business_id, biz_date, working_rate, 
               EXTRACT(DOW FROM biz_date) as day_of_week
        FROM status_history 
        WHERE business_id <= 3
        ORDER BY business_id, biz_date DESC
        LIMIT 10
        """
        
        results = db.fetch_all(check_query)
        for row in results:
            weekday_names = ['日', '月', '火', '水', '木', '金', '土']
            weekday_name = weekday_names[int(row['day_of_week'])]
            print(f"  店舗{row['business_id']}: {row['biz_date']} ({weekday_name}) - {row['working_rate']}%")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_working_trend_data()
