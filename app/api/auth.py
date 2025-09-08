from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Cookie, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr
import sys
import bcrypt
import jwt
import secrets
import os
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

# 認証設定をインポート
from app.core.auth_config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_DAYS
from app.core.database import DatabaseManager

router = APIRouter(tags=["auth"])
security = HTTPBearer(auto_error=False)

# テンプレートの設定
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

# 入力モデル
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordReset(BaseModel):
    email: EmailStr

# データベースユーティリティ関数
def get_user_by_email(db, email):
    """メールアドレスでユーザーを検索"""
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                result = cursor.fetchone()
                return result
    except Exception as e:
        print(f"ユーザー検索エラー: {e}")
        return None

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

# API エンドポイント
@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db = DatabaseManager()
):
    """ユーザー登録"""
    
    # メールアドレスの重複チェック
    existing_user = get_user_by_email(db, email)
    if existing_user:
        return templates.TemplateResponse(
            "components/auth_response.html", 
            {"request": request, "error": "このメールアドレスは既に登録されています"}
        )
    
    # パスワードのハッシュ化
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # 確認トークンの生成
    verification_token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(days=1)
    
    # 環境設定の取得
    is_development = os.getenv("ENVIRONMENT", "development") == "development"
    
    # ユーザー作成
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (name, email, password_hash, email_verified, verification_token, 
                    verification_token_expires_at, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (
                    name,
                    email,
                    password_hash,
                    is_development, # 開発環境では自動認証
                    verification_token,
                    expires,
                    datetime.now(),
                    datetime.now()
                ))
                user_id = cursor.fetchone()[0]
                conn.commit()
        
        # 確認メールの送信
        verification_url = f"{request.base_url}api/auth/verify-email?token={verification_token}"
        
        # 開発環境ではコンソール出力、本番環境では実際にメール送信
        if not is_development:
            from app.core.email_service import send_verification_email_background
            send_verification_email_background(background_tasks, email, name, verification_url)
        else:
            print(f"\n=== 開発モード: メール確認 ===")
            print(f"ユーザー: {name} <{email}>")
            print(f"確認URL: {verification_url}")
            print(f"============================\n")
        
        # JWTトークン生成
        token = create_access_token({"sub": str(user_id), "name": name, "email": email})
        
        # レスポンス
        response = templates.TemplateResponse(
            "components/auth_response.html",
            {
                "request": request,
                "success": "アカウント登録が完了しました！",
                "user_name": name,
                "reload": True
            }
        )
        
        # クッキーにトークンをセット
        response.set_cookie(
            key="token",
            value=token,
            httponly=True,
            max_age=60*60*24*JWT_ACCESS_TOKEN_EXPIRE_DAYS,
            secure=False, # 開発環境ではFalse
            samesite="lax"
        )
        
        return response
    
    except Exception as e:
        print(f"ユーザー登録エラー: {e}")
        return templates.TemplateResponse(
            "components/auth_response.html",
            {"request": request, "error": "登録中にエラーが発生しました。もう一度お試しください。"}
        )

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """ユーザーログイン"""
    db = DatabaseManager()
    
    # ユーザー検索
    user = get_user_by_email(db, email)
    if not user:
        return templates.TemplateResponse(
            "components/auth_response.html",
            {"request": request, "error": "メールアドレスまたはパスワードが正しくありません"}
        )
    
    # パスワード検証
    password_hash = user["password_hash"]
    if not verify_password(password, password_hash):
        return templates.TemplateResponse(
            "components/auth_response.html",
            {"request": request, "error": "メールアドレスまたはパスワードが正しくありません"}
        )
    
    # JWTトークン生成
    token = create_access_token({
        "sub": str(user["id"]),
        "name": user["name"],
        "email": user["email"]
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
        secure=False, # 開発環境ではFalse
        samesite="lax"
    )
    
    return response

@router.get("/logout")
async def logout():
    """ログアウト処理"""
    response = JSONResponse({"success": True, "message": "ログアウトしました"})
    response.delete_cookie(key="token")
    return response

@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(
    request: Request,
    token: str
):
    """メールアドレス確認処理"""
    db = DatabaseManager()
    
    # トークンからユーザーを検索
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, email, verification_token_expires_at
                    FROM users
                    WHERE verification_token = %s
                """, (token,))
                user = cursor.fetchone()
    except Exception as e:
        print(f"ユーザー検索エラー: {e}")
        return templates.TemplateResponse(
            "auth_message.html", 
            {"request": request, "error": "検証中にエラーが発生しました。もう一度お試しください。"}
        )
    
    if not user:
        return templates.TemplateResponse(
            "auth_message.html", 
            {"request": request, "error": "無効なトークンです。登録手続きをやり直してください。"}
        )
    
    # トークンの有効期限チェック
    if datetime.now() > user["verification_token_expires_at"]:
        return templates.TemplateResponse(
            "auth_message.html", 
            {"request": request, "error": "トークンの有効期限が切れています。登録手続きをやり直してください。"}
        )
    
    # メールの確認処理
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users
                    SET email_verified = TRUE,
                        verification_token = NULL,
                        verification_token_expires_at = NULL,
                        updated_at = %s
                    WHERE id = %s
                """, (
                    datetime.now(),
                    user["id"]
                ))
                conn.commit()
        
        return templates.TemplateResponse(
            "auth_message.html", 
            {
                "request": request, 
                "success": "メールアドレスの確認が完了しました。ログインしてください。",
                "redirect_url": "/",
                "redirect_text": "ホームに戻る"
            }
        )
    except Exception as e:
        print(f"メール確認エラー: {e}")
        return templates.TemplateResponse(
            "auth_message.html", 
            {"request": request, "error": "メール確認中にエラーが発生しました。後ほど再試行してください。"}
        )

@router.get("/me")
async def get_current_user(
    token: Optional[str] = Cookie(None)
):
    """現在のユーザー情報取得"""
    if not token:
        return {"authenticated": False}
    
    try:
        # トークンのデコード
        payload = decode_token(token)
        if not payload:
            return {"authenticated": False}
        
        # ユーザー情報を返す
        return {
            "authenticated": True,
            "user": {
                "id": payload.get("sub"),
                "name": payload.get("name"),
                "email": payload.get("email")
            }
        }
    except Exception as e:
        print(f"認証エラー: {e}")
        return {"authenticated": False}

@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...)
):
    """パスワードリセット"""
    db = DatabaseManager()
    
    # ユーザー検索（セキュリティのため存在しなくても同じメッセージ）
    user = get_user_by_email(db, email)
    
    if user:
        # リセットトークンの生成
        reset_token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=1)
        
        # トークンをDBに保存
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE users
                        SET reset_password_token = %s,
                            reset_password_token_expires_at = %s,
                            updated_at = %s
                        WHERE id = %s
                    """, (
                        reset_token,
                        expires,
                        datetime.now(),
                        user["id"]
                    ))
                    conn.commit()
            
            # リセットURLの作成
            reset_url = f"{request.base_url}reset-password?token={reset_token}"
            
            # 環境設定の取得
            is_development = os.getenv("ENVIRONMENT", "development") == "development"
            
            # 開発環境ではコンソール出力、本番環境では実際にメール送信
            if not is_development:
                from app.core.email_service import send_password_reset_email_background
                send_password_reset_email_background(background_tasks, email, user["name"], reset_url)
            else:
                print(f"[開発用] パスワードリセットURL: {reset_url}")
                
        except Exception as e:
            print(f"パスワードリセットエラー: {e}")
    
    # ユーザーが存在しなくても同じ応答を返す
    return templates.TemplateResponse(
        "components/auth_response.html",
        {
            "request": request,
            "success": "パスワードリセット用のメールを送信しました"
        }
    )
