"""
履歴保存処理

status_historyテーブルへの保存
"""

from typing import Dict, Any

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class HistorySaver:
    """履歴保存処理クラス"""
    
    def __init__(self, database):
        self.database = database
    
    def save_to_status_history(self, history_data: Dict[str, Any]):
        """status_historyテーブルに稼働率データを保存"""
        try:
            # 既存データを削除（重複回避）
            delete_query = """
                DELETE FROM status_history 
                WHERE business_id = %s AND biz_date = %s
            """
            self.database.execute(
                delete_query, 
                (history_data["business_id"], history_data["biz_date"])
            )
            
            # 新しいデータを挿入
            insert_query = """
                INSERT INTO status_history 
                (business_id, biz_date, working_rate)
                VALUES (%s, %s, %s)
            """
            self.database.execute(insert_query, (
                history_data["business_id"],
                history_data["biz_date"],
                history_data["working_rate"]
            ))
            
            logger.debug(f"status_history保存成功: {history_data['business_id']} - {history_data['working_rate']:.2f}%")
            
        except Exception as e:
            logger.error(f"status_history保存エラー: {e}")
            raise
