from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from scout_ui.models.store import User
import hashlib
import secrets
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# セッション管理用の辞書（本番環境ではRedisなどを使用）
active_sessions = {}

def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    salt = os.getenv("PASSWORD_SALT", "default_salt")
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証"""
    return hash_password(plain_password) == hashed_password

def create_session(user_id: int) -> str:
    """セッションを作成"""
    session_token = secrets.token_urlsafe(32)
    expiry = datetime.now() + timedelta(hours=int(os.getenv("SESSION_TIMEOUT", "3600")) // 3600)
    
    active_sessions[session_token] = {
        "user_id": user_id,
        "expires_at": expiry
    }
    
    return session_token

def validate_session(session_token: str) -> dict:
    """セッションを検証"""
    if session_token not in active_sessions:
        return None
    
    session_data = active_sessions[session_token]
    
    # セッション期限チェック
    if datetime.now() > session_data["expires_at"]:
        del active_sessions[session_token]
        return None
    
    return session_data

def authenticate_user(db: Session, username: str, password: str) -> User:
    """ユーザー認証"""
    try:
        # 簡易認証（本番環境では適切なユーザーテーブルを使用）
        # 現在は環境変数から管理者ユーザーを取得
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        if username == admin_username and password == admin_password:
            # 仮のユーザーオブジェクトを作成
            class MockUser:
                def __init__(self):
                    self.id = 1
                    self.username = admin_username
                    self.is_active = True
            
            return MockUser()
        
        return None
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return None

def get_current_user(request: Request):
    """現在のユーザーを取得"""
    from scout_ui.core.database import get_db_session
    
    try:
        # セッションからユーザーIDを取得
        user_id = request.session.get("user_id")
        session_token = request.session.get("session_token")
        
        if not user_id or not session_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証が必要です",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # セッション検証
        session_data = validate_session(session_token)
        if not session_data or session_data["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="セッションが無効です",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 仮のユーザーオブジェクトを返す
        class MockUser:
            def __init__(self):
                self.id = user_id
                self.username = request.session.get("username", "admin")
                self.is_active = True
        
        return MockUser()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー情報の取得中にエラーが発生しました"
        )

def require_auth(request: Request):
    """認証が必要なエンドポイント用のデコレータ"""
    return get_current_user(request)

def cleanup_expired_sessions():
    """期限切れセッションをクリーンアップ"""
    current_time = datetime.now()
    expired_tokens = [
        token for token, data in active_sessions.items()
        if current_time > data["expires_at"]
    ]
    
    for token in expired_tokens:
        del active_sessions[token]
    
    logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")

def create_access_token(user_id: int) -> str:
    """アクセストークンを作成"""
    return create_session(user_id)

def logout_user(session_token: str) -> bool:
    """ユーザーをログアウト"""
    if session_token in active_sessions:
        del active_sessions[session_token]
        return True
    return False

def verify_token(token: str) -> dict:
    """トークンを検証"""
    return validate_session(token)

def get_current_user_optional(request: Request):
    """現在のユーザーを取得（オプショナル）- ログインしていなくてもエラーを出さない"""
    try:
        # セッションからユーザーIDを取得
        user_id = request.session.get("user_id")
        session_token = request.session.get("session_token")
        
        if not user_id or not session_token:
            return None
        
        # セッション検証
        session_data = validate_session(session_token)
        if not session_data or session_data["user_id"] != user_id:
            return None
        
        # 仮のユーザーオブジェクトを返す
        class MockUser:
            def __init__(self):
                self.id = user_id
                self.username = request.session.get("username", "admin")
                self.is_active = True
        
        return MockUser()
        
    except Exception as e:
        logger.error(f"Get current user optional error: {str(e)}")
        return None