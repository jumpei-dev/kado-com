#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャストID抽出のデバッグテスト
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging

# ログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_cast_id_extraction():
    """HTMLファイルからキャストID抽出をテスト"""
    html_file = "/Users/admin/Projects/kado-com/data/raw_html/cityhaven/人妻城_cast_list_20250825_215250.html"
    
    # HTMLファイルを読み込み
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # sugunavi_wrapper要素を検索
    wrapper_elements = soup.find_all('div', {'class': 'sugunavi_wrapper'})
    print(f"✓ sugunavi_wrapper要素数: {len(wrapper_elements)}")
    
    successful_extractions = 0
    
    for i, wrapper_element in enumerate(wrapper_elements[:5]):  # 最初の5個をテスト
        print(f"\n=== Wrapper {i+1} ===")
        
        # デバッグ：wrapper_element内のa要素を全て確認
        all_a_elements = wrapper_element.find_all('a', href=True)
        print(f"🔍 wrapper_element内のa要素数: {len(all_a_elements)}")
        
        for j, a_element in enumerate(all_a_elements):
            href = a_element.get('href', '')
            print(f"  a要素{j+1}: href='{href}'")
            
            # girlid-xxxパターンを検索
            match = re.search(r'girlid-(\d+)', href)
            if match:
                cast_id = match.group(1)
                print(f"✅ キャストID抽出成功: {cast_id} from {href}")
                successful_extractions += 1
                break
        else:
            # wrapper内容を確認
            wrapper_text = wrapper_element.get_text(strip=True)[:200]
            print(f"❌ キャストID抽出失敗")
            print(f"   wrapper内容（最初200文字）: {wrapper_text}")
    
    print(f"\n=== 結果 ===")
    print(f"成功した抽出: {successful_extractions} / {min(5, len(wrapper_elements))}")

if __name__ == "__main__":
    test_cast_id_extraction()
