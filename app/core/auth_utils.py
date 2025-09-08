"""
認証関連の設定と関数
"""

import os
from datetime import datetime, timedelta
import jwt
from fastapi import Request, Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer
from app.core.database import get_database

# JWT設定
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "kado-com-very-secret-key-for-development")  # 本番環境では環境変数から
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_DAYS = 7

# 認証関係の関数
def create_jwt_token(data: dict, expires_delta: timedelta = None):
    """JWT認証トークンを生成"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=JWT_ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt

async def verify_token(token: str):
    """JWTトークンを検証"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

async def get_current_user(token: str = Cookie(None), db = Depends(get_database)):
    """現在のユーザーを取得（Cookieからトークンを取得）"""
    if not token:
        return None
        
    payload = await verify_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = await db.get_user_by_id(user_id)
    if not user:
        return None
        
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "email_verified": user["email_verified"],
        "can_see_contents": user["can_see_contents"]
    }

# 認証が必要なエンドポイント用の依存性
def require_auth(current_user = Depends(get_current_user)):
    """認証を要求（認証されていなければ401エラー）"""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="認証が必要です")
    
    return current_user

# メール確認が必要なエンドポイント用の依存性
def require_verified_email(current_user = Depends(get_current_user)):
    """メール確認済みを要求（確認されていなければ403エラー）"""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="認証が必要です")
    
    if not current_user.get("email_verified"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="メールアドレスの確認が必要です")
    
    return current_user

# コンテンツアクセス権限が必要なエンドポイント用の依存性
def require_content_access(current_user = Depends(get_current_user)):
    """コンテンツアクセス権限を要求（権限がなければ403エラー）"""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="認証が必要です")
    
    if not current_user.get("email_verified"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="メールアドレスの確認が必要です")
    
    if not current_user.get("can_see_contents"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="このコンテンツへのアクセス権限がありません")
    
    return current_user
