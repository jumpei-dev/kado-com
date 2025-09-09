"""
シンプル認証API
- メール認証不要
- LINEでの手動登録を前提
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form, Cookie, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
import sys
from pathlib import Path

# プロジェクトルートへのパス設定
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 認証設定
from app.core.config import config_manager
from app.core.database import DatabaseManager

# 設定読み込み
auth_config = config_manager.get_auth_config()
JWT_SECRET_KEY = auth_config.get("secret_key", "fallback-secret-key")
JWT_ALGORITHM = auth_config.get("algorithm", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_DAYS = auth_config.get("access_token_expire_days", 7)

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

# ユーティリティ関数
def verify_password(plain_password, hashed_password):
    """パスワード検証"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict):
    """JWTトークン生成"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token):
    """トークンのデコード"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except:
        return None

def get_user_by_username(username: str) -> Dict[str, Any]:
    """ユーザー名でユーザーを検索"""
    db = DatabaseManager()
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE name = %s",
                    (username,)
                )
                return cursor.fetchone()
    except Exception as e:
        print(f"ユーザー検索エラー: {e}")
        return None

# API エンドポイント
@router.post("/api/auth/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """ユーザーログイン - ユーザー名とパスワードでログイン"""
    # ユーザー検索
    user = get_user_by_username(username)
    
    # ユーザーが存在しない場合
    if not user:
        return templates.TemplateResponse(
            "components/auth_response.html",
            {"request": request, "error": "ユーザー名またはパスワードが正しくありません"}
        )
    
    # パスワード検証
    password_hash = user["password_hash"]
    if not verify_password(password, password_hash):
        return templates.TemplateResponse(
            "components/auth_response.html",
            {"request": request, "error": "ユーザー名またはパスワードが正しくありません"}
        )
    
    # アクティブユーザーかチェック
    if not user.get("is_active", True):
        return templates.TemplateResponse(
            "components/auth_response.html",
            {"request": request, "error": "このアカウントは現在無効化されています。管理者にお問い合わせください。"}
        )
    
    # JWTトークン生成
    token = create_access_token({
        "sub": str(user["id"]),
        "name": user["name"],
        "can_see_contents": user.get("can_see_contents", False)
    })
    
    # レスポンス
    response = templates.TemplateResponse(
        "components/auth_response.html",
        {
            "request": request,
            "success": "ログインしました！",
            "user_name": user["name"],
            "reload": True
        }
    )
    
    # クッキーにトークンをセット
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        max_age=60*60*24*JWT_ACCESS_TOKEN_EXPIRE_DAYS,
        secure=False,  # 本番環境ではTrueに
        samesite="lax"
    )
    
    return response

@router.get("/logout")
async def logout_get():
    """ログアウト処理 (GET)"""
    response = JSONResponse({"success": True, "message": "ログアウトしました"})
    response.delete_cookie(key="token")
    return response

@router.post("/api/auth/logout")
async def logout_post():
    """ログアウト処理 (POST)"""
    response = JSONResponse({"success": True, "message": "ログアウトしました"})
    response.delete_cookie(key="token")
    return response

@router.get("/api/auth/me")
async def get_current_user(
    request: Request,
    token: Optional[str] = Cookie(None)
):
    """現在のユーザー情報を取得"""
    # トークンが存在しない場合
    if not token:
        return {"authenticated": False}
    
    # トークンの検証
    payload = decode_token(token)
    if not payload:
        return {"authenticated": False}
    
    # ユーザーID取得
    user_id = payload.get("sub")
    if not user_id:
        return {"authenticated": False}
    
    # データベースからユーザー情報を取得
    db = DatabaseManager()
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, can_see_contents, created_at, is_active
                    FROM users
                    WHERE id = %s AND is_active = TRUE
                    """,
                    (user_id,)
                )
                user = cursor.fetchone()
                
                if not user:
                    return {"authenticated": False}
                
                # レスポンスデータ整形
                return {
                    "authenticated": True,
                    "user": {
                        "id": str(user["id"]),
                        "name": user["name"],
                        "can_see_contents": user["can_see_contents"],
                        "created_at": user["created_at"].isoformat() if user["created_at"] else None
                    }
                }
    except Exception as e:
        print(f"ユーザー情報取得エラー: {e}")
        return {"authenticated": False}
