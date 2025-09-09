#!/bin/bash

# 認証システム切り替え実行スクリプト
echo "========================================"
echo "    認証システム切り替え実行ツール     "
echo "========================================"
echo "このスクリプトは以下の処理を行います："
echo "1. データベースマイグレーション実行"
echo "2. 認証システム切り替えスクリプト実行"
echo "3. アプリケーション再起動"
echo "----------------------------------------"

# プロジェクトルートに移動
PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"
cd "$PROJECT_ROOT"

# 確認
echo -n "処理を実行しますか？ [y/N]: "
read answer
if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "処理を中止しました。"
    exit 0
fi

# データベースマイグレーション
echo -e "\n[1/3] データベースマイグレーションを実行します..."
echo "マイグレーションSQLファイル: db_migration_users.sql"

# 実際のデータベースマイグレーション実行コマンド
# ここはユーザーの環境に合わせて修正してください
echo "注意: SQLの実行は手動で行ってください"
echo "適切なデータベースツールを使用して db_migration_users.sql を実行してください"
echo "例: psql -U username -d database_name -f db_migration_users.sql"

# 続行確認
echo -n "マイグレーションが完了したら続行します。続行しますか？ [y/N]: "
read answer
if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "処理を中止しました。"
    exit 0
fi

# 認証システム切り替え
echo -e "\n[2/3] 認証システム切り替えスクリプトを実行します..."
python update_auth_system.py

# アプリケーション再起動
echo -e "\n[3/3] アプリケーションを再起動します..."
echo "現在のアプリケーションを停止し、再起動してください"
echo "例: ./run_app.py を再実行"

echo -e "\n処理が完了しました！"
echo "新しい認証システムが適用されました。"
echo "管理者アカウントでログインし、/admin/users でユーザー管理が行えます。"
