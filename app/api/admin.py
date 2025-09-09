"""
管理者用ユーザー管理API
LINEでのユーザー登録リクエストを受けて管理者が手動でユーザーを作成する
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import bcrypt
from pathlib import Path
import secrets
import string
from datetime import datetime
import sys

# プロジェクトルートへのパス設定
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from app.core.database import DatabaseManager
from app.core.auth_service import auth_service

router = APIRouter(tags=["admin"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

def generate_password(length=10):
    """ランダムなパスワードを生成"""
    # 英数字をバランス良く含めるためのセット
    alphabet = string.ascii_letters + string.digits
    # 最低1つの数字を含めるための処理
    password = ''.join(secrets.choice(alphabet) for i in range(length-1))
    password += secrets.choice(string.digits)  # 最後に必ず数字を追加
    # シャッフルして順番をランダムに
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    return ''.join(password_list)

def hash_password(password):
    """パスワードをハッシュ化"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

async def admin_required(request: Request):
    """管理者権限を要求するミドルウェア"""
    user = await auth_service.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="認証が必要です")
    
    # 管理者権限チェック
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    
    return user

# ユーザー管理ページ
@router.get("/admin/users", response_class=HTMLResponse)
async def user_list_page(request: Request, admin = Depends(admin_required)):
    """管理者用: ユーザー一覧ページ"""
    db = DatabaseManager()
    
    # ユーザー一覧取得
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, can_see_contents, is_active, created_at
                    FROM users
                    ORDER BY created_at DESC
                """)
                users = cursor.fetchall()
    except Exception as e:
        print(f"ユーザー一覧取得エラー: {e}")
        users = []
    
    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "users": users, "admin": admin}
    )

# 新規ユーザー作成API
@router.post("/api/admin/users/create")
async def create_user(
    request: Request,
    name: str = Form(...),
    can_see_contents: bool = Form(False),
    admin = Depends(admin_required)
):
    """管理者用: 新規ユーザー作成"""
    db = DatabaseManager()
    
    # ユーザー名重複チェック
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE name = %s", (name,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    return JSONResponse(
                        status_code=400,
                        content={"success": False, "message": "このユーザー名は既に使用されています"}
                    )
    except Exception as e:
        print(f"ユーザー重複チェックエラー: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"データベースエラー: {str(e)}"}
        )
    
    # ランダムパスワード生成
    password = generate_password()
    password_hash = hash_password(password)
    
    # ユーザー作成
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users 
                    (name, password_hash, can_see_contents, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    name, 
                    password_hash, 
                    can_see_contents, 
                    True, 
                    datetime.now(), 
                    datetime.now()
                ))
                user_id = cursor.fetchone()["id"]
                conn.commit()
    except Exception as e:
        print(f"ユーザー作成エラー: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"ユーザー作成エラー: {str(e)}"}
        )
    
    return JSONResponse(
        content={
            "success": True,
            "user_id": str(user_id),
            "name": name,
            "password": password,  # 管理者に一度だけ表示
            "message": "ユーザーを作成しました"
        }
    )

# ユーザー無効化/有効化API
@router.post("/api/admin/users/{user_id}/toggle-status")
async def toggle_user_status(
    request: Request,
    user_id: str,
    is_active: bool = Form(...),
    admin = Depends(admin_required)
):
    """管理者用: ユーザーの有効/無効を切り替え"""
    db = DatabaseManager()
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET is_active = %s, updated_at = %s
                    WHERE id = %s
                """, (is_active, datetime.now(), user_id))
                conn.commit()
                
                if cursor.rowcount == 0:
                    return JSONResponse(
                        status_code=404,
                        content={"success": False, "message": "ユーザーが見つかりません"}
                    )
    except Exception as e:
        print(f"ユーザーステータス更新エラー: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"更新エラー: {str(e)}"}
        )
    
    return JSONResponse(
        content={
            "success": True,
            "message": f"ユーザーを{'有効' if is_active else '無効'}にしました"
        }
    )
