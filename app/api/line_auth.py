"""
LINE認証連携API
- LINE認証コールバック処理
- LINEプロフィール連携
"""

from fastapi import APIRouter, Request, Response, Form, Query, HTTPException, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import secrets
from pathlib import Path

# 認証サービスのインポート
from app.core.auth_service import auth_service

# テンプレート設定
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# ロガー設定
logger = logging.getLogger(__name__)

# ルーター定義
router = APIRouter(prefix="/api/auth/line", tags=["auth"])

@router.get("/login")
async def line_login(request: Request, response: Response) -> RedirectResponse:
    """LINE認証開始"""
    try:
        # ランダムなstate値を生成（CSRF対策）
        state = secrets.token_urlsafe(32)
        
        # 現在のユーザー情報を取得
        current_user = await auth_service.get_current_user(request)
        
        # stateをCookieに保存
        response = RedirectResponse(url=auth_service.generate_line_auth_url(state))
        response.set_cookie(
            key="line_auth_state",
            value=state,
            httponly=True,
            max_age=60 * 10,  # 10分間
            samesite="lax"
        )
        
        # 現在のユーザーIDも保存（ログイン済みの場合）
        if current_user:
            response.set_cookie(
                key="line_auth_user_id",
                value=str(current_user["id"]),
                httponly=True,
                max_age=60 * 10,  # 10分間
                samesite="lax"
            )
        
        logger.info("LINE認証開始")
        return response
        
    except Exception as e:
        logger.error(f"LINE認証開始エラー: {str(e)}")
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@router.get("/callback")
async def line_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
) -> HTMLResponse:
    """LINE認証コールバック処理"""
    try:
        # エラーの場合
        if error:
            logger.error(f"LINE認証エラー: {error}")
            return templates.TemplateResponse(
                "auth_message.html",
                {"request": request, "message": "LINE認証に失敗しました。", "error": True}
            )
            
        # stateの検証
        cookie_state = request.cookies.get("line_auth_state")
        if not state or not cookie_state or state != cookie_state:
            logger.error("LINE認証: 無効なstate")
            return templates.TemplateResponse(
                "auth_message.html",
                {"request": request, "message": "セキュリティ上の問題が発生しました。もう一度お試しください。", "error": True}
            )
            
        # コードを検証してLINEユーザー情報を取得
        line_user = await auth_service.verify_line_code(code)
        if not line_user:
            logger.error("LINE認証: プロフィール取得失敗")
            return templates.TemplateResponse(
                "auth_message.html",
                {"request": request, "message": "LINE情報の取得に失敗しました。", "error": True}
            )
            
        # 現在のユーザーIDを取得（ログイン済みの場合）
        user_id = request.cookies.get("line_auth_user_id")
        current_user = await auth_service.get_current_user(request)
        
        if current_user:
            # ログイン済みの場合、アカウント連携
            user_id = current_user["id"]
            success = await auth_service.link_line_account(
                user_id, 
                line_user["line_id"], 
                line_user["display_name"]
            )
            
            if success:
                # Cookieを削除するレスポンス
                response = templates.TemplateResponse(
                    "auth_message.html",
                    {
                        "request": request, 
                        "message": f"LINEアカウント「{line_user['display_name']}」との連携が完了しました。", 
                        "success": True
                    }
                )
                response.delete_cookie("line_auth_state")
                response.delete_cookie("line_auth_user_id")
                return response
            else:
                return templates.TemplateResponse(
                    "auth_message.html",
                    {"request": request, "message": "アカウント連携に失敗しました。", "error": True}
                )
        else:
            # 未ログインの場合、エラー表示
            return templates.TemplateResponse(
                "auth_message.html",
                {"request": request, "message": "LINE連携にはログインが必要です。先にログインしてください。", "error": True}
            )
            
    except Exception as e:
        logger.error(f"LINE認証コールバックエラー: {str(e)}")
        return templates.TemplateResponse(
            "auth_message.html",
            {"request": request, "message": "LINE認証処理中にエラーが発生しました。", "error": True}
        )

@router.get("/status")
async def line_connection_status(request: Request) -> JSONResponse:
    """LINEアカウント連携状況を取得"""
    try:
        current_user = await auth_service.get_current_user(request)
        
        if not current_user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"connected": False, "error": "未ログイン"}
            )
            
        line_connected = await auth_service.is_line_connected(current_user["id"])
        
        return JSONResponse(
            content={
                "connected": line_connected
            }
        )
        
    except Exception as e:
        logger.error(f"LINE連携状況取得エラー: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "LINE連携状況の取得中にエラーが発生しました。"}
        )
