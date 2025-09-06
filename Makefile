# 稼働.com M# Tailwind CSSのビルド
css:
	@echo "🎨 Building Tailwind CSS..."
	@npx tailwindcss -i ./app/tailwind.input.css -o ./app/static/css/tailwind.css --watchile
# 開発環境の起動や管理のための簡易コマンド集

.PHONY: run css htmx install install-deps clean

# アプリを起動
run:
	@echo "🚀 Starting kado-com application..."
	@cd app && python3 main.py || python main.py

# Tailwind CSSのビルド
css:
	@echo "� Building Tailwind CSS..."
	@npx tailwindcss -i ./tailwind.input.css -o ./app/static/css/tailwind.css --watch

# HTMX のダウンロード
htmx:
	@echo "⚡ Downloading HTMX..."
	@mkdir -p app/static/js
	@curl -s https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js -o app/static/js/htmx.min.js

# 依存関係のインストール
install-deps:
	@echo "📦 Installing dependencies..."
	@pip install fastapi uvicorn jinja2 python-multipart aiofiles
	@npm install -D tailwindcss

# 初期セットアップ
install: install-deps htmx
	@echo "✅ Setup complete!"

# 開発環境のクリーンアップ
clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
