#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
開発用: HTML判定前の詳細出力ツール
新しい店舗追加時のデバッグ専用

本番のスクレイピングロジックを使用しつつ、
判定前の元HTML内容を詳細出力する開発支援ツール
"""

import sys
import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 本番コードインポート
from batch.jobs.status_collection.collector import collect_all_working_status
from batch.core.database import DatabaseManager
from batch.jobs.status_collection.cityheaven_strategy import CityheavenStrategy
from bs4 import BeautifulSoup


class DevelopmentHTMLDebugger:
    """開発用HTMLデバッグ出力クラス"""
    
    def __init__(self):
        self.debug_mode = True
        self.db_manager = None
    
    async def initialize(self):
        """非同期初期化"""
        self.db_manager = DatabaseManager()
        # DatabaseManagerは既に初期化済みなので、initializeメソッドは不要
    
    async def debug_scraping_with_html_output(self, business_id: str = None):
        """
        本番コードでスクレイピング実行 + 開発用HTML詳細出力
        
        Args:
            business_id: 指定がない場合は最初のbusinessを対象
        """
        print("🔧 開発モード: HTML詳細出力付きスクレイピング実行")
        print("=" * 80)
        
        # 初期化
        await self.initialize()
        
        # businessデータ取得
        if business_id:
            business = await self._get_business_by_id(business_id)
        else:
            business = await self._get_first_business()
        
        if not business:
            print("❌ 店舗データが見つかりません")
            return []
        
        print(f"🏪 対象店舗: {business['name']} (ID: {business['id']})")
        print(f"🌐 URL: {business['base_url']}")
        print()
        
        # 本番のCityheavenStrategyを使用
        print("🚀 リアルタイムスクレイピング開始...")
        
        try:
            # 暫定: 手動スクレイピング（本番コード整備後に置き換え予定）
            cast_list = await self._manual_scraping(business)
            
            if not cast_list:
                print("❌ キャストデータが取得できませんでした")
                return []
            
            print(f"✅ スクレイピング完了: {len(cast_list)}件のキャストデータを取得")
            
            # 開発用: HTML詳細出力
            await self._output_debug_html(cast_list, business)
            
            # 本番コード: DB保存
            saved_count = await self._save_to_database(cast_list)
            
            print(f"\n💾 DB保存完了: {saved_count}件のステータスを保存")
            
            # 最終サマリー
            self._display_final_summary(cast_list)
            
            return cast_list
            
        except Exception as e:
            print(f"❌ スクレイピングエラー: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        finally:
            # データベース接続のクリーンアップは不要（自動管理）
            pass
    
    async def _get_first_business(self) -> Optional[Dict[str, Any]]:
        """最初のbusinessを取得"""
        try:
            businesses = self.db_manager.get_businesses()
            if businesses:
                # 辞書の最初の値を取得
                first_business = list(businesses.values())[0]
                return {
                    'id': first_business.get('Business ID'),
                    'name': first_business.get('Name', first_business.get('name')),
                    'base_url': first_business.get('Base URL', '')
                }
            return None
        except Exception as e:
            print(f"❌ Business取得エラー: {e}")
            return None
    
    async def _get_business_by_id(self, business_id: str) -> Optional[Dict[str, Any]]:
        """指定IDのbusinessを取得"""
        try:
            businesses = self.db_manager.get_businesses()
            for business in businesses.values():
                if str(business.get('Business ID')) == str(business_id):
                    return {
                        'id': business.get('Business ID'),
                        'name': business.get('Name', business.get('name')),
                        'base_url': business.get('Base URL', '')
                    }
            print(f"❌ 指定されたBusiness ID '{business_id}' は見つかりませんでした")
            return None
        except Exception as e:
            print(f"❌ Business取得エラー: {e}")
            return None
    
    async def _output_debug_html(self, cast_list: List[Any], business: Dict[str, Any]):
        """開発用: 判定前HTML詳細出力"""
        print(f"\n🔍 開発用HTML詳細出力")
        print("=" * 80)
        
        # サマリー計算
        working_count = sum(1 for cast in cast_list if getattr(cast, 'is_working', False))
        on_shift_count = sum(1 for cast in cast_list if getattr(cast, 'is_on_shift', False))
        
        print(f"📊 判定結果サマリー:")
        print(f"   総キャスト数: {len(cast_list)}")
        print(f"   出勤中: {on_shift_count} ({on_shift_count/len(cast_list)*100:.1f}%)")
        print(f"   稼働中: {working_count} ({working_count/len(cast_list)*100:.1f}%)")
        
        # カテゴリ別分類
        working_casts = [cast for cast in cast_list if getattr(cast, 'is_working', False)]
        on_shift_not_working = [cast for cast in cast_list 
                               if getattr(cast, 'is_on_shift', False) and not getattr(cast, 'is_working', False)]
        off_shift_casts = [cast for cast in cast_list if not getattr(cast, 'is_on_shift', False)]
        
        print(f"\n📋 カテゴリ別詳細:")
        print(f"   🟢 稼働中: {len(working_casts)}人")
        print(f"   🟡 出勤中（非稼働）: {len(on_shift_not_working)}人")
        print(f"   🔴 非出勤: {len(off_shift_casts)}人")
        
        # 各カテゴリの詳細HTML出力
        await self._output_category_details("🟢 稼働中キャスト", working_casts[:5])
        await self._output_category_details("🟡 出勤中（非稼働）キャスト", on_shift_not_working[:5])
        
        if len(off_shift_casts) > 0:
            print(f"\n🔴 非出勤キャスト: {len(off_shift_casts)}人（詳細表示省略）")
    
    async def _output_category_details(self, category_name: str, cast_list: List[Any]):
        """カテゴリ別詳細出力"""
        if not cast_list:
            print(f"\n{category_name}: 該当なし")
            return
            
        print(f"\n{category_name} (最大5件表示)")
        print("-" * 60)
        
        for i, cast in enumerate(cast_list, 1):
            cast_id = getattr(cast, 'cast_id', 'N/A')
            is_on_shift = getattr(cast, 'is_on_shift', False)
            is_working = getattr(cast, 'is_working', False)
            
            print(f"\n【{i}】キャストID: {cast_id}")
            print(f"   🎯 最終判定: is_on_shift={is_on_shift}, is_working={is_working}")
            
            # HTML詳細情報（castオブジェクトから取得可能な情報を表示）
            if hasattr(cast, 'business_id'):
                print(f"   🏪 店舗ID: {cast.business_id}")
            
            if hasattr(cast, 'recorded_at'):
                print(f"   📅 記録時刻: {cast.recorded_at}")
            
            # TODO: 実際のHTML内容表示
            # 本番パーサーからHTML要素を取得する方法を実装予定
            print(f"   📄 元HTML詳細: [実装予定]")
            print(f"   ※ wrapper要素の出勤時間・待機状態表示を検討中")
    
    async def _save_to_database(self, cast_list: List[Any]) -> int:
        """DB保存処理"""
        try:
            if not self.db_manager:
                print("❌ DatabaseManagerが初期化されていません")
                return 0
            
            # 本番のDB保存ロジックを使用
            saved_count = 0
            for cast in cast_list:
                try:
                    # castオブジェクトをdict形式に変換してDB保存
                    cast_data = {
                        'business_id': getattr(cast, 'business_id', None),
                        'cast_id': getattr(cast, 'cast_id', None),
                        'is_working': getattr(cast, 'is_working', False),
                        'is_on_shift': getattr(cast, 'is_on_shift', False),
                        'recorded_at': getattr(cast, 'recorded_at', datetime.now()),
                        'extraction_type': 'debug'
                    }
                    
                    # 個別保存（本番のsave_cast_statusメソッドを使用）
                    result = await self.db_manager.save_cast_status(cast_data)
                    if result:
                        saved_count += 1
                        
                except Exception as e:
                    print(f"⚠️ キャスト{getattr(cast, 'cast_id', 'N/A')}の保存エラー: {e}")
                    continue
            
            return saved_count
            
        except Exception as e:
            print(f"❌ DB保存処理エラー: {e}")
            return 0
    
    def _display_final_summary(self, cast_list: List[Any]):
        """最終サマリー表示"""
        working_count = sum(1 for cast in cast_list if getattr(cast, 'is_working', False))
        on_shift_count = sum(1 for cast in cast_list if getattr(cast, 'is_on_shift', False))
        
        print("\n" + "=" * 80)
        print("🎉 開発用デバッグ完了")
        print("=" * 80)
        print(f"📈 処理結果:")
        print(f"   総処理件数: {len(cast_list)}件")
        print(f"   出勤中キャスト: {on_shift_count}人")
        print(f"   稼働中キャスト: {working_count}人")
        print(f"   稼働率: {working_count/on_shift_count*100:.1f}%" if on_shift_count > 0 else "   稼働率: N/A")
        print(f"   出勤率: {on_shift_count/len(cast_list)*100:.1f}%")


async def main():
    """メイン実行関数"""
    debugger = DevelopmentHTMLDebugger()
    
    # 最初の店舗で実行
    results = await debugger.debug_scraping_with_html_output()
    
    if results:
        print(f"\n✅ 開発用デバッグ実行完了: {len(results)}件処理")
    else:
        print("\n❌ 開発用デバッグ実行失敗")


if __name__ == "__main__":
    asyncio.run(main())
