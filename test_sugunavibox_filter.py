#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sugunavibox限定テスト
"""

import sys
import os
from bs4 import BeautifulSoup
import re

def test_sugunavibox_filtering():
    """sugunaviboxを含むwrapper要素の正確な特定をテスト"""
    html_file = "/Users/admin/Projects/kado-com/data/raw_html/cityhaven/人妻城_cast_list_20250825_215250.html"
    
    # HTMLファイルを読み込み
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. 全sugunavi_wrapper要素を取得
    all_wrappers = soup.find_all('div', class_='sugunavi_wrapper')
    print(f"📦 全sugunavi_wrapper要素: {len(all_wrappers)}個")
    
    # 2. sugunaviboxを含むwrapper要素を特定
    wrappers_with_sugunavibox = []
    for i, wrapper in enumerate(all_wrappers):
        suguna_box = wrapper.find(class_='sugunavibox')
        if suguna_box:
            wrappers_with_sugunavibox.append(wrapper)
            
            # デバッグ: girlid-xxxパターンがあるかチェック
            a_elements = wrapper.find_all('a', href=True)
            has_girlid = False
            for a_element in a_elements:
                href = a_element.get('href', '')
                if re.search(r'girlid-(\d+)', href):
                    has_girlid = True
                    break
            
            print(f"  Wrapper {i+1}: sugunavibox=✓, girlid={'✓' if has_girlid else '✗'}")
    
    print(f"\n🎯 sugunaviboxを含むwrapper: {len(wrappers_with_sugunavibox)}個")
    
    # 3. girlid-xxxパターンを持つwrapper要素をさらにフィルタ
    cast_wrappers = []
    for wrapper in wrappers_with_sugunavibox:
        a_elements = wrapper.find_all('a', href=True)
        for a_element in a_elements:
            href = a_element.get('href', '')
            if re.search(r'girlid-(\d+)', href):
                cast_wrappers.append(wrapper)
                break
    
    print(f"👥 girlid-xxxパターンを持つwrapper: {len(cast_wrappers)}個")
    
    # 4. 最初の5個の詳細を表示
    print(f"\n=== 最初の5個の詳細 ===")
    for i, wrapper in enumerate(cast_wrappers[:5]):
        # girlid抽出
        a_elements = wrapper.find_all('a', href=True)
        cast_id = None
        for a_element in a_elements:
            href = a_element.get('href', '')
            match = re.search(r'girlid-(\d+)', href)
            if match:
                cast_id = match.group(1)
                break
        
        # sugunavibox内容
        suguna_box = wrapper.find(class_='sugunavibox')
        suguna_text = suguna_box.get_text(strip=True)[:100] if suguna_box else "N/A"
        
        print(f"Wrapper {i+1}: cast_id={cast_id}, sugunavibox='{suguna_text}...'")

if __name__ == "__main__":
    test_sugunavibox_filtering()
