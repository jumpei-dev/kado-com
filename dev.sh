#!/bin/bash

# 稼働.com 開発スクリプト
# 開発環境の起動や管理のための簡易コマンド集

# 引数に応じてコマンドを実行
case "$1" in
  install)
    echo "📦 依存関係をインストールしています..."
    pip install -r requirements.txt
    cd app && npm install -D tailwindcss
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
    echo "🚀 アプリケーションを起動しています..."
    cd /Users/admin/Projects/kado-com/app && python3 -m uvicorn main:app --reload
    ;;

  dev)
    echo "🛠️ 開発環境を一括で起動します..."
    # 開発環境を一括で起動（バックグラウンドでTailwindCSSを実行）
    cd app && npx tailwindcss -i ./tailwind.input.css -o ./static/css/tailwind.css &
    TAILWIND_PID=$!
    echo "TailwindCSSビルドを開始しました (PID: $TAILWIND_PID)"
    
    # アプリケーション起動
    echo "アプリケーションを起動しています..."
    cd /Users/admin/Projects/kado-com/app && python3 -m uvicorn main:app --reload
    
    # アプリケーションが終了したらTailwindCSSのプロセスも終了
    kill $TAILWIND_PID
    ;;

  clean)
    echo "🧹 不要なファイルを削除しています..."
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -delete
    ;;

  *)
    echo "使用方法: ./dev.sh [コマンド]"
    echo "利用可能なコマンド:"
    echo "  install  - 依存関係をインストール"
    echo "  css      - TailwindCSSをビルド（監視モード）"
    echo "  htmx     - HTMXをダウンロード"
    echo "  run      - アプリケーションを起動"
    echo "  dev      - 開発環境を一括で起動（CSS + アプリ）"
    echo "  clean    - 不要なファイルを削除"
    ;;
esac
