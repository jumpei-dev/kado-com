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
try:
    from schedulers import run_status_collection_scheduler, run_working_rate_scheduler
    from jobs.status_collection import run_status_collection
    from jobs.working_rate_calculation import run_working_rate_calculation
    from utils.logging_utils import setup_logging
    from utils.config import get_config
    from core.database import DatabaseManager
except ImportError:
    import os
    os.chdir(str(Path(__file__).parent))
    from schedulers import run_status_collection_scheduler, run_working_rate_scheduler
    from jobs.status_collection import run_status_collection
    from jobs.working_rate_calculation import run_working_rate_calculation
    from utils.logging_utils import setup_logging
    from utils.config import get_config
    from core.database import DatabaseManager

import asyncio
import argparse
import sys
import logging
from pathlib import Path

# batchディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# バッチコンポーネントをインポート
try:
    from scheduler import run_scheduler
    from jobs.status_collection import run_status_collection
    from jobs.status_history import run_status_history, get_business_history_summary
    from utils.logging_utils import setup_logging
    from utils.config import get_config, load_config_from_file
    from core.database import DatabaseManager
except ImportError:
    # 相対インポートのフォールバック
    import os
    os.chdir(str(Path(__file__).parent))
    from scheduler import run_scheduler
    from jobs.status_collection import run_status_collection
    from jobs.status_history import run_status_history, get_business_history_summary
    from utils.logging_utils import setup_logging
    from utils.config import get_config, load_config_from_file
    from core.database import DatabaseManager

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

async def main():
    """メイン実行関数"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # ログ設定
    config = get_config()
    setup_logging(
        log_level=config.logging.level,
        log_dir=config.logging.log_dir
    )
    
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
            print("稼働状況取得を手動実行中...")
            result = await run_status_collection(
                force=args.force,
                business_id=args.business_id
            )
            print(f"結果: 成功={result.success}, 処理数={result.processed_count}, エラー数={result.error_count}")
            return 0 if result.success else 1
            
        elif args.command == 'calculate':
            print("稼働率計算を手動実行中...")
            target_date = None
            if args.date:
                target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
            
            result = run_working_rate_calculation(
                target_date=target_date,
                force=args.force
            )
            print(f"結果: 成功={result.success}, 処理数={result.processed_count}, エラー数={result.error_count}")
            return 0 if result.success else 1
            
        elif args.command == 'test-db':
            print("データベース接続をテスト中...")
            db_manager = DatabaseManager()
            businesses = db_manager.get_businesses()
            print(f"接続成功: {len(businesses)}店舗が見つかりました")
            
            for business in businesses[:3]:  # 最初の3店舗を表示
                print(f"  - {business['name']} (ID: {business['business_id']})")
            return 0
        
    except KeyboardInterrupt:
        logger.info("ユーザーによる操作中断")
        return 0
    except Exception as e:
        logger.exception(f"予期しないエラー: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

def run_history_command(args):
    """ステータス履歴計算コマンドを実行する"""
    print("ステータス履歴計算ジョブを実行中...")
    result = run_status_history(
        business_id=args.business_id,
        target_date=args.date,
        force=args.force
    )
    
    print(f"\nステータス履歴結果:")
    print(f"成功: {result.success}")
    print(f"処理件数: {result.processed_count}")
    print(f"エラー件数: {result.error_count}")
    
    if result.errors:
        print(f"エラーメッセージ:")
        for error in result.errors:
            print(f"  - {error}")
    
    if result.duration_seconds:
        print(f"実行時間: {result.duration_seconds:.2f}s")
    
    return 0 if result.success else 1

def run_summary_command(args):
    """サマリーコマンドを実行する"""
    print(f"店舗{args.business_id}のステータス履歴サマリーを取得中...")
    
    try:
        summary = get_business_history_summary(args.business_id, args.days)
        
        if 'error' in summary:
            print(f"エラー: {summary['error']}")
            return 1
        
        print(f"\nステータス履歴サマリー (過去{args.days}日間):")
        print(f"店舗ID: {summary['business_id']}")
        print(f"計算済み日数: {summary['summary']['days_calculated']}")
        print(f"平均稼働率: {summary['summary']['average_rate']:.2f}%")
        print(f"最高稼働率: {summary['summary']['max_rate']:.2f}%")
        print(f"最低稼働率: {summary['summary']['min_rate']:.2f}%")
        
        if summary['history']:
            print(f"\n日別詳細:")
            for day in summary['history']:
                print(f"  {day['date']}: {day['working_rate']:.2f}% ({day['total_casts']}名)")
        
        return 0
        
    except Exception as e:
        print(f"サマリー取得エラー: {e}")
        return 1

def run_test_db_command(args):
    """データベース接続をテストする"""
    print("データベース接続をテスト中...")
    
    try:
        db_manager = DatabaseManager()
        businesses = db_manager.get_businesses()
        
        print(f"✓ データベース接続成功")
        print(f"✓ {len(businesses)}件のアクティブな店舗を発見:")
        
        for business in businesses[:5]:  # 最初の5件を表示
            print(f"  - {business['name']} ({business['site_type']})")
        
        if len(businesses) > 5:
            print(f"  ... 他{len(businesses) - 5}件")
        
        return 0
        
    except Exception as e:
        print(f"✗ データベース接続失敗: {e}")
        return 1

async def main():
    """メインエントリーポイント"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # 設定ファイルの読み込み
    if args.config:
        load_config_from_file(args.config)
    
    # 基本的なログ設定
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 適切なコマンドにルーティング
    if args.command == 'scheduler':
        print("バッチスケジューラーデーモンを開始中...")
        print("停止するにはCtrl+Cを押してください")
        await run_scheduler()
        return 0
    
    elif args.command == 'collect':
        return await run_collect_command(args)
    
    elif args.command == 'history':
        return run_history_command(args)
    
    elif args.command == 'summary':
        return run_summary_command(args)
    
    elif args.command == 'test-db':
        return run_test_db_command(args)
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nユーザーによる操作中断")
        sys.exit(0)
    except Exception as e:
        print(f"予期しないエラー: {e}")
        sys.exit(1)
