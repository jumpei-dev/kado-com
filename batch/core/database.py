"""
バッチ処理システムのためのデータベース接続と操作。
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection_string = "postgresql://postgres.hnmbsqydlfemlmsyexrq:Ggzzmmb3@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
    
    @contextmanager
    def get_connection(self):
        """自動クリーンアップ機能付きでデータベース接続を取得する"""
        conn = None
        try:
            conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
            conn.autocommit = True
            yield conn
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """SELECTクエリを実行して結果を返す"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    def execute_command(self, command: str, params: tuple = None) -> int:
        """INSERT/UPDATE/DELETEコマンドを実行して影響を受けた行数を返す"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(command, params)
                return cursor.rowcount
    
    def get_businesses(self) -> List[Dict[str, Any]]:
        """すべてのアクティブな店舗を取得する"""
        query = """
        SELECT business_id, name, area, prefecture, type, capacity, 
               open_hour, close_hour, schedule_url1, in_scope,
               working_type, cast_type, shift_type, media
        FROM business 
        WHERE in_scope = true
        ORDER BY name
        """
        results = self.execute_query(query)
        
        # 結果を辞書形式に変換してstatus_collection.pyで期待される形式に合わせる
        businesses = {}
        for i, row in enumerate(results):
            businesses[i] = {
                "Business ID": row["business_id"],  # 列名でアクセス
                "name": row["name"],
                "area": row["area"], 
                "prefecture": row["prefecture"],
                "type": row["type"],
                "capacity": row["capacity"],
                "open_hour": row["open_hour"],
                "close_hour": row["close_hour"], 
                "URL": row["schedule_url1"],  # schedule_url1をURLとして使用
                "in_scope": row["in_scope"],
                "working_type": row["working_type"],
                "cast_type": row["cast_type"],
                "shift_type": row["shift_type"],
                "media": row["media"]
            }
        
        return businesses
    
    def get_casts_by_business(self, business_id: int) -> List[Dict[str, Any]]:
        """指定した店舗のすべてのキャストを取得する"""
        query = """
        SELECT cast_id, business_id, name, profile_url
        FROM cast 
        WHERE business_id = %s AND is_active = true
        ORDER BY name
        """
        return self.execute_query(query, (business_id,))
    
    def insert_status(self, cast_id: str, is_working: bool, is_on_shift: bool, recorded_at: str) -> bool:
        """新しいステータスレコードを挿入する"""
        try:
            command = """
            INSERT INTO status (cast_id, is_working, is_on_shift, recorded_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cast_id, recorded_at) DO UPDATE SET
            is_working = EXCLUDED.is_working,
            is_on_shift = EXCLUDED.is_on_shift
            """
            rows = self.execute_command(command, (cast_id, is_working, is_on_shift, recorded_at))
            return rows > 0
        except Exception as e:
            logger.error(f"キャストID {cast_id} のステータス挿入エラー: {e}")
            return False
    
    def get_status_history_dates_to_calculate(self, business_id: int, days_back: int = 30) -> List[str]:
        """ステータス履歴の計算が必要な日付を取得する"""
        query = """
        WITH date_range AS (
            SELECT generate_series(
                CURRENT_DATE - INTERVAL '%s days',
                CURRENT_DATE - INTERVAL '1 day',
                '1 day'::interval
            )::date AS target_date
        )
        SELECT dr.target_date::text
        FROM date_range dr
        LEFT JOIN status_history sh ON sh.business_id = %s 
            AND sh.biz_date = dr.target_date
        WHERE sh.business_id IS NULL
        ORDER BY dr.target_date
        """
        results = self.execute_query(query, (days_back, business_id))
        return [row['target_date'] for row in results]
    
    def calculate_and_insert_status_history(self, business_id: int, calculation_date: str) -> bool:
        """指定した日付のステータス履歴を計算して挿入する"""
        try:
            command = """
            WITH business_hours AS (
                SELECT open_hour, close_hour
                FROM business WHERE business_id = %s
            ),
            status_data AS (
                SELECT 
                    s.cast_id,
                    COUNT(CASE WHEN s.is_working THEN 1 END) as working_count,
                    COUNT(*) as total_count
                FROM status s
                CROSS JOIN business_hours bh
                WHERE s.business_id = %s
                AND s.recorded_at::date = %s
                AND EXTRACT(HOUR FROM s.recorded_at) BETWEEN 
                    EXTRACT(HOUR FROM bh.open_hour) AND 
                    EXTRACT(HOUR FROM bh.close_hour)
                GROUP BY s.cast_id
            )
            INSERT INTO status_history (business_id, biz_date, working_rate)
            SELECT 
                %s,
                %s::date,
                CASE 
                    WHEN SUM(total_count) > 0 THEN 
                        ROUND((SUM(working_count)::decimal / SUM(total_count)) * 100, 2)
                    ELSE 0
                END
            FROM status_data
            ON CONFLICT (business_id, biz_date) DO UPDATE SET
            working_rate = EXCLUDED.working_rate
            """
            rows = self.execute_command(command, (business_id, business_id, calculation_date, business_id, calculation_date))
            return rows > 0
        except Exception as e:
            logger.error(f"店舗ID {business_id}、日付 {calculation_date} のステータス履歴計算エラー: {e}")
            return False
