#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正されたcityheaven_parsersでのテスト
"""

import sys
import os
sys.path.insert(0, '/Users/admin/Projects/kado-com/batch')

from datetime import datetime
import logging

# ログ設定をINFOレベルに
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    # 相対インポートを避けて直接インポート
    from jobs.status_collection.cityheaven_parsers import CityheavenNewParser
    print("✅ CityheavenNewParserのインポート成功")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    # ダミーのCastStatusを定義
    from dataclasses import dataclass
    
    @dataclass
    class CastStatus:
        name: str
        is_working: bool
        business_id: str
        cast_id: str
        on_shift: bool
        shift_times: str
        working_times: str
    
    # CityheavenNewParserを手動インポート
    sys.path.insert(0, '/Users/admin/Projects/kado-com/batch/jobs/status_collection')
    import cityheaven_parsers
    CityheavenNewParser = cityheaven_parsers.CityheavenNewParser
    print("✅ 手動インポート成功")

def test_modified_parser():
    """修正されたパーサーをテスト"""
    html_file = "/Users/admin/Projects/kado-com/data/raw_html/cityhaven/人妻城_cast_list_20250825_215250.html"
    
    # HTMLファイルを読み込み
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # HTML取得時刻
    html_acquisition_time = datetime(2025, 8, 25, 21, 52, 50)
    
    # パーサーをインスタンス化
    parser = CityheavenNewParser()
    
    print(f"📋 HTML内容長: {len(html_content)} 文字")
    print(f"⏰ HTML取得時刻: {html_acquisition_time}")
    
    # パース実行
    cast_list = parser.parse_cast_list(html_content, html_acquisition_time)
    
    print(f"\n=== 結果 ===")
    print(f"抽出されたキャスト数: {len(cast_list)}")
    
    # 稼働中のキャストをカウント
    working_count = sum(1 for cast in cast_list if cast.is_working)
    print(f"稼働中のキャスト: {working_count} 人")
    
    # 結果の詳細表示（最初の5件と稼働中の最初の3件）
    print("\n--- 最初の5件 ---")
    for i, cast_status in enumerate(cast_list[:5]):
        print(f"キャスト{i+1}: ID={cast_status.cast_id}, 稼働中={cast_status.is_working}")
    
    print("\n--- 稼働中のキャスト（最初の3件） ---")
    working_casts = [cast for cast in cast_list if cast.is_working]
    for i, cast_status in enumerate(working_casts[:3]):
        print(f"稼働中{i+1}: ID={cast_status.cast_id}, 名前={cast_status.name}")

if __name__ == "__main__":
    test_modified_parser()
