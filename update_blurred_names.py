#!/usr/bin/env python3
"""
店舗のblurred_name更新スクリプト

このスクリプトは以下の機能を提供します：
1. 既存の店舗名からblurred_nameを自動生成
2. 既存のblurred_nameがある場合はスキップ（オプションで強制更新も可能）
3. CSVファイルからblurred_nameを一括更新
4. 生成ルールのカスタマイズ

使用方法:
python update_blurred_names.py --auto-generate    # 自動生成
python update_blurred_names.py --from-csv data.csv  # CSVから更新
python update_blurred_names.py --preview          # プレビューのみ（実際の更新はしない）
"""

import argparse
import csv
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.absolute()))

try:
    from app.core.database import get_database
except ImportError:
    print("❌ データベース接続モジュールが見つかりません")
    print("このスクリプトはプロジェクトルートから実行してください")
    sys.exit(1)


def generate_blurred_name(original_name: str) -> str:
    """
    店舗名からblurred_nameを生成する
    
    生成ルール:
    - 2文字以下: 全て〇
    - 3-4文字: 最後の1文字以外を〇
    - 5文字以上: 最後の2-3文字以外を〇
    """
    if not original_name:
        return ""
    
    length = len(original_name)
    
    if length <= 2:
        return "〇" * length
    elif length <= 4:
        # 最後の1文字以外をぼかし
        return "〇" * (length - 1) + original_name[-1:]
    else:
        # 長い名前: 最後の2-3文字以外をぼかし
        keep_chars = min(3, length // 2)
        return "〇" * (length - keep_chars) + original_name[-keep_chars:]


def load_blurred_names_from_csv(csv_file_path: str) -> dict:
    """CSVファイルからblurred_nameのマッピングを読み込む"""
    mapping = {}
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            required_columns = ['name', 'blurred_name']
            
            if not all(col in reader.fieldnames for col in required_columns):
                print(f"❌ CSVファイルに必要な列が不足しています: {required_columns}")
                return {}
            
            for row in reader:
                original_name = row['name'].strip()
                blurred_name = row['blurred_name'].strip()
                
                if original_name and blurred_name:
                    mapping[original_name] = blurred_name
                    
        print(f"✅ CSVから {len(mapping)} 件のマッピングを読み込みました")
        return mapping
        
    except FileNotFoundError:
        print(f"❌ CSVファイルが見つかりません: {csv_file_path}")
        return {}
    except Exception as e:
        print(f"❌ CSVファイル読み込みエラー: {e}")
        return {}


def get_stores_data():
    """データベースから店舗データを取得（実際のDB構造に応じて調整が必要）"""
    # TODO: 実際のデータベース構造に合わせて修正
    # 現在はダミーデータを返す
    dummy_stores = [
        {"id": 1, "name": "チュチュバナナ", "blurred_name": None},
        {"id": 2, "name": "ハニービー", "blurred_name": None},
        {"id": 3, "name": "バンサー", "blurred_name": None},
        {"id": 4, "name": "ウルトラグレース", "blurred_name": None},
        {"id": 5, "name": "メルティキス", "blurred_name": None},
        {"id": 6, "name": "ピュアハート", "blurred_name": None},
        {"id": 7, "name": "シャイニーガール", "blurred_name": None},
        {"id": 8, "name": "エンジェルフェザー", "blurred_name": None},
        {"id": 9, "name": "プリンセスルーム", "blurred_name": None},
        {"id": 10, "name": "ルビーパレス", "blurred_name": None},
        {"id": 11, "name": "人妻城", "blurred_name": None},
    ]
    
    return dummy_stores


def update_store_blurred_name(store_id: int, blurred_name: str):
    """店舗のblurred_nameを更新（実際のDB更新処理）"""
    # TODO: 実際のデータベース更新処理を実装
    # 現在はログ出力のみ
    print(f"  📝 店舗ID {store_id} のblurred_nameを更新: {blurred_name}")


def preview_updates(stores_data, csv_mapping=None, force_update=False):
    """更新内容をプレビュー表示"""
    print("\n📋 更新プレビュー:")
    print("-" * 60)
    
    update_count = 0
    skip_count = 0
    
    for store in stores_data:
        store_id = store["id"]
        original_name = store["name"]
        current_blurred = store.get("blurred_name")
        
        # 新しいblurred_nameを決定
        if csv_mapping and original_name in csv_mapping:
            new_blurred = csv_mapping[original_name]
            source = "CSV"
        else:
            new_blurred = generate_blurred_name(original_name)
            source = "自動生成"
        
        # 更新が必要かチェック
        needs_update = force_update or not current_blurred or current_blurred != new_blurred
        
        if needs_update:
            status = "🔄 更新"
            update_count += 1
        else:
            status = "⏭️  スキップ"
            skip_count += 1
        
        print(f"{status} ID:{store_id:3d} | {original_name:15s} → {new_blurred:15s} ({source})")
    
    print("-" * 60)
    print(f"更新対象: {update_count} 件, スキップ: {skip_count} 件")
    
    return update_count


def main():
    parser = argparse.ArgumentParser(description="店舗のblurred_name更新スクリプト")
    parser.add_argument("--auto-generate", action="store_true", 
                       help="自動生成でblurred_nameを更新")
    parser.add_argument("--from-csv", type=str, metavar="CSV_FILE",
                       help="CSVファイルからblurred_nameを読み込んで更新")
    parser.add_argument("--preview", action="store_true",
                       help="プレビューのみ（実際の更新はしない）")
    parser.add_argument("--force", action="store_true",
                       help="既存のblurred_nameも強制更新")
    parser.add_argument("--export-csv", type=str, metavar="OUTPUT_FILE",
                       help="現在の店舗データをCSVにエクスポート")
    
    args = parser.parse_args()
    
    if not any([args.auto_generate, args.from_csv, args.export_csv]):
        parser.print_help()
        return
    
    print("🏪 店舗blurred_name更新ツール")
    print("=" * 50)
    
    # 店舗データを取得
    try:
        stores_data = get_stores_data()
        print(f"📊 {len(stores_data)} 件の店舗データを取得しました")
    except Exception as e:
        print(f"❌ 店舗データ取得エラー: {e}")
        return
    
    # CSVエクスポート
    if args.export_csv:
        try:
            with open(args.export_csv, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['id', 'name', 'blurred_name'])
                writer.writeheader()
                
                for store in stores_data:
                    writer.writerow({
                        'id': store['id'],
                        'name': store['name'],
                        'blurred_name': store.get('blurred_name', '')
                    })
            
            print(f"✅ CSVファイルにエクスポート完了: {args.export_csv}")
            return
            
        except Exception as e:
            print(f"❌ CSVエクスポートエラー: {e}")
            return
    
    # CSVからマッピングを読み込み
    csv_mapping = None
    if args.from_csv:
        csv_mapping = load_blurred_names_from_csv(args.from_csv)
        if not csv_mapping:
            return
    
    # プレビュー表示
    update_count = preview_updates(stores_data, csv_mapping, args.force)
    
    if update_count == 0:
        print("✅ 更新が必要な店舗はありません")
        return
    
    # プレビューモードの場合はここで終了
    if args.preview:
        print("\n👀 プレビューモードのため、実際の更新は行いません")
        return
    
    # 確認プロンプト
    print(f"\n❓ {update_count} 件の店舗を更新しますか？ (y/N): ", end="")
    if input().lower() != 'y':
        print("❌ 更新をキャンセルしました")
        return
    
    # 実際の更新処理
    print("\n🔄 更新を開始します...")
    updated_count = 0
    
    for store in stores_data:
        store_id = store["id"]
        original_name = store["name"]
        current_blurred = store.get("blurred_name")
        
        # 新しいblurred_nameを決定
        if csv_mapping and original_name in csv_mapping:
            new_blurred = csv_mapping[original_name]
        else:
            new_blurred = generate_blurred_name(original_name)
        
        # 更新が必要かチェック
        needs_update = args.force or not current_blurred or current_blurred != new_blurred
        
        if needs_update:
            try:
                update_store_blurred_name(store_id, new_blurred)
                updated_count += 1
            except Exception as e:
                print(f"❌ ID {store_id} の更新エラー: {e}")
    
    print(f"\n✅ 更新完了: {updated_count} 件の店舗を更新しました")


if __name__ == "__main__":
    main()
