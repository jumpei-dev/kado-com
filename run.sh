#!/bin/bash
# データベース接続設定
export DATABASE_URL="postgresql://postgres.hnmbsqydlfemlmsyexrq:Ggzzmmb3@57.182.231.186:6543/postgres?sslmode=require"

# プロジェクトディレクトリに移動し、PYTHONPATHを設定してアプリを実行
cd /Users/admin/Projects/kado-com && PYTHONPATH=/Users/admin/Projects/kado-com python3 app/run_app.py
