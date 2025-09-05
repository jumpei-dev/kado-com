#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細デバッグパーサーの結果をデータベースに保存する実用的テストツール
"""

import sys
import os
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Any, Optional

# バッチモジュールを追加
sys.path.append('./batch')

try:
    from core.database import DatabaseManager
    print("✅ DatabaseManager インポート成功")
except ImportError as e:
    print(f"❌ DatabaseManager インポートエラー: {e}")
    sys.exit(1)

class ManualStatusCollector:
    """手動ステータス収集ツール"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def parse_cast_data(self, soup: BeautifulSoup, business_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        """キャストデータをパース（改良版ロジック使用）"""
        cast_list = []
        
        try:
            # sugunaviboxを含むwrapperを特定
            sugunavi_wrappers = soup.find_all('div', class_='sugunavi_wrapper')
            target_wrappers = [w for w in sugunavi_wrappers if w.find(class_='sugunavibox')]
            
            print(f"📦 対象wrapper: {len(target_wrappers)}個")
            
            for wrapper in target_wrappers:
                cast_data = self._process_wrapper(wrapper, business_id, current_time)
                if cast_data:
                    cast_list.append(cast_data)
            
            return cast_list
            
        except Exception as e:
            print(f"❌ パースエラー: {e}")
            return []
    
    def _process_wrapper(self, wrapper_element, business_id: str, current_time: datetime) -> Optional[Dict[str, Any]]:
        """wrapper処理"""
        try:
            cast_id = self._extract_cast_id(wrapper_element)
            if not cast_id:
                return None
            
            is_on_shift = self._determine_on_shift(wrapper_element, current_time)
            is_working = self._determine_working(wrapper_element, current_time, is_on_shift)
            
            return {
                'business_id': business_id,
                'cast_id': cast_id,
                'is_working': is_working,
                'is_on_shift': is_on_shift,
                'collected_at': current_time
            }
        except:
            return None
    
    def _extract_cast_id(self, wrapper_element) -> Optional[str]:
        """cast_id抽出"""
        try:
            for a_element in wrapper_element.find_all('a', href=True):
                match = re.search(r'girlid-(\d+)', a_element['href'])
                if match:
                    return match.group(1)
            return None
        except:
            return None
    
    def _determine_on_shift(self, wrapper_element, current_time: datetime) -> bool:
        """on_shift判定"""
        try:
            time_elements = wrapper_element.find_all(class_=lambda x: x and 'shukkin_detail_time' in str(x))
            for time_element in time_elements:
                time_text = time_element.get_text(strip=True)
                
                # 休み判定
                if any(keyword in time_text for keyword in ['お休み', '調整中', 'OFF']):
                    return False
                
                # 時間範囲判定
                if self._is_current_time_in_range(time_text, current_time):
                    return True
            return False
        except:
            return False
    
    def _determine_working(self, wrapper_element, current_time: datetime, is_on_shift: bool) -> bool:
        """is_working判定"""
        try:
            if not is_on_shift:
                return False
            
            suguna_box = wrapper_element.find(class_='sugunavibox')
            if not suguna_box:
                return False
            
            full_content = suguna_box.get_text(strip=True)
            
            # 受付終了 = 完売状態 = 稼働中として扱う
            if '受付終了' in full_content:
                return True
            
            # 時刻ベースの判定
            title_elements = suguna_box.find_all(class_='title')
            for title_element in title_elements:
                title_text = title_element.get_text(strip=True)
                if self._is_time_current_or_later(title_text, current_time):
                    return True
            
            return False
        except:
            return False
    
    def _is_current_time_in_range(self, time_text: str, current_time: datetime) -> bool:
        """時間範囲判定"""
        try:
            match = re.search(r'(\d{1,2}):(\d{2})[\s～〜\-~]+(\d{1,2}):(\d{2})', time_text)
            if match:
                start_hour, start_min, end_hour, end_min = map(int, match.groups())
                
                current_minutes = current_time.hour * 60 + current_time.minute
                start_minutes = start_hour * 60 + start_min
                end_minutes = end_hour * 60 + end_min
                
                if start_minutes <= end_minutes:
                    return start_minutes <= current_minutes <= end_minutes
                else:
                    return current_minutes >= start_minutes or current_minutes <= end_minutes
            return False
        except:
            return False
    
    def _is_time_current_or_later(self, title_text: str, current_time: datetime) -> bool:
        """現在時刻以降判定"""
        try:
            time_patterns = re.findall(r'(\d{1,2}):(\d{2})', title_text)
            for hour_str, min_str in time_patterns:
                hour, minute = int(hour_str), int(min_str)
                target_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                time_diff = (target_time - current_time).total_seconds() / 60
                if time_diff >= 0:
                    return True
            return False
        except:
            return False
    
    def save_to_database(self, cast_list: List[Dict[str, Any]]) -> bool:
        """データベースに保存"""
        try:
            if not cast_list:
                print("⚠️ 保存対象のデータがありません")
                return False
            
            print(f"💾 データベース保存開始: {len(cast_list)}件")
            
            # CastStatus形式でデータを保存
            success_count = 0
            for cast_data in cast_list:
                try:
                    # 手動でINSERTクエリを実行
                    query = """
                        INSERT INTO cast_status (business_id, cast_id, is_working, is_on_shift, collected_at, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    current_time = datetime.now()
                    params = (
                        cast_data['business_id'],
                        cast_data['cast_id'],
                        cast_data['is_working'],
                        cast_data['is_on_shift'],
                        cast_data['collected_at'],
                        current_time,
                        current_time
                    )
                    
                    # データベース操作（簡単な方法）
                    self.db.execute_query(query, params)
                    success_count += 1
                    
                except Exception as save_error:
                    print(f"❌ 保存エラー (cast_id: {cast_data.get('cast_id')}): {save_error}")
            
            print(f"✅ 保存完了: {success_count}/{len(cast_list)}件成功")
            return success_count > 0
            
        except Exception as e:
            print(f"❌ データベース保存エラー: {e}")
            return False

async def test_from_html_file():
    """HTMLファイルからのテスト"""
    print("📁 HTMLファイルからのテスト実行")
    print("="*80)
    
    # HTMLファイル読み込み
    html_file = "/Users/admin/Projects/kado-com/data/raw_html/cityhaven/人妻城_cast_list_20250825_215250.html"
    
    if not os.path.exists(html_file):
        print(f"❌ HTMLファイルが見つかりません: {html_file}")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    current_time = datetime(2025, 8, 25, 21, 52, 50)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # パース実行
    collector = ManualStatusCollector()
    cast_list = collector.parse_cast_data(soup, "hitozuma_shiro", current_time)
    
    # 結果表示
    working_count = sum(1 for cast in cast_list if cast['is_working'])
    on_shift_count = sum(1 for cast in cast_list if cast['is_on_shift'])
    
    print(f"🎯 解析結果:")
    print(f"  総キャスト: {len(cast_list)} 人")
    print(f"  出勤中: {on_shift_count} 人")
    print(f"  稼働中: {working_count} 人")
    
    # データベース保存
    if cast_list:
        success = collector.save_to_database(cast_list)
        if success:
            print("✅ データベース保存成功")
        else:
            print("❌ データベース保存失敗")
    
    return cast_list

def main():
    """メイン関数"""
    print("🎯 手動ステータス収集＆DB保存ツール")
    print("="*100)
    print(f"⏰ 実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        cast_data = asyncio.run(test_from_html_file())
        print(f"\n🏁 処理完了: {len(cast_data) if cast_data else 0}件処理")
        
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
