"""
新しい認証API
- ログイン/ログアウト機能
- HTMXとの連携対応
- シンプルなユーザー管理
"""

from fastapi import APIRouter, Request, Response, Form, HTTPException, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os
from pathlib import Path
import logging

# 認証サービスのインポート
from app.core.auth_service import auth_service
from app.core.config import config_manager

# テンプレート設定
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# ロガー設定
logger = logging.getLogger(__name__)

# ルーター定義
router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
) -> HTMLResponse:
    """ログイン処理"""
    try:
        logger.info(f"ログイン試行: ユーザー {username}")
        
        # ユーザー認証
        user = await auth_service.authenticate_user(username, password)
        
        if not user:
            logger.warning(f"ログイン失敗: ユーザー {username} - 無効な認証情報")
            config_data = config_manager.config
            return templates.TemplateResponse(
                "components/auth_response.html",
                {"request": request, "error": "ユーザー名またはパスワードが正しくありません。", "config": config_data}
            )
        
        # アクセストークンの作成
        token_data = {"sub": str(user["id"])}
        access_token = auth_service.create_access_token(token_data)
        
        # トークンをCookieに設定
        config_data = config_manager.config
        response = templates.TemplateResponse(
            "components/auth_response.html",
            {
                "request": request,
                "success": "ログインしました。",
                "user_name": user["username"],
                "reload": True,
                "config": config_data
            }
        )
        
        # セキュアなCookie設定
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=60 * 60 * 24 * 7,  # 7日間
            samesite="lax",
            secure=os.getenv("ENVIRONMENT", "development") == "production"
        )
        
        logger.info(f"ログイン成功: ユーザー {username}")
        return response
        
    except Exception as e:
        logger.error(f"ログイン処理エラー: {str(e)}")
        config_data = config_manager.config
        return templates.TemplateResponse(
            "components/auth_response.html",
            {"request": request, "error": "ログイン処理中にエラーが発生しました。", "config": config_data}
        )

@router.get("/logout")
async def logout_get(request: Request, response: Response) -> RedirectResponse:
    """GETメソッドによるログアウト処理（ブラウザからの直接アクセス用）"""
    try:
        # トークンCookieを削除
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.delete_cookie(key="access_token")
        
        logger.info("ログアウト成功 (GETメソッド)")
        return response
        
    except Exception as e:
        logger.error(f"ログアウト処理エラー (GET): {str(e)}")
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@router.post("/logout")
async def logout_post(request: Request) -> JSONResponse:
    """POSTメソッドによるログアウト処理（APIからのアクセス用）"""
    try:
        logger.info("ログアウトリクエスト受信 (POSTメソッド)")
        
        # JSONレスポンスを作成し、Cookieを削除
        response = JSONResponse(
            content={"success": True, "message": "ログアウトしました"},
            status_code=status.HTTP_200_OK
        )
        response.delete_cookie(key="access_token")
        
        logger.info("ログアウト成功 (POSTメソッド)")
        return response
        
    except Exception as e:
        logger.error(f"ログアウト処理エラー (POST): {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "detail": "ログアウト処理中にエラーが発生しました"}
        )

@router.get("/me", response_class=JSONResponse)
async def get_current_user_info(request: Request):
    """現在のログインユーザー情報を取得するAPI
    
    このエンドポイントは、現在ログインしているユーザーの情報を返します。
    クライアントサイドでユーザーの認証状態を確認するために使用されます。
    """
    try:
        logger.info("ユーザー情報リクエスト受信: /api/auth/me")
        
        # 現在のユーザーを取得
        current_user = await auth_service.get_current_user(request)
        
        # 認証されていない場合
        if not current_user:
            logger.warning("認証されていないユーザーからのリクエスト")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"authenticated": False, "detail": "認証されていないか、セッションが無効です"}
            )
        
        # ユーザー情報をクリーンアップ（パスワードハッシュなど機密情報を除外）
        user_info = {
            "authenticated": True,
            "user": {
                "id": current_user["id"],
                "username": current_user["username"],
                "is_admin": current_user.get("is_admin", False)
            }
        }
        
        logger.info(f"ユーザー情報を返却: ID={current_user['id']}, 名前={current_user['username']}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=user_info
        )
        
    except Exception as e:
        logger.error(f"ユーザー情報取得エラー: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"authenticated": False, "detail": "サーバー内部エラーが発生しました"}
        )

@router.get("/user")
async def get_user(request: Request) -> JSONResponse:
    """現在のユーザー情報を取得"""
    try:
        user = await auth_service.get_current_user(request)
        
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"authenticated": False}
            )
            
        return JSONResponse(
            content={
                "authenticated": True,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "is_admin": user["is_admin"]
                }
            }
        )
        
    except Exception as e:
        logger.error(f"ユーザー情報取得エラー: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "ユーザー情報の取得中にエラーが発生しました。"}
        )

@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    admin_key: Optional[str] = Form(None)
) -> HTMLResponse:
    """ユーザー登録（管理者キーが必要）"""
    try:
        # 管理者キーの検証 (実際の実装では環境変数や設定ファイルから取得)
        valid_admin_key = os.getenv("ADMIN_KEY", "admin123")
        is_admin = False
        
        # 一般ユーザー登録の場合は管理者キーが必要
        if not admin_key or admin_key != valid_admin_key:
            config_data = config_manager.config
            return templates.TemplateResponse(
                "components/auth_response.html",
                {"request": request, "error": "ユーザー登録には管理者キーが必要です。", "config": config_data}
            )
            
        # 管理者登録の場合
        if admin_key == os.getenv("SUPER_ADMIN_KEY", "super123"):
            is_admin = True
            
        # ユーザー作成
        new_user = await auth_service.create_user(username, password, is_admin)
        
        if not new_user:
            config_data = config_manager.config
            return templates.TemplateResponse(
                "components/auth_response.html",
                {"request": request, "error": "このユーザー名は既に使用されています。", "config": config_data}
            )
            
        logger.info(f"ユーザー登録成功: {username}, 管理者: {is_admin}")
        config_data = config_manager.config
        return templates.TemplateResponse(
            "components/auth_response.html",
            {
                "request": request,
                "success": "ユーザー登録が完了しました。登録したアカウントでログインしてください。",
                "config": config_data
            }
        )
        
    except Exception as e:
        logger.error(f"ユーザー登録エラー: {str(e)}")
        config_data = config_manager.config
        return templates.TemplateResponse(
            "components/auth_response.html",
            {"request": request, "error": "ユーザー登録中にエラーが発生しました。", "config": config_data}
        )


@router.get("/me")
async def get_current_user(request: Request) -> dict:
    """現在のユーザー情報を取得"""
    try:
        # auth_serviceを使用してユーザー情報を取得
        user_info = await auth_service.get_current_user(request)
        
        if not user_info:
            return {"logged_in": False, "can_see_contents": False}
        
        can_see_contents = user_info.get('can_see_contents', False)
        is_admin = user_info.get('is_admin', False)
        
        # 🔧 開発用: adminユーザーは強制的にcan_see_contents=Trueにする
        if is_admin:
            can_see_contents = True
        
        return {
            "logged_in": True,
            "can_see_contents": can_see_contents,
            "username": user_info['username'],
            "is_admin": is_admin
        }
        
    except Exception as e:
        logger.error(f"ユーザー情報取得エラー: {str(e)}")
        return {"logged_in": False, "can_see_contents": False}
