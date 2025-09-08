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
                "can_see_contents": False
            },
            {
                "name": "管理者",
                "email": "admin@kadocom.com",
                "password": "admin123",
                "email_verified": True,
                "can_see_contents": True
            }
        ]
        
        for user_data in dummy_users:
            # すでに存在するかチェック
            existing = await check_user_exists(db, user_data["email"])
            if existing:
                print(f"ユーザー既に存在: {user_data['email']}")
                continue
            
            # パスワードハッシュ化
            password_hash = bcrypt.hashpw(user_data["password"].encode(), bcrypt.gensalt()).decode()
            
            # ユーザー作成
            await create_user(db, {
                "name": user_data["name"],
                "email": user_data["email"],
                "password_hash": password_hash,
                "email_verified": user_data["email_verified"],
                "can_see_contents": user_data.get("can_see_contents", False),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            
            print(f"ダミーユーザー作成: {user_data['email']}")
    except Exception as e:
        logger.error(f"ダミーユーザー作成エラー: {e}")
        print(f"ダミーユーザー作成中にエラーが発生しました: {e}")

async def create_users_table(db):
    """ユーザーテーブルを作成"""
    try:
        conn = await db.get_connection()
        async with conn.cursor() as cursor:
            # テーブルが存在するかチェック
            await cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
            """)
            table_exists = (await cursor.fetchone())[0]
            
            if not table_exists:
                # テーブル作成
                await cursor.execute("""
                    CREATE TABLE users (
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
                    )
                """)
                await conn.commit()
                print("✅ ユーザーテーブルを作成しました")
    except Exception as e:
        logger.error(f"テーブル作成エラー: {e}")
        print(f"ユーザーテーブル作成中にエラーが発生しました: {e}")
        print(f"ユーザーテーブル作成中にエラーが発生しました: {e}")

async def check_user_exists(db, email):
    """ユーザーが存在するか確認"""
    try:
        conn = await db.get_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
            count = (await cursor.fetchone())[0]
            return count > 0
    except Exception as e:
        logger.error(f"ユーザー確認エラー: {e}")
        return False

async def create_user(db, user_data):
    """ユーザーを作成"""
    try:
        conn = await db.get_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO users (name, email, password_hash, email_verified, can_see_contents, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_data["name"],
                user_data["email"],
                user_data["password_hash"],
                user_data["email_verified"],
                user_data["can_see_contents"],
                user_data["created_at"],
                user_data["updated_at"]
            ))
            await conn.commit()
    except Exception as e:
        logger.error(f"ユーザー作成エラー: {e}")

# 直接実行された場合
if __name__ == "__main__":
    asyncio.run(create_dummy_users())
