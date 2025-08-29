"""
履歴サマリー取得処理

店舗の稼働率履歴データの取得
"""

from typing import Dict, Any

try:
    from ..core.database import DatabaseManager
except ImportError:
    from core.database import DatabaseManager

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


def get_business_history_summary(business_id: int, days: int = 7) -> Dict[str, Any]:
    """
    店舗のステータス履歴サマリーを取得する（status_history.py互換）
    
    Args:
        business_id: サマリーを取得する店舗ID
        days: 含める最近の日数
    
    Returns:
        履歴データとサマリー統計を含む辞書
    """
    try:
        database = DatabaseManager()
        
        query = """
            SELECT 
                biz_date,
                working_rate
            FROM status_history 
            WHERE business_id = %s 
            AND biz_date >= CURRENT_DATE - INTERVAL %s DAY
            ORDER BY biz_date DESC
        """
        
        results = database.fetch_all(query, (business_id, days))
        
        if not results:
            return {"business_id": business_id, "history": [], "summary": {}}
        
        # サマリー統計を計算
        rates = [r['working_rate'] for r in results if r['working_rate'] is not None]
        
        summary = {
            "business_id": business_id,
            "history": [
                {
                    "date": r['biz_date'].isoformat() if hasattr(r['biz_date'], 'isoformat') else str(r['biz_date']),
                    "working_rate": float(r['working_rate']) if r['working_rate'] else 0.0
                }
                for r in results
            ],
            "summary": {
                "days_calculated": len(results),
                "average_rate": sum(rates) / len(rates) if rates else 0.0,
                "max_rate": max(rates) if rates else 0.0,
                "min_rate": min(rates) if rates else 0.0
            }
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"店舗 {business_id} の履歴サマリー取得エラー: {e}")
        return {"business_id": business_id, "error": str(e)}
