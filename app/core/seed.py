import bcrypt
import asyncio
from datetime import datetime
from app.core.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

async def create_dummy_users():
    """開発用のダミーユーザーを作成"""
    try:
        # データベースマネージャーの初期化
        db = DatabaseManager()
        
        # ユーザーテーブル作成 (存在しない場合)
        await create_users_table(db)
        
        # ダミーユーザーのリスト
        dummy_users = [
            {
                "name": "test_user",
                "password": "password123",
                "can_see_contents": True,
                "is_active": True,
                "is_admin": False
            },
            {
                "name": "dev_user",
                "password": "dev12345",
                "can_see_contents": False,
                "is_active": True,
                "is_admin": False
            },
            {
                "name": "admin_user",
                "password": "admin123",
                "can_see_contents": True,
                "is_active": True,
                "is_admin": True
            }
        ]
        
        for user_data in dummy_users:
            # すでに存在するかチェック
            existing = await check_user_exists(db, user_data["name"])
            if existing:
                print(f"ユーザー既に存在: {user_data['name']}")
                continue
            
            # パスワードハッシュ化
            password_hash = bcrypt.hashpw(user_data["password"].encode(), bcrypt.gensalt()).decode()
            
            # ユーザー作成
            await create_user(db, {
                "name": user_data["name"],
                "password_hash": password_hash,
                "can_see_contents": user_data.get("can_see_contents", False),
                "is_active": user_data.get("is_active", True),
                "is_admin": user_data.get("is_admin", False),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            
            print(f"ダミーユーザー作成: {user_data['name']}")
    except Exception as e:
        logger.error(f"ダミーユーザー作成エラー: {e}")
        print(f"ダミーユーザー作成中にエラーが発生しました: {e}")

async def create_users_table(db):
    """ユーザーテーブルを作成"""
    try:
        conn = await db.get_connection_async()
        with conn.cursor() as cursor:
            # テーブルが存在するかチェック
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            """)
            table_exists = cursor.fetchone()['exists']
            
            if not table_exists:
                # テーブル作成
                cursor.execute("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        can_see_contents BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_admin BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print("✅ ユーザーテーブルを作成しました")
    except Exception as e:
        logger.error(f"テーブル作成エラー: {e}")
        print(f"ユーザーテーブル作成中にエラーが発生しました: {e}")
        print(f"ユーザーテーブル作成中にエラーが発生しました: {e}")

async def check_user_exists(db, username):
    """ユーザーが存在するか確認"""
    try:
        conn = await db.get_connection_async()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE name = %s", (username,))
            count = cursor.fetchone()['count']
            return count > 0
    except Exception as e:
        logger.error(f"ユーザー確認エラー: {e}")
        return False

async def create_user(db, user_data):
    """ユーザーを作成"""
    try:
        conn = await db.get_connection_async()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (name, password_hash, can_see_contents, is_active, is_admin, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_data["name"],
                user_data["password_hash"],
                user_data["can_see_contents"],
                user_data["is_active"],
                user_data["is_admin"],
                user_data["created_at"],
                user_data["updated_at"]
            ))
            conn.commit()
    except Exception as e:
        logger.error(f"ユーザー作成エラー: {e}")

# 直接実行された場合
if __name__ == "__main__":
    asyncio.run(create_dummy_users())
