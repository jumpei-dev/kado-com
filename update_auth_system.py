"""
認証システムの切り替えスクリプト
- メール認証から簡易認証への切り替え
"""

import os
import sys
import shutil
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

def main():
    print("=" * 50)
    print("認証システム切り替えツール")
    print("メール認証 → 簡易認証（LINE連携用）")
    print("=" * 50)
    
    # 1. バックアップの作成
    backup_auth_api()
    
    # 2. 新しい認証システムの適用
    apply_new_auth_system()
    
    print("\n認証システムの切り替えが完了しました！")
    print("""
次のステップ:
1. データベースに対してマイグレーションスクリプト 'db_migration_users.sql' を実行
2. アプリケーションを再起動して新しい認証システムをテスト
3. 管理者アカウントでログイン後、/admin/users にアクセスしてユーザー管理
""")

def backup_auth_api():
    """既存の認証APIファイルをバックアップ"""
    auth_file = project_root / "app" / "api" / "auth.py"
    backup_file = project_root / "app" / "api" / "auth.py.bak"
    
    if auth_file.exists():
        print(f"既存の認証APIをバックアップ中: {backup_file}")
        shutil.copy2(auth_file, backup_file)
        print("バックアップ完了")
    else:
        print(f"警告: 認証APIファイル {auth_file} が見つかりません")

def apply_new_auth_system():
    """新しい認証システムを適用"""
    # 1. 新しい認証APIを適用
    auth_simple_file = project_root / "app" / "api" / "auth_simple.py"
    auth_file = project_root / "app" / "api" / "auth.py"
    
    if auth_simple_file.exists():
        print(f"新しい認証システムを適用中: {auth_simple_file} → {auth_file}")
        shutil.copy2(auth_simple_file, auth_file)
        print("認証APIの更新完了")
    else:
        print(f"エラー: 新しい認証APIファイル {auth_simple_file} が見つかりません")
        return
    
    # 2. メインアプリケーションファイルを更新
    update_main_app()

def update_main_app():
    """メインアプリケーションファイルを更新"""
    main_app_file = project_root / "app" / "main.py"
    
    if not main_app_file.exists():
        print(f"エラー: メインアプリケーションファイル {main_app_file} が見つかりません")
        return
    
    print(f"メインアプリケーションを更新中: {main_app_file}")
    
    with open(main_app_file, "r") as f:
        content = f.read()
    
    # 管理者ルーターのインポートと登録を追加
    if "from app.api.admin import router as admin_router" not in content:
        # インポート部分を探して追加
        import_section = "from app.api import"
        new_import = "from app.api.admin import router as admin_router"
        
        if import_section in content:
            content = content.replace(
                import_section, 
                import_section + "\n" + new_import
            )
        else:
            print("警告: インポート部分が見つかりませんでした。手動で追加してください。")
    
    # ルーター登録部分を探して追加
    if "app.include_router(admin_router)" not in content:
        router_section = "app.include_router("
        new_router = "app.include_router(admin_router)"
        
        if router_section in content:
            # 最後のinclude_routerの後に追加
            last_include = content.rfind("app.include_router(")
            if last_include != -1:
                end_of_line = content.find("\n", last_include)
                if end_of_line != -1:
                    content = content[:end_of_line+1] + new_router + "\n" + content[end_of_line+1:]
        else:
            print("警告: ルーター登録部分が見つかりませんでした。手動で追加してください。")
    
    # 変更を保存
    with open(main_app_file, "w") as f:
        f.write(content)
    
    print("メインアプリケーションの更新完了")

if __name__ == "__main__":
    main()
