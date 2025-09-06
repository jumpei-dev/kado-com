from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# 必要最小限の入力モデルのみ
class MagicLinkRequest(BaseModel):
    email: EmailStr

# レスポンスは辞書で直接返す
DUMMY_USER = {
    "id": "dev-user-001",
    "email": "dev@example.com",
    "is_active": True
}

@router.post("/magic-link")
async def request_magic_link(request: MagicLinkRequest) -> Dict[str, Any]:
    """Magic Link送信 (開発版はダミー応答)"""
    return {
        "message": f"Magic linkを {request.email} に送信しました",
        "dev_info": "開発環境のため実際の送信は行われません"
    }

@router.post("/verify")
async def verify_magic_link(token: str) -> Dict[str, Any]:
    """Magic Link検証 (開発版は任意のトークンでOK)"""
    if not token:
        raise HTTPException(status_code=400, detail="トークンが必要です")
    
    # 開発版: 任意のトークンで認証成功
    return {
        "access_token": f"dev-token-{token}",
        "token_type": "bearer",
        "user": DUMMY_USER
    }

@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """現在のユーザー情報取得"""
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="認証が必要です")
    
    # 開発版: トークンがあれば認証済みとみなす
    return {
        "user": DUMMY_USER,
        "authenticated": True,
        "allowed": True
    }

@router.get("/status")
async def check_auth_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """認証状態確認"""
    try:
        token = credentials.credentials
        if token:
            return {
                "user": DUMMY_USER,
                "authenticated": True
            }
    except:
        pass
    
    return {
        "user": None,
        "authenticated": False
    }

@router.post("/logout")
async def logout() -> Dict[str, Any]:
    """ログアウト"""
    return {"message": "ログアウトしました"}
