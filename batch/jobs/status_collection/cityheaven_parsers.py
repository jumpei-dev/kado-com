"""
Cityheaven用パーサー（type別実装）

指示書準拠の各typeパターンに対応したパーサー実装
"""

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

try:
    from ..utils.logging_utils import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

logger = get_logger(__name__)


class CityheavenParserBase(ABC):
    """Cityheavenパーサーの基底クラス"""
    
    @abstractmethod
    async def parse_cast_data(
        self, 
        soup: BeautifulSoup, 
        business_id: str, 
        current_time: datetime
    ) -> List[Dict[str, Any]]:
        """キャストデータをパースする抽象メソッド"""
        pass


class CityheavenTypeAAAParser(CityheavenParserBase):
    """type=a,a,a パターン用パーサー（指示書準拠）"""
    
    async def parse_cast_data(self, soup: BeautifulSoup, business_id: str, current_time: datetime) -> List[Dict[str, Any]]:
        """
        指示書準拠の type=a,a,a パターン
        
        条件:
        - Class名が"sugunavi_wrapper"のdiv要素
        - その中でsugunaviboxを含むものが対象（5-40個程度）
        """
        cast_list = []
        
        try:
            # 1. sugunavi_wrapperを全て取得
            sugunavi_wrappers = soup.find_all('div', class_='sugunavi_wrapper')
            logger.info(f"📦 sugunavi_wrapper要素: {len(sugunavi_wrappers)}個発見")
            
            # 2. その中でsugunaviboxを含むものを特定
            target_wrappers = []
            for wrapper in sugunavi_wrappers:
                suguna_box = wrapper.find(class_='sugunavibox')
                if suguna_box:
                    target_wrappers.append(wrapper)
            
            logger.info(f"🎯 sugunaviboxを含むwrapper: {len(target_wrappers)}個（期待範囲: 5-40個）")
            
            if len(target_wrappers) == 0:
                logger.warning("⚠️ 対象wrapper要素が見つかりません")
                return cast_list
            
            # 3. 各target_wrapperを指示書通りに処理
            for i, wrapper in enumerate(target_wrappers):
                try:
                    cast_data = await self._process_wrapper_type_aaa(wrapper, business_id, current_time)
                    if cast_data:
                        cast_list.append(cast_data)
                        logger.debug(f"✅ キャスト情報抽出成功: {i+1}/{len(target_wrappers)} - {cast_data['cast_id']}")
                    else:
                        logger.debug(f"⚠️ キャスト情報抽出失敗: {i+1}/{len(target_wrappers)}")
                        
                except Exception as extract_error:
                    logger.error(f"❌ キャスト{i+1}抽出エラー: {extract_error}")
            
            logger.info(f"🎯 type=a,a,a パターン完了: {len(cast_list)}件のキャスト情報を抽出")
                    
        except Exception as e:
            logger.error(f"type=a,a,a パターン解析エラー: {str(e)}")
            
        return cast_list
    
    async def _process_wrapper_type_aaa(self, wrapper_element, business_id: str, current_time: datetime) -> Optional[Dict[str, Any]]:
        """
        指示書準拠の単一wrapper要素処理 (type=a,a,a)
        
        指示書の抽出要件:
        1. cast_id: a要素のhrefからgirlid-xxxxxを抽出
        2. on_shift: shukkin_detail_timeの時間範囲と現在時刻を比較  
        3. is_working: sugunavibox内のclass="title"から時間を抽出し、現在時刻以降 & on_shift=true
        """
        
        try:
            # 1. cast_idの抽出（指示書準拠）
            cast_id = self._extract_cast_id_type_aaa(wrapper_element)
            if not cast_id:
                logger.debug("❌ cast_id抽出失敗: girlid-xxxxx形式が見つかりません")
                return None
            
            # 🔍 生データ抽出・出力機能
            raw_data = self._extract_raw_data_for_debug(wrapper_element, cast_id)
            self._output_raw_data_debug(cast_id, raw_data)
            
            # 2. on_shiftの判定（指示書準拠）
            is_on_shift = self._determine_on_shift_type_aaa(wrapper_element, current_time)
            
            # 3. is_workingの判定（指示書準拠）
            is_working = self._determine_working_type_aaa(wrapper_element, current_time, is_on_shift)
            
            logger.debug(f"📊 キャスト{cast_id}: on_shift={is_on_shift}, is_working={is_working}")
            
            cast_result = {
                'business_id': business_id,
                'cast_id': cast_id,
                'is_working': is_working,
                'is_on_shift': is_on_shift,
                'collected_at': current_time,
                'extraction_type': 'aaa'
            }
            
            # 🔍 個別キャストデータのJSON出力
            logger.info(f"✅ キャスト{cast_id}抽出成功:")
            logger.info(f"   {json.dumps(cast_result, ensure_ascii=False, indent=4, default=str)}")
            
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
        
        要件: sugunavibox内のclass="title"から時間を抽出し、
             以下の条件が両方満たされる場合にis_working=true:
             1. その時間が現在時刻以降（現在時刻と同じかそれより後）
             2. on_shift=true
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
                else:
                    # 日跨ぎ（例: 22:00-6:00）
                    in_range = current_minutes >= start_minutes or current_minutes <= end_minutes
                
                logger.debug(f"⏰ 時間範囲判定: {start_hour:02d}:{start_min:02d}-{end_hour:02d}:{end_min:02d}, 現在:{current_time.hour:02d}:{current_time.minute:02d}, 結果:{in_range}")
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
                    return True
                else:
                    logger.debug(f"❌ 現在時刻より前: 対象時刻:{hour:02d}:{minute:02d}, 差分:{time_diff:.1f}分")
            
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
    
    def _output_raw_data_debug(self, cast_id: str, raw_data: Dict[str, Any]):
        """
        生データをデバッグ出力
        """
        logger.info(f"🔍 キャスト{cast_id} 生データ:")
        logger.info(f"   出勤時間: {raw_data['shukkin_detail_time']}")
        logger.info(f"   sugunavibox title: {raw_data['sugunavibox_titles']}")
        logger.info(f"   sugunavibox 全体: {raw_data['sugunavibox_full_content'][:200]}..." if len(raw_data['sugunavibox_full_content']) > 200 else f"   sugunavibox 全体: {raw_data['sugunavibox_full_content']}")


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
    """Cityheavenパーサーファクトリー"""
    
    @staticmethod
    def get_parser(cast_type: str, working_type: str, shift_type: str) -> CityheavenParserBase:
        """typeの組み合わせに応じたパーサーを返す"""
        if cast_type == "a" and working_type == "a" and shift_type == "a":
            return CityheavenTypeAAAParser()
        elif cast_type == "a" and working_type == "a" and shift_type == "b":
            return CityheavenTypeAABParser()
        elif cast_type == "a" and working_type == "b" and shift_type == "a":
            return CityheavenTypeABAParser()
        elif cast_type == "b":
            return CityheavenTypeBParser()
        elif cast_type == "c":
            return CityheavenTypeCParser()
        else:
            logger.warning(f"⚠️ 未対応type組み合わせ: cast={cast_type}, working={working_type}, shift={shift_type}")
            return CityheavenFallbackParser()
