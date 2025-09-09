#!/usr/bin/env python3
"""
認証システム移行スクリプト
- 新しい認証システムへの移行を実行します
"""

import os
import sys
import argparse
from pathlib import Path
import logging
import asyncio

# プロジェクトルートを追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 必要なモジュールをインポート
try:
    from app.core.database import DatabaseManager
except ImportError:
    logger.error("アプリケーションモジュールの読み込みに失敗しました。パスが正しいか確認してください。")
    sys.exit(1)

async def apply_migration():
    """データベースマイグレーションを実行"""
    try:
        logger.info("データベースマイグレーションを開始します...")
        db = DatabaseManager()
        
        # マイグレーションSQLの読み込み
        migration_file = project_root / "migrations" / "auth_system_renewal.sql"
        
        if not migration_file.exists():
            logger.error(f"マイグレーションファイルが見つかりません: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            sql = f.read()
            
        # SQLの実行
        await db.execute(sql)
        logger.info("マイグレーションが正常に適用されました。")
        
        # テーブルの確認
        result = await db.fetch_one("SELECT COUNT(*) FROM users")
        logger.info(f"ユーザーテーブルのレコード数: {result['count']}")
        
        # 管理者の確認
        admin = await db.fetch_one("SELECT username, is_admin FROM users WHERE is_admin = TRUE")
        if admin:
            logger.info(f"管理者ユーザーが存在します: {admin['username']}")
        else:
            logger.warning("管理者ユーザーが存在しません。")
            
        return True
        
    except Exception as e:
        logger.error(f"マイグレーション中にエラーが発生しました: {str(e)}")
        return False

async def update_config_files():
    """設定ファイルの更新"""
    try:
        logger.info("設定ファイルを更新しています...")
        
        # 既存のauth_simple.pyをauth.pyにコピー
        source_path = project_root / "app" / "api" / "auth_new.py"
        target_path = project_root / "app" / "api" / "auth.py"
        
        # ファイルの存在確認
        if not source_path.exists():
            logger.error(f"ソースファイルが見つかりません: {source_path}")
            return False
            
        # バックアップを作成
        if target_path.exists():
            backup_path = project_root / "app" / "api" / "auth.py.bak"
            if not backup_path.exists():
                target_path.rename(backup_path)
                logger.info(f"バックアップを作成しました: {backup_path}")
                
        # 新ファイルをコピー
        with open(source_path, 'r') as src, open(target_path, 'w') as dst:
            dst.write(src.read())
            
        logger.info(f"APIファイルを更新しました: {target_path}")
        
        # 認証レスポンステンプレートの更新
        source_path = project_root / "app" / "templates" / "components" / "auth_response_new.html"
        target_path = project_root / "app" / "templates" / "components" / "auth_response.html"
        
        # ファイルの存在確認
        if not source_path.exists():
            logger.error(f"ソースファイルが見つかりません: {source_path}")
            return False
            
        # バックアップを作成
        if target_path.exists():
            backup_path = project_root / "app" / "templates" / "components" / "auth_response.html.bak"
            if not backup_path.exists():
                target_path.rename(backup_path)
                logger.info(f"バックアップを作成しました: {backup_path}")
                
        # 新ファイルをコピー
        with open(source_path, 'r') as src, open(target_path, 'w') as dst:
            dst.write(src.read())
            
        logger.info(f"レスポンステンプレートを更新しました: {target_path}")
        
        # 認証モーダルテンプレートの更新
        source_path = project_root / "app" / "templates" / "components" / "auth_modals_new.html"
        target_path = project_root / "app" / "templates" / "components" / "auth_modals.html"
        
        # ファイルの存在確認
        if not source_path.exists():
            logger.error(f"ソースファイルが見つかりません: {source_path}")
            return False
            
        # バックアップを作成
        if target_path.exists():
            backup_path = project_root / "app" / "templates" / "components" / "auth_modals.html.bak"
            if not backup_path.exists():
                target_path.rename(backup_path)
                logger.info(f"バックアップを作成しました: {backup_path}")
                
        # 新ファイルをコピー
        with open(source_path, 'r') as src, open(target_path, 'w') as dst:
            dst.write(src.read())
            
        logger.info(f"モーダルテンプレートを更新しました: {target_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"設定ファイルの更新中にエラーが発生しました: {str(e)}")
        return False

async def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="認証システム移行スクリプト")
    parser.add_argument('--dry-run', action='store_true', help='実際の変更を行わずに処理を確認')
    parser.add_argument('--skip-migration', action='store_true', help='データベースマイグレーションをスキップ')
    parser.add_argument('--skip-config', action='store_true', help='設定ファイルの更新をスキップ')
    
    args = parser.parse_args()
    
    logger.info("認証システム移行スクリプトを開始します...")
    logger.info(f"ドライラン: {'はい' if args.dry_run else 'いいえ'}")
    
    if args.dry_run:
        logger.info("ドライランモードです。実際の変更は行われません。")
        return
        
    success = True
    
    # データベースマイグレーション
    if not args.skip_migration:
        migration_success = await apply_migration()
        if not migration_success:
            logger.error("マイグレーションが失敗しました。")
            success = False
    else:
        logger.info("データベースマイグレーションはスキップされました。")
        
    # 設定ファイルの更新
    if not args.skip_config:
        config_success = await update_config_files()
        if not config_success:
            logger.error("設定ファイルの更新が失敗しました。")
            success = False
    else:
        logger.info("設定ファイルの更新はスキップされました。")
        
    if success:
        logger.info("認証システムの移行が完了しました！")
        logger.info("サーバーを再起動して変更を適用してください。")
    else:
        logger.error("認証システムの移行中にエラーが発生しました。ログを確認してください。")

if __name__ == "__main__":
    asyncio.run(main())
