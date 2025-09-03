#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
リアルタイム人妻城解析デバッグツール
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import asyncio
from typing import Dict, List, Any, Optional
import sys
import os

# バッチモジュールを追加
sys.path.append('./batch')
from core.database import DatabaseManager

class LiveDetailedCityheavenParser:
    """リアルタイム詳細デバッグ機能付きCityheavenパーサー"""
    
    async def parse_cast_data(self, soup: BeautifulSoup, business_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        """キャストデータをパース（出勤中キャストのみ詳細デバッグ出力）"""
        cast_list = []
        
        try:
            # 1. sugunavi_wrapperを全て取得
            sugunavi_wrappers = soup.find_all('div', class_='sugunavi_wrapper')
            print(f"📦 sugunavi_wrapper要素: {len(sugunavi_wrappers)}個発見")
            
            # 2. その中でsugunaviboxを含むものを特定
            target_wrappers = []
            for wrapper in sugunavi_wrappers:
                suguna_box = wrapper.find(class_='sugunavibox')
                if suguna_box:
                    target_wrappers.append(wrapper)
            
            print(f"🎯 sugunaviboxを含むwrapper: {len(target_wrappers)}個（期待範囲: 5-40個）")
            
            # 3. 全件を処理し、on_shiftのキャストは詳細デバッグ出力
            for i, wrapper in enumerate(target_wrappers):
                try:
                    # まず簡単にon_shift判定
                    is_on_shift_preview = self._determine_on_shift(wrapper, current_time)
                    
                    if is_on_shift_preview:
                        # on_shiftの場合は詳細デバッグ出力
                        cast_data = await self._process_wrapper_with_debug(wrapper, business_id, current_time)
                    else:
                        # on_shiftでない場合は簡単に処理
                        cast_data = await self._process_wrapper_simple(wrapper, business_id, current_time)
                    
                    if cast_data:
                        cast_list.append(cast_data)
                        
                except Exception as extract_error:
                    print(f"❌ キャスト{i+1}抽出エラー: {extract_error}")
            
            print(f"🎯 リアルタイム解析完了: {len(cast_list)}件のキャスト情報を抽出")
                    
        except Exception as e:
            print(f"解析エラー: {str(e)}")
            
        return cast_list

    async def _process_wrapper_with_debug(self, wrapper_element, business_id: str, current_time: datetime) -> Optional[Dict[str, Any]]:
        """詳細デバッグ付きwrapper処理"""
        try:
            # cast_idの抽出
            cast_id = self._extract_cast_id(wrapper_element)
            if not cast_id:
                return None
            
            # 判定実行
            is_on_shift = self._determine_on_shift(wrapper_element, current_time)
            is_working = self._determine_working(wrapper_element, current_time, is_on_shift)
            
            # 詳細デバッグ出力
            self._output_detailed_debug(cast_id, wrapper_element, current_time, is_on_shift, is_working)
            
            return {
                'business_id': business_id,
                'cast_id': cast_id,
                'is_working': is_working,
                'is_on_shift': is_on_shift,
                'collected_at': current_time,
                'extraction_type': 'live'
            }
            
        except Exception as e:
            print(f"wrapper処理エラー: {str(e)}")
            return None
    
    async def _process_wrapper_simple(self, wrapper_element, business_id: str, current_time: datetime) -> Optional[Dict[str, Any]]:
        """簡単なwrapper処理"""
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
                'collected_at': current_time,
                'extraction_type': 'live'
            }
            
        except Exception:
            return None

    def _extract_cast_id(self, wrapper_element) -> Optional[str]:
        """cast_id抽出"""
        try:
            a_elements = wrapper_element.find_all('a', href=True)
            
            for a_element in a_elements:
                href = a_element['href']
                match = re.search(r'girlid-(\d+)', href)
                if match:
                    return match.group(1)
            return None
        except Exception:
            return None
    
    def _determine_on_shift(self, wrapper_element, current_time: datetime) -> bool:
        """on_shift判定（シンプル版: HTML取得時点が出勤時間内かどうかのみ）"""
        try:
            time_elements = wrapper_element.find_all(class_=lambda x: x and 'shukkin_detail_time' in str(x))
            if not time_elements:
                return False
            
            for time_element in time_elements:
                time_text = time_element.get_text(strip=True)
                
                if self._is_休み_or_調整中(time_text):
                    return False
                
                if self._is_current_time_in_range(time_text, current_time):
                    return True
            
            return False
        except Exception:
            return False
    
    def _determine_working(self, wrapper_element, current_time: datetime, is_on_shift: bool) -> bool:
        """is_working判定"""
        try:
            if not is_on_shift:
                return False
            
            suguna_box = wrapper_element.find(class_='sugunavibox')
            if not suguna_box:
                return False
            
            title_elements = suguna_box.find_all(class_='title')
            if not title_elements:
                return False
            
            for title_element in title_elements:
                title_text = title_element.get_text(strip=True)
                
                if self._is_time_current_or_later(title_text, current_time):
                    return True
            
            return False
        except Exception:
            return False
    
    def _is_休み_or_調整中(self, time_text: str) -> bool:
        """お休み/調整中判定"""
        休み_keywords = ['お休み', '出勤調整中', '次回', '出勤予定', '調整中', 'OFF', 'お疲れ様']
        return any(keyword in time_text for keyword in 休み_keywords)
    
    def _is_current_time_in_range(self, time_text: str, current_time: datetime) -> bool:
        """時間範囲判定"""
        try:
            time_pattern = r'(\d{1,2}):(\d{2})[\s～〜\-~]+(\d{1,2}):(\d{2})'
            match = re.search(time_pattern, time_text)
            
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
        except Exception:
            return False
    
    def _is_time_current_or_later(self, title_text: str, current_time: datetime) -> bool:
        """現在時刻以降判定"""
        try:
            time_patterns = re.findall(r'(\d{1,2}):(\d{2})', title_text)
            
            if not time_patterns:
                return False
            
            for hour_str, min_str in time_patterns:
                hour, minute = int(hour_str), int(min_str)
                target_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                time_diff = (target_time - current_time).total_seconds() / 60
                
                if time_diff >= 0:
                    return True
            
            return False
        except Exception:
            return False
    
    def _output_detailed_debug(self, cast_id: str, wrapper_element, current_time: datetime, 
                              is_on_shift: bool, is_working: bool):
        """詳細デバッグ出力"""
        
        print(f"\n{'='*80}")
        print(f"🔍 リアルタイムデバッグ - キャスト ID: {cast_id}")
        print(f"{'='*80}")
        
        print(f"📅 現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 出勤時間の詳細
        print(f"\n⏰ 出勤時間情報:")
        time_elements = wrapper_element.find_all(class_=lambda x: x and 'shukkin_detail_time' in str(x))
        if time_elements:
            for i, time_element in enumerate(time_elements, 1):
                time_text = time_element.get_text(strip=True)
                print(f"   出勤時間{i}: '{time_text}'")
        else:
            print("   ❌ 出勤時間要素が見つかりません")
        
        # 待機状態表記の詳細
        print(f"\n💼 待機状態表記:")
        suguna_box = wrapper_element.find(class_='sugunavibox')
        if suguna_box:
            title_elements = suguna_box.find_all(class_='title')
            if title_elements:
                for i, title_element in enumerate(title_elements, 1):
                    title_text = title_element.get_text(strip=True)
                    print(f"   待機状態{i}: '{title_text}'")
            else:
                print("   ❌ title要素が見つかりません")
            
            full_content = suguna_box.get_text(strip=True)
            print(f"\n📦 sugunavibox全体: '{full_content}'")
        else:
            print("   ❌ sugunavibox要素が見つかりません")
        
        print(f"\n🎯 判定結果:")
        print(f"   is_on_shift (出勤中): {is_on_shift}")
        print(f"   is_working (稼働中): {is_working}")
        
        # 判定ロジックの詳細
        print(f"\n🧮 判定詳細:")
        print(f"   【出勤判定】現在時刻({current_time.hour:02d}:{current_time.minute:02d})が出勤時間内かどうか")
        
        if time_elements:
            for time_element in time_elements:
                time_text = time_element.get_text(strip=True)
                is_休み = self._is_休み_or_調整中(time_text)
                is_in_range = self._is_current_time_in_range(time_text, current_time)
                print(f"     '{time_text}' → 休み/調整中: {is_休み}, 時間範囲内: {is_in_range}")
        
        print(f"   【稼働判定】")
        if suguna_box and title_elements:
            for title_element in title_elements:
                title_text = title_element.get_text(strip=True)
                is_current_or_later = self._is_time_current_or_later(title_text, current_time)
                
                time_patterns = re.findall(r'(\d{1,2}):(\d{2})', title_text)
                if time_patterns:
                    hour, minute = int(time_patterns[0][0]), int(time_patterns[0][1])
                    target_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    time_diff = (target_time - current_time).total_seconds() / 60
                    print(f"     '{title_text}' → 現在時刻以降: {is_current_or_later}")
                    print(f"       💡 計算: {hour:02d}:{minute:02d} - {current_time.hour:02d}:{current_time.minute:02d} = {time_diff:.1f}分{'後' if time_diff >= 0 else '前'}")
                else:
                    print(f"     '{title_text}' → 時刻なし")
        
        print(f"{'='*80}\n")


async def test_live_debug():
    """リアルタイム解析テスト"""
    
    print("🌐 リアルタイム人妻城解析開始")
    print("="*100)
    
    try:
        # データベースから店舗情報取得
        db = DatabaseManager()
        businesses = db.get_businesses()
        
        if not businesses:
            print("❌ Businessレコードが見つかりません")
            return
            
        first_business = businesses[0]
        url = first_business.get("URL")
        business_name = first_business.get("name", "不明")
        
        print(f"🏪 店舗名: {business_name}")
        print(f"🔗 URL: {url}")
        
        if not url:
            print("❌ URLが設定されていません")
            return
        
        # 現在時刻
        current_time = datetime.now()
        print(f"⏰ 現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # HTMLを取得
        print("\n📥 HTMLを取得中...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        html_content = response.text
        
        print(f"📋 HTML取得完了: {len(html_content)} 文字")
        
        # BeautifulSoupでパース
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # パーサーをインスタンス化して解析
        parser = LiveDetailedCityheavenParser()
        cast_list = await parser.parse_cast_data(soup, "hitozuma_shiro", current_time)
        
        print(f"\n🎯 最終結果サマリー")
        print("="*100)
        print(f"総キャスト数: {len(cast_list)}")
        
        working_count = sum(1 for cast in cast_list if cast['is_working'])
        on_shift_count = sum(1 for cast in cast_list if cast['is_on_shift'])
        
        print(f"出勤中キャスト: {on_shift_count} 人")
        print(f"稼働中キャスト: {working_count} 人")
        
        if working_count > 0:
            print(f"\n✅ 稼働中キャスト:")
            working_casts = [cast for cast in cast_list if cast['is_working']]
            for i, cast in enumerate(working_casts):
                print(f"  {i+1}. キャストID: {cast['cast_id']}")
        else:
            print(f"\n⚠️ 現在稼働中のキャストはいません")
            
        print(f"\n📊 リアルタイム解析完了！")
        
    except requests.RequestException as e:
        print(f"❌ HTTP リクエストエラー: {e}")
    except Exception as e:
        print(f"❌ 解析エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_live_debug())
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
