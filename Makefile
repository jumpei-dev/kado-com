# 稼働.com Makefile
# 開発環境の起動や管理のための簡易コマンド集

.PHONY: run css htmx install install-deps clean dev

# アプリを起動
run:
	@echo "🚀 Starting kado-com application..."
	@cd app && python3 main.py || python main.py

# Tailwind CSSのビルド
css:
	@echo "🎨 Building Tailwind CSS..."
	@cd app && npx tailwindcss -i ./tailwind.input.css -o ./static/css/tailwind.css --watch

# HTMX のダウンロード
htmx:
	@echo "⚡ Downloading HTMX..."
	@mkdir -p app/static/js
	@curl -s https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js -o app/static/js/htmx.min.js

# 依存関係のインストール
install-deps:
	@echo "📦 Installing dependencies..."
	@pip install -r requirements.txt
	@cd app && npm install -D tailwindcss

# インストールと初期セットアップ
install: install-deps htmx css
	@echo "✅ Installation complete!"

# 不要なファイルの削除
clean:
	@echo "🧹 Cleaning up..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete

# 開発環境を一行で起動（Tailwindのビルドとサーバーの起動）
dev:
	@echo "🚀 Starting development environment..."
	@cd app && npx tailwindcss -i ./tailwind.input.css -o ./static/css/tailwind.css && python -m uvicorn main:app --reload
