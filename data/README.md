# Data Directory

このディレクトリには稼働.comシステムで収集・処理されるデータファイルが格納されます。

## ディレクトリ構成

```
data/
├── raw_html/         # 取得したHTMLファイル
│   ├── cityhaven/   # CityHeaven HTMLデータ
│   │   ├── shop1_cast_list_20250905_121012.html
│   │   ├── shop2_cast_list_20250905_131435.html
│   │   └── ...
│   └── deliher_town/ # デリヘルタウン HTMLデータ
├── parsed_data/     # 解析済みデータ（JSON形式）
│   ├── shop1_cast_list_analysis_20250905_121012.json
│   └── ...
└── test_samples/    # テスト用サンプルデータ
```

## HTMLファイル命名規則

### CityHeaven
```
{店舗名}_cast_list_{YYYYMMDD}_{HHMMSS}.html
```
例：`nasu-kadan_cast_list_20250905_215657.html`

### 解析済みデータ
```
{店舗名}_cast_list_analysis_{YYYYMMDD}_{HHMMSS}.json
```

## 使用方法

### HTMLファイル取得
```bash
# URLからHTMLを取得・保存
python batch/main.py debug-html --url "https://www.cityheaven.net/example/attend/"
```

### ローカルHTMLファイル解析
```bash
# 保存済みHTMLファイルを解析
python batch/main.py debug-html --local-file "nasu-kadan_cast_list_20250905_215657.html"
```

## 注意事項

- HTMLファイルは自動的に`data/raw_html/cityhaven/`に保存されます
- 解析結果は`data/parsed_data/`に保存されます
- テスト用データは`data/test_samples/`に配置してください

詳細な使用方法は `/Users/admin/Projects/kado-com/README.md` を参照してください。