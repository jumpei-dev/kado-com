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
from typing import List, Optional
from pydantic import BaseModel

# プロジェクトルートへのパス設定
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from app.core.database import DatabaseManager
from app.core.auth_service import auth_service

router = APIRouter(tags=["admin"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

# ユーザー一括更新のモデル
class UserUpdateItem(BaseModel):
    id: str
    can_see_contents: bool
    is_admin: bool
    is_active: bool

class UserBulkUpdateRequest(BaseModel):
    users: List[UserUpdateItem]

def generate_password(length=4):
    """4桁の数字のみのパスワードを生成"""
    # 数字のみの4桁パスワード
    return ''.join(secrets.choice(string.digits) for i in range(length))

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
async def user_list_page(
    request: Request, 
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 15,
    admin = Depends(admin_required)
):
    """管理者用: ユーザー一覧ページ"""
    db = DatabaseManager()
    
    # ユーザー一覧取得
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # 検索条件の構築
                search_condition = ""
                params = []
                
                if search:
                    search_condition = "WHERE name LIKE %s"
                    search_term = f"%{search}%"
                    params = [search_term]
                
                # 総件数を取得
                count_sql = f"SELECT COUNT(*) as total FROM users {search_condition}"
                cursor.execute(count_sql, params)
                total_count = cursor.fetchone()["total"]
                
                # ページネーションの計算
                offset = (page - 1) * page_size
                
                # ユーザー一覧を取得
                sql = f"""
                    SELECT id, name, can_see_contents, is_active, is_admin, created_at
                    FROM users
                    {search_condition}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                # パラメータにページネーション情報を追加
                params.extend([page_size, offset])
                cursor.execute(sql, params)
                users = cursor.fetchall()
                
                # ページネーション情報
                pagination = {
                    "total": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size
                }
    except Exception as e:
        print(f"ユーザー一覧取得エラー: {e}")
        users = []
        pagination = {"total": 0, "page": 1, "page_size": page_size, "total_pages": 1}
    
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request, 
            "users": users, 
            "admin": admin,
            "pagination": pagination,
            "search": search
        }
    )


# 新規ユーザー作成API
@router.post("/api/admin/users/create")
async def create_user(
    request: Request,
    name: str = Form(...),
    can_see_contents: bool = Form(False),
    is_admin: bool = Form(False),
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
                    (name, password_hash, can_see_contents, is_active, is_admin, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    name, 
                    password_hash, 
                    can_see_contents,
                    True,
                    is_admin,
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

# ユーザー管理者権限トグルAPI
@router.post("/api/admin/users/{user_id}/toggle-admin")
async def toggle_user_admin(
    request: Request,
    user_id: str,
    is_admin: bool = Form(...),
    admin = Depends(admin_required)
):
    """管理者用: ユーザーの管理者権限を切り替え"""
    db = DatabaseManager()
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET is_admin = %s, updated_at = %s
                    WHERE id = %s
                """, (is_admin, datetime.now(), user_id))
                conn.commit()
                
                if cursor.rowcount == 0:
                    return JSONResponse(
                        status_code=404,
                        content={"success": False, "message": "ユーザーが見つかりません"}
                    )
    except Exception as e:
        print(f"ユーザー管理者権限更新エラー: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"更新エラー: {str(e)}"}
        )
    
    return JSONResponse(
        content={
            "success": True,
            "message": f"ユーザーを{'管理者に' if is_admin else '一般ユーザーに'}設定しました"
        }
    )

# ユーザー一括更新API
@router.post("/api/admin/users/bulk-update")
async def bulk_update_users(
    request: Request, 
    update_data: UserBulkUpdateRequest,
    admin = Depends(admin_required)
):
    """管理者用: ユーザー情報を一括更新する"""
    db = DatabaseManager()
    
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                for user_item in update_data.users:
                    cursor.execute(
                        """
                        UPDATE users 
                        SET can_see_contents = %s, is_admin = %s, is_active = %s, updated_at = %s
                        WHERE id = %s
                        """,
                        (
                            user_item.can_see_contents, 
                            user_item.is_admin, 
                            user_item.is_active,
                            datetime.now(),
                            user_item.id
                        )
                    )
            conn.commit()
        
        return JSONResponse(
            content={
                "success": True, 
                "message": "ユーザー情報を一括更新しました"
            }
        )
    except Exception as e:
        print(f"ユーザー一括更新エラー: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"更新エラー: {str(e)}"}
        )

# パスワード再生成API
@router.post("/api/admin/users/{user_id}/reset-password")
async def reset_user_password(
    request: Request,
    user_id: str,
    admin = Depends(admin_required)
):
    """管理者用: ユーザーのパスワードをリセットする"""
    db = DatabaseManager()
    
    try:
        # ランダムなパスワードを生成
        password = generate_password()
        password_hash = hash_password(password)
        
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # ユーザー存在確認
                cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    return JSONResponse(
                        status_code=404,
                        content={"success": False, "message": "ユーザーが見つかりません"}
                    )
                
                # パスワードハッシュを更新
                cursor.execute(
                    """
                    UPDATE users 
                    SET password_hash = %s, updated_at = %s
                    WHERE id = %s
                    """,
                    (password_hash, datetime.now(), user_id)
                )
                conn.commit()
        
        # 成功レスポンス（平文パスワードを含む - 一度だけ表示）
        return JSONResponse(
            content={
                "success": True, 
                "message": "パスワードを再設定しました", 
                "password": password,
                "user_name": user["name"]
            }
        )
    except Exception as e:
        print(f"パスワードリセットエラー: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"パスワード再設定エラー: {str(e)}"}
        )
