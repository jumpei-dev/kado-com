#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本番バッチ処理を直接実行する簡単なテストツール
"""

import os
import sys
import subprocess
from datetime import datetime

def run_batch_command(command_args, description):
    """バッチコマンドを実行"""
    print(f"\n🎯 {description}")
    print("="*80)
    print(f"⏰ 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 実行コマンド: python3 {' '.join(command_args)}")
    print("-"*80)
    
    try:
        # batch/main.pyを直接実行
        result = subprocess.run(
            ['python3', 'batch/main.py'] + command_args,
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=300  # 5分タイムアウト
        )
        
        # 標準出力を表示
        if result.stdout:
            print("📤 標準出力:")
            print(result.stdout)
        
        # エラー出力を表示
        if result.stderr:
            print("⚠️ エラー出力:")
            print(result.stderr)
        
        # 終了コードをチェック
        if result.returncode == 0:
            print(f"✅ {description} 成功")
        else:
            print(f"❌ {description} 失敗 (終了コード: {result.returncode})")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} タイムアウト (5分)")
        return False
    except Exception as e:
        print(f"❌ {description} 実行エラー: {e}")
        return False
    finally:
        print(f"⏰ 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

def test_status_collection():
    """ステータス収集のテスト"""
    return run_batch_command(
        ['status-collection'],
        "キャスト稼働ステータス収集"
    )

def test_working_rate_calculation():
    """稼働率計算のテスト"""
    return run_batch_command(
        ['working-rate'],
        "キャスト稼働率計算"
    )

def show_help():
    """ヘルプを表示"""
    return run_batch_command(
        ['--help'],
        "バッチ処理ヘルプ表示"
    )

def main():
    """メイン関数"""
    print("🚀 本番バッチ処理テストツール")
    print("="*100)
    print(f"📍 作業ディレクトリ: {os.getcwd()}")
    print(f"🐍 Python バージョン: {sys.version}")
    
    if len(sys.argv) < 2:
        print("\n📖 使用方法:")
        print("  python test_batch_runner.py status          # ステータス収集実行")  
        print("  python test_batch_runner.py rate            # 稼働率計算実行")
        print("  python test_batch_runner.py help            # ヘルプ表示")
        print("\n🎯 デフォルトでステータス収集を実行します...")
        command = "status"
    else:
        command = sys.argv[1].lower()
    
    success = False
    
    if command == "status":
        success = test_status_collection()
    elif command == "rate":  
        success = test_working_rate_calculation()
    elif command == "help":
        success = show_help()
    else:
        print(f"❌ 不明なコマンド: {command}")
        print("利用可能: status, rate, help")
        return
    
    print(f"\n🏁 最終結果: {'成功' if success else '失敗'}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 処理が中断されました")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
