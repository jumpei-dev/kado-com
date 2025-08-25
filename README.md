# 稼働.com

風俗店の稼働状況をリアルタイムで収集・分析し、稼働率ランキングを提供するLINE Botシステム

## 📋 概要

**稼働.com**は、シティヘブンとデリヘルタウンから風俗店の稼働状況を自動収集し、稼働率に基づいたランキングを提供するシステムです。公式LINEアカウントからのみアクセス可能で、ID単位での閲覧権限管理を行います。

### 主な機能

- 🏆 **稼働率ランキング**: 店舗の稼働率に基づいたリアルタイムランキング
- 🔍 **店舗検索・詳細**: 特定店舗の詳細情報と稼働履歴
- 📊 **稼働データ分析**: 時間帯別・日別の稼働傾向分析
- 🔐 **アクセス制御**: LINE ID単位での閲覧権限管理
- 📱 **LIFF対応**: LINE内でのシームレスな利用体験

## 🏗️ システム構成

### アーキテクチャ

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   LINE Bot   │    │  LIFF Web   │    │  FastAPI    │
│             │───▶│    App      │───▶│   Backend   │
│             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                   ┌─────────────┐           │
                   │   Google    │◀──────────┘
                   │ Spreadsheet │
                   │     DB      │
                   └─────────────┘
                           ▲
                           │
                   ┌─────────────┐
                   │   GitHub    │
                   │   Actions   │
                   │   Batch     │
                   └─────────────┘
```

### 技術スタック

- **ホスティング**: Cloudflare Pages
- **認証**: LINE LIFF
- **バックエンド**: FastAPI + Uvicorn
- **バッチ処理**: GitHub Actions
- **スクレイピング**: Selenium
- **データベース**: Google Spreadsheet
- **CI/CD**: GitHub Actions
- **監視・通知**: LINE Notify

## 📁 プロジェクト構成

```
kado-com/
├── app/                    # FastAPI Webアプリケーション
│   ├── api/               # API エンドポイント
│   ├── models/            # データモデル
│   ├── services/          # ビジネスロジック
│   ├── middleware/        # ミドルウェア
│   └── utils/             # ユーティリティ
├── frontend/              # フロントエンド（LIFF）
│   ├── static/            # 静的ファイル
│   ├── templates/         # HTMLテンプレート
│   └── components/        # 再利用可能コンポーネント
├── batch/                 # バッチ処理
│   ├── scheduler/         # スケジュール管理・実行判定
│   ├── processors/        # データ処理
│   ├── scrapers/          # スクレイピング
│   ├── services/          # 共通サービス
│   └── utils/             # ユーティリティ
├── admin/                 # 管理者用ツール
├── config/                # 設定ファイル
├── tests/                 # テスト
├── .github/workflows/     # GitHub Actions
└── docs/                  # ドキュメント
```

## 🔄 バッチ処理スケジュール

### 自動実行タスク

| タスク | 実行頻度 | 説明 |
|--------|----------|------|
| **キャスト情報取得** | 6時間毎 | 出勤スケジュール情報を取得 |
| **稼働状況取得** | 30分毎 | リアルタイムの稼働状況を取得 |
| **稼働率計算** | 1日1回 | 前日の稼働率を計算・保存 |

### 稼働率計算ロジック

```
稼働率(%) = (実際の稼働時間 / 出勤予定時間) × 100

- 部屋数を超える同時稼働の場合、部屋割れ補正を適用
- 例: 2部屋に3人同時稼働 → 66%の補正係数を適用
- 営業時間外のデータは除外して計算
```

## 📊 データベース構成

### Google Spreadsheet シート構成

#### Business（店舗マスタ）
```
- BusinessID: 店舗ID
- Area: エリア（東京、大阪等）
- Prefecture: 都道府県
- Type: 業種（デリヘル、ソープ等）
- Name: 店舗名
- Capacity: 部屋数
- OpenHour: 開業時間
- CloseHour: 閉業時間
- ScheduleURL1: スクレイピング先URL
```

#### Status（稼働状況）
```
- BusinessID: 店舗ID
- Datetime: 取得日時
- CastID: キャストID
- IsActive: 稼働中フラグ
- OvercapacityCoefficient: 部屋割れ係数
```

#### StatusHistory（稼働履歴）
```
- BusinessID: 店舗ID
- Date: 日付
- WorkingRate: 稼働率(%)
```

#### Cast（キャスト情報）
```
- BusinessID: 店舗ID
- Name: キャスト名
- Date: 取得日時
- Schedule: 出勤時間
- IsWorking: 稼働フラグ
```

## 🚀 セットアップ

### 1. 必要な環境変数

```env
# Google Spreadsheet
GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
SPREADSHEET_NAME=kado-com-db

# LINE設定
LIFF_ID=your-liff-id
LINE_CHANNEL_ACCESS_TOKEN=your-access-token
LINE_NOTIFY_TOKEN=your-notify-token

# FastAPI設定
SECRET_KEY=your-secret-key
DEBUG=false
```

### 2. 依存関係のインストール

```bash
# アプリケーション用
pip install -r requirements.txt

# バッチ処理用
pip install -r batch-requirements.txt
```

### 3. Googleスプレッドシートの準備

1. Google Cloud Consoleでサービスアカウントを作成
2. Google Sheets APIを有効化
3. スプレッドシートを作成し、サービスアカウントに編集権限を付与
4. 必要なシートを作成（Business, Status, StatusHistory, Cast, AuthorizedUsers）

### 4. LINE LIFF設定

1. LINE Developersでプロバイダーとチャンネルを作成
2. LIFF アプリを追加
3. エンドポイントURLを設定

## 🔧 開発・デプロイ

### ローカル開発

```bash
# アプリケーション起動
cd app
uvicorn main:app --reload --port 8000

# バッチテスト実行
cd batch
python main.py cast --dry-run
```

### GitHub Actionsによる自動デプロイ

- **アプリケーション**: Cloudflare Pagesに自動デプロイ
- **バッチ処理**: GitHub Actionsで定期実行

## 📈 マネタイズ

### 収益モデル

- **月額利用料**: ID単位での閲覧権限販売
- **管理機能**: 手動でのID許可制御
- **プレミアム機能**: 詳細分析・アラート機能（将来実装予定）

### ユーザー管理

- LINE IDベースでのアクセス制御
- スプレッドシートでの許可ユーザー管理
- 管理者による手動承認システム

## 🛡️ セキュリティ

- **認証**: LINE LIFF による確実な本人確認
- **アクセス制御**: ID単位での厳密な権限管理
- **データ保護**: スクレイピング対象サイトのガイドライン遵守
- **レート制限**: 適切な間隔でのデータ取得

## 📚 API仕様

### 主要エンドポイント

```
GET  /api/ranking              # 稼働率ランキング取得
GET  /api/ranking/trending     # 稼働率上昇トレンド
GET  /api/business/{id}        # 店舗詳細情報
GET  /api/business/{id}/history # 店舗稼働履歴
POST /api/admin/users          # ユーザー管理（管理者のみ）
```

## 📋 今後の開発予定

- [ ] Figmaベースの本格的UIデザイン実装
- [ ] プッシュ通知機能
- [ ] 詳細な稼働分析レポート
- [ ] モバイルアプリ版の検討
- [ ] AI予測機能の追加

## 🤝 コントリビューション

このプロジェクトは現在プライベート開発中です。

## 📄 ライセンス

このプロジェクトは商用利用を目的として開発されています。

## 📞 サポート

技術的な問題や機能要望がある場合は、プロジェクト管理者までお問い合わせください。

---

**稼働.com** - 風俗業界の稼働データを革新的に可視化するシステム
