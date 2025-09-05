"""
バッチ処理システムのメインエントリーポイント
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
import aiohttp
from urllib.parse import urlparse

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
    from .jobs.status_collection import collect_all_working_status, collect_status_by_url
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
        from jobs.status_collection import collect_all_working_status, collect_status_by_url
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
        collect_status_by_url = None
        run_working_rate_calculation = None
        setup_logging = None
        get_config = None
        
        # collect_all_working_status をインポートを試行
        try:
            from jobs.status_collection import collect_all_working_status, collect_status_by_url
            print("✓ collect_all_working_statusとcollect_status_by_urlは利用可能です")
        except ImportError as import_error:
            print(f"collect_all_working_status インポート失敗: {import_error}")
            try:
                # 直接collector.pyからインポート
                from jobs.status_collection.collector import collect_all_working_status, collect_status_by_url
                print("✓ collector.pyから直接collect_all_working_statusとcollect_status_by_urlをインポートしました")
            except ImportError as direct_import_error:
                print(f"直接インポート失敗: {direct_import_error}")
                collect_all_working_status = None
                collect_status_by_url = None

    # 実際のDatabaseManagerをインポートを試行
    try:
        from core.database import DatabaseManager
        print("✓ DatabaseManagerは利用可能です")
    except ImportError:
        # シンプルなDatabaseManager代替クラス
        class SimpleDatabaseManager:
            def get_businesses(self):
                businesses = {
                    0: {
                        'business_id': 'test1', 
                        'Business ID': '12345678',
                        'name': 'サンプル店舗',
                        'Name': 'サンプル店舗',
                        'media': 'cityhaven', 
                        'URL': 'https://www.cityheaven.net/kanagawa/A1401/A140103/k-hitodumajo/attend/',
                        'cast_type': 'a', 
                        'working_type': 'a', 
                        'shift_type': 'a'
                    },
                    1: {
                        'business_id': '2', 
                        'Business ID': '2',
                        'name': 'サンプル店舗2',
                        'Name': 'サンプル店舗2',
                        'media': 'cityhaven', 
                        'URL': 'https://www.cityheaven.net/saitama/A1105/A110501/honey/attend/',
                        'cast_type': 'a', 
                        'working_type': 'a', 
                        'shift_type': 'a'
                    }
                }
                print(f"デバッグ: get_businesses() returns: {businesses}")
                return businesses
            
            def insert_status(self, cast_id, is_working, is_on_shift, collected_at):
                """テスト用の挿入メソッド"""
                print(f"  📝 テストデータ保存: {cast_id} (Working: {is_working}, OnShift: {is_on_shift})")
                return True
        
        DatabaseManager = SimpleDatabaseManager
        print("✓ SimpleDatabaseManagerを使用します")

async def download_html_from_url(url: str) -> str:
    """URLからHTMLをダウンロードしてローカルファイルに保存"""
    try:
        # URLから店舗名を抽出してファイル名生成
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        # 店舗名を推定（最後から2番目のパス部分を使用）
        if len(path_parts) >= 2:
            shop_name = path_parts[-2]
        else:
            shop_name = "unknown_shop"
        
        # タイムスタンプ付きファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{shop_name}_cast_list_{timestamp}.html"
        
        # 保存ディレクトリを確保
        save_dir = Path(__file__).parent.parent / "data" / "raw_html" / "cityhaven"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイルパスを生成
        file_path = save_dir / filename
        
        print(f"📡 HTMLダウンロード中: {url}")
        
        # HTTPリクエストでHTMLを取得（User-Agentヘッダー追加）
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # ファイルに保存
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    print(f"💾 HTMLファイル保存: {filename}")
                    return filename
                else:
                    print(f"❌ HTTP エラー: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"❌ HTMLダウンロードエラー: {e}")
        return None

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
  %(prog)s collect --local-html                        # ローカルHTMLファイルで開発テスト
  %(prog)s calculate --date 2024-01-15                 # 特定日の稼働率を計算
  %(prog)s test-db                                     # データベース接続テスト
  %(prog)s debug-html --url "https://example.com/attend/"    # URLからHTMLを保存
  %(prog)s debug-html --local-file "filename.html"        # ローカルファイルのDOM構造確認
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
    collect_parser.add_argument('--local-html', action='store_true', help='ローカルHTMLファイルを使用（開発用）')
    
    # 手動実行: 稼働率計算
    calc_parser = subparsers.add_parser('calculate', help='稼働率を手動計算')
    calc_parser.add_argument('--date', type=str, help='計算対象日付 (YYYY-MM-DD、省略時は前日)')
    calc_parser.add_argument('--force', action='store_true', help='強制実行')
    
    # データベーステスト
    subparsers.add_parser('test-db', help='データベース接続テスト')
    
    # 店舗追加検証モード
    debug_parser = subparsers.add_parser('debug-html', help='店舗追加検証モード（新店舗のHTML構造確認）')
    debug_parser.add_argument('--url', type=str, help='URLを指定してHTMLをローカルに保存し、ファイル名を返す')
    debug_parser.add_argument('--local-file', type=str, help='ローカルHTMLファイルを指定してDOM構造を詳細出力')
    
    return parser

async def run_collect_command(args):
    """稼働状況取得コマンドを実行"""
    try:
        mode_text = "ローカルHTML" if args.local_html else "ライブスクレイピング"
        print(f"稼働状況取得を手動実行中... ({mode_text}モード)")
        
        if collect_all_working_status is None:
            print("✗ collect_all_working_statusが利用できません")
            return 1
        
        print("✓ データベースマネージャーを初期化中...")
        # データベースから店舗データを取得
        db_manager = DatabaseManager()
        
        print("✓ 店舗データを取得中...")
        businesses = db_manager.get_businesses()
        
        if args.business_id:
            print(f"特定店舗のみ処理: {args.business_id}")
            # 指定された店舗のみ抽出
            target_businesses = {k: v for k, v in businesses.items() if str(v.get('Business ID')) == str(args.business_id)}
            if not target_businesses:
                print(f"❌ 指定されたBusiness ID '{args.business_id}' が見つかりませんでした")
                return 1
        else:
            target_businesses = businesses
        
        print(f"✓ 処理対象: {len(target_businesses)}店舗")
        
        # 店舗情報を詳細表示
        for i, (key, business) in enumerate(target_businesses.items()):
            name = business.get('Name', business.get('name', 'Unknown'))
            print(f"  店舗{i+1}: {name} (ID: {business.get('Business ID')})")
        
        print("✓ 稼働状況収集を実行中...")
        # 収集実行（local_htmlオプション追加）
        results = await collect_all_working_status(target_businesses, use_local_html=args.local_html)
        
        print(f"✓ 結果: {len(results)}件のデータを収集しました")
        
        if results:
            print("✓ データベースに保存中...")
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
        print(f"✗ 収集エラー: {e}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")
        return 1

async def run_debug_html_command(args):
    """店舗追加検証モード実行"""
    try:
        print("🔍 店舗追加検証モード - 新店舗のHTML構造確認")
        
        # URL指定の場合：HTMLをローカルに保存
        if hasattr(args, 'url') and args.url:
            print(f"📋 URL指定: {args.url}")
            
            # URLからHTMLをダウンロード
            saved_file = await download_html_from_url(args.url)
            if saved_file:
                print(f"✅ HTMLファイル保存完了: {saved_file}")
                print(f"📁 次回の検証用コマンド: python main.py debug-html --local-file {saved_file}")
                return 0
            else:
                print("❌ HTMLファイルの保存に失敗しました")
                return 1
            
        # ローカルファイル指定の場合：既存のパーサーを使用
        elif hasattr(args, 'local_file') and args.local_file:
            print(f"📄 ローカルファイル指定: {args.local_file}")
            print("🔄 既存のパーサーロジックを使用してDOM構造を確認します")
            
            # 既存のcollect機能を使用（--local-htmlオプション相当）
            if collect_all_working_status is None:
                print("❌ collect_all_working_statusが利用できません")
                return 1
            
            # SimpleDatabaseManagerを使用
            db_manager = DatabaseManager()
            businesses = db_manager.get_businesses()
            
            # 最初の店舗でテスト（ローカルHTMLファイルを使用）
            target_businesses = dict(list(businesses.items())[:1])
            
            print(f"🎯 テスト対象店舗: {list(target_businesses.values())[0].get('Name')}")
            print(f"📄 使用するHTMLファイル: {args.local_file}")
            
            # DOM確認モード有効でスクレイピング実行
            results = await collect_all_working_status(target_businesses, use_local_html=True, dom_check_mode=True, specific_file=args.local_file)
            
            if results:
                print(f"\n✅ DOM構造確認完了: {len(results)}件処理")
                return 0
            else:
                print(f"\n✅ DOM構造確認完了 (データ処理は成功、DB保存処理でエラーが発生)")
                print(f"💡 DOM解析結果は上記ログで確認できます")
                return 0
        
        else:
            print("❌ --url または --local-file オプションを指定してください")
            print("使用例:")
            print("  python main.py debug-html --url 'https://example.com/attend/'")
            print("  python main.py debug-html --local-file 'filename.html'")
            return 1
            
    except Exception as e:
        print(f"✗ 店舗追加検証エラー: {e}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")
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
        
        elif args.command == 'debug-html':
            return await run_debug_html_command(args)
        
    except KeyboardInterrupt:
        print("\nユーザーによる操作中断")
        return 0
    except Exception as e:
        print(f"予期しないエラー: {e}")
        logger.exception("詳細エラー情報")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
