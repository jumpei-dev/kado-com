#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細デバッグパーサーの結果をデータベースに保存するテストツール
"""

from bs4 import BeautifulSoup
from datetime import datetime
import re
import asyncio
from typing import Dict, List, Any, Optional
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# 環境変数から接続情報を取得（修正版）
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.pqnrfxibgtixwxicafdy:kado-com-2024@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres')

class DetailedCityheavenParserWithDB:
    """詳細デバッグ機能付きCityheavenパーサー（DB保存機能付き）"""
    
    def __init__(self, log_level=None):
        """
        初期化
        Args:
            log_level: "DEBUG" | "INFO" | "ERROR" | None (自動判定)
        """
        self.log_level = log_level or self._get_log_level()
        self.connection = None
        self.processed_count = 0
        self.logged_count = 0
        self.max_log_casts = int(os.getenv('LOG_MAX_CASTS', '10'))
        self._connect_to_db()
        
        print(f"🎯 ログレベル: {self.log_level}")
        print(f"📝 最大ログ出力数: {self.max_log_casts}キャスト")
    
    def _get_log_level(self):
        """環境に応じたログレベル取得"""
        if os.getenv('GITHUB_ACTIONS') == 'true':
            return "INFO"  # GitHub Actions実行時は簡潔ログ
        elif os.getenv('DEBUG_MODE') == 'true':
            return "DEBUG"  # ローカルデバッグ時は詳細ログ
        else:
            return "INFO"   # 通常時は簡潔ログ
    
    def _connect_to_db(self):
        """データベースに接続"""
        try:
            self.connection = psycopg2.connect(DATABASE_URL)
            print("✅ データベース接続成功")
        except Exception as e:
            print(f"❌ データベース接続エラー: {e}")
            self.connection = None
    
    async def parse_and_save_cast_data(self, soup: BeautifulSoup, business_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        """キャストデータをパース＆DB保存"""
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
            
            # 3. 全件を処理（出勤中の場合は詳細HTML出力）
            on_shift_count = 0
            for i, wrapper in enumerate(target_wrappers):
                try:
                    cast_data = await self._process_wrapper(wrapper, business_id, current_time)
                    if cast_data:
                        cast_list.append(cast_data)
                        if cast_data['is_on_shift']:
                            on_shift_count += 1
                            # 出勤中キャストが多すぎる場合は最初の5件のみ詳細出力
                            if on_shift_count <= 5:
                                print(f"📝 出勤中キャスト {on_shift_count}/5 の詳細を表示中...")
                            elif on_shift_count == 6:
                                print(f"⚠️ 出勤中キャストが多いため、残りの詳細出力をスキップします")
                        
                except Exception as extract_error:
                    print(f"❌ キャスト{i+1}抽出エラー: {extract_error}")
            
            print(f"🎯 パース完了: {len(cast_list)}件のキャスト情報を抽出")
            
            # 4. データベースに保存
            if cast_list:
                await self._save_to_database(cast_list, business_id, current_time)
            else:
                print("⚠️ 保存対象のキャストデータがありません")
                    
        except Exception as e:
            print(f"パース&保存エラー: {str(e)}")
            
        return cast_list

    async def _process_wrapper(self, wrapper_element, business_id: str, current_time: datetime) -> Optional[Dict[str, Any]]:
        """wrapper処理（HTML内容出力付き）"""
        try:
            # cast_idの抽出
            cast_id = self._extract_cast_id(wrapper_element)
            if not cast_id:
                return None
            
            # 判定実行
            is_on_shift = self._determine_on_shift(wrapper_element, current_time)
            is_working = self._determine_working(wrapper_element, current_time, is_on_shift)
            
            # 出勤中の場合は詳細HTML内容を出力（最初の5件のみ）
            if is_on_shift:
                # グローバルカウンタの代わりに、簡易的に判定
                cast_id_num = int(cast_id) if cast_id.isdigit() else 0
                if cast_id_num % 7 == 0:  # 約7件に1件の割合で詳細出力
                    self._output_html_details(cast_id, wrapper_element, current_time, is_on_shift, is_working)
            
            return {
                'business_id': business_id,
                'cast_id': cast_id,
                'is_working': is_working,
                'is_on_shift': is_on_shift,
                'recorded_at': current_time,
                'extraction_type': 'manual_debug'
            }
            
        except Exception as e:
            print(f"wrapper処理エラー: {str(e)}")
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
        """is_working判定（受付終了=完売として稼働中扱い）"""
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
    
    def _output_html_details(self, cast_id: str, wrapper_element, current_time: datetime, 
                            is_on_shift: bool, is_working: bool):
        """出勤中キャストの詳細HTML内容を出力"""
        
        print(f"\n{'='*80}")
        print(f"🔍 出勤中キャスト詳細 - ID: {cast_id}")
        print(f"{'='*80}")
        print(f"📅 HTML取得時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 判定結果: on_shift={is_on_shift}, is_working={is_working}")
        
        # 1. 出勤時間の詳細
        print(f"\n⏰ 出勤時間情報:")
        time_elements = wrapper_element.find_all(class_=lambda x: x and 'shukkin_detail_time' in str(x))
        if time_elements:
            for i, time_element in enumerate(time_elements, 1):
                time_text = time_element.get_text(strip=True)
                print(f"   出勤時間{i}: '{time_text}'")
                print(f"   HTML: {time_element}")
        else:
            print("   ❌ 出勤時間要素が見つかりません")
        
        # 2. 待機状態表記の詳細
        print(f"\n💼 待機状態表記:")
        suguna_box = wrapper_element.find(class_='sugunavibox')
        if suguna_box:
            title_elements = suguna_box.find_all(class_='title')
            if title_elements:
                for i, title_element in enumerate(title_elements, 1):
                    title_text = title_element.get_text(strip=True)
                    print(f"   待機状態{i}: '{title_text}'")
                    print(f"   HTML: {title_element}")
            else:
                print("   ❌ title要素が見つかりません")
            
            # sugunaviboxの全体コンテンツ
            print(f"\n📦 sugunavibox全体:")
            full_content = suguna_box.get_text(strip=True)
            print(f"   テキスト: '{full_content}'")
            print(f"   HTML: {suguna_box}")
        else:
            print("   ❌ sugunavibox要素が見つかりません")
        
        # 3. 判定ロジックの詳細説明
        print(f"\n🧮 判定ロジック詳細:")
        print(f"   【出勤判定】HTML取得時刻({current_time.hour:02d}:{current_time.minute:02d})が出勤時間内かどうか")
        
        if time_elements:
            for time_element in time_elements:
                time_text = time_element.get_text(strip=True)
                is_休み = self._is_休み_or_調整中(time_text)
                is_in_range = self._is_current_time_in_range(time_text, current_time)
                print(f"     '{time_text}' → 休み/調整中: {is_休み}, 時間範囲内: {is_in_range}")
        
        print(f"   【稼働判定】")
        if suguna_box:
            full_content = suguna_box.get_text(strip=True)
            
            # 受付終了チェック
            if '受付終了' in full_content:
                print(f"     '受付終了' を検出 → 完売状態のため is_working=True")
            else:
                title_elements = suguna_box.find_all(class_='title')
                for title_element in title_elements:
                    title_text = title_element.get_text(strip=True)
                    is_current_or_later = self._is_time_current_or_later(title_text, current_time)
                    
                    # 時間差の詳細計算
                    time_patterns = re.findall(r'(\d{1,2}):(\d{2})', title_text)
                    if time_patterns:
                        hour, minute = int(time_patterns[0][0]), int(time_patterns[0][1])
                        target_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        time_diff = (target_time - current_time).total_seconds() / 60
                        print(f"     '{title_text}' → 現在時刻以降: {is_current_or_later}")
                        print(f"       💡 詳細計算: {hour:02d}:{minute:02d} - {current_time.hour:02d}:{current_time.minute:02d} = {time_diff:.1f}分{'後' if time_diff >= 0 else '前'}")
                    else:
                        print(f"     '{title_text}' → 時刻なし")
        
        print(f"   最終結果: on_shift={is_on_shift} → is_working={is_working}")
        print(f"{'='*80}\n")
    
    async def _save_to_database(self, cast_list: List[Dict[str, Any]], business_id: str, current_time: datetime):
        """データベースに保存（修正版）"""
        try:
            if not self.connection:
                print("❌ データベース接続がありません")
                return
            
            print(f"\n💾 データベース保存開始: {len(cast_list)}件のレコード")
            
            # カーソルを作成
            cursor = self.connection.cursor()
            
            # 保存SQL
            insert_sql = """
                INSERT INTO status (
                    business_id, cast_id, is_working, is_on_shift, recorded_at, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            # バッチで保存
            success_count = 0
            for cast_data in cast_list:
                try:
                    cursor.execute(insert_sql, (
                        cast_data['business_id'],
                        cast_data['cast_id'],
                        cast_data['is_working'],
                        cast_data['is_on_shift'],
                        cast_data['recorded_at'],
                        current_time,  # created_at
                        current_time   # updated_at
                    ))
                    success_count += 1
                except Exception as save_error:
                    print(f"❌ レコード保存エラー (cast_id: {cast_data['cast_id']}): {save_error}")
            
            # コミット
            self.connection.commit()
            cursor.close()
            
            print(f"✅ データベース保存完了: {success_count}/{len(cast_list)}件成功")
            
            # 保存結果の詳細
            working_count = sum(1 for cast in cast_list if cast['is_working'])
            on_shift_count = sum(1 for cast in cast_list if cast['is_on_shift'])
            
            print(f"📊 保存内容サマリー:")
            print(f"   総キャスト: {len(cast_list)} 人")
            print(f"   出勤中: {on_shift_count} 人")
            print(f"   稼働中: {working_count} 人")
            print(f"   保存成功: {success_count} 人")
            
        except Exception as e:
            print(f"❌ データベース保存エラー: {e}")
            import traceback
            traceback.print_exc()
            
            # ロールバック
            if self.connection:
                self.connection.rollback()
    
    def get_business_from_db(self) -> Optional[Dict[str, Any]]:
        """Businessテーブルから最初のレコードを取得"""
        try:
            if not self.connection:
                print("❌ データベース接続がありません")
                return None
                
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM business LIMIT 1")
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            print(f"❌ Business取得エラー: {e}")
            return None
    
    def __del__(self):
        """デストラクタ"""
        if self.connection:
            self.connection.close()


async def test_save_to_database():
    """データベース保存テスト"""
    
    print("💾 詳細デバッグパーサー結果のデータベース保存テスト開始")
    print("="*100)
    
    try:
        # HTMLファイルを読み込み
        html_file = "/Users/admin/Projects/kado-com/data/raw_html/cityhaven/人妻城_cast_list_20250825_215250.html"
        
        if not os.path.exists(html_file):
            print(f"❌ HTMLファイルが見つかりません: {html_file}")
            return
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # HTML取得時刻（ファイルの作成時刻）
        current_time = datetime(2025, 8, 25, 21, 52, 50)
        
        # BeautifulSoupでパース
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # パーサーをインスタンス化
        parser = DetailedCityheavenParserWithDB()
        
        print(f"📋 HTML内容長: {len(html_content)} 文字")
        print(f"⏰ HTML取得時刻: {current_time}")
        print(f"🏪 店舗ID: 12345678")  # 人妻城のbusiness_id
        print()
        
        # パース＆保存実行
        cast_list = await parser.parse_and_save_cast_data(soup, "12345678", current_time)
        
        print(f"\n🎯 最終結果サマリー")
        print("="*100)
        print(f"総処理件数: {len(cast_list)}")
        
        working_count = sum(1 for cast in cast_list if cast['is_working'])
        on_shift_count = sum(1 for cast in cast_list if cast['is_on_shift'])
        
        print(f"出勤中キャスト: {on_shift_count} 人")
        print(f"稼働中キャスト: {working_count} 人")
        
        if working_count > 0:
            print(f"\n✅ 稼働中キャスト（DB保存済み）:")
            working_casts = [cast for cast in cast_list if cast['is_working']]
            for i, cast in enumerate(working_casts[:5]):  # 最大5件表示
                print(f"  {i+1}. キャストID: {cast['cast_id']} (is_working: {cast['is_working']}, is_on_shift: {cast['is_on_shift']})")
            
            if len(working_casts) > 5:
                print(f"  ... 他 {len(working_casts) - 5}件")
        else:
            print(f"\n⚠️ 現在稼働中のキャストはいません")
        
        print(f"\n📊 データベース保存処理完了！")
        print(f"\n💡 Supabaseで確認するSQL:")
        print(f"SELECT cast_id, is_working, is_on_shift, recorded_at FROM status WHERE business_id = '12345678' ORDER BY recorded_at DESC LIMIT 10;")
        
    except Exception as e:
        print(f"❌ 処理エラー: {e}")
        import traceback
        traceback.print_exc()


async def test_save_live_data():
    """リアルタイムデータのデータベース保存テスト"""
    
    print("🌐 リアルタイムデータのデータベース保存テスト開始")
    print("="*100)
    
    try:
        import requests
        
        # パーサーをインスタンス化
        parser = DetailedCityheavenParserWithDB()
        
        # データベースから店舗情報取得
        business = parser.get_business_from_db()
        
        if not business:
            print("❌ Businessレコードが見つかりません")
            return
            
        url = business.get("url")
        business_name = business.get("name", "不明")
        business_id = business.get("id", "unknown")
        
        print(f"🏪 店舗名: {business_name}")
        print(f"🆔 店舗ID: {business_id}")
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
        
        # パース＆保存実行
        cast_list = await parser.parse_and_save_cast_data(soup, business_id, current_time)
        
        print(f"\n🎯 リアルタイム保存結果")
        print("="*100)
        print(f"総処理件数: {len(cast_list)}")
        
        working_count = sum(1 for cast in cast_list if cast['is_working'])
        on_shift_count = sum(1 for cast in cast_list if cast['is_on_shift'])
        
        print(f"出勤中キャスト: {on_shift_count} 人")
        print(f"稼働中キャスト: {working_count} 人")
        
        print(f"\n📊 リアルタイムデータベース保存完了！")
        
    except Exception as e:
        print(f"❌ リアルタイム処理エラー: {e}")
        import traceback
        traceback.print_exc()


def main():
    """メイン関数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "live":
        # リアルタイムデータの保存
        asyncio.run(test_save_live_data())
    else:
        # ファイルからのデータ保存
        asyncio.run(test_save_to_database())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
