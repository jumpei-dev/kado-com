from fastapi import Request
from app.core.auth_service import auth_service

async def check_user_permissions(request: Request) -> dict:
    """リクエストからユーザー権限を確認"""
    try:
        # auth_serviceを使用してユーザー情報を取得
        user_info = await auth_service.get_current_user(request)
        
        print(f"🔍 [DEBUG] check_user_permissions: user_info={'あり' if user_info else 'なし'}")
        
        if not user_info:
            print("🔍 [DEBUG] check_user_permissions: ユーザー情報なし - ログアウト状態")
            return {"logged_in": False, "can_see_contents": False}
        
        can_see_contents = user_info.get('can_see_contents', False)
        is_admin = user_info.get('is_admin', False)
        
        # 🔧 開発用: adminユーザーは強制的にcan_see_contents=Trueにする
        if is_admin:
            can_see_contents = True
            print(f"🔧 [DEBUG] admin強制設定: {user_info['username']} -> can_see_contents=True")
        
        result = {
            "logged_in": True,
            "can_see_contents": can_see_contents,
            "username": user_info['username'],
            "is_admin": is_admin
        }
        
        print(f"🔍 [DEBUG] check_user_permissions結果: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ [DEBUG] check_user_permissions エラー: {e}")
        return {"logged_in": False, "can_see_contents": False}