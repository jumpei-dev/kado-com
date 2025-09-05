"""
DB統合テスト - HTML読み込み→解析→本番DB保存
"""
import asyncio
import sys
from pathlib import Path
from datetime i        # Step 4: 本番DB保存（is_dummy=trueで安全保存）
        print("🗃️ Step 4: 本番DB保存（is_dummy=true）")
        saved_count = 0
        try:
            for cast_status in valid_cast_data:
                try:
                    db_result = self.db_manager.insert_status(
                        business_id=business_data['business_id'],
                        cast_id=cast_status['cast_id'],
                        is_working=cast_status['is_working'],
                        is_on_shift=cast_status['is_on_shift'],
                        collected_at=cast_status['collected_at'],
                        is_dummy=True  # テスト保存フラグ
                    )
                    
                    if db_result:
                        saved_count += 1
                        logger.debug(f"✅ キャスト {cast_status['cast_id']} 保存成功")m typing import List, Dict, Any
import logging

# テスト用パス設定
test_dir = Path(__file__).parent
batch_dir = test_dir.parent
sys.path.insert(0, str(batch_dir))

# バッチモジュールをインポート
from jobs.status_collection.cityheaven_parsers import CityheavenTypeAAAParser
from jobs.status_collection.html_loader import HTMLLoader
from core.database import DatabaseManager
from tests.utils.test_helpers import TestDataManager, create_test_business_data, validate_cast_status_data

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDBIntegration:
    """DB統合テストクラス"""
    
    def __init__(self):
        self.test_data_manager = TestDataManager()
        self.db_manager = DatabaseManager()
        self.parser = CityheavenTypeAAAParser()
    
    async def test_html_to_db_integration(self, html_file: str, business_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        HTML読み込み→解析→本番DB保存の統合テスト
        
        Args:
            html_file: テスト対象のHTMLファイル名
            business_data: 店舗データ（Noneの場合はデフォルトを使用）
        
        Returns:
            テスト結果の詳細データ
        """
        print(f"\n🧪 DB統合テスト開始: {html_file}")
        
        if business_data is None:
            business_data = create_test_business_data()
        
        test_result = {
            'html_file': html_file,
            'business_data': business_data,
            'test_timestamp': datetime.now(),
            'success': False,
            'parse_count': 0,
            'save_count': 0,
            'validation_errors': [],
            'error_message': None,
            'cast_data': []
        }
        
        try:
            # Step 1: HTML読み込み
            print("📄 Step 1: HTML読み込み")
            html_loader = HTMLLoader(use_local_html=True)
            html_content, html_timestamp = await html_loader.load_html_content(
                business_name=business_data['name'],
                business_id=business_data['business_id'],
                local_file=html_file
            )
            print(f"✅ HTMLファイル読み込み完了: {len(html_content):,}文字")
            
            # Step 2: HTML解析
            print("🔍 Step 2: HTML解析")
            cast_statuses = await self.parser.parse_cast_list(html_content, html_timestamp, False, business_data['business_id'])
            test_result['parse_count'] = len(cast_statuses)
            print(f"✅ 解析完了: {len(cast_statuses)}件のキャストデータ")
            
            # Step 3: データ妥当性検証
            print("✔️ Step 3: データ妥当性検証")
            valid_cast_data = []
            for cast_status in cast_statuses:
                # cast_statusは既に辞書型として返される
                cast_dict = {
                    'cast_id': cast_status['cast_id'],
                    'business_id': cast_status['business_id'],
                    'name': cast_status.get('name', 'Unknown'),
                    'is_working': cast_status['is_working'],
                    'is_on_shift': cast_status['is_on_shift'],
                    'collected_at': cast_status['collected_at'],
                    'shift_times': cast_status.get('shift_times', None),
                    'working_times': cast_status.get('working_times', None)
                }
                
                if validate_cast_status_data(cast_dict):
                    valid_cast_data.append(cast_dict)
                else:
                    test_result['validation_errors'].append(f"キャスト{cast_status['cast_id']}: データ妥当性エラー")
            
            test_result['cast_data'] = valid_cast_data
            print(f"✅ 妥当性検証完了: {len(valid_cast_data)}件が有効")
            
            # Step 4: 本番DB保存（is_dummy=trueで安全保存）
            print("🗃️ Step 4: 本番DB保存（is_dummy=true）")
            saved_count = 0
            
            for cast_status in valid_cast_data:
                try:
                    db_result = await self.db_manager.insert_status(
                        business_id=business_data['business_id'],
                        cast_id=cast_status['cast_id'],
                        is_working=cast_status['is_working'],
                        is_on_shift=cast_status['is_on_shift'],
                        collected_at=cast_status['collected_at'],
                        is_dummy=True  # テスト保存フラグ
                    )
                    
                    if db_result:
                        saved_count += 1
                        logger.debug(f"✅ キャスト {cast_status['cast_id']} 保存成功")
                except Exception as cast_error:
                    logger.error(f"❌ キャスト保存エラー: {cast_error}")
                    continue
            
            test_result['save_count'] = saved_count
            test_result['success'] = True
            print(f"✅ DB保存完了: {saved_count}件保存")
            
        except Exception as e:
            test_result['error_message'] = str(e)
            print(f"❌ 統合テストエラー: {e}")
            logger.error(f"詳細: {str(e)}", exc_info=True)
        
        return test_result
    
    def print_test_summary(self, test_result: Dict[str, Any]):
        """テスト結果サマリーを表示"""
        print("\n" + "=" * 60)
        print("🧪 DB統合テスト結果サマリー")
        print("=" * 60)
        print(f"📄 ファイル: {test_result['html_file']}")
        print(f"🏪 店舗: {test_result['business_data']['name']}")
        print(f"📅 実行時刻: {test_result['test_timestamp']}")
        print(f"✅ 成功: {'Yes' if test_result['success'] else 'No'}")
        print(f"🔍 解析件数: {test_result['parse_count']}件")
        print(f"💾 保存件数: {test_result['save_count']}件")
        
        if test_result['error_message']:
            print(f"🚨 実行エラー: {test_result['error_message']}")
        
        if test_result['validation_errors']:
            print(f"⚠️ 検証エラー: {len(test_result['validation_errors'])}件")
        
        print("=" * 60)


async def run_integration_test(html_file: str):
    """統合テスト実行"""
    test_integration = TestDBIntegration()
    
    # テストデータ作成
    business_data = create_test_business_data()
    
    # 統合テスト実行
    result = await test_integration.test_html_to_db_integration(html_file, business_data)
    
    # 結果表示
    test_integration.print_test_summary(result)
    
    return result


if __name__ == "__main__":
    # コマンドライン引数チェック
    if len(sys.argv) < 2:
        print("❌ エラー: HTMLファイル名を指定してください")
        print("使用例: python test_db_integration.py k-hitodumajo_cast_list_20250905_121012.html")
        sys.exit(1)
    
    html_file = sys.argv[1]
    
    # テスト実行
    result = asyncio.run(run_integration_test(html_file))
    
    if result['success']:
        print("\n🎉 統合テスト成功!")
        sys.exit(0)
    else:
        print("\n💥 統合テスト失敗!")
        sys.exit(1)
