import sys
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import bcrypt
from datetime import datetime, timedelta
import secrets
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

logger = logging.getLogger(__name__)
class DatabaseManager:
    def __init__(self, connection_string=None):
        # まず環境変数を確認、次にconfigを確認、最後にフォールバック
        from app.core.config import get_database_url
        self.connection_string = connection_string or os.getenv("DATABASE_URL") or get_database_url() or "postgresql://postgres:postgres@localhost:5432/kadocom"
        self.connection = None
        self.cursor = None
    
    @contextmanager
    def get_connection(self):
        """自動クリーンアップ機能付きでデータベース接続を取得する"""
        conn = None
        try:
            conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
            yield conn
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    async def connect(self):
        """データベースに接続"""
        try:
            self.connection = psycopg2.connect(self.connection_string)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            logger.info("✅ データベース接続成功")
            return self
        except Exception as e:
            logger.error(f"❌ データベース接続エラー: {str(e)}")
            raise
    
    async def disconnect(self):
        """データベース接続を閉じる"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("✅ データベース接続を閉じました")
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """SELECTクエリを実行して結果を返す"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """SELECTクエリを実行して全結果を返す"""
        return self.execute_query(query, params)
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """SELECTクエリを実行して最初の結果を返す"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return dict(result) if result else None
    
    def execute_command(self, command: str, params: tuple = None) -> int:
        """INSERT/UPDATE/DELETEコマンドを実行して影響を受けた行数を返す"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(command, params)
                conn.commit()
                return cursor.rowcount
    
    # ユーザー関連のメソッド
    async def get_user_by_email(self, email):
        """メールアドレスでユーザーを検索"""
        try:
            return self.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        except Exception as e:
            logger.error(f"❌ ユーザー検索エラー: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id):
        """IDでユーザーを検索"""
        try:
            return self.fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
        except Exception as e:
            logger.error(f"❌ ユーザー検索エラー: {str(e)}")
            return None
    
    async def create_user(self, name, email, password, email_verified=False, can_see_contents=False):
        """新規ユーザーを作成"""
        try:
            # パスワードのハッシュ化
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            query = """
            INSERT INTO users 
            (name, email, password_hash, email_verified, can_see_contents, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            now = datetime.now()
            result = self.fetch_one(query, (
                name, 
                email, 
                password_hash,
                email_verified,
                can_see_contents,
                now,
                now
            ))
            
            return result["id"] if result else None
        except Exception as e:
            logger.error(f"❌ ユーザー作成エラー: {str(e)}")
            return None
    
    async def update_user_verification(self, user_id, email_verified=True):
        """ユーザーのメール確認状態を更新"""
        try:
            rows = self.execute_command(
                """
                UPDATE users 
                SET email_verified = %s, updated_at = %s
                WHERE id = %s
                """, 
                (email_verified, datetime.now(), user_id)
            )
            return rows > 0
        except Exception as e:
            logger.error(f"❌ ユーザー更新エラー: {str(e)}")
            return False
    
    async def update_user_reset_token(self, email, token, expires_at):
        """パスワードリセットトークンを設定"""
        try:
            rows = self.execute_command(
                """
                UPDATE users 
                SET reset_password_token = %s, 
                    reset_password_token_expires_at = %s,
                    updated_at = %s
                WHERE email = %s
                """, 
                (token, expires_at, datetime.now(), email)
            )
            return rows > 0
        except Exception as e:
            logger.error(f"❌ トークン更新エラー: {str(e)}")
            return False
    
    async def update_user_password(self, user_id, password):
        """ユーザーのパスワードを更新"""
        try:
            # パスワードをハッシュ化
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            rows = self.execute_command(
                """
                UPDATE users 
                SET password_hash = %s,
                    reset_password_token = NULL,
                    reset_password_token_expires_at = NULL,
                    updated_at = %s
                WHERE id = %s
                """, 
                (password_hash, datetime.now(), user_id)
            )
            return rows > 0
        except Exception as e:
            logger.error(f"❌ パスワード更新エラー: {str(e)}")
            return False
    
    async def update_content_access(self, user_id, can_access):
        """コンテンツアクセス権限を更新"""
        try:
            rows = self.execute_command(
                """
                UPDATE users 
                SET can_see_contents = %s, updated_at = %s
                WHERE id = %s
                """, 
                (can_access, datetime.now(), user_id)
            )
            return rows > 0
        except Exception as e:
            logger.error(f"❌ アクセス権限更新エラー: {str(e)}")
            return False
    
    # 店舗関連のメソッド
    def get_businesses(self):
        """すべてのアクティブな店舗を取得する"""
        try:
            query = """
            SELECT business_id, name, area, prefecture, type, capacity, 
                   open_hour, close_hour, schedule_url, in_scope,
                   working_type, cast_type, shift_type, media,
                   blurred_name, updated_at
            FROM business 
            WHERE in_scope = true
            ORDER BY name
            """
            results = self.execute_query(query)
            
            # 結果を辞書形式に変換してAPIで期待される形式に合わせる
            businesses = {}
            for i, row in enumerate(results):
                businesses[i] = {
                    "Business ID": row["business_id"],
                    "name": row["name"],
                    "blurred_name": row.get("blurred_name") or row["name"],
                    "area": row["area"], 
                    "prefecture": row["prefecture"],
                    "type": row["type"],
                    "capacity": row.get("capacity"),
                    "open_hour": row.get("open_hour"),
                    "close_hour": row.get("close_hour"), 
                    "URL": row.get("schedule_url"),
                    "in_scope": row["in_scope"],
                    "working_type": row.get("working_type"),
                    "cast_type": row.get("cast_type"),
                    "shift_type": row.get("shift_type"),
                    "media": row.get("media"),
                    "last_updated": row.get("updated_at", datetime.now().strftime("%Y-%m-%d"))
                }
            
            logger.info(f"✅ データベースから{len(businesses)}件の店舗を取得しました")
            return businesses
            
        except Exception as e:
            logger.error(f"❌ 店舗データ取得エラー: {e}")
            logger.info("🔄 ダミーデータにフォールバックします")
            # データベース接続が利用できない場合はダミーデータを返す
            return {
                0: {"Business ID": 1, "name": "チュチュバナナ", "blurred_name": "チ○○バ○○", "prefecture": "東京都", "area": "関東", "type": "ソープランド", "in_scope": True, "last_updated": "2025-09-07"},
                1: {"Business ID": 2, "name": "クラブA", "blurred_name": "ク○○A", "prefecture": "大阪府", "area": "関西", "type": "キャバクラ", "in_scope": True, "last_updated": "2025-09-07"},
                2: {"Business ID": 3, "name": "レモネード", "blurred_name": "レ○○○ド", "prefecture": "名古屋市", "area": "中部", "type": "ピンサロ", "in_scope": True, "last_updated": "2025-09-07"}
            }
    

    def get_store_ranking(self, area="all", business_type="all", spec="all", period="week", limit=20, offset=0):
        """店舗のランキングを取得する"""
        try:
            # WHERE条件を構築
            where_conditions = ["b.in_scope = true"]
            params = []
            
            if area != "all":
                where_conditions.append("b.area = %s")
                params.append(area)
            
            if business_type != "all":
                where_conditions.append("b.type = %s")
                params.append(business_type)
            
            if spec != "all":
                where_conditions.append("b.cast_type = %s")
                params.append(spec)
            
            where_clause = " AND ".join(where_conditions)
            
            # 期間に応じた稼働率計算
            if period == "month":
                period_condition = "sh.biz_date >= DATE_TRUNC('month', CURRENT_DATE) AND sh.biz_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'"
            elif period == "last_month":
                period_condition = "sh.biz_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month' AND sh.biz_date < DATE_TRUNC('month', CURRENT_DATE)"
            elif period == "week":
                period_condition = "sh.biz_date >= CURRENT_DATE - INTERVAL '7 days'"
            else:
                period_condition = "sh.biz_date >= CURRENT_DATE - INTERVAL '1 day'"
            
            query = f"""
            SELECT 
                b.business_id,
                b.name,
                b.blurred_name,
                b.area,
                b.prefecture,
                b.type,
                b.cast_type,
                COALESCE(AVG(sh.working_rate), 0) as avg_working_rate
            FROM business b
            LEFT JOIN status_history sh ON b.business_id = sh.business_id AND {period_condition}
            WHERE {where_clause}
            GROUP BY b.business_id, b.name, b.blurred_name, b.area, b.prefecture, b.type, b.cast_type
            ORDER BY avg_working_rate DESC
            LIMIT %s OFFSET %s
            """
            
            params.extend([limit, offset])
            results = self.execute_query(query, tuple(params))
            
            # 結果をリスト形式に変換
            ranking = []
            for row in results:
                ranking.append({
                    "business_id": row["business_id"],
                    "name": row["name"],
                    "blurred_name": row.get("blurred_name", row["name"]),
                    "area": row["area"],
                    "prefecture": row["prefecture"],
                    "type": row["type"],
                    "cast_type": row.get("cast_type", "スタンダード"),
                    "avg_working_rate": round(float(row["avg_working_rate"]), 1)
                })
            
            logger.info(f"✅ ランキングデータを{len(ranking)}件取得しました")
            return ranking
            
        except Exception as e:
            logger.error(f"❌ ランキングデータ取得エラー: {e}")
            return []
    
    async def get_store_details(self, business_id):
        """店舗の詳細を取得する"""
        try:
            # 店舗の基本情報を取得
            query = """
            SELECT business_id, name, area, prefecture, type, capacity,
                   open_hour, close_hour, schedule_url, in_scope,
                   working_type, cast_type, shift_type, media,
                   blurred_name, updated_at
            FROM business 
            WHERE business_id = %s AND in_scope = true
            """
            
            result = self.execute_query(query, (business_id,))
            if not result:
                return None
            
            store = result[0]
            today = datetime.now()
            
            # 今月の平均稼働率データを取得（一覧画面と同じロジック）
            current_rate_query = """
            SELECT COALESCE(AVG(working_rate), 0) as avg_working_rate
            FROM status_history 
            WHERE business_id = %s 
            AND biz_date >= DATE_TRUNC('month', CURRENT_DATE) 
            AND biz_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            """
            current_rate_result = self.execute_query(current_rate_query, (business_id,))
            current_rate = float(current_rate_result[0]["avg_working_rate"]) if current_rate_result else 0.0
            
            # エリア平均稼働率を取得
            area_avg_query = """
            SELECT AVG(sh.working_rate) as avg_rate
            FROM status_history sh
            JOIN business b ON sh.business_id = b.business_id
            WHERE b.area = %s AND sh.biz_date >= CURRENT_DATE - INTERVAL '7 days'
            """
            area_avg_result = self.execute_query(area_avg_query, (store["area"],))
            area_avg = float(area_avg_result[0]["avg_rate"]) if area_avg_result and area_avg_result[0]["avg_rate"] else 0.0
            
            # 業種平均稼働率を取得
            genre_avg_query = """
            SELECT AVG(sh.working_rate) as avg_rate
            FROM status_history sh
            JOIN business b ON sh.business_id = b.business_id
            WHERE b.type = %s AND sh.biz_date >= CURRENT_DATE - INTERVAL '7 days'
            """
            genre_avg_result = self.execute_query(genre_avg_query, (store["type"],))
            genre_avg = float(genre_avg_result[0]["avg_rate"]) if genre_avg_result and genre_avg_result[0]["avg_rate"] else 0.0
            
            # 過去7日間の履歴データを取得
            history_query = """
            SELECT biz_date, working_rate
            FROM status_history
            WHERE business_id = %s AND biz_date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY biz_date ASC
            """
            history_result = self.execute_query(history_query, (business_id,))
            
            history = []
            weekdays = ["月", "火", "水", "木", "金", "土", "日"]
            for i in range(7):
                target_date = today - timedelta(days=6-i)
                # 該当日のデータを検索
                day_data = next((h for h in history_result if h["biz_date"] == target_date.date()), None)
                rate = float(day_data["working_rate"]) if day_data else 0.0
                
                history.append({
                    "label": weekdays[i],
                    "rate": round(rate, 1),
                    "date": target_date
                })
            
            # 詳細データを構築
            details = {
                "business_id": store["business_id"],
                "name": store["name"],
                "blurred_name": store.get("blurred_name", store["name"]),
                "area": store["area"],
                "prefecture": store["prefecture"],
                "type": store["type"],
                "cast_type": store.get("cast_type", "スタンダード"),
                "working_rate": round(current_rate, 1),
                "area_avg_rate": round(area_avg, 1),
                "genre_avg_rate": round(genre_avg, 1),
                "updated_at": store.get("updated_at", today).strftime("%Y年%m月%d日") if store.get("updated_at") else today.strftime("%Y年%m月%d日"),
                "history": history,
                "capacity": store.get("capacity"),
                "open_hour": str(store.get("open_hour", "")),
                "close_hour": str(store.get("close_hour", "")),
                "schedule_url": store.get("schedule_url"),
                "working_type": store.get("working_type"),
                "shift_type": store.get("shift_type"),
                "media": store.get("media")
            }
            
            logger.info(f"✅ 店舗詳細データを取得しました: {store['name']}")
            return details
            
        except Exception as e:
            logger.error(f"❌ 店舗詳細データ取得エラー (ID: {business_id}): {e}")
            logger.info("🔄 ダミーデータにフォールバックします")
            
            # エラー時はダミーデータを返す
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
                    "working_rate": 85.5,
                    "area_avg_rate": 78.2,
                    "genre_avg_rate": 82.5,
                    "updated_at": today.strftime("%Y年%m月%d日"),
                    "history": [
                        {"label": "月", "rate": 85.5, "date": today - timedelta(days=7)},
                        {"label": "火", "rate": 82.3, "date": today - timedelta(days=6)},
                        {"label": "水", "rate": 79.8, "date": today - timedelta(days=5)},
                        {"label": "木", "rate": 80.1, "date": today - timedelta(days=4)},
                        {"label": "金", "rate": 83.5, "date": today - timedelta(days=3)},
                        {"label": "土", "rate": 87.2, "date": today - timedelta(days=2)},
                        {"label": "日", "rate": 88.1, "date": today - timedelta(days=1)}
                    ]
                }
            }
            return dummy_data.get(business_id)

    async def get_connection_async(self):
        """Async用のデータベース接続を取得する"""
        try:
            conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
            return conn
        except Exception as e:
            logger.error(f"❌ データベース接続エラー: {str(e)}")
            raise

# API用のデータベースヘルパー関数
db_manager = None

async def get_database():
    """依存性注入用のデータベースマネージャーを取得する"""
    global db_manager
    if db_manager is None:
        try:
            db_manager = DatabaseManager()
            await db_manager.connect()
        except Exception as e:
            # エラーがあった場合はインスタンス化のみ（接続なし）
            logger.error(f"データベース接続エラー: {e}")
            db_manager = DatabaseManager()
    return db_manager

# usersテーブルの初期化
async def init_users_table():
    """usersテーブルを作成し、ダミーユーザーを追加する"""
    db = await get_database()
    try:
        # usersテーブルの作成
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            email_verified BOOLEAN DEFAULT FALSE,
            can_see_contents BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(255),
            verification_token_expires_at TIMESTAMP,
            reset_password_token VARCHAR(255),
            reset_password_token_expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        db.execute_command(create_users_table)
        logger.info("✅ usersテーブル作成完了")
        
        # ダミーユーザーの作成
        await create_dummy_users(db)
        
    except Exception as e:
        logger.error(f"❌ データベース初期化エラー: {str(e)}")
