# 稼働.com - バッチ処理システム

風俗店の稼働状況を自動収集・分析するバッチ処理システム

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

## 🏗️ **システム構成**

### バッチ処理システム
```
batch/
├── core/              # コアモジュール
│   ├── database.py   # データベース管理
│   ├── models.py     # データモデル
│   └── scraper.py    # スクレイピング機能
├── jobs/              # バッチジョブ
│   ├── status_collection/    # ステータス収集（30分間隔）
│   │   ├── collector.py     # 収集メイン処理
│   │   ├── cityheaven_parsers.py  # 🔧 HTML解析（受付終了判定付き）
│   │   ├── cityheaven_strategy.py # 戦略パターン
│   │   ├── database_saver.py      # DB保存処理
│   │   ├── html_loader.py         # HTML取得
│   │   └── webdriver_manager.py   # WebDriver管理
│   └── working_rate_calculation/  # 稼働率計算（日次）
│       ├── calculator.py          # 🔧 計算統合（capacity対応）
│       ├── rate_calculator.py     # 🔧 稼働率計算（capacity補正）
│       ├── data_retriever.py      # データ取得
│       ├── history_saver.py       # 履歴保存
│       └── models.py              # データモデル
├── schedulers/        # スケジューラー
│   ├── batch_scheduler.py         # メインスケジューラー
│   ├── status_collection_scheduler.py  # 収集スケジューラー
│   └── working_rate_scheduler.py      # 稼働率スケジューラー
├── tests/             # テスト
│   ├── integration/   # 統合テスト
│   │   ├── test_html_to_db.py           # HTML→DB統合テスト
│   │   └── test_working_rate_calculation.py  # 稼働率計算テスト
│   └── utils/         # テストユーティリティ
├── utils/            # ユーティリティ
│   ├── config.py     # 設定管理
│   ├── datetime_utils.py  # 日時処理
│   └── logging_utils.py   # ログ管理
└── main.py           # 🔧 CLIエントリーポイント（新機能コマンド付き）
```

### データディレクトリ
```
data/
├── raw_html/         # 取得したHTMLファイル
│   ├── cityhaven/   # CityHeaven HTMLデータ
│   └── deliher_town/ # デリヘルタウン HTMLデータ
├── parsed_data/     # 解析済みデータ
└── test_samples/    # テスト用サンプル
```

### 設定ファイル
```
config/
├── development.yaml  # 開発環境設定
├── production.yaml   # 本番環境設定
└── testing.yaml     # テスト環境設定
```

## 🚀 **セットアップ**

1. **依存関係インストール**
   ```bash
   pip install -r requirements.txt
   ```

2. **データベース設定**
   - Supabaseプロジェクトを作成
   - 環境変数またはconfig/production.yamlで接続情報を設定

3. **バッチスケジューラー起動**
   ```bash
   python batch/main.py status-collection  # 稼働状況収集スケジューラー
   python batch/main.py working-rate       # 稼働率計算スケジューラー
   ```

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

## 📈 **機能**

- **🔧 自動スクレイピング**: 店舗の稼働情報を30分間隔で収集（受付終了判定付き）
- **🔧 capacity補正稼働率計算**: ソープランド店舗の物理的制約を考慮した正確な稼働率算出
- **営業時間考慮**: 店舗の営業時間内のみスクレイピング実行
- **エラー処理**: 堅牢なエラーハンドリングとリトライ機能
- **ログ管理**: 詳細なログ出力とローテーション
- **🔧 詳細デバッグ**: キャスト稼働判定の詳細分析機能（DOM確認モード）
- **🔧 テスト機能**: 店舗設定の一時変更とテスト機能

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

## 📝 **ライセンス**

Private Project

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
