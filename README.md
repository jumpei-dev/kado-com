# 稼働.com - バッチ処理システム

風俗店の稼働状況を自動収集・分析するバッチ処理システム

## 📊 データベース構造

### Business（店舗）
管理者があらかじめ登録しておく店舗マスタ情報

| カラム名 | 型 | 説明 |
|---------|-----|------|
| business_id | BIGINT (Primary Key) | 店舗ID |
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
| id | BIGSERIAL (Primary Key) | レコードID |
| datetime | TIMESTAMP | 取得日時 |
| business_id | BIGINT | 店舗ID（Business.business_idと関連） |
| cast_id | BIGINT | キャストID |
| is_working | BOOLEAN | 稼働しているか |
| is_on_shift | BOOLEAN | 出勤しているか |
| is_dummy | BOOLEAN | テストデータフラグ |

### StatusHistory（稼働履歴）
1日に1回（閉店時間後）算出する稼働率

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | BIGSERIAL (Primary Key) | レコードID |
| business_id | BIGINT | 店舗ID（Business.business_idと関連） |
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

## � 詳細デバッグ機能

### キャスト稼働判定デバッグツール

HTMLを取得してキャストの稼働状況を判定する際の重要なデバッグ機能です。

#### 使用方法
```bash
python3 test_detailed_debug.py
```

#### 出力内容

**1. 基本情報**
- HTML内容長とsugunavi_wrapper要素数
- sugunaviboxでフィルタリングされたキャスト数（期待値: 41人）

**2. 各キャストの詳細分析（出勤中のみ）**
```
🔍 デバッグ詳細出力 - キャスト ID: 60539207
================================================================================
📅 HTML取得時間: 2025-08-25 21:52:50

⏰ 出勤時間情報:
   出勤時間1: '10:30～2:00'
   DOM内容: <p class="time_font_size shadow shukkin_detail_time">...</p>

💼 待機状態表記:
   待機状態1: '次回22:10～'
   DOM内容: <div class="title"><span>次回22:10～</span></div>

📦 sugunavibox全体:
   '次回22:10～合言葉【即姫+10分】今すぐ遊べる女の子選んで+10分GET'

🎯 ソースコード判定結果:
   is_on_shift (出勤中): True
   is_working (稼働中): True

🧮 判定ロジック詳細:
   【出勤判定 (on_shift)】
     '10:30～2:00' → 休み/調整中: False, 時間範囲内: True
   【稼働判定 (is_working)】
     '次回22:10～' → 現在時刻以降: True
       💡 詳細計算: 22:10 - 21:52 = 17.2分後
   最終結果: on_shift=True AND 現在時刻以降=True → is_working=True
```

#### 判定ロジック

**出勤判定 (is_on_shift)**
1. 出勤時間が「お休み」「調整中」等でないか確認
2. 現在時刻が出勤時間範囲内にあるか確認
3. 夜間営業の場合の跨日計算に対応

**稼働判定 (is_working)**
1. 出勤中（is_on_shift=True）が前提条件
2. 待機状態が「次回XX:XX～」形式で未来時刻を示すか確認
3. 「XX:XX ～待機中」（過去時刻）は非稼働として判定
4. 「受付終了」は自動的に非稼働

#### 実際の分析例

**✅ 稼働中パターン**
- `次回22:10～` → 17.2分後 → is_working=True
- `次回23:40～` → 107.2分後 → is_working=True

**❌ 非稼働パターン**
- `21:13 ～待機中` → 39.8分前 → is_working=False
- `受付終了` → title要素なし → is_working=False

このデバッグ機能により、HTML解析とキャスト稼働判定の精度を詳細に検証できます。

## �📈 機能

- **自動スクレイピング**: 店舗の稼働情報を30分間隔で収集
- **稼働率計算**: 日次で稼働率を算出・保存
- **営業時間考慮**: 店舗の営業時間内のみスクレイピング実行
- **エラー処理**: 堅牢なエラーハンドリングとリトライ機能
- **ログ管理**: 詳細なログ出力とローテーション
- **詳細デバッグ**: キャスト稼働判定の詳細分析機能

## 📝 ライセンス

Private Project
