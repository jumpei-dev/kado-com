"""
データベース保存処理

稼働ステータスデータのデータベース保存を管理
"""

from typing import List, Dict, Any

try:
    from ..core.database import DatabaseManager
except ImportError:
    try:
        from core.database import DatabaseManager
    except ImportError:
        DatabaseManager = None

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


async def save_working_status_to_database(cast_data_list: List[Dict[str, Any]]) -> bool:
    """稼働ステータスデータをデータベースに保存"""
    if not cast_data_list:
        logger.info("保存するデータがありません")
        return True
    
    try:
        if DatabaseManager:
            database = DatabaseManager()
        else:
            logger.error("DatabaseManagerが利用できません")
            return False
        
        # バッチでデータを保存（テーブル名をstatusに変更）
        insert_query = """
            INSERT INTO status 
            (business_id, cast_id, is_working, is_on_shift, datetime) 
            VALUES (%s, %s, %s, %s, %s)
        """
        
        # 個別にデータを保存
        saved_count = 0
        for cast_data in cast_data_list:
            try:
                database.execute_command(insert_query, (
                    cast_data["business_id"],
                    cast_data["cast_id"], 
                    cast_data["is_working"],
                    cast_data["is_on_shift"],
                    cast_data["collected_at"]
                ))
                saved_count += 1
            except Exception as save_error:
                logger.error(f"個別保存エラー: {save_error}")
        
        logger.info(f"稼働ステータスをデータベースに保存しました: {saved_count} 件")
        return True
        
    except Exception as e:
        logger.error(f"データベース保存エラー: {str(e)}")
        return False
