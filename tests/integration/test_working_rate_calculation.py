"""
Working Rate Calculation統合テスト
business id 1、2025年9月5日のworking rateを計算するテスト
"""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
batch_dir = project_root / "batch"
sys.path.insert(0, str(batch_dir))

# バッチモジュールをインポート
from jobs.working_rate_calculation import run_working_rate_calculation
from core.database import DatabaseManager

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WorkingRateCalculationTest:
    """Working Rate Calculation統合テストクラス"""
    
    def __init__(self):
        # run_working_rate_calculation関数を直接使用するため、個別のインスタンスは不要
        pass
    
    async def run_working_rate_test(self, business_id: int, target_date: date) -> Dict[str, Any]:
        """
        Working Rate Calculation統合テスト実行
        
        Args:
            business_id: 対象店舗ID
            target_date: 計算対象日付
        
        Returns:
            テスト結果の詳細データ
        """
        print(f"\n📊 Working Rate Calculation統合テスト開始")
        print(f"📅 対象日付: {target_date}")
        print(f"🏪 対象店舗ID: {business_id}")
        
        test_result = {
            'business_id': business_id,
            'target_date': target_date,
            'test_timestamp': datetime.now(),
            'success': False,
            'working_rate': None,
            'status_record_count': 0,
            'on_shift_count': 0,
            'working_count': 0,
            'business_info': None,
            'error_message': None,
            'calculation_result': None
        }
        
        try:
            # Step 1: 店舗情報確認
            print("🏪 Step 1: 店舗情報確認")
            db_manager = DatabaseManager()
            business_query = "SELECT * FROM business WHERE business_id = %s"
            businesses = db_manager.execute_query(business_query, (business_id,))
            if not businesses:
                raise ValueError(f"Business ID {business_id} が見つかりません")
            
            business_info = businesses[0]
            test_result['business_info'] = dict(business_info)
            print(f"✅ 店舗情報取得: {business_info['name']}")
            print(f"   営業時間: {business_info['open_hour']} - {business_info['close_hour']}")
            print(f"   InScope: {business_info['in_scope']}")
            
            # Step 2: statusデータ確認
            print("📊 Step 2: statusデータ確認")
            status_query = """
                SELECT COUNT(*) as total_count, 
                       COUNT(CASE WHEN is_working = true THEN 1 END) as working_count,
                       COUNT(CASE WHEN is_on_shift = true THEN 1 END) as on_shift_count
                FROM status 
                WHERE business_id = %s 
                AND DATE(recorded_at) = %s
            """
            status_stats = db_manager.execute_query(status_query, (business_id, target_date))
            if status_stats:
                stats = status_stats[0]
                test_result['status_record_count'] = stats['total_count']
                test_result['on_shift_count'] = stats['on_shift_count']
                test_result['working_count'] = stats['working_count']
                
                print(f"✅ statusデータ確認完了:")
                print(f"   総レコード数: {stats['total_count']}")
                print(f"   出勤中レコード数: {stats['on_shift_count']}")
                print(f"   稼働中レコード数: {stats['working_count']}")
            
            # Step 3: 既存のstatus_history確認
            print("📈 Step 3: 既存のstatus_history確認")
            history_query = "SELECT * FROM status_history WHERE business_id = %s AND biz_date = %s"
            existing_history = db_manager.execute_query(history_query, (business_id, target_date))
            if existing_history:
                print(f"⚠️  既存のstatus_historyデータあり: {existing_history[0]['working_rate']}%")
                print("   削除してから新規計算を実行します")
                # 既存データを削除
                delete_query = "DELETE FROM status_history WHERE business_id = %s AND biz_date = %s"
                db_manager.execute_command(delete_query, (business_id, target_date))
                print("✅ 既存データ削除完了")
            else:
                print("✅ status_historyに既存データなし")
            
            # Step 4: working rate計算実行
            print("🧮 Step 4: working rate計算実行")
            calculation_result = await run_working_rate_calculation(
                target_date=target_date,
                force=True  # 強制実行
            )
            
            test_result['calculation_result'] = {
                'success': calculation_result.success,
                'processed_count': calculation_result.processed_count,
                'error_count': calculation_result.error_count,
                'errors': calculation_result.errors,
                'duration_seconds': calculation_result.duration_seconds,
                'calculated_businesses': calculation_result.calculated_businesses
            }
            
            if calculation_result.success:
                print(f"✅ working rate計算完了:")
                print(f"   処理店舗数: {calculation_result.processed_count}")
                print(f"   エラー数: {calculation_result.error_count}")
                print(f"   実行時間: {calculation_result.duration_seconds:.2f}秒")
            else:
                print(f"❌ working rate計算失敗:")
                for error in calculation_result.errors:
                    print(f"   エラー: {error}")
            
            # Step 5: 計算結果確認
            print("📋 Step 5: 計算結果確認")
            result_history = db_manager.execute_query(history_query, (business_id, target_date))
            if result_history:
                working_rate = result_history[0]['working_rate']
                test_result['working_rate'] = working_rate
                print(f"✅ 計算結果取得成功: {working_rate}%")
                
                # 手動計算で検証
                if test_result['on_shift_count'] > 0:
                    manual_rate = (test_result['working_count'] / test_result['on_shift_count']) * 100
                    print(f"🔍 手動計算検証: {manual_rate:.2f}%")
                    print(f"   計算式: {test_result['working_count']} / {test_result['on_shift_count']} * 100")
                else:
                    print("🔍 手動計算検証: 出勤中レコードなし、稼働率0%")
                
                test_result['success'] = True
            else:
                print("❌ 計算結果がstatus_historyに保存されていません")
            
        except Exception as e:
            test_result['error_message'] = str(e)
            print(f"❌ 統合テストエラー: {e}")
            logger.error(f"詳細: {str(e)}", exc_info=True)
        
        return test_result
    
    def print_test_summary(self, test_result: Dict[str, Any]):
        """テスト結果サマリーを表示"""
        print("\n" + "=" * 60)
        print("📊 Working Rate Calculation テスト結果サマリー")
        print("=" * 60)
        print(f"🏪 店舗: {test_result['business_info']['name'] if test_result['business_info'] else 'Unknown'}")
        print(f"📅 対象日付: {test_result['target_date']}")
        print(f"📅 実行時刻: {test_result['test_timestamp']}")
        print(f"✅ 成功: {'Yes' if test_result['success'] else 'No'}")
        
        if test_result['working_rate'] is not None:
            print(f"📈 稼働率: {test_result['working_rate']}%")
        
        print(f"📊 データ統計:")
        print(f"   総レコード数: {test_result['status_record_count']}")
        print(f"   出勤中レコード数: {test_result['on_shift_count']}")
        print(f"   稼働中レコード数: {test_result['working_count']}")
        
        if test_result['calculation_result']:
            calc_result = test_result['calculation_result']
            print(f"🧮 計算処理:")
            print(f"   処理店舗数: {calc_result['processed_count']}")
            print(f"   エラー数: {calc_result['error_count']}")
            print(f"   実行時間: {calc_result['duration_seconds']:.2f}秒")
        
        if test_result['error_message']:
            print(f"🚨 実行エラー: {test_result['error_message']}")
        
        print("=" * 60)


def run_test(business_id: int, target_date: date):
    """テスト実行関数"""
    test_integration = WorkingRateCalculationTest()
    
    # 統合テスト実行（非同期）
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            test_integration.run_working_rate_test(business_id, target_date)
        )
    finally:
        loop.close()
    
    # 結果表示
    test_integration.print_test_summary(result)
    
    return result


if __name__ == "__main__":
    # デフォルト値の設定
    business_id = 1  # 関内人妻城
    target_date = date(2025, 9, 5)  # 2025年9月5日
    
    # コマンドライン引数がある場合はそれを使用
    if len(sys.argv) >= 2:
        business_id = int(sys.argv[1])
    if len(sys.argv) >= 3:
        target_date = datetime.strptime(sys.argv[2], '%Y-%m-%d').date()
    
    print(f"🧪 Working Rate Calculation統合テスト")
    print(f"📅 対象: Business ID {business_id}, {target_date}")
    
    # テスト実行
    result = run_test(business_id, target_date)
    
    if result['success']:
        print("\n🎉 統合テスト成功!")
        sys.exit(0)
    else:
        print("\n💥 統合テスト失敗!")
        sys.exit(1)
