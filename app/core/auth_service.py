"""
新しい認証サービス
- シンプルなユーザー名/パスワード認証
- JWT認証トークン管理
- 管理者アカウント対応
"""

import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
import os
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from app.core.database import DatabaseManager

# ロガー設定
logger = logging.getLogger(__name__)

class AuthService:
    """認証サービスクラス"""
    
    def __init__(self):
        """初期化"""
        self.secret_key = os.getenv("JWT_SECRET_KEY", "kado-com-very-secret-key-for-development")
        self.algorithm = "HS256"
        self.token_expire_days = 7
        self.db = DatabaseManager()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """パスワード検証"""
        try:
            # パスワードを検証 (encrypted_passwordを使用)
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        except Exception as e:
            logger.error(f"パスワード検証エラー: {e}")
            return False

    def hash_password(self, password: str) -> str:
        """パスワードのハッシュ化"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """アクセストークンの作成"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.token_expire_days)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Dict[str, Any]:
        """トークンのデコード"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """ユーザー認証"""
        try:
            logger.info(f"ユーザー認証処理: {username}")
            
            # データベースからユーザーを取得
            query = """
            SELECT id, name, password_hash, is_admin 
            FROM users 
            WHERE name = %s
            """
            # 非同期関数ではないのでawaitを使わない
            user = self.db.fetch_one(query, (username,))
            
            if not user:
                logger.warning(f"ユーザーが存在しません: {username}")
                return None
                
            logger.info(f"ユーザー情報取得: ID={user['id']}, 名前={user['name']}")
            
            # パスワード検証
            hashed_password = user['password_hash']
            logger.info(f"パスワードハッシュ確認: {type(hashed_password)} - {hashed_password[:10]}...")
            
            if not self.verify_password(password, hashed_password):
                logger.warning(f"パスワード検証失敗: {username}")
                return None
                
            # 認証成功: ユーザー情報を返す
            logger.info(f"認証成功: {username}")
            return {
                "id": user['id'],
                "username": user['name'],
                "is_admin": user['is_admin']
            }
            
        except Exception as e:
            print(f"認証エラー: {str(e)}")
            return None

    async def get_current_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """現在のユーザーを取得"""
        try:
            # Cookieからトークンを取得
            token = request.cookies.get("access_token")
            if not token:
                return None
                
            # トークンをデコード
            payload = self.decode_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                return None
                
            # データベースからユーザー情報を取得
            query = """
            SELECT id, name, is_admin 
            FROM users 
            WHERE id = %s
            """
            user = self.db.fetch_one(query, (user_id,))
            
            if not user:
                return None
                
            return {
                "id": user['id'],
                "username": user['name'],
                "is_admin": user['is_admin']
            }
            
        except Exception as e:
            print(f"ユーザー取得エラー: {str(e)}")
            return None

    async def create_user(self, username: str, password: str, is_admin: bool = False) -> Optional[Dict[str, Any]]:
        """新規ユーザー作成"""
        try:
            # 既存ユーザーのチェック
            check_query = "SELECT id FROM users WHERE name = %s"
            existing_user = self.db.fetch_one(check_query, (username,))
            
            if existing_user:
                return None  # ユーザー名が既に存在
                
            # パスワードをハッシュ化
            hashed_password = self.hash_password(password)
            
            # ユーザーを作成
            insert_query = """
            INSERT INTO users (name, password_hash, is_admin) 
            VALUES (%s, %s, %s) 
            RETURNING id, name, is_admin
            """
            new_user = self.db.fetch_one(
                insert_query, 
                (username, hashed_password, is_admin)
            )
            
            if not new_user:
                return None
                
            return {
                "id": new_user['id'],
                "username": new_user['name'],
                "is_admin": new_user['is_admin']
            }
            
        except Exception as e:
            print(f"ユーザー作成エラー: {str(e)}")
            return None

# 認証サービスのシングルトンインスタンス
auth_service = AuthService()
