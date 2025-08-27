# 稼働.com - バッチ処理システム

風俗店の稼働状況を自動収集・分析するバッチ処理システム

## 📊 データベース構造

### Business（店舗）
管理者があらかじめ登録しておく店舗マスタ情報

| カラム名 | 型 | 説明 |
|---------|-----|------|
| business_id | TEXT (Primary Key) | 店舗ID |
| area | TEXT | 日本の中のエリア |
| prefecture | TEXT | 都道府県 |
| type | TEXT | 業種 |
| name | TEXT | 店舗名 |
| capacity | INTEGER | 部屋数 |
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
| id | SERIAL (Primary Key) | レコードID |
| datetime | TIMESTAMP | 取得日時 |
| business_id | TEXT | 店舗ID（Business.business_idと関連） |
| cast_id | TEXT | キャストID |
| is_working | BOOLEAN | 稼働しているか |
| is_on_shift | BOOLEAN | 出勤しているか |

### StatusHistory（稼働履歴）
1日に1回（閉店時間後）算出する稼働率

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | SERIAL (Primary Key) | レコードID |
| business_id | TEXT | 店舗ID（Business.business_idと関連） |
| date | DATE | 日付 |
| working_rate | DECIMAL | 稼働率(%) |

## 🏗️ システム構成

### バッチ処理システム
```
batch/
├── core/              # コアモジュール
│   ├── database.py   # データベース管理
│   ├── models.py     # データモデル
│   └── scraper.py    # スクレイピング機能
├── jobs/              # バッチジョブ
│   ├── status_collection.py  # ステータス収集（30分間隔）
│   └── working_rate_calculation.py # 稼働率計算（日次）および稼働履歴計算
├── scheduler/         # スケジューラー
│   └── main.py       # メインスケジューラー
└── utils/            # ユーティリティ
    ├── config.py     # 設定管理
    ├── datetime_utils.py  # 日時処理
    └── logging_utils.py   # ログ管理
```

### 設定ファイル
```
config/
├── development.yaml  # 開発環境設定
├── production.yaml   # 本番環境設定
└── testing.yaml     # テスト環境設定
```

## 🚀 セットアップ

1. **依存関係インストール**
   ```bash
   pip install -r requirements.txt
   ```

2. **データベース設定**
   - Supabaseプロジェクトを作成
   - 環境変数またはconfig/production.yamlで接続情報を設定

3. **バッチスケジューラー起動**
   ```bash
   python -m batch.scheduler.main
   ```

## 📈 機能

- **自動スクレイピング**: 店舗の稼働情報を30分間隔で収集
- **稼働率計算**: 日次で稼働率を算出・保存
- **営業時間考慮**: 店舗の営業時間内のみスクレイピング実行
- **エラー処理**: 堅牢なエラーハンドリングとリトライ機能
- **ログ管理**: 詳細なログ出力とローテーション

## 📝 ライセンス

Private Project
