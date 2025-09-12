"""
blurred_name機能のためのユーティリティ関数

このモジュールは以下の機能を提供します：
- 店舗名のぼかし処理ルール
- 権限に応じた表示名の決定
- DB統合のためのヘルパー関数
"""

from typing import Dict, Any, Optional


def generate_blurred_name(original_name: str) -> str:
    """
    店舗名からblurred_nameを自動生成する
    
    Args:
        original_name: 元の店舗名
        
    Returns:
        ぼかし処理された店舗名
        
    Rules:
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


def get_store_display_info(store_data: Dict[str, Any], can_see_contents: bool) -> Dict[str, Any]:
    """
    権限に応じて適切な店舗名表示情報を返す
    
    Args:
        store_data: 店舗データ（name, blurred_nameを含む）
        can_see_contents: ユーザーがコンテンツを閲覧可能かどうか
        
    Returns:
        表示用の店舗名情報
        - display_name: 実際に表示する名前
        - original_name: 元の店舗名
        - blurred_name: ぼかし処理された名前
        - is_blurred: ぼかし表示されているかどうか
    """
    original_name = store_data.get("name", "")
    blurred_name = store_data.get("blurred_name")
    
    # blurred_nameが設定されていない場合は自動生成
    if not blurred_name:
        blurred_name = generate_blurred_name(original_name)
    
    if can_see_contents:
        return {
            "display_name": original_name,
            "original_name": original_name,
            "blurred_name": blurred_name,
            "is_blurred": False
        }
    else:
        return {
            "display_name": blurred_name,
            "original_name": original_name,
            "blurred_name": blurred_name,
            "is_blurred": True
        }


def apply_blurred_names_to_stores(stores_list: list, can_see_contents: bool) -> list:
    """
    店舗リストに対してblurred_name処理を一括適用
    
    Args:
        stores_list: 店舗データのリスト
        can_see_contents: ユーザーがコンテンツを閲覧可能かどうか
        
    Returns:
        blurred_name処理が適用された店舗リスト
    """
    processed_stores = []
    
    for store in stores_list:
        # 店舗の表示情報を取得
        display_info = get_store_display_info(store, can_see_contents)
        
        # 元の店舗データをコピーして表示情報を追加
        processed_store = store.copy()
        processed_store.update({
            "name": display_info["display_name"],
            "original_name": display_info["original_name"],
            "blurred_name": display_info["blurred_name"],
            "is_blurred": display_info["is_blurred"]
        })
        
        processed_stores.append(processed_store)
    
    return processed_stores


def validate_blurred_name(original_name: str, blurred_name: str) -> Dict[str, Any]:
    """
    blurred_nameの妥当性をチェック
    
    Args:
        original_name: 元の店舗名
        blurred_name: ぼかし処理された名前
        
    Returns:
        バリデーション結果
        - is_valid: 妥当性
        - errors: エラーメッセージのリスト
        - suggestions: 推奨値
    """
    errors = []
    
    if not original_name:
        errors.append("元の店舗名が空です")
    
    if not blurred_name:
        errors.append("blurred_nameが空です")
    
    if original_name and blurred_name:
        # 長さチェック
        if len(blurred_name) != len(original_name):
            errors.append(f"長さが一致しません (元: {len(original_name)}, ぼかし: {len(blurred_name)})")
        
        # 〇以外の文字が元の名前と一致するかチェック
        for i, char in enumerate(blurred_name):
            if char != "〇" and i < len(original_name):
                if char != original_name[i]:
                    errors.append(f"位置 {i+1} の文字が元の名前と一致しません (元: '{original_name[i]}', ぼかし: '{char}')")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "suggestions": generate_blurred_name(original_name) if original_name else ""
    }


def get_blurred_name_statistics(stores_list: list) -> Dict[str, Any]:
    """
    blurred_name設定状況の統計を取得
    
    Args:
        stores_list: 店舗データのリスト
        
    Returns:
        統計情報
    """
    total_stores = len(stores_list)
    has_blurred = 0
    needs_generation = 0
    validation_errors = 0
    
    for store in stores_list:
        original_name = store.get("name", "")
        blurred_name = store.get("blurred_name", "")
        
        if blurred_name:
            has_blurred += 1
            # バリデーションチェック
            validation = validate_blurred_name(original_name, blurred_name)
            if not validation["is_valid"]:
                validation_errors += 1
        else:
            needs_generation += 1
    
    return {
        "total_stores": total_stores,
        "has_blurred_name": has_blurred,
        "needs_generation": needs_generation,
        "validation_errors": validation_errors,
        "completion_rate": (has_blurred / total_stores * 100) if total_stores > 0 else 0
    }


# 使用例とテストケース
if __name__ == "__main__":
    # テストケース
    test_cases = [
        "チュチュバナナ",
        "ハニービー", 
        "バンサー",
        "ウルトラグレース",
        "人妻城",
        "A",
        "AB",
        "ABC"
    ]
    
    print("🧪 blurred_name生成テスト")
    print("-" * 40)
    
    for name in test_cases:
        blurred = generate_blurred_name(name)
        validation = validate_blurred_name(name, blurred)
        status = "✅" if validation["is_valid"] else "❌"
        
        print(f"{status} {name:15s} → {blurred:15s}")
        if not validation["is_valid"]:
            for error in validation["errors"]:
                print(f"    ⚠️ {error}")
    
    print("\n🔍 表示情報テスト")
    print("-" * 40)
    
    sample_store = {
        "name": "エンジェルフェザー",
        "blurred_name": "〇〇〇〇〇フェザー"
    }
    
    # 権限ありの場合
    display_with_permission = get_store_display_info(sample_store, True)
    print(f"権限あり: {display_with_permission}")
    
    # 権限なしの場合  
    display_without_permission = get_store_display_info(sample_store, False)
    print(f"権限なし: {display_without_permission}")
