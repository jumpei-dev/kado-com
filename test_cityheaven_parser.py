#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CityheavenNewParserのデバッグテスト
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
import logging

# ログ設定をDEBUGレベルに
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    # パス追加
    sys.path.insert(0, '/Users/admin/Projects/kado-com/batch')
    
    # 必要なモジュールを直接インポート
    from bs4 import BeautifulSoup
    from datetime import datetime
    import re
    from dataclasses import dataclass
    from typing import Optional
    
    # CastStatusを定義
    @dataclass
    class CastStatus:
        name: str
        is_working: bool
        business_id: str
        cast_id: str
        on_shift: bool
        shift_times: str
        working_times: str
    
    print("✅ 必要モジュールのインポート成功")
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

class SimpleCityheavenParser:
    """簡単なCityheavenパーサー（テスト用）"""
    
    def parse_cast_list(self, html_content: str, html_acquisition_time: datetime) -> list[CastStatus]:
        """キャスト一覧を解析"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            cast_list = []
            
            # sugunavi_wrapperセクションを探す
            sugunavi_sections = soup.find_all('div', {'class': 'sugunavi_wrapper'})
            if not sugunavi_sections:
                print("❌ sugunavi_wrapperセクションが見つかりません")
                return []
            
            print(f"📋 {len(sugunavi_sections)} 個のsugunavi_wrapperセクション発見")
            
            # 各セクションを処理
            for i, section in enumerate(sugunavi_sections):
                cast_status = self._parse_single_cast(section, html_acquisition_time)
                if cast_status:
                    cast_list.append(cast_status)
                    print(f"✅ キャスト{i+1}解析成功: {cast_status.cast_id}")
                else:
                    print(f"⚠️ キャスト{i+1}解析失敗")
            
            print(f"✅ キャスト解析完了: {len(cast_list)}/{len(sugunavi_sections)} 人")
            return cast_list
            
        except Exception as e:
            print(f"❌ HTML解析エラー: {e}")
            return []
    
    def _parse_single_cast(self, cast_element, html_acquisition_time: datetime) -> Optional[CastStatus]:
        """単一のキャスト要素を解析"""
        try:
            # キャストIDを取得
            cast_id = self._extract_cast_id(cast_element)
            if not cast_id:
                return None
            
            # 名前はIDで代用
            cast_name = f"Cast_{cast_id}"
            
            # 働き状況を判定
            is_working = self._determine_working_status(cast_element, html_acquisition_time)
            
            # CastStatusオブジェクトを作成
            cast_status = CastStatus(
                name=cast_name,
                is_working=is_working,
                business_id="hitozuma_shiro",
                cast_id=cast_id,
                on_shift=True,  # 簡単化
                shift_times="",
                working_times=""
            )
            
            return cast_status
            
        except Exception as e:
            print(f"❌ 単一キャスト解析エラー: {e}")
            return None
    
    def _extract_cast_id(self, cast_element) -> Optional[str]:
        """キャストIDを抽出"""
        try:
            # cast_element内のa要素を全て確認
            all_a_elements = cast_element.find_all('a', href=True)
            
            for a_element in all_a_elements:
                href = a_element.get('href', '')
                # girlid-xxxパターンを検索
                match = re.search(r'girlid-(\d+)', href)
                if match:
                    cast_id = match.group(1)
                    return cast_id
            
            return None
            
        except Exception as e:
            print(f"❌ キャストID抽出エラー: {e}")
            return None
    
    def _determine_working_status(self, cast_element, html_acquisition_time: datetime) -> bool:
        """働き状況を判定"""
        try:
            # sugunavibox内のtitle要素から時間情報を取得
            suguna_box = cast_element.find('div', {'class': 'sugunavibox'})
            if not suguna_box:
                return False
            
            title_elements = suguna_box.find_all('div', {'class': 'title'})
            if not title_elements:
                return False
            
            # 時間パターンを検索
            for title_element in title_elements:
                title_text = title_element.get_text(strip=True)
                print(f"🔍 タイトル: {title_text}")
                
                # 「21:11～待機中」のようなパターンをチェック
                time_match = re.search(r'(\d{1,2}):(\d{2})～待機中', title_text)
                if time_match:
                    start_hour = int(time_match.group(1))
                    start_minute = int(time_match.group(2))
                    
                    # HTML取得時刻と比較
                    html_time = html_acquisition_time.time()
                    start_time = html_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                    
                    # 時間が経過しているかチェック
                    if html_time >= start_time:
                        print(f"❌ 時間経過済み: {title_text}")
                        return False
                    else:
                        print(f"✅ 待機中: {title_text}")
                        return True
            
            return False
            
        except Exception as e:
            print(f"❌ 働き状況判定エラー: {e}")
            return False

def test_cityheaven_new_parser():
    """CityheavenNewParserをテスト（ローカル実装版）"""
    html_file = "/Users/admin/Projects/kado-com/data/raw_html/cityhaven/人妻城_cast_list_20250825_215250.html"
    
    # HTMLファイルを読み込み
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # HTML取得時刻（ファイルの作成時刻）
    html_acquisition_time = datetime(2025, 8, 25, 21, 52, 50)
    
    # CityheavenNewParserをローカル実装でテスト
    parser = TestCityheavenNewParser()
    
    print(f"📋 HTML内容長: {len(html_content)} 文字")
    print(f"⏰ HTML取得時刻: {html_acquisition_time}")
    
    # パース実行
    cast_list = parser.parse_cast_list(html_content, html_acquisition_time)
    
    print(f"
=== 結果 ===")
    print(f"抽出されたキャスト数: {len(cast_list)}")
    
    # 結果の詳細表示（最初の3件）
    for i, cast_status in enumerate(cast_list[:3]):
        print(f"
キャスト{i+1}:")
        print(f"  名前: {cast_status.name}")
        print(f"  ID: {cast_status.cast_id}")
        print(f"  稼働中: {cast_status.is_working}")
        print(f"  出勤中: {cast_status.on_shift}")
        print(f"  業務ID: {cast_status.business_id}")

class TestCityheavenNewParser:
    """テスト用CityheavenNewParser（ローカル実装）"""
    
    def parse_cast_list(self, html_content: str, html_acquisition_time: datetime):
        """修正版のparse_cast_list"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            cast_list = []
            
            # sugunavi_wrapperセクションを探す
            sugunavi_sections = soup.find_all('div', {'class': 'sugunavi_wrapper'})
            if not sugunavi_sections:
                print("❌ sugunavi_wrapperセクションが見つかりません")
                return []
            
            print(f"📋 {len(sugunavi_sections)} 個のsugunavi_wrapperセクション発見")
            
            # sugunaviboxを含むwrapper要素に限定
            cast_sections = []
            for section in sugunavi_sections:
                suguna_box = section.find('div', {'class': 'sugunavibox'})
                if suguna_box:
                    # さらにgirlid-xxxパターンがあるかチェック
                    a_elements = section.find_all('a', href=True)
                    for a_element in a_elements:
                        href = a_element.get('href', '')
                        if re.search(r'girlid-(\d+)', href):
                            cast_sections.append(section)
                            break
            
            print(f"👥 キャストデータを持つセクション: {len(cast_sections)} 個")
            
            # 各キャストセクションを処理
            for i, section in enumerate(cast_sections):
                try:
                    cast_status = self._parse_single_cast(section, html_acquisition_time)
                    if cast_status:
                        cast_list.append(cast_status)
                        print(f"✅ キャスト{i+1}解析成功: {cast_status.cast_id}")
                    else:
                        print(f"⚠️ キャスト{i+1}解析失敗")
                except Exception as e:
                    print(f"❌ キャスト{i+1}の解析エラー: {e}")
                    continue
            
            print(f"✅ キャスト解析完了: {len(cast_list)}/{len(cast_sections)} 人")
            return cast_list
            
        except Exception as e:
            print(f"❌ HTML解析エラー: {e}")
            return []
    
    def _parse_single_cast(self, cast_element, html_acquisition_time: datetime):
        """単一のキャスト要素を解析"""
        try:
            # キャストIDを取得
            cast_id = self._extract_cast_id(cast_element)
            if not cast_id:
                return None
            
            # 働き状況を判定
            is_working = self._determine_working_status(cast_element, html_acquisition_time)
            
            # CastStatusオブジェクトを作成
            cast_status = CastStatus(
                name=f"Cast_{cast_id}",
                is_working=is_working,
                business_id="hitozuma_shiro",
                cast_id=cast_id,
                on_shift=True,
                shift_times="",
                working_times=""
            )
            
            return cast_status
            
        except Exception as e:
            print(f"❌ 単一キャスト解析エラー: {e}")
            return None
    
    def _extract_cast_id(self, cast_element):
        """キャストIDを抽出"""
        try:
            all_a_elements = cast_element.find_all('a', href=True)
            
            for a_element in all_a_elements:
                href = a_element.get('href', '')
                match = re.search(r'girlid-(\d+)', href)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"❌ キャストID抽出エラー: {e}")
            return None
    
    def _determine_working_status(self, cast_element, html_acquisition_time: datetime):
        """働き状況を判定"""
        try:
            suguna_box = cast_element.find('div', {'class': 'sugunavibox'})
            if not suguna_box:
                return False
            
            title_elements = suguna_box.find_all('div', {'class': 'title'})
            if not title_elements:
                return False
            
            for title_element in title_elements:
                title_text = title_element.get_text(strip=True)
                
                # 「21:11～待機中」のようなパターンをチェック
                time_match = re.search(r'(\d{1,2}):(\d{2})～待機中', title_text)
                if time_match:
                    start_hour = int(time_match.group(1))
                    start_minute = int(time_match.group(2))
                    
                    html_time = html_acquisition_time.time()
                    start_time = html_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                    
                    # 時間が経過しているかチェック
                    if html_time >= start_time:
                        return False
                    else:
                        return True
            
            return False
            
        except Exception as e:
            print(f"❌ 働き状況判定エラー: {e}")
            return False

if __name__ == "__main__":
    test_cityheaven_new_parser()
