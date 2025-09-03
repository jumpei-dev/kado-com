#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全独立版のcityheaven parser テスト
"""

from bs4 import BeautifulSoup
from datetime import datetime
import re
from dataclasses import dataclass
from typing import Optional
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CastStatus:
    name: str
    is_working: bool
    business_id: str
    cast_id: str
    on_shift: bool
    shift_times: str
    working_times: str

class IndependentCityheavenParser:
    """完全独立版のCityheavenパーサー"""
    
    def parse_cast_list(self, html_content: str, html_acquisition_time: datetime) -> list[CastStatus]:
        """キャスト一覧を解析"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            cast_list = []
            
            # sugunavi_wrapperセクションを探す
            sugunavi_sections = soup.find_all('div', {'class': 'sugunavi_wrapper'})
            if not sugunavi_sections:
                logger.warning("sugunavi_wrapperセクションが見つかりません")
                return []
            
            logger.info(f"📋 {len(sugunavi_sections)} 個のsugunavi_wrapperセクション発見")
            
            # 各セクションを直接処理
            for i, section in enumerate(sugunavi_sections):
                try:
                    cast_status = self._parse_single_cast(section, html_acquisition_time)
                    if cast_status:
                        cast_list.append(cast_status)
                        if i < 5:  # 最初の5件のみデバッグ表示
                            logger.info(f"✅ キャスト{i+1}: ID={cast_status.cast_id}, 稼働中={cast_status.is_working}")
                except Exception as e:
                    logger.error(f"キャスト{i+1}の解析エラー: {e}")
                    continue
            
            logger.info(f"✅ キャスト解析完了: {len(cast_list)}/{len(sugunavi_sections)} 人")
            return cast_list
            
        except Exception as e:
            logger.error(f"HTML解析エラー: {e}")
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
                on_shift=True,
                shift_times="",
                working_times=""
            )
            
            return cast_status
            
        except Exception as e:
            logger.error(f"単一キャスト解析エラー: {e}")
            return None
    
    def _extract_cast_id(self, cast_element) -> Optional[str]:
        """キャストIDを抽出"""
        try:
            all_a_elements = cast_element.find_all('a', href=True)
            
            for a_element in all_a_elements:
                href = a_element.get('href', '')
                match = re.search(r'girlid-(\d+)', href)
                if match:
                    cast_id = match.group(1)
                    return cast_id
            
            return None
            
        except Exception as e:
            logger.error(f"キャストID抽出エラー: {e}")
            return None
    
    def _determine_working_status(self, cast_element, html_acquisition_time: datetime) -> bool:
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
                    
                    # HTML取得時刻と比較
                    html_time = html_acquisition_time.time()
                    start_time = html_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                    
                    # 時間が経過しているかチェック
                    if html_time >= start_time:
                        return False  # 時間経過済み
                    else:
                        return True   # 待機中
            
            return False
            
        except Exception as e:
            logger.error(f"働き状況判定エラー: {e}")
            return False

def main():
    """メイン処理"""
    html_file = "/Users/admin/Projects/kado-com/data/raw_html/cityhaven/人妻城_cast_list_20250825_215250.html"
    
    # HTMLファイルを読み込み
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # HTML取得時刻
    html_acquisition_time = datetime(2025, 8, 25, 21, 52, 50)
    
    # パーサーをインスタンス化
    parser = IndependentCityheavenParser()
    
    print(f"📋 HTML内容長: {len(html_content)} 文字")
    print(f"⏰ HTML取得時刻: {html_acquisition_time}")
    
    # パース実行
    cast_list = parser.parse_cast_list(html_content, html_acquisition_time)
    
    print(f"\n=== 最終結果 ===")
    print(f"総キャスト数: {len(cast_list)}")
    
    # 稼働中のキャストをカウント
    working_count = sum(1 for cast in cast_list if cast.is_working)
    print(f"稼働中のキャスト: {working_count} 人")
    
    if working_count > 0:
        print("\n--- 稼働中キャスト詳細 ---")
        working_casts = [cast for cast in cast_list if cast.is_working]
        for i, cast_status in enumerate(working_casts[:5]):  # 最初の5件
            print(f"  {i+1}. ID={cast_status.cast_id}, 稼働={cast_status.is_working}")

if __name__ == "__main__":
    main()
