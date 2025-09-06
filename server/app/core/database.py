import sys
import os

# batch/core/database.py を利用するためのパス追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'batch'))

try:
    from core.database import DatabaseManager
    print("✅ batch/core/database.py を正常にインポートしました")
except ImportError as e:
    print(f"⚠️ batch/core/database.py のインポートに失敗: {e}")
    # フォールバック: 簡易版のDatabaseManager
    class DatabaseManager:
        def __init__(self):
            pass
        
        def get_businesses(self):
            return {}

# API用のデータベースヘルパー関数
async def get_database():
    """Dependency: データベース接続を取得"""
    return DatabaseManager()
