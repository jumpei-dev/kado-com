"""
Cityheaven用パーサー（新実装）

HTMLコンテンツから直接CastStatusを抽出するパーサー実装
"""

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re
import logging

try:
    from ...core.models import CastStatus
except ImportError:
    try:
        from core.models import CastStatus
    except ImportError as e:
        print(f"CastStatus import failed: {e}")
        # Fallback CastStatus definition
        class CastStatus:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    try:
        from utils.logging_utils import get_logger
    except ImportError:
        def get_logger(name):
            import logging
            return logging.getLogger(name)

logger = get_logger(__name__)


class CityheavenParserBase(ABC):
    """Cityheavenパーサーの基底クラス"""
    
    @abstractmethod
    async def parse_cast_list(self, html_content: str, html_acquisition_time: datetime, dom_check_mode: bool = False, business_id: str = "test") -> List['CastStatus']:
        """
        HTMLコンテンツからCastStatusオブジェクトのリストを生成
        
        Args:
            html_content: HTMLコンテンツ
            html_acquisition_time: HTML取得時刻
            dom_check_mode: DOM確認モード
            business_id: 店舗ID
            
        Returns:
            CastStatusオブジェクトのリスト
        """
        pass


class CityheavenTypeAAAParser(CityheavenParserBase):
    """type=a,a,a パターン用パーサー（指示書準拠）"""
    
    def __init__(self):
        self.dom_check_mode = False  # DOM確認モードフラグ
    
    async def parse_cast_list(self, html_content: str, html_acquisition_time: datetime, dom_check_mode: bool = False, business_id: str = "test") -> List['CastStatus']:
        """
        指示書準拠の type=a,a,a パターン
        
        条件:
        - Class名が"sugunavi_wrapper"のdiv要素
        - その中でsugunaviboxを含むものが対象（5-40個程度）
        
        Args:
            html_content: HTMLコンテンツ
            html_acquisition_time: HTML取得時刻
            dom_check_mode: 追加店舗DOM確認モード（HTML詳細出力）
            business_id: 店舗ID
        """
        # CastStatusクラスをインポート
        try:
            from ...core.models import CastStatus
        except ImportError:
            try:
                from core.models import CastStatus
            except ImportError:
                # CastStatusクラスが見つからない場合の仮実装
                class CastStatus:
                    def __init__(self, cast_id, cast_name, is_working, on_shift, collected_at):
                        self.cast_id = cast_id
                        self.cast_name = cast_name
                        self.is_working = is_working
                        self.on_shift = on_shift
                        self.collected_at = collected_at
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # DOM確認モードをインスタンス変数に設定
        self.dom_check_mode = dom_check_mode
        
        cast_list = []
        current_time = html_acquisition_time  # 変数名を統一
        
        # DOM確認モード用のヘッダー
        if dom_check_mode:
            print(f"\n🔍 【追加店舗DOM確認モード】")
            print(f"📅 HTML取得時刻: {html_acquisition_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
        
        try:
            # 1. sugunavi_wrapperを全て取得
            sugunavi_wrappers = soup.find_all('div', class_='sugunavi_wrapper')
            logger.info(f"📦 sugunavi_wrapper要素: {len(sugunavi_wrappers)}個発見")
            
            if dom_check_mode:
                print(f"📦 発見した要素: {len(sugunavi_wrappers)}個のsugunavi_wrapper")
            
            # 2. その中でsugunaviboxを含むものを特定
            target_wrappers = []
            for wrapper in sugunavi_wrappers:
                suguna_box = wrapper.find(class_='sugunavibox')
                if suguna_box:
                    target_wrappers.append(wrapper)
            
            logger.info(f"🎯 sugunaviboxを含むwrapper: {len(target_wrappers)}個（期待範囲: 5-40個）")
            
            if dom_check_mode:
                print(f"🎯 有効なキャスト要素: {len(target_wrappers)}個")
            
            if len(target_wrappers) == 0:
                logger.warning("⚠️ 対象wrapper要素が見つかりません")
                return cast_list
            
            # 3. 各target_wrapperを指示書通りに処理
            for i, wrapper in enumerate(target_wrappers):
                try:
                    cast_data = await self._process_wrapper_type_aaa(wrapper, business_id, current_time, dom_check_mode)
                    if cast_data:
                        cast_list.append(cast_data)
                        if dom_check_mode:
                            logger.debug(f"✅ キャスト情報抽出成功: {i+1}/{len(target_wrappers)} - {cast_data['cast_id']}")
                        else:
                            # 簡略版ログ：5件ごとに進捗表示
                            if (i + 1) % 5 == 0 or i == len(target_wrappers) - 1:
                                logger.info(f"✅ キャスト情報抽出進捗: {i+1}/{len(target_wrappers)}件処理完了")
                    else:
                        if dom_check_mode:
                            logger.debug(f"⚠️ キャスト情報抽出失敗: {i+1}/{len(target_wrappers)}")
                        
                except Exception as extract_error:
                    logger.error(f"❌ キャスト{i+1}抽出エラー: {extract_error}")
            
            # DOM確認モード用の最終サマリー
            if dom_check_mode:
                self._display_dom_check_summary(cast_list)
            
            logger.info(f"🎯 type=a,a,a パターン完了: {len(cast_list)}件のキャスト情報を抽出")
                    
        except Exception as e:
            logger.error(f"type=a,a,a パターン解析エラー: {str(e)}")
            
        return cast_list
    
    async def _process_wrapper_type_aaa(self, wrapper_element, business_id: str, current_time: datetime, dom_check_mode: bool = False) -> Optional[Dict[str, Any]]:
        """
        指示書準拠の単一wrapper要素処理 (type=a,a,a)
        
        指示書の抽出要件:
        1. cast_id: a要素のhrefからgirlid-xxxxxを抽出
        2. on_shift: shukkin_detail_timeの時間範囲と現在時刻を比較  
        3. is_working: sugunavibox内のclass="title"から時間を抽出し、現在時刻以降 & on_shift=true
        
        Args:
            dom_check_mode: 追加店舗DOM確認モード（HTML詳細出力）
        """
        
        try:
            # 1. cast_idの抽出（指示書準拠）
            cast_id = self._extract_cast_id_type_aaa(wrapper_element)
            if not cast_id:
                logger.debug("❌ cast_id抽出失敗: girlid-xxxxx形式が見つかりません")
                return None
            
            # 生データ抽出・出力機能を削除（ログ簡略化）
            
            # 2. on_shiftの判定（指示書準拠）
            is_on_shift = self._determine_on_shift_type_aaa(wrapper_element, current_time)
            
            # 3. is_workingの判定（指示書準拠）
            is_working = self._determine_working_type_aaa(wrapper_element, current_time, is_on_shift)
            
            # DOM確認モード時の詳細HTML出力
            if dom_check_mode and is_on_shift:
                self._output_cast_dom_details(cast_id, wrapper_element, current_time, is_on_shift, is_working)
            elif not dom_check_mode:
                # 通常時の簡潔デバッグ出力
                self._output_detailed_debug(cast_id, wrapper_element, current_time, is_on_shift, is_working)
            
            logger.debug(f"📊 キャスト{cast_id}: on_shift={is_on_shift}, is_working={is_working}")
            
            cast_result = {
                'business_id': business_id,
                'cast_id': cast_id,
                'is_working': is_working,
                'is_on_shift': is_on_shift,
                'collected_at': current_time,
                'extraction_type': 'aaa'
            }
            
            # JSON出力を削除（ログ簡略化）
            # logger.debug(f"キャスト{cast_id}: working={is_working}, on_shift={is_on_shift}")
            
            return cast_result
            
        except Exception as e:
            logger.error(f"wrapper処理エラー (type=aaa): {str(e)}")
            return None
    
    def _extract_cast_id_type_aaa(self, wrapper_element) -> Optional[str]:
        """
        指示書準拠のcast_id抽出 (type=a,a,a)
        
        要件: a要素のhrefにgirlid-xxxxxとあるのがcastID
        """
        
        try:
            # wrapper内のa要素を全て取得
            a_elements = wrapper_element.find_all('a', href=True)
            
            for a_element in a_elements:
                href = a_element['href']
                
                # girlid-xxxxxの部分を正規表現で抽出
                import re
                match = re.search(r'girlid-(\d+)', href)
                if match:
                    cast_id = match.group(1)  # 数値部分のみ
                    logger.debug(f"✅ cast_id抽出成功: {cast_id} from {href}")
                    return cast_id
            
            logger.debug("❌ cast_id抽出失敗: girlid-xxxxx形式が見つかりません")
            return None
            
        except Exception as e:
            logger.error(f"cast_id抽出エラー (type=aaa): {str(e)}")
            return None
    
    def _determine_on_shift_type_aaa(self, wrapper_element, current_time: datetime) -> bool:
        """
        指示書準拠のon_shift判定 (type=a,a,a)
        
        要件: class名に"shukkin_detail_time"があるもののコンテンツから時間帯を抽出し、
             現在時刻がその範囲内ならon_shift=true
        """
        
        try:
            # shukkin_detail_timeクラスの要素を探す（部分一致で検索）
            time_elements = wrapper_element.find_all(class_=lambda x: x and 'shukkin_detail_time' in str(x))
            
            if not time_elements:
                logger.debug("❌ shukkin_detail_time要素が見つからないためon_shift=False")
                return False
            
            for time_element in time_elements:
                time_text = time_element.get_text(strip=True)
                logger.debug(f"⏰ 時間テキスト発見: '{time_text}'")
                
                # お休みや調整中の場合はfalse
                if self._is_休み_or_調整中(time_text):
                    logger.debug(f"😴 お休み/調整中のためon_shift=False: '{time_text}'")
                    return False
                
                # 時間範囲の解析と判定
                if self._is_current_time_in_range_type_aaa(time_text, current_time):
                    logger.debug(f"✅ 現在時刻が範囲内のためon_shift=True: '{time_text}'")
                    return True
                else:
                    logger.debug(f"❌ 現在時刻が範囲外のためon_shift=False: '{time_text}'")
            
            return False
            
        except Exception as e:
            logger.error(f"on_shift判定エラー (type=aaa): {str(e)}")
            return False
    
    def _determine_working_type_aaa(self, wrapper_element, current_time: datetime, is_on_shift: bool) -> bool:
        """
        指示書準拠のis_working判定 (type=a,a,a)
        
        要件: 
        1. 「受付終了」がある場合は完売とみなしてis_working=true（ただしon_shift=trueの場合のみ）
        2. sugunavibox内のclass="title"から時間を抽出し、現在時刻以降の場合にis_working=true
        3. on_shift=trueが前提条件
        """
        
        try:
            # on_shiftがfalseなら即座にfalse
            if not is_on_shift:
                logger.debug("❌ on_shift=Falseのためis_working=False")
                return False
            
            # sugunavibox要素を探す
            suguna_box = wrapper_element.find(class_='sugunavibox')
            if not suguna_box:
                logger.debug("❌ sugunaviboxが見つからないためis_working=False")
                return False
            
            # sugunaviboxの全テキストを取得して「受付終了」をチェック
            suguna_box_text = suguna_box.get_text(strip=True)
            if '受付終了' in suguna_box_text:
                logger.debug(f"✅ 「受付終了」検出 → 完売状態のためis_working=True")
                return True
            
            # sugunavibox内のclass="title"要素を探す
            title_elements = suguna_box.find_all(class_='title')
            
            if not title_elements:
                logger.debug("❌ class='title'要素が見つからないためis_working=False")
                return False
            
            for title_element in title_elements:
                title_text = title_element.get_text(strip=True)
                logger.debug(f"📄 titleテキスト発見: '{title_text}'")
                
                # timeとして解釈可能な文字列を抽出し、現在時刻以降かチェック
                if self._is_time_current_or_later_type_aaa(title_text, current_time):
                    logger.debug(f"✅ 現在時刻以降の時間のためis_working=True: '{title_text}'")
                    return True
                else:
                    logger.debug(f"❌ 現在時刻より前または無効時間のためis_working=False: '{title_text}'")
            
            return False
            
        except Exception as e:
            logger.error(f"is_working判定エラー (type=aaa): {str(e)}")
            return False
    
    def _is_休み_or_調整中(self, time_text: str) -> bool:
        """お休みや調整中の判定"""
        休み_keywords = ['お休み', '出勤調整中', '次回', '出勤予定', '調整中', 'OFF', 'お疲れ様']
        return any(keyword in time_text for keyword in 休み_keywords)
    
    def _is_current_time_in_range_type_aaa(self, time_text: str, current_time: datetime) -> bool:
        """
        指示書準拠の時間範囲判定 (type=a,a,a)
        
        "12:00~24:00"のような時間帯文字列から範囲を抽出し、現在時刻が含まれるかチェック
        """
        
        try:
            import re
            
            # 時間範囲のパターンマッチング（例: "12:00～18:00", "12:00〜18:00", "12:00-18:00"）
            time_pattern = r'(\d{1,2}):(\d{2})[\s～〜\-~]+(\d{1,2}):(\d{2})'
            match = re.search(time_pattern, time_text)
            
            if match:
                start_hour, start_min, end_hour, end_min = map(int, match.groups())
                
                # 現在時刻を分に変換
                current_minutes = current_time.hour * 60 + current_time.minute
                start_minutes = start_hour * 60 + start_min
                end_minutes = end_hour * 60 + end_min
                
                # 日跨ぎのケースを考慮
                if start_minutes <= end_minutes:
                    # 通常の時間範囲（例: 12:00-18:00）
                    in_range = start_minutes <= current_minutes <= end_minutes
                    range_type = "通常範囲"
                else:
                    # 日跨ぎ（例: 22:00-6:00）
                    in_range = current_minutes >= start_minutes or current_minutes <= end_minutes
                    range_type = "日跨ぎ範囲"
                
                logger.debug(f"⏰ 時間範囲判定: {start_hour:02d}:{start_min:02d}-{end_hour:02d}:{end_min:02d}, 現在:{current_time.hour:02d}:{current_time.minute:02d}, 結果:{in_range}")
                # 詳細計算ログを削除（ログ簡略化）
                return in_range
            else:
                logger.debug(f"❌ 時間範囲パターンなし: '{time_text}'")
                
        except Exception as e:
            logger.error(f"時間範囲判定エラー (type=aaa): {str(e)}")
        
        return False
    
    def _is_time_current_or_later_type_aaa(self, title_text: str, current_time: datetime) -> bool:
        """
        指示書準拠の現在時刻以降判定 (type=a,a,a)
        
        titleテキストから時間を抽出し、現在時刻以降（現在時刻と同じかそれより後）かチェック
        """
        
        try:
            import re
            
            # 時間パターンの抽出（例: "13:30", "14:00"など）
            time_patterns = re.findall(r'(\d{1,2}):(\d{2})', title_text)
            
            if not time_patterns:
                logger.debug(f"❌ 時間パターンなし: '{title_text}'")
                return False
            
            for hour_str, min_str in time_patterns:
                hour, minute = int(hour_str), int(min_str)
                
                # 今日の該当時刻を作成
                target_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # 現在時刻との差分を分で計算
                time_diff = (target_time - current_time).total_seconds() / 60
                
                # 現在時刻以降かチェック（0分以上後、つまり現在時刻と同じかそれより後）
                if time_diff >= 0:
                    logger.debug(f"✅ 現在時刻以降判定成功: 対象時刻:{hour:02d}:{minute:02d}, 現在:{current_time.hour:02d}:{current_time.minute:02d}, 差分:{time_diff:.1f}分")
                    # 詳細計算ログを削除（ログ簡略化）
                    return True
                else:
                    logger.debug(f"❌ 現在時刻より前: 対象時刻:{hour:02d}:{minute:02d}, 差分:{time_diff:.1f}分")
                    # 詳細計算ログを削除（ログ簡略化）
            
            return False
                
        except Exception as e:
            logger.error(f"現在時刻以降判定エラー (type=aaa): {str(e)}")
            return False
    
    def _extract_raw_data_for_debug(self, wrapper_element, cast_id: str) -> Dict[str, Any]:
        """
        デバッグ用の生データ抽出
        """
        raw_data = {
            "cast_id": cast_id,
            "shukkin_detail_time": [],
            "sugunavibox_titles": [],
            "sugunavibox_full_content": ""
        }
        
        try:
            # shukkin_detail_time要素のテキスト抽出
            time_elements = wrapper_element.find_all(class_=lambda x: x and 'shukkin_detail_time' in str(x))
            for time_element in time_elements:
                time_text = time_element.get_text(strip=True)
                if time_text:
                    raw_data["shukkin_detail_time"].append(time_text)
            
            # sugunavibox要素の詳細抽出
            suguna_box = wrapper_element.find(class_='sugunavibox')
            if suguna_box:
                # sugunaviboxの全内容
                raw_data["sugunavibox_full_content"] = suguna_box.get_text(strip=True)
                
                # sugunavibox内のtitle要素
                title_elements = suguna_box.find_all(class_='title')
                for title_element in title_elements:
                    title_text = title_element.get_text(strip=True)
                    if title_text:
                        raw_data["sugunavibox_titles"].append(title_text)
        
        except Exception as e:
            logger.error(f"生データ抽出エラー: {e}")
        
        return raw_data
    
    def _output_raw_data_debug(self, cast_id: str, raw_data: Dict[str, Any], dom_check_mode: bool = False):
        """
        生データをデバッグ出力（現在は無効化）
        """
        # 詳細ログは削除（リクエストによる）
        pass

    def _output_detailed_debug(self, cast_id: str, wrapper_element, current_time: datetime, 
                              is_on_shift: bool, is_working: bool):
        """
        デバッグ用詳細出力
        
        出力内容:
        - キャストID
        - HTML取得時間
        - 出勤時間（shukkin_detail_time）
        - 待機状態表記（sugunavibox title）
        - 現在のソースコードによる稼働判定
        - DOM要素の生コンテンツ
        """
        
        print(f"\n{'='*80}")
        print(f"🔍 デバッグ詳細出力 - キャスト ID: {cast_id}")
        print(f"{'='*80}")
        
        # 1. HTML取得時間
        print(f"📅 HTML取得時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 2. 出勤時間の詳細
        print(f"\n⏰ 出勤時間情報:")
        time_elements = wrapper_element.find_all(class_=lambda x: x and 'shukkin_detail_time' in str(x))
        if time_elements:
            for i, time_element in enumerate(time_elements, 1):
                time_text = time_element.get_text(strip=True)
                print(f"   出勤時間{i}: '{time_text}'")
                print(f"   DOM内容: {time_element}")
        else:
            print("   ❌ 出勤時間要素が見つかりません")
        
        # 3. 待機状態表記の詳細
        print(f"\n💼 待機状態表記:")
        suguna_box = wrapper_element.find(class_='sugunavibox')
        if suguna_box:
            title_elements = suguna_box.find_all(class_='title')
            if title_elements:
                for i, title_element in enumerate(title_elements, 1):
                    title_text = title_element.get_text(strip=True)
                    print(f"   待機状態{i}: '{title_text}'")
                    print(f"   DOM内容: {title_element}")
            else:
                print("   ❌ title要素が見つかりません")
            
            # sugunaviboxの全体コンテンツも表示
            print(f"\n📦 sugunavibox全体:")
            full_content = suguna_box.get_text(strip=True)
            print(f"   '{full_content}'")
        else:
            print("   ❌ sugunavibox要素が見つかりません")
        
        # 4. 稼働判定結果
        print(f"\n🎯 ソースコード判定結果:")
        print(f"   is_on_shift (出勤中): {is_on_shift}")
        print(f"   is_working (稼働中): {is_working}")
        
        # 5. 判定ロジックの詳細
        print(f"\n🧮 判定ロジック詳細:")
        
        # on_shift判定の詳細
        print(f"   【出勤判定 (on_shift)】")
        if time_elements:
            for time_element in time_elements:
                time_text = time_element.get_text(strip=True)
                is_休み = self._is_休み_or_調整中(time_text)
                is_in_range = self._is_current_time_in_range_type_aaa(time_text, current_time)
                print(f"     '{time_text}' → 休み/調整中: {is_休み}, 時間範囲内: {is_in_range}")
        
        # is_working判定の詳細
        print(f"   【稼働判定 (is_working)】")
        if suguna_box:
            title_elements = suguna_box.find_all(class_='title')
            for title_element in title_elements:
                title_text = title_element.get_text(strip=True)
                is_current_or_later = self._is_time_current_or_later_type_aaa(title_text, current_time)
                print(f"     '{title_text}' → 現在時刻以降: {is_current_or_later}")
        
        print(f"   最終結果: on_shift={is_on_shift} AND 現在時刻以降=? → is_working={is_working}")
        
        print(f"{'='*80}\n")

    def _output_cast_dom_details(self, cast_id: str, wrapper_element, current_time: datetime, 
                                is_on_shift: bool, is_working: bool):
        """追加店舗DOM確認モード用：キャストHTML詳細出力"""
        status_icon = "🟢" if is_working else ("🟡" if is_on_shift else "🔴")
        print(f"\n{status_icon} 【キャストID: {cast_id}】")
        print("-" * 50)
        
        # 出勤時間情報
        time_elements = wrapper_element.find_all(class_=lambda x: x and 'shukkin_detail_time' in str(x))
        if time_elements:
            print(f"⏰ 出勤時間情報:")
            for i, time_element in enumerate(time_elements, 1):
                time_text = time_element.get_text(strip=True)
                print(f"   出勤時間{i}: '{time_text}'")
                print(f"   HTML: {time_element}")
        else:
            print(f"⏰ 出勤時間情報: 見つかりませんでした")
        
        # 待機状態情報
        suguna_box = wrapper_element.find(class_='sugunavibox')
        if suguna_box:
            full_content = suguna_box.get_text(strip=True)
            print(f"\n💼 待機状態:")
            print(f"   全文: '{full_content}'")
            
            title_elements = suguna_box.find_all(class_='title')
            if title_elements:
                for i, title in enumerate(title_elements, 1):
                    title_text = title.get_text(strip=True)
                    print(f"   title{i}: '{title_text}'")
                    print(f"   HTML: {title}")
            else:
                print(f"   title要素: 見つかりませんでした")
                
            print(f"\n   sugunavibox HTML:")
            print(f"   {suguna_box}")
        else:
            print(f"\n💼 待機状態: sugunavibox要素が見つかりませんでした")
        
        print(f"\n🎯 判定結果: on_shift={is_on_shift}, is_working={is_working}")
        
        # 判定ロジックの詳細
        print(f"🧮 判定根拠:")
        print(f"   HTML取得時刻: {current_time.strftime('%H:%M')}")
        
        if time_elements:
            for i, time_element in enumerate(time_elements, 1):
                time_text = time_element.get_text(strip=True)
                in_range = self._is_current_time_in_range_type_aaa(time_text, current_time)
                print(f"   出勤判定{i}: '{time_text}' → 時間内={in_range}")
        
        if suguna_box and is_on_shift:
            if '受付終了' in full_content:
                print(f"   稼働判定: '受付終了'検出 → 完売状態=稼働中 → working={is_working}")
            else:
                title_elements = suguna_box.find_all(class_='title')
                for i, title in enumerate(title_elements, 1):
                    title_text = title.get_text(strip=True)
                    is_future = self._is_time_current_or_later_type_aaa(title_text, current_time)
                    print(f"   稼働判定{i}: '{title_text}' → 未来時刻={is_future}")
        elif suguna_box and not is_on_shift:
            print(f"   稼働判定: on_shift=Falseのためスキップ")
        
        print("-" * 50)
    
    def _display_dom_check_summary(self, cast_list: List[Dict[str, Any]]):
        """追加店舗DOM確認モード用：最終サマリー表示"""
        working_count = sum(1 for cast in cast_list if cast.get('is_working', False))
        on_shift_count = sum(1 for cast in cast_list if cast.get('is_on_shift', False))
        
        print(f"\n" + "=" * 80)
        print(f"🎉 追加店舗DOM確認モード - 処理完了")
        print("=" * 80)
        print(f"📈 最終結果:")
        print(f"   総処理件数: {len(cast_list)}件")
        print(f"   出勤中キャスト: {on_shift_count}人")
        print(f"   稼働中キャスト: {working_count}人")
        print(f"   稼働率: {working_count/on_shift_count*100:.1f}%" if on_shift_count > 0 else "   稼働率: N/A")
        print(f"   出勤率: {on_shift_count/len(cast_list)*100:.1f}%" if len(cast_list) > 0 else "   出勤率: N/A")
        print("=" * 80)


class CityheavenTypeAABParser(CityheavenParserBase):
    """type=a,a,b パターン用パーサー（将来実装）"""
    
    async def parse_cast_data(self, soup: BeautifulSoup, business_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        logger.info("🔧 type=a,a,b パターンは未実装のため空リストを返します")
        return []


class CityheavenTypeABAParser(CityheavenParserBase):
    """type=a,b,a パターン用パーサー（将来実装）"""
    
    async def parse_cast_data(self, soup: BeautifulSoup, business_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        logger.info("🔧 type=a,b,a パターンは未実装のため空リストを返します")
        return []


class CityheavenTypeBParser(CityheavenParserBase):
    """cast_type=b パターン用パーサー（将来実装）"""
    
    async def parse_cast_data(self, soup: BeautifulSoup, business_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        logger.info("🔧 cast_type=b パターンは未実装のため空リストを返します")
        return []


class CityheavenTypeCParser(CityheavenParserBase):
    """cast_type=c パターン用パーサー（将来実装）"""
    
    async def parse_cast_data(self, soup: BeautifulSoup, business_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        logger.info("🔧 cast_type=c パターンは未実装のため空リストを返します")
        return []


class CityheavenFallbackParser(CityheavenParserBase):
    """フォールバックパーサー（汎用的な抽出）"""
    
    async def parse_cast_data(self, soup: BeautifulSoup, business_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        logger.info("🔧 フォールバックパターンは未実装のため空リストを返します")
        return []


class CityheavenParserFactory:
    """Cityheavenパーサーファクトリー（新実装）"""
    
    @staticmethod
    def get_parser(business_id: str) -> 'CityheavenTypeAAAParser':
        """business_idに基づいてパーサーを返す（現在はtype=a,a,aパーサーを使用）"""
        return CityheavenTypeAAAParser()
