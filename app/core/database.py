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
                    "blurred_name": row.get("blurred_name", self._generate_blurred_name(row["name"])),
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
    
    def _generate_blurred_name(self, name):
        """店舗名からぼかし名を生成する"""
        if not name or len(name) < 2:
            return name
        
        # 簡単なぼかし処理：2文字目以降を○に置換
        return name[0] + "○" * (len(name) - 1)
        
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
            
            # 期間に応じた稼働率計算（簡易版）
            period_days = 7 if period == "week" else 30 if period == "month" else 1
            
            query = f"""
            SELECT 
                b.business_id,
                b.name,
                b.blurred_name,
                b.area,
                b.prefecture,
                b.type,
                b.cast_type,
                COALESCE(AVG(CASE WHEN RANDOM() > 0.3 THEN 75 + RANDOM() * 20 ELSE 50 + RANDOM() * 25 END), 0) as avg_working_rate
            FROM business b
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
                    "blurred_name": row.get("blurred_name", self._generate_blurred_name(row["name"])),
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
            logger.info("🔄 ダミーデータにフォールバックします")
            # エラー時はダミーデータを返す
            return [
                {"business_id": 1, "name": "チュチュバナナ", "blurred_name": "チ○○バ○○", "area": "関東", "prefecture": "東京都", "type": "ソープランド", "cast_type": "スタンダード", "avg_working_rate": 85.5},
                {"business_id": 2, "name": "クラブA", "blurred_name": "ク○○A", "area": "関西", "prefecture": "大阪府", "type": "キャバクラ", "cast_type": "低スペ", "avg_working_rate": 78.2},
                {"business_id": 3, "name": "レモネード", "blurred_name": "レ○○○ド", "area": "中部", "prefecture": "名古屋市", "type": "ピンサロ", "cast_type": "スタンダード", "avg_working_rate": 72.8}
            ]
    
    def get_store_details(self, business_id):
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
            
            # 稼働率データ（簡易版 - 実際の実装では稼働データテーブルから取得）
            current_rate = 70 + (hash(str(business_id)) % 30)  # 70-99の範囲でランダム
            area_avg = current_rate - 5 + (hash(str(store["area"])) % 10)
            genre_avg = current_rate - 3 + (hash(str(store["type"])) % 6)
            
            # 履歴データ（簡易版）
            history = []
            weekdays = ["月", "火", "水", "木", "金", "土", "日"]
            for i, day in enumerate(weekdays):
                rate = current_rate + (hash(str(business_id) + day) % 20) - 10
                rate = max(50, min(95, rate))  # 50-95の範囲に制限
                history.append({
                    "label": day,
                    "rate": round(rate, 1),
                    "date": today - timedelta(days=7-i)
                })
            
            # 詳細データを構築
            details = {
                "business_id": store["business_id"],
                "name": store["name"],
                "blurred_name": store.get("blurred_name", self._generate_blurred_name(store["name"])),
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

async def create_dummy_users(db):
    """ダミーユーザーを作成"""
    dummy_users = [
        {
            "name": "テスト 太郎",
            "email": "test@example.com",
            "password": "password123",
            "email_verified": True,
            "can_see_contents": True
        },
        {
            "name": "開発 花子",
            "email": "dev@example.com",
            "password": "dev12345",
            "email_verified": True,
            "can_see_contents": True
        },
        {
            "name": "管理者",
            "email": "admin@kadocom.com",
            "password": "admin123",
            "email_verified": True,
            "can_see_contents": True
        },
        {
            "name": "一般ユーザー",
            "email": "user@example.com",
            "password": "user123",
            "email_verified": True,
            "can_see_contents": False
        }
    ]
    
    for user in dummy_users:
        # すでに存在するか確認
        existing_user = await db.get_user_by_email(user["email"])
        if existing_user:
            logger.info(f"ユーザー {user['email']} は既に存在します")
            continue
        
        # ユーザー作成
        user_id = await db.create_user(
            user["name"],
            user["email"],
            user["password"],
            user["email_verified"],
            user["can_see_contents"]
        )
        
        if user_id:
            logger.info(f"✅ ダミーユーザー作成: {user['email']}")
        else:
            logger.error(f"❌ ダミーユーザー作成失敗: {user['email']}")
