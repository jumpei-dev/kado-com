#!/usr/bin/env python3

"""
修正されたauth_serviceの認証テスト
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.auth_service import auth_service
from fastapi import Request

class MockRequest:
    def __init__(self, token=None):
        self.cookies = {"access_token": token} if token else {}

async def test_auth_flow():
    """認証フローの完全テスト"""
    print("=== 認証フローテスト開始 ===\n")
    
    # 1. 管理者ユーザーでログイン
    admin_username = "admin"  # can_see_contents=True
    password = "admin123"
    
    print(f"1. 管理者ユーザー認証テスト: {admin_username}")
    user = await auth_service.authenticate_user(admin_username, password)
    
    if user:
        print(f"✓ 認証成功:")
        print(f"  - ID: {user['id']}")
        print(f"  - ユーザー名: {user['username']}")
        print(f"  - is_admin: {user['is_admin']}")
        print(f"  - can_see_contents: {user.get('can_see_contents', 'フィールドなし')}")
        
        # 2. トークン生成
        print(f"\n2. トークン生成")
        token_data = {"sub": str(user['id'])}
        token = auth_service.create_access_token(token_data)
        print(f"✓ トークン生成成功: {token[:50]}...")
        
        # 3. トークンから現在ユーザー取得
        print(f"\n3. トークンからユーザー取得")
        mock_request = MockRequest(token)
        current_user = await auth_service.get_current_user(mock_request)
        
        if current_user:
            print(f"✓ ユーザー取得成功:")
            print(f"  - ID: {current_user['id']}")
            print(f"  - ユーザー名: {current_user['username']}")
            print(f"  - is_admin: {current_user['is_admin']}")
            print(f"  - can_see_contents: {current_user.get('can_see_contents', 'フィールドなし')}")
        else:
            print("✗ ユーザー取得失敗")
            
    else:
        print(f"✗ 認証失敗: {admin_username}")
    
    print("\n" + "="*50)
    
    # 一般ユーザーのテスト
    normal_username = "test_user"  # can_see_contents=True  
    print(f"\n4. 一般ユーザー認証テスト: {normal_username}")
    user2 = await auth_service.authenticate_user(normal_username, "password123")
    
    if user2:
        print(f"✓ 認証成功:")
        print(f"  - ID: {user2['id']}")
        print(f"  - ユーザー名: {user2['username']}")
        print(f"  - is_admin: {user2['is_admin']}")
        print(f"  - can_see_contents: {user2.get('can_see_contents', 'フィールドなし')}")
    else:
        print(f"✗ 認証失敗: {normal_username}")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
