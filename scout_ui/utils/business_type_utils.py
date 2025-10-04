import yaml
import os
from typing import Optional

def load_config() -> dict:
    """設定ファイルを読み込む"""
    config_path = os.path.join(os.path.dirname(__file__), '../../config/config.yml')
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def convert_business_type_to_japanese(business_type: str) -> str:
    """
    業種の英語名を日本語に変換する
    
    Args:
        business_type (str): 英語の業種名
        
    Returns:
        str: 日本語の業種名。マッピングが見つからない場合は「一般」を返す
    """
    try:
        config = load_config()
        business_types_mapping = config.get('business_types', {})
        return business_types_mapping.get(business_type, '一般')
    except Exception as e:
        print(f"業種変換エラー: {e}")
        return '一般'

def get_all_business_types() -> dict:
    """
    すべての業種マッピングを取得する
    
    Returns:
        dict: 業種マッピング辞書
    """
    try:
        config = load_config()
        return config.get('business_types', {})
    except Exception as e:
        print(f"業種マッピング取得エラー: {e}")
        return {}