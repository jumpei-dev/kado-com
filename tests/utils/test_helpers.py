"""
テストヘルパー関数とユーティリティ
"""
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class TestDataManager:
    """テストデータ管理クラス"""
    
    def __init__(self):
        self.sample_html_dir = "data/raw_html/cityhaven"
        self.expected_results_dir = "tests/fixtures/expected_results"
    
    def get_sample_html_path(self, filename: str) -> str:
        """サンプルHTMLファイルのパスを取得"""
        return f"{self.sample_html_dir}/{filename}"
    
    def get_expected_result_path(self, filename: str) -> str:
        """期待結果ファイルのパスを取得"""
        return f"{self.expected_results_dir}/{filename}"


def create_test_business_data() -> Dict[str, Any]:
    """テスト用店舗データを作成（実在のDB店舗を使用）"""
    return {
        'business_id': 1,  # 実際のDB: 関内人妻城
        'name': '関内人妻城',
        'area': 'テストエリア',
        'prefecture': '神奈川県',
        'type': 'テスト業種',
        'capacity': 10,
        'open_hour': '10:00',
        'close_hour': '02:00',
        'schedule_url1': 'https://test.example.com'
    }


def validate_cast_status_data(cast_data: Dict[str, Any]) -> bool:
    """キャストステータスデータの妥当性を検証"""
    required_fields = ['cast_id', 'business_id', 'is_working', 'is_on_shift', 'collected_at']
    
    # 必須フィールドチェック
    for field in required_fields:
        if field not in cast_data:
            logger.warning(f"必須フィールド不足: {field}")
            return False
    
    # データ型チェック
    if not isinstance(cast_data['cast_id'], (int, str)):
        logger.warning(f"cast_id型エラー: {type(cast_data['cast_id'])}")
        return False
    
    if not isinstance(cast_data['business_id'], (int, str)):
        logger.warning(f"business_id型エラー: {type(cast_data['business_id'])}")
        return False
    
    if not isinstance(cast_data['is_working'], bool):
        logger.warning(f"is_working型エラー: {type(cast_data['is_working'])}")
        return False
    
    if not isinstance(cast_data['is_on_shift'], bool):
        logger.warning(f"is_on_shift型エラー: {type(cast_data['is_on_shift'])}")
        return False
    
    return True


def create_test_cast_data(count: int = 5) -> List[Dict[str, Any]]:
    """テスト用キャストデータを作成"""
    test_casts = []
    base_time = datetime.now()
    
    for i in range(count):
        cast_data = {
            'cast_id': 999990000 + i,  # テスト用BIGINT ID
            'business_id': 999999001,
            'name': f'テストキャスト{i+1}',
            'is_working': i % 2 == 0,  # 交互にTrue/False
            'is_on_shift': True,
            'collected_at': base_time,
            'shift_times': [f'{10+i}:00-{20+i}:00'],
            'working_times': None
        }
        test_casts.append(cast_data)
    
    return test_casts


def assert_cast_data_equals(actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
    """キャストデータの比較"""
    important_fields = ['cast_id', 'business_id', 'is_working', 'is_on_shift']
    
    for field in important_fields:
        if actual.get(field) != expected.get(field):
            logger.error(f"フィールド不一致 {field}: actual={actual.get(field)} vs expected={expected.get(field)}")
            return False
    
    return True
