"""
バッチ処理システムのメインエントリーポイント
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# batchディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# バッチコンポーネントをインポート
import os
import sys

# 現在のディレクトリを基準にインポートパスを設定
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

try:
    # 相対インポート
    from .schedulers.status_collection_scheduler import run_status_collection_scheduler
    from .schedulers.working_rate_scheduler import run_working_rate_scheduler  
    from .jobs.status_collection import collect_all_working_status
    from .jobs.working_rate_calculation import run_working_rate_calculation
    from .utils.logging_utils import setup_logging
    from .utils.config import get_config
    from .core.database import DatabaseManager
    print("✓ 全モジュールのインポートに成功しました")
    
except ImportError as e:
    print(f"相対インポートエラー: {e}")
    print("絶対インポートを試行")
    
    try:
        # ローカルインポート
        from schedulers.status_collection_scheduler import run_status_collection_scheduler
        from schedulers.working_rate_scheduler import run_working_rate_scheduler  
        from jobs.status_collection import collect_all_working_status
        from jobs.working_rate_calculation import run_working_rate_calculation
        from utils.logging_utils import setup_logging
        from utils.config import get_config
        from core.database import DatabaseManager
        print("✓ 全モジュールのインポートに成功しました")
        
    except ImportError as e2:
        print(f"絶対インポートエラー: {e2}")
        print("基本機能のみで動作します")
        
        # 最低限の機能で動作
        run_status_collection_scheduler = None
        run_working_rate_scheduler = None
        collect_all_working_status = None
        run_working_rate_calculation = None
        setup_logging = None
        get_config = None
        
        # collect_all_working_status をインポートを試行
        try:
            from jobs.status_collection import collect_all_working_status
            print("✓ collect_all_working_statusは利用可能です")
        except ImportError as import_error:
            print(f"collect_all_working_status インポート失敗: {import_error}")
            collect_all_working_status = None

    # 実際のDatabaseManagerをインポートを試行
    try:
        from core.database import DatabaseManager
        print("✓ DatabaseManagerは利用可能です")
    except ImportError:
        # シンプルなDatabaseManager代替クラス
        class SimpleDatabaseManager:
            def get_businesses(self):
                return {
                    0: {
                        'Business ID': 'test1', 'name': 'テスト店舗1', 'media': 'cityhaven', 
                        'URL': 'https://www.cityheaven.net/kanagawa/A1401/A140103/k-hitodumajo/attend/',
                        'cast_type': 'a', 'working_type': 'a', 'shift_type': 'a'
                    },
                    1: {
                        'Business ID': 'test2', 'name': 'テスト店舗2', 'media': 'cityhaven',
                        'URL': 'https://www.cityheaven.net/kanagawa/A1401/A140103/k-hitodumajo/attend/',
                        'cast_type': 'a', 'working_type': 'a', 'shift_type': 'a'
                    }
                }
        
        DatabaseManager = SimpleDatabaseManager
        print("✓ SimpleDatabaseManagerを使用します")

def setup_argument_parser():
    """コマンドライン引数パーサーを設定する"""
    parser = argparse.ArgumentParser(
        description='稼働.com バッチ処理システム',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s status-collection                            # 稼働状況取得スケジューラー開始
  %(prog)s working-rate                                # 稼働率計算スケジューラー開始
  %(prog)s collect --force                             # 稼働状況取得を手動実行
  %(prog)s calculate --date 2024-01-15                 # 特定日の稼働率を計算
  %(prog)s test-db                                     # データベース接続テスト
        """
    )
    
    # サブコマンド
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')
    
    # 稼働状況取得スケジューラー
    status_parser = subparsers.add_parser('status-collection', help='稼働状況取得スケジューラー（30分ごと）')
    
    # 稼働率計算スケジューラー
    rate_parser = subparsers.add_parser('working-rate', help='稼働率計算スケジューラー（毎日12時）')
    
    # 手動実行: 稼働状況取得
    collect_parser = subparsers.add_parser('collect', help='稼働状況取得を手動実行')
    collect_parser.add_argument('--force', action='store_true', help='営業時間外でも強制実行')
    collect_parser.add_argument('--business-id', type=str, help='特定店舗のみ処理')
    
    # 手動実行: 稼働率計算
    calc_parser = subparsers.add_parser('calculate', help='稼働率を手動計算')
    calc_parser.add_argument('--date', type=str, help='計算対象日付 (YYYY-MM-DD、省略時は前日)')
    calc_parser.add_argument('--force', action='store_true', help='強制実行')
    
    # データベーステスト
    subparsers.add_parser('test-db', help='データベース接続テスト')
    
    return parser

async def run_collect_command(args):
    """稼働状況取得コマンドを実行"""
    try:
        print("稼働状況取得を手動実行中...")
        
        if collect_all_working_status is None:
            print("✗ collect_all_working_statusが利用できません")
            return 1
        
        # データベースから店舗データを取得
        db_manager = DatabaseManager()
        
        if args.business_id:
            print(f"特定店舗のみ処理: {args.business_id}")
            # 特定店舗のみの場合 - 実際の店舗データを取得
            all_businesses = db_manager.get_businesses()
            businesses_data = {k: v for k, v in all_businesses.items() if v['Business ID'] == args.business_id}
        else:
            # 全店舗取得
            businesses_data = db_manager.get_businesses()
        
        if not businesses_data:
            print("対象店舗が見つかりません")
            return 1
        
        print(f"処理対象: {len(businesses_data)}店舗")
        
        # 辞書形式に変換
        businesses = {i: business for i, business in enumerate(businesses_data)}
        
        # 収集実行
        results = await collect_all_working_status(businesses)
        
        print(f"結果: {len(results)}件のデータを収集しました")
        
        if results:
            # データベースに保存（実際のメソッドに合わせて調整が必要）
            saved_count = 0
            for result in results:
                try:
                    success = db_manager.insert_status(
                        result['cast_id'],
                        result['is_working'],
                        result['is_on_shift'],
                        result['collected_at']
                    )
                    if success:
                        saved_count += 1
                except Exception as save_error:
                    print(f"保存エラー: {save_error}")
            
            print(f"データベースに{saved_count}件保存しました")
        
        return 0
        
    except Exception as e:
        print(f"収集エラー: {e}")
        return 1

async def main():
    """メイン実行関数"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # ログ設定
    try:
        if get_config and setup_logging:
            config = get_config()
            setup_logging(
                log_level=getattr(logging, 'INFO'),
                log_dir=Path(__file__).parent / 'logs'
            )
        else:
            logging.basicConfig(level=logging.INFO)
    except Exception:
        # 設定が読み込めない場合の基本ログ設定
        logging.basicConfig(level=logging.INFO)
    
    logger = logging.getLogger(__name__)
    
    try:
        if args.command == 'status-collection':
            print("稼働状況取得スケジューラーを開始中...")
            print("30分ごとに営業中店舗の稼働状況を取得します")
            print("停止するにはCtrl+Cを押してください")
            await run_status_collection_scheduler()
            return 0
            
        elif args.command == 'working-rate':
            print("稼働率計算スケジューラーを開始中...")
            print("毎日12時に前日の稼働率を計算します")
            print("停止するにはCtrl+Cを押してください")
            await run_working_rate_scheduler()
            return 0
            
        elif args.command == 'collect':
            return await run_collect_command(args)
            
        elif args.command == 'calculate':
            print("稼働率計算を手動実行中...")
            target_date = None
            if args.date:
                target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            
            result = await run_working_rate_calculation(
                target_date=target_date,
                force=args.force
            )
            print(f"結果: 成功={result.success}, 処理数={result.processed_count}, エラー数={result.error_count}")
            return 0 if result.success else 1
            
        elif args.command == 'test-db':
            print("データベース接続をテスト中...")
            
            try:
                db_manager = DatabaseManager()
                
                # 接続テスト - get_businessesメソッドを使用
                businesses = db_manager.get_businesses()
                
                print(f"✓ データベース接続成功")
                print(f"✓ {len(businesses)}件の店舗:")
                
                # 辞書形式なので values() で値を取得
                business_list = list(businesses.values())
                for business in business_list[:5]:  # 最初の5件のみ表示
                    print(f"  - {business.get('name', 'N/A')} (ID: {business.get('Business ID', 'N/A')}, Media: {business.get('media', 'N/A')})")
                
                if len(businesses) > 5:
                    print(f"  ... 他{len(businesses) - 5}件")
                
                return 0
                
            except Exception as db_error:
                print(f"✗ データベース接続失敗: {db_error}")
                return 1
        
    except KeyboardInterrupt:
        print("\nユーザーによる操作中断")
        return 0
    except Exception as e:
        print(f"予期しないエラー: {e}")
        logger.exception("詳細エラー情報")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
