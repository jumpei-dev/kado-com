import sys
import os
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

logger = logging.getLogger(__name__)

try:
    from batch.core.database import DatabaseManager
    logger.info("✅ batch/core/database.py を正常にインポートしました")
except ImportError as e:
    logger.error(f"⚠️ batch/core/database.py のインポートに失敗: {e}")
    # フォールバック: 簡易版のDatabaseManager
    class DatabaseManager:
        def __init__(self):
            pass
        
        def get_businesses(self):
            # ダミーデータを返す
            return {
                0: {"Business ID": 1, "name": "チュチュバナナ", "blurred_name": "チ○○バ○○", "prefecture": "東京都", "area": "関東", "type": "ソープランド", "in_scope": True, "last_updated": "2025-09-07"},
                1: {"Business ID": 2, "name": "クラブA", "blurred_name": "ク○○A", "prefecture": "大阪府", "area": "関西", "type": "キャバクラ", "in_scope": True, "last_updated": "2025-09-07"},
                2: {"Business ID": 3, "name": "レモネード", "blurred_name": "レ○○○ド", "prefecture": "名古屋市", "area": "中部", "type": "ピンサロ", "in_scope": True, "last_updated": "2025-09-07"}
            }
            
        def get_store_ranking(self, area="all", business_type="all", spec="all", period="week", limit=20, offset=0):
            # ダミーのランキングデータを返す
            return [
                {"business_id": 1, "name": "チュチュバナナ", "blurred_name": "チ○○バ○○", "area": "関東", "prefecture": "東京都", "type": "ソープランド", "cast_type": "スタンダード", "avg_working_rate": 85.5},
                {"business_id": 2, "name": "クラブA", "blurred_name": "ク○○A", "area": "関西", "prefecture": "大阪府", "type": "キャバクラ", "cast_type": "低スペ", "avg_working_rate": 78.2},
                {"business_id": 3, "name": "レモネード", "blurred_name": "レ○○○ド", "area": "中部", "prefecture": "名古屋市", "type": "ピンサロ", "cast_type": "スタンダード", "avg_working_rate": 72.8}
            ]
        
        def get_store_details(self, business_id):
            # ダミーの詳細データを返す
            from datetime import datetime, timedelta
            today = datetime.now()
            
            dummy_data = {
                1: {
                    "business_id": 1,
                    "name": "チュチュバナナ",
                    "blurred_name": "チ○○バ○○",
                    "area": "関東",
                    "prefecture": "東京都",
                    "type": "ソープランド",
                    "cast_type": "スタンダード",
                    "current_rate": 85.5,
                    "updated_at": today.strftime("%Y年%m月%d日"),
                    "weekly_history": [
                        {"label": "先週", "rate": 85.5, "date": today - timedelta(days=7)},
                        {"label": "2週間前", "rate": 82.3, "date": today - timedelta(days=14)},
                        {"label": "3週間前", "rate": 79.8, "date": today - timedelta(days=21)},
                        {"label": "4週間前", "rate": 80.1, "date": today - timedelta(days=28)}
                    ],
                    "monthly_history": [
                        {"label": "過去1ヶ月", "rate": 82.5, "date": today - timedelta(days=30)},
                        {"label": "過去2ヶ月", "rate": 80.7, "date": today - timedelta(days=60)},
                        {"label": "過去3ヶ月", "rate": 79.3, "date": today - timedelta(days=90)}
                    ]
                },
                2: {
                    "business_id": 2,
                    "name": "クラブA",
                    "blurred_name": "ク○○A",
                    "area": "関西",
                    "prefecture": "大阪府",
                    "type": "キャバクラ",
                    "cast_type": "低スペ",
                    "current_rate": 78.2,
                    "updated_at": today.strftime("%Y年%m月%d日"),
                    "weekly_history": [
                        {"label": "先週", "rate": 78.2, "date": today - timedelta(days=7)},
                        {"label": "2週間前", "rate": 75.6, "date": today - timedelta(days=14)},
                        {"label": "3週間前", "rate": 77.4, "date": today - timedelta(days=21)},
                        {"label": "4週間前", "rate": 73.9, "date": today - timedelta(days=28)}
                    ],
                    "monthly_history": [
                        {"label": "過去1ヶ月", "rate": 76.3, "date": today - timedelta(days=30)},
                        {"label": "過去2ヶ月", "rate": 74.5, "date": today - timedelta(days=60)},
                        {"label": "過去3ヶ月", "rate": 75.2, "date": today - timedelta(days=90)}
                    ]
                },
                3: {
                    "business_id": 3,
                    "name": "レモネード",
                    "blurred_name": "レ○○○ド",
                    "area": "中部",
                    "prefecture": "名古屋市",
                    "type": "ピンサロ",
                    "cast_type": "スタンダード",
                    "current_rate": 72.8,
                    "updated_at": today.strftime("%Y年%m月%d日"),
                    "weekly_history": [
                        {"label": "先週", "rate": 72.8, "date": today - timedelta(days=7)},
                        {"label": "2週間前", "rate": 70.5, "date": today - timedelta(days=14)},
                        {"label": "3週間前", "rate": 68.3, "date": today - timedelta(days=21)},
                        {"label": "4週間前", "rate": 71.2, "date": today - timedelta(days=28)}
                    ],
                    "monthly_history": [
                        {"label": "過去1ヶ月", "rate": 70.1, "date": today - timedelta(days=30)},
                        {"label": "過去2ヶ月", "rate": 68.7, "date": today - timedelta(days=60)},
                        {"label": "過去3ヶ月", "rate": 69.4, "date": today - timedelta(days=90)}
                    ]
                }
            }
            
            return dummy_data.get(business_id)

# API用のデータベースヘルパー関数
db_manager = DatabaseManager()

async def get_database():
    """依存性注入用のデータベースマネージャーを取得する"""
    try:
        # ここで実際のデータベース接続を試みる場合の処理
        # 本番環境では実際の接続を返す
        return db_manager
    except Exception as e:
        # エラーがあった場合もダミーデータを返せるようにする
        logger.error(f"データベース接続エラー: {e}")
        return db_manager
