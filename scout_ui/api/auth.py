from fastapi import APIRouter, Request, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging
from typing import Optional

from scout_ui.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    logout_user,
    verify_token
)
from scout_ui.core.database import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: Optional[bool] = False

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    redirect_url: Optional[str] = None

class LogoutResponse(BaseModel):
    success: bool
    message: str
    redirect_url: str

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest
):
    """
    User login endpoint
    """
    try:
        logger.info(f"Login attempt for user: {login_data.username}")
        
        # Authenticate user
        user = await authenticate_user(login_data.username, login_data.password)
        
        if not user:
            logger.warning(f"Failed login attempt for user: {login_data.username}")
            return LoginResponse(
                success=False,
                message="ユーザー名またはパスワードが正しくありません"
            )
        
        # Create access token
        token_data = {
            "user_id": user["id"],
            "username": user["username"],
            "remember_me": login_data.remember_me
        }
        
        access_token = create_access_token(token_data, remember_me=login_data.remember_me)
        
        # Set session data
        request.session["access_token"] = access_token
        request.session["user_id"] = user["id"]
        request.session["username"] = user["username"]
        
        logger.info(f"Successful login for user: {login_data.username}")
        
        return LoginResponse(
            success=True,
            message="ログインに成功しました",
            user={
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email", ""),
                "role": user.get("role", "user")
            },
            redirect_url="/dashboard"
        )
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return LoginResponse(
            success=False,
            message="ログイン処理中にエラーが発生しました"
        )

@router.post("/login/form")
async def login_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False)
):
    """
    Form-based login endpoint for HTML forms
    """
    try:
        # 簡単な認証（テスト用）
        if username == "admin" and password == "admin":
            # セッションにユーザー情報を保存
            request.session["user_id"] = 1
            request.session["username"] = username
            request.session["session_token"] = "test_token_123"
            
            # テスト用のセッションを作成
            from scout_ui.core.auth import active_sessions
            from datetime import datetime, timedelta
            active_sessions["test_token_123"] = {
                "user_id": 1,
                "expires_at": datetime.now() + timedelta(hours=24)
            }
            
            logger.info(f"Test login successful for user: {username}")
            return RedirectResponse(url="/dashboard", status_code=302)
        else:
            return RedirectResponse(
                url="/login?error=ユーザー名またはパスワードが正しくありません",
                status_code=302
            )
            
    except Exception as e:
        logger.error(f"Form login error: {e}")
        return RedirectResponse(
            url="/login?error=ログイン処理中にエラーが発生しました",
            status_code=302
        )
@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request):
    """
    User logout endpoint
    """
    try:
        # Get current user info for logging
        username = request.session.get("username", "unknown")
        
        # Logout user (invalidate token if stored in database)
        access_token = request.session.get("access_token")
        if access_token:
            await logout_user(access_token)
        
        # Clear session
        request.session.clear()
        
        logger.info(f"User logged out: {username}")
        
        return LogoutResponse(
            success=True,
            message="ログアウトしました",
            redirect_url="/login"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return LogoutResponse(
            success=False,
            message="ログアウト処理中にエラーが発生しました",
            redirect_url="/login"
        )

@router.get("/logout")
async def logout_get(request: Request):
    """
    GET logout endpoint for direct URL access
    """
    result = await logout(request)
    return RedirectResponse(url=result.redirect_url, status_code=302)

@router.get("/me")
async def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Get current user information
    """
    try:
        current_user = get_current_user(request)
        if not current_user:
            raise HTTPException(status_code=401, detail="認証が必要です")
            
        return {
            "success": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": getattr(current_user, 'email', ''),
                "role": getattr(current_user, 'role', 'user'),
                "created_at": getattr(current_user, 'created_at', None),
                "last_login": getattr(current_user, 'last_login', None)
            }
        }
        
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(status_code=500, detail="ユーザー情報の取得に失敗しました")

@router.post("/verify")
async def verify_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Verify authentication token
    """
    try:
        if not credentials:
            return {"valid": False, "message": "認証トークンが提供されていません"}
        
        # Verify token
        payload = verify_token(credentials.credentials)
        
        if payload:
            return {
                "valid": True,
                "user_id": payload.get("user_id"),
                "username": payload.get("username")
            }
        else:
            return {"valid": False, "message": "無効な認証トークンです"}
            
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return {"valid": False, "message": "認証トークンの検証中にエラーが発生しました"}

@router.get("/status")
async def auth_status(request: Request):
    """
    Check authentication status
    """
    try:
        # Check if user is logged in via session
        user_id = request.session.get("user_id")
        username = request.session.get("username")
        access_token = request.session.get("access_token")
        
        if user_id and username and access_token:
            # Verify token is still valid
            payload = verify_token(access_token)
            if payload:
                return {
                    "authenticated": True,
                    "user": {
                        "id": user_id,
                        "username": username
                    }
                }
        
        return {"authenticated": False}
        
    except Exception as e:
        logger.error(f"Auth status check error: {e}")
        return {"authenticated": False, "error": str(e)}