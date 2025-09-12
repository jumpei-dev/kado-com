# 稼働.com - 統合管理システム

風俗店の稼働状況を自動収集・分析し、Webインターフェースで可視化する統合管理システム

## 🏗️ **システム構成**

### Webアプリケーション (FastAPI)
- **フロントエンド**: HTML/CSS/JavaScript (HTMX, Tailwind CSS)
- **バックエンド**: FastAPI + SQLAlchemy
- **認証システム**: JWT認証、パスワードリセット機能
- **データ可視化**: Chart.js による稼働率グラフ表示
- **管理機能**: 店舗管理、ユーザー管理

### バッチ処理システム
- **自動データ収集**: 30分間隔での稼働状況スクレイピング
- **稼働率計算**: 日次での稼働率算出・履歴保存
- **GitHub Actions**: クラウド環境での自動バッチ実行

### CI/CD & 自動化
- **GitHub Actions**: バッチ処理の自動実行
- **スケジュール実行**: cron式による定期実行
- **手動実行**: ワークフロー手動トリガー対応

## ✨ **最新実装機能**

### � **Capacity補正機能**
- **ソープランド店舗専用**: 物理的制約（部屋数）を考慮した稼働数上限制御
- **自動補正**: `working_count = min(検出稼働数, capacity値)`で正確な稼働率算出
- **対象**: `type=soapland`の店舗のみに適用

### ⏰ **出勤時間終了判定機能**
- **1時間前ルール**: 出勤時間終了1時間前の「受付終了」は`is_working=false`
- **完売判定**: 出勤時間に余裕がある「受付終了」は`is_working=true`（完売状態）
- **既存コード活用**: 時間範囲判定ロジックを100%再利用した効率的実装

### 🎨 **UI最適化**
- **出勤率削除**: システム上意味の薄い指標を削除し、稼働率に集中
- **情報簡素化**: DOM確認モードで重要指標のみ表示

### ⚙️ **テスト機能**
- **一時設定**: `--capacity`, `--type`オプションで店舗設定を一時変更
- **自動復元**: テスト実行後に元の設定に自動復元
- **DOM確認モード**: 詳細なHTML構造確認と判定根拠表示

## �📊 **データベース構造**

### Business（店舗）
管理者があらかじめ登録しておく店舗マスタ情報

| カラム名 | 型 | 説明 |
|---------|-----|------|
| business_id | BIGINT (Primary Key) | 店舗ID |
| area | TEXT | 日本の中のエリア |
| prefecture | TEXT | 都道府県 |
| **type** | TEXT | **業種（soapland等）** |
| name | TEXT | 店舗名 |
| **capacity** | INTEGER | **部屋数（稼働数上限）** |
| status_accuracy | TEXT | 情報の正確性 |
| working_type | TEXT | 稼働表示タイプ |
| in_scope | BOOLEAN | 計算対象とするか |
| open_hour | TEXT | 開業時間 |
| close_hour | TEXT | 閉業時間 |
| regular_holiday | TEXT | 定休日 |
| schedule_url1 | TEXT | スクレイピング先URL |

### Status（稼働）
30分ごとに自動取得する稼働状況データ

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | BIGSERIAL (Primary Key) | レコードID |
| datetime | TIMESTAMP | 取得日時 |
| business_id | BIGINT | 店舗ID（Business.business_idと関連） |
| cast_id | BIGINT | キャストID |
| **is_working** | BOOLEAN | **稼働しているか（capacity補正適用）** |
| **is_on_shift** | BOOLEAN | **出勤しているか** |
| is_dummy | BOOLEAN | テストデータフラグ |

### StatusHistory（稼働履歴）
1日に1回（閉店時間後）算出する稼働率

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | BIGSERIAL (Primary Key) | レコードID |
| business_id | BIGINT | 店舗ID（Business.business_idと関連） |
| date | DATE | 日付 |
| **working_rate** | DECIMAL | **稼働率%（capacity補正済み）** |

## 📁 **プロジェクト構造**

### Webアプリケーション
```
app/
├── api/                    # APIエンドポイント
│   ├── admin.py           # 管理者API
│   ├── auth.py            # 認証API
│   ├── auth_new.py        # 新認証システム
│   ├── pages.py           # ページルーティング
│   ├── stores.py          # 店舗API
│   └── twitter.py         # Twitter連携
├── core/                   # コアモジュール
│   ├── auth_config.py     # 認証設定
│   ├── auth_service.py    # 認証サービス
│   ├── auth_utils.py      # 認証ユーティリティ
│   ├── config.py          # アプリ設定
│   ├── database.py        # データベース管理
│   ├── email_service.py   # メール送信サービス
│   └── seed.py            # データシード
├── models/                 # データモデル
│   └── store.py           # 店舗モデル
├── static/                 # 静的ファイル
│   ├── css/               # スタイルシート
│   └── js/                # JavaScript
├── templates/              # HTMLテンプレート
│   ├── admin/             # 管理画面
│   ├── components/        # コンポーネント
│   └── partials/          # パーシャル
├── utils/                  # ユーティリティ
└── main.py                # FastAPIアプリケーション
```

### バッチ処理システム
```
batch/
├── core/                   # コアモジュール
│   ├── database.py        # データベース管理
│   ├── models.py          # データモデル
│   └── scraper.py         # スクレイピング機能
├── jobs/                   # バッチジョブ
│   ├── status_collection/ # ステータス収集（30分間隔）
│   │   ├── collector.py           # 収集メイン処理
│   │   ├── cityheaven_parsers.py  # 🔧 HTML解析（受付終了判定付き）
│   │   ├── cityheaven_strategy.py # 戦略パターン
│   │   ├── database_saver.py      # DB保存処理
│   │   ├── html_loader.py         # HTML取得
│   │   ├── aiohttp_loader.py      # 非同期HTTP取得
│   │   └── webdriver_manager.py   # WebDriver管理
│   └── working_rate_calculation/  # 稼働率計算（日次）
│       ├── calculator.py          # 🔧 計算統合（capacity対応）
│       ├── rate_calculator.py     # 🔧 稼働率計算（capacity補正）
│       ├── data_retriever.py      # データ取得
│       ├── history_saver.py       # 履歴保存
│       ├── history_summary.py     # 履歴サマリー
│       └── models.py              # データモデル
├── schedulers/             # スケジューラー
│   ├── batch_scheduler.py         # メインスケジューラー
│   ├── status_collection_scheduler.py  # 収集スケジューラー
│   └── working_rate_scheduler.py      # 稼働率スケジューラー
├── tests/                  # テスト
│   ├── integration/       # 統合テスト
│   │   ├── test_html_to_db.py           # HTML→DB統合テスト
│   │   └── test_working_rate_calculation.py  # 稼働率計算テスト
│   └── utils/             # テストユーティリティ
├── utils/                  # ユーティリティ
│   ├── config.py          # 設定管理
│   ├── datetime_utils.py  # 日時処理
│   ├── debug_html_output.py # HTMLデバッグ
│   └── logging_utils.py   # ログ管理
├── main.py                 # 🔧 CLIエントリーポイント
└── requirements.txt        # Python依存関係
```

### CI/CD & 自動化
```
.github/
└── workflows/              # GitHub Actionsワークフロー
    ├── batch-job.yml      # 基本バッチ処理
    ├── advanced-batch.yml # 高度なバッチ処理
    └── README.md          # ワークフロー説明
```

### 設定・データ・その他
```
config/
├── base.yaml        # 基本設定
└── config.yml       # アプリケーション設定

data/
├── README.md        # データディレクトリ説明
└── blurred_names_template.csv  # 匿名化テンプレート

shared/
├── __init__.py
└── config.py        # 共有設定

tests/
├── integration/     # 統合テスト
├── batch_utils/     # バッチユーティリティテスト
├── core/           # コアモジュールテスト
├── jobs/           # ジョブテスト
├── schedulers/     # スケジューラーテスト
└── utils/          # テストヘルパー

docs/
└── blurred_name_implementation.md  # 実装ドキュメント

migrations/
└── auth_system_renewal.sql  # データベースマイグレーション

_backup/
└── auth/           # 認証システムバックアップ
```

## 🚀 **GitHub Actions 自動化**

### ワークフロー概要

#### 基本バッチ処理 (`batch-job.yml`)
- **稼働率計算**: 毎日日本時間12時（UTC 3時）
- **稼働状況取得**: 30分ごと
- **手動実行**: ワークフロー画面から実行可能

#### 高度なバッチ処理 (`advanced-batch.yml`)
- **並行実行**: マトリックス戦略による複数ジョブ同時実行
- **エラーハンドリング**: 詳細なログ出力とアーティファクト保存
- **ヘルスチェック**: 15分ごとのシステム監視
- **クリーンアップ**: 毎日午前2時の自動データクリーンアップ

### 必要なGitHub Secrets
```
DATABASE_URL          # データベース接続URL
DB_PASSWORD           # データベースパスワード
AUTH_SECRET_KEY       # 認証用秘密鍵
X_BEARER_TOKEN        # X API Bearer Token
X_API_KEY             # X API Key
X_API_SECRET          # X API Secret
X_ACCESS_TOKEN        # X Access Token
X_ACCESS_TOKEN_SECRET # X Access Token Secret
```

## 🚀 **セットアップ**

### 1. 依存関係インストール
```bash
# プロジェクトルート
pip install -r requirements.txt

# バッチ処理用
cd batch
pip install -r requirements.txt

# フロントエンド（Tailwind CSS）
cd app
npm install
```

### 2. データベース設定
- Supabaseプロジェクトを作成
- `config/secret.yml`で接続情報を設定（GitHub Secretsから自動生成）

### 3. アプリケーション起動

#### Webアプリケーション
```bash
# 開発サーバー起動
cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# または
python app/run_app.py
```

#### バッチ処理（ローカル実行）
```bash
# 稼働状況収集
python batch/main.py status-collection

# 稼働率計算
python batch/main.py working-rate-calculation

# データベーステスト
python batch/main.py test-db
```

#### GitHub Actions（自動実行）
1. GitHubリポジトリのSecretsを設定
2. `.github/workflows/`のワークフローが自動実行
3. 手動実行も可能（Actions画面から）

## 🛠️ **コマンドライン操作**

### **基本操作**
```bash
# データベース接続テスト
python batch/main.py test-db

# 稼働状況収集（手動実行）
python batch/main.py collect --force

# 稼働率計算（手動実行）
python batch/main.py calculate --date 2025-09-05 --force
```

### **🔧 新機能：店舗テスト機能**
```bash
# capacity補正テスト（一時設定）
python batch/main.py test-working-rate \
  --business-id 1 \
  --date 2025-09-05 \
  --capacity 6 \
  --type soapland

# DOM確認モード（HTML構造詳細確認）
python batch/main.py debug-html \
  --url "https://www.cityheaven.net/example/attend/"

python batch/main.py debug-html \
  --local-file "shop_cast_list_20250905_215657.html"
```

### **🔧 新機能：HTML取得・解析**
```bash
# URLからHTML取得・保存
python batch/main.py debug-html --url "https://example.com/attend/"

# ローカルHTMLファイルでDOM構造確認
python batch/main.py debug-html --local-file "filename.html"

# DB統合テスト（HTML→解析→DB保存）
python batch/main.py test-db-integration filename.html --business-name "店舗名"
```

## 🔍 **詳細デバッグ機能**

### **DOM確認モード**
新実装の受付終了判定ロジックを詳細に確認できます。

#### **出力例**
```
🟡 【キャストID: 54285420】
⏰ 出勤時間情報: '10:00～22:00'
💼 待機状態: '受付終了'
⏰ 出勤時間終了1時間前検出: 終了22:00, 現在21:56
🎯 判定結果: on_shift=True, is_working=False
🧮 判定根拠: '受付終了'検出 → しかし出勤終了1時間前 → working=False

🟢 【キャストID: 61166345】
⏰ 出勤時間情報: '16:00～0:00'
💼 待機状態: '受付終了'
🎯 判定結果: on_shift=True, is_working=True
🧮 判定根拠: '受付終了'検出 → 完売状態=稼働中 → working=True
```

### **判定ロジック**

#### **出勤判定 (is_on_shift)**
1. 出勤時間が「お休み」「調整中」等でないか確認
2. 現在時刻が出勤時間範囲内にあるか確認
3. 夜間営業の場合の跨日計算に対応

#### **稼働判定 (is_working)**
1. 出勤中（is_on_shift=True）が前提条件
2. 🔧 **新機能**: 「受付終了」の場合、出勤時間終了1時間前かチェック
   - **1時間前以降**: `is_working=false`（終了間近）
   - **1時間前より前**: `is_working=true`（完売状態）
3. 待機状態が「次回XX:XX～」形式で未来時刻を示すか確認
4. 「XX:XX ～待機中」（過去時刻）は非稼働として判定

#### **🔧 Capacity補正判定**
```
検出稼働数: 8人
店舗capacity: 6人
→ 補正後稼働数: 6人（min(8, 6)）
→ 稼働率: 6人 / 出勤中人数 × 100%
```

## 📈 **主要機能**

### Webアプリケーション機能
- **🔐 認証システム**: JWT認証、パスワードリセット、メール認証
- **📊 データ可視化**: Chart.js による稼働率グラフ表示
- **🏪 店舗管理**: 店舗情報の表示・検索・フィルタリング
- **👥 ユーザー管理**: 管理者によるユーザー管理機能
- **📱 レスポンシブUI**: Tailwind CSS + HTMX による現代的なUI
- **🐦 Twitter連携**: ソーシャルメディア統合

### バッチ処理機能
- **🔧 自動スクレイピング**: 店舗の稼働情報を30分間隔で収集（受付終了判定付き）
- **🔧 capacity補正稼働率計算**: ソープランド店舗の物理的制約を考慮した正確な稼働率算出
- **⏰ 営業時間考慮**: 店舗の営業時間内のみスクレイピング実行
- **🛡️ エラー処理**: 堅牢なエラーハンドリングとリトライ機能
- **📝 ログ管理**: 詳細なログ出力とローテーション
- **🔧 詳細デバッグ**: キャスト稼働判定の詳細分析機能（DOM確認モード）
- **🧪 テスト機能**: 店舗設定の一時変更とテスト機能

### CI/CD & 自動化機能
- **⚙️ GitHub Actions**: クラウド環境での自動バッチ実行
- **📅 スケジュール実行**: cron式による定期実行
- **🎛️ 手動実行**: ワークフロー手動トリガー対応
- **📊 並行処理**: マトリックス戦略による効率的な処理
- **🔍 監視機能**: ヘルスチェックとエラー通知

## 🎯 **実装検証済み機能**

### **✅ Capacity補正テスト**
- **吉原かまくら御殿**: capacity=6で8人→6人補正動作確認
- **稼働率**: 補正前66.7% → 補正後50.0%で物理的制約を反映

### **✅ 受付終了判定テスト**
- **なす花壇**: 22:00終了×21:56時点の「受付終了」→ is_working=false
- **なす花壇**: 0:00終了×21:56時点の「受付終了」→ is_working=true

### **✅ UI最適化**
- **出勤率削除**: システム上意味の薄い指標を削除済み
- **情報集約**: 稼働率のみに集中した表示

## 🔧 **技術スタック**

### フロントエンド
- **HTML/CSS/JavaScript**: 基本的なWeb技術
- **Tailwind CSS**: ユーティリティファーストCSSフレームワーク
- **HTMX**: 動的なHTMLアップデート
- **Chart.js**: データ可視化ライブラリ

### バックエンド
- **Python 3.11+**: メインプログラミング言語
- **FastAPI**: 高性能WebAPIフレームワーク
- **SQLAlchemy**: ORM（Object-Relational Mapping）
- **Pydantic**: データバリデーション
- **Uvicorn**: ASGIサーバー

### データベース
- **PostgreSQL**: メインデータベース（Supabase）
- **Alembic**: データベースマイグレーション

### スクレイピング・データ処理
- **BeautifulSoup4**: HTML解析
- **aiohttp**: 非同期HTTP通信
- **Selenium**: WebDriverによる動的コンテンツ取得
- **Pandas**: データ処理・分析

### CI/CD・インフラ
- **GitHub Actions**: 自動化ワークフロー
- **Docker**: コンテナ化（予定）
- **Supabase**: データベースホスティング

### 開発・テスト
- **pytest**: テストフレームワーク
- **Black**: コードフォーマッター
- **isort**: インポート整理
- **mypy**: 型チェック

## 📝 **ライセンス**

Private Project - 商用利用禁止

## 🤝 **コントリビューション**

このプロジェクトはプライベートプロジェクトです。

## 📞 **サポート**

技術的な問題や質問がある場合は、プロジェクト管理者にお問い合わせください。
