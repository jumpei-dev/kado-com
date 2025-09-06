# 稼働.com Makefile
# 開発環境の起動や管理のための簡易コマンド集

.PHONY: run server frontend install test lint clean

# 現在のディレクトリを取得
CURDIR := $(shell pwd)

# アプリ全体を起動（サーバー＋フロントエンド）
run:
	@echo "🚀 Starting kado-com application..."
	@cd $(CURDIR) && python3 scripts/run_app.py || python scripts/run_app.py

# サーバーのみ起動
server:
	@echo "🌐 Starting API server..."
	@cd server && python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 || python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# フロントエンドのみ起動
frontend:
	@echo "🖥️ Starting frontend..."
	@cd frontend && npm run dev

# 依存関係のインストール
install:
	@echo "📦 Installing server dependencies..."
	@cd server && pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	@cd frontend && npm install

# テスト実行
test:
	@echo "🧪 Running tests..."
	@cd tests && pytest

# Lint実行
lint:
	@echo "🧹 Running linting..."
	@cd server && pylint app
	@cd frontend && npm run lint

# キャッシュなど不要ファイルを削除
clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@rm -rf frontend/node_modules
	@rm -rf frontend/dist
