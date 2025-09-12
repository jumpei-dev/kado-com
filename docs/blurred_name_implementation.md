# blurred_name機能の実装

このドキュメントでは、店舗名のぼかし表示機能（blurred_name）の実装について説明します。

## 概要

blurred_name機能は、ユーザーの権限に応じて店舗名を部分的に隠す機能です。
`can_see_contents=false` のユーザーには店舗名が「〇〇〇〇フェザー」のような形で表示されます。

## 実装方針の変更

### 従来の実装（動的生成）
- リクエストのたびに店舗名からblurred_nameを動的生成
- パフォーマンスが悪く、一貫性に欠ける

### 新しい実装（DB事前保存）
- データベースに事前にblurred_nameを保存
- パフォーマンス向上と表示の一貫性を実現
- 必要に応じて手動調整も可能

## ファイル構成

```
app/
├── api/
│   ├── auth.py          # /me エンドポイント追加
│   └── stores.py        # 権限チェック統合、動的生成削除
├── utils/
│   └── blurred_name_utils.py  # ユーティリティ関数
└── templates/components/
    ├── store_card.html    # 権限表示アイコン追加
    └── store_detail.html  # 権限表示アイコン追加

data/
└── blurred_names_template.csv  # CSVテンプレート

update_blurred_names.py     # 更新スクリプト
```

## 主な変更内容

### 1. auth.py - 権限チェックエンドポイント追加

```python
@router.get("/me")
async def get_current_user(request: Request) -> dict:
    """現在のユーザー情報を取得"""
    # クッキーからトークンを取得してユーザー権限を返す
```

### 2. stores.py - DB値使用への変更

```python
# 動的生成関数を削除
# def apply_name_blurring(name: str, can_see_contents: bool) -> dict:

# DB値を使用する新しい関数
from app.utils.blurred_name_utils import get_store_display_info
```

### 3. blurred_name_utils.py - ユーティリティ関数

- `generate_blurred_name()`: 自動生成ルール
- `get_store_display_info()`: 権限に応じた表示名決定
- `validate_blurred_name()`: バリデーション
- `get_blurred_name_statistics()`: 設定状況統計

### 4. update_blurred_names.py - 更新スクリプト

```bash
# 自動生成でプレビュー
python update_blurred_names.py --auto-generate --preview

# CSVから更新
python update_blurred_names.py --from-csv data/blurred_names_template.csv

# 現在の状況をCSVエクスポート
python update_blurred_names.py --export-csv current_stores.csv
```

## ぼかし処理ルール

| 文字数 | ルール | 例 |
|--------|---------|-----|
| 1-2文字 | 全て〇 | `AB` → `〇〇` |
| 3-4文字 | 最後1文字以外〇 | `ABC` → `〇〇C` |
| 5文字以上 | 最後2-3文字以外〇 | `エンジェルフェザー` → `〇〇〇〇〇フェザー` |

## 権限による表示制御

### can_see_contents = true の場合
- `display_name`: 元の店舗名
- `is_blurred`: false
- アイコン表示なし

### can_see_contents = false の場合
- `display_name`: blurred_name
- `is_blurred`: true  
- 🔒 アイコン表示

## テンプレートでの使用方法

```html
<!-- 店舗名表示 -->
<h3>{{ store.name }}</h3>

<!-- 権限制限アイコン -->
{% if store.is_blurred %}
<div class="bg-orange-100 text-orange-600" title="権限が必要です">
  <svg>🔒</svg>
</div>
{% endif %}
```

## データ更新手順

### 1. 現在の状況確認
```bash
python update_blurred_names.py --auto-generate --preview
```

### 2. CSVでカスタマイズ（必要に応じて）
```bash
# 現在のデータをエクスポート
python update_blurred_names.py --export-csv stores.csv

# stores.csvを編集してblurred_nameをカスタマイズ

# カスタマイズしたCSVから更新
python update_blurred_names.py --from-csv stores.csv --preview
```

### 3. 実際の更新実行
```bash
python update_blurred_names.py --auto-generate  # 確認プロンプトあり
```

## 動作確認

### 1. ユーティリティ関数のテスト
```bash
python app/utils/blurred_name_utils.py
```

### 2. アプリケーション起動
```bash
python run_app.py
```

### 3. 確認ポイント
- ログアウト状態で店舗一覧を確認（ぼかし表示になっているか）
- ログイン後に店舗一覧を確認（元の名前が表示されるか）
- 🔒 アイコンが適切に表示されるか

## トラブルシューティング

### blurred_nameが表示されない
1. ユーザーの`can_see_contents`フラグを確認
2. `/api/auth/me`エンドポイントの応答確認
3. JavaScriptの権限チェック動作確認

### 更新スクリプトエラー
1. データベース接続確認
2. CSVファイルの形式確認（UTF-8, カンマ区切り）
3. 権限・パス確認

### パフォーマンス問題
- DBのblurred_nameフィールドにインデックス追加を検討
- キャッシュ機能の追加を検討

## 今後の拡張予定

1. **詳細権限制御**: 店舗ごとの個別権限設定
2. **動的ぼかしレベル**: ユーザーレベルに応じたぼかし強度
3. **ログ機能**: blurred_name表示の監査ログ
4. **管理画面**: blurred_nameの一括編集インターフェース
