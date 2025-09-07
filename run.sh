#!/bin/bash

# 稼働.com 開発用スクリプト
# 使い方: ./run.sh [コマンド]
#   install - 依存関係をインストール
#   css     - TailwindCSSをビルド（監視モード）
#   htmx    - HTMXをダウンロード
#   run     - FastAPIサーバーのみ起動
#   dev     - 開発サーバーを起動（TailwindCSSも同時に起動）
#   clean   - 不要なファイルを削除

# エラーハンドリング
set -e

# カレントディレクトリをスクリプトのあるディレクトリに変更
cd "$(dirname "$0")"

# コマンドライン引数を解析
command=${1:-"dev"}

case $command in
    install)
        echo "📦 依存関係をインストールしています..."
        pip install -r requirements.txt
        cd app && npm install -D tailwindcss
        mkdir -p app/static/js
        curl -s https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js -o app/static/js/htmx.min.js
        echo "✅ インストール完了"
        ;;
        
    css)
        echo "🎨 TailwindCSSをビルドしています..."
        cd app && npx tailwindcss -i ./tailwind.input.css -o ./static/css/tailwind.css --watch
        ;;
        
    htmx)
        echo "⚡ HTMXをダウンロードしています..."
        mkdir -p app/static/js
        curl -s https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js -o app/static/js/htmx.min.js
        ;;
        
    run)
        echo "🚀 FastAPIサーバーを起動しています..."
        echo "💡 詳細なデバッグ情報を表示します"
        # より詳細なログレベルを設定
        export PYTHONPATH="$PWD"
        export PYTHONUNBUFFERED=1
        export PYTHONVERBOSE=1
        echo "📂 カレントディレクトリ: $(pwd)"
        
        # デバッグスクリプトを実行
        echo "🔍 デバッグ診断を実行"
        python3 debug_app.py
        
        echo "🔧 uvicornをデバッグモードで実行"
        python3 -m uvicorn app.main:app --reload --port 8080 --log-level debug
        ;;
        
    dev)
        echo "🚀 開発環境を起動しています..."
        # TailwindCSSをバックグラウンドで起動
        cd app && npx tailwindcss -i ./tailwind.input.css -o ./static/css/tailwind.css --watch &
        CSS_PID=$!
        
        # サーバーを起動
        cd app && python3 -m uvicorn main:app --reload
        
        # 終了時にバックグラウンドプロセスをクリーンアップ
        kill $CSS_PID
        ;;
        
    clean)
        echo "🧹 不要なファイルを削除しています..."
        find . -name "*.pyc" -delete
        find . -name "__pycache__" -delete
        ;;
        
    *)
        echo "❌ 不明なコマンドです: $command"
        echo "使用可能なコマンド:"
        echo "  install  - 依存関係をインストール"
        echo "  css      - TailwindCSSをビルド（監視モード）"
        echo "  htmx     - HTMXをダウンロード"
        echo "  run      - FastAPIサーバーのみ起動"
        echo "  dev      - 開発環境を一括で起動（CSS + アプリ）"
        echo "  clean    - 不要なファイルを削除"
        exit 1
        ;;
esac

exit 0
