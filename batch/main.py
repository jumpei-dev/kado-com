"""
バッチ処理システムのメインエントリーポイント
"""

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
  %(prog)s scheduler                                    # スケジューラーデーモンを実行
  %(prog)s collect --force                             # ステータス収集を強制実行
  %(prog)s collect --business-id 1                     # 特定店舗のみ収集
  %(prog)s history --date 2024-01-15                   # 特定日の履歴を計算
  %(prog)s history --business-id 1 --force             # 履歴計算を強制実行
  %(prog)s summary --business-id 1 --days 7            # 7日間のサマリーを取得
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        help='設定ファイルのパス'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='ログレベル (デフォルト: INFO)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')
    
    # スケジューラーコマンド
    scheduler_parser = subparsers.add_parser('scheduler', help='ジョブスケジューラーを実行')
    
    # ステータス収集コマンド
    collect_parser = subparsers.add_parser('collect', help='ステータス収集ジョブを実行')
    collect_parser.add_argument('--business-id', type=int, help='処理する特定の店舗ID')
    collect_parser.add_argument('--force', action='store_true', help='営業時間外でも強制実行')
    
    # ステータス履歴コマンド
    history_parser = subparsers.add_parser('history', help='ステータス履歴計算を実行')
    history_parser.add_argument('--business-id', type=int, help='処理する特定の店舗ID')
    history_parser.add_argument('--date', help='計算する特定の日付 (YYYY-MM-DD)')
    history_parser.add_argument('--force', action='store_true', help='任意の時刻に強制実行')
    
    # サマリーコマンド
    summary_parser = subparsers.add_parser('summary', help='ステータス履歴サマリーを取得')
    summary_parser.add_argument('--business-id', type=int, required=True, help='店舗ID')
    summary_parser.add_argument('--days', type=int, default=7, help='日数 (デフォルト: 7)')
    
    # データベーステストコマンド
    test_parser = subparsers.add_parser('test-db', help='データベース接続をテスト')
    
    return parser

async def run_collect_command(args):
    """ステータス収集コマンドを実行する"""
    print("ステータス収集ジョブを実行中...")
    result = await run_status_collection(
        business_id=args.business_id,
        force=args.force
    )
    
    print(f"\nステータス収集結果:")
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
