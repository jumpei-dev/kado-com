"""
テストヘルパー関数
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class TestDataManager:
    """テストデータ管理クラス"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent.parent
        self.fixtures_dir = self.test_dir / "fixtures"
        self.sample_html_dir = self.fixtures_dir / "sample_html"
        self.expected_results_dir = self.fixtures_dir / "expected_results"
    
    def load_sample_html(self, filename: str) -> str:
        """サンプルHTMLファイルを読み込み"""
        file_path = self.sample_html_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"サンプルHTMLファイルが見つかりません: {filename}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_expected_result(self, filename: str) -> Dict[str, Any]:
        """期待される結果を読み込み"""
        file_path = self.expected_results_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"期待結果ファイルが見つかりません: {filename}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_expected_result(self, data: Dict[str, Any], filename: str):
        """期待される結果を保存（テストデータ作成用）"""
        self.expected_results_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.expected_results_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def create_test_business_data() -> Dict[str, Any]:
    """テスト用店舗データを作成"""
    return {
        'business_id': 999999001,  # bigint型に適したテスト用ID
        'Business ID': 999999001,
        'name': 'テスト店舗',
        'Name': 'テスト店舗',
        'media': 'cityhaven',
        'URL': 'https://test.example.com/attend/',
        'cast_type': 'a',
        'working_type': 'a',
        'shift_type': 'a'
    }


def validate_cast_status_data(cast_data: Dict[str, Any]) -> bool:
    """キャストステータスデータの妥当性検証"""
    required_fields = [
        'cast_id', 'business_id', 'is_working', 'is_on_shift', 
        'collected_at', 'name'
    ]
    
    for field in required_fields:
        if field not in cast_data:
            return False
    
    # データ型チェック
    if not isinstance(cast_data['is_working'], bool):
        return False
    if not isinstance(cast_data['is_on_shift'], bool):
        return False
    
    return True
