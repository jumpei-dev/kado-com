#!/usr/bin/env python3
"""
権限デバッグ用スクリプト
現在のユーザーの権限状況を確認します
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.absolute()))

try:
    from app.core.auth_service import AuthService
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("このスクリプトはプロジェクトルートから実行してください")
    sys.exit(1)


async def debug_user_permissions():
    """ユーザー権限をデバッグ"""
    try:
        auth_service = AuthService()
        
        print("🔍 ユーザー権限デバッグ")
        print("=" * 50)
        
        # 全ユーザーを取得（実装に応じて調整が必要）
        print("📋 データベース内の全ユーザー:")
        
        # TODO: 実際のauth_serviceに合わせて実装
        # users = await auth_service.get_all_users()
        
        # 仮のテスト用
        print("  ⚠️ get_all_users()メソッドが未実装のため、個別チェックを実行")
        
        # 特定のユーザーIDでテスト（adminユーザーのIDを想定）
        test_user_ids = [1, 11]  # ログに表示されたID=11を含む
        
        for user_id in test_user_ids:
            try:
                # TODO: get_user_by_id メソッドが必要
                print(f"\n👤 ユーザーID {user_id} の確認:")
                print("  ⚠️ get_user_by_id()メソッドが未実装")
                
            except Exception as e:
                print(f"  ❌ ユーザーID {user_id} 取得エラー: {e}")
        
        print("\n🧪 auth_service の利用可能メソッド:")
        methods = [method for method in dir(auth_service) if not method.startswith('_')]
        for method in methods:
            print(f"  - {method}")
            
        print("\n🔧 テスト用トークン生成:")
        try:
            # テスト用のトークン生成（実装に応じて調整）
            print("  ⚠️ トークン生成テストは未実装")
        except Exception as e:
            print(f"  ❌ トークン生成エラー: {e}")
            
    except Exception as e:
        print(f"❌ デバッグ実行エラー: {e}")
        import traceback
        traceback.print_exc()


def check_user_attributes():
    """ユーザーモデルの属性をチェック"""
    try:
        # ユーザーモデルをインポート
        from app.models.user import User  # パスは実際の構造に合わせて調整
        
        print("\n📋 Userモデルの属性:")
        print("-" * 30)
        
        # クラス属性を確認
        for attr_name in dir(User):
            if not attr_name.startswith('_'):
                attr_value = getattr(User, attr_name, None)
                print(f"  {attr_name}: {type(attr_value).__name__}")
                
    except ImportError as e:
        print(f"\n⚠️ Userモデルのインポートに失敗: {e}")
        print("  models/user.py の場所を確認してください")
    except Exception as e:
        print(f"\n❌ 属性チェックエラー: {e}")


if __name__ == "__main__":
    print("🚀 権限デバッグスクリプト開始")
    
    # 非同期関数を実行
    asyncio.run(debug_user_permissions())
    
    # ユーザーモデル属性チェック
    check_user_attributes()
    
    print("\n✅ デバッグ完了")
