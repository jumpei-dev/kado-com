from fastapi.responses import StreamingResponse
from scout_ui.models.store import StoreView
from typing import List
import csv
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generate_csv_response(stores: List[StoreView], filename: str = None) -> StreamingResponse:
    """店舗データをCSV形式でエクスポート"""
    try:
        # ファイル名が指定されていない場合は現在日時を使用
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stores_export_{timestamp}.csv"
        
        # CSVデータを生成
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー行を書き込み
        headers = [
            "店舗ID",
            "店舗名",
            "エリア",
            "都道府県",
            "業種",
            "定員",
            "営業開始時間",
            "営業終了時間",
            "稼働率",
            "キャスト数",
            "アクティブキャスト数",
            "平均評価",
            "最終更新日",
            "対象店舗"
        ]
        writer.writerow(headers)
        
        # データ行を書き込み
        for store in stores:
            row = [
                store.id,
                store.name,
                store.area,
                store.prefecture,
                store.business_type,
                store.capacity,
                store.open_hour.strftime("%H:%M") if store.open_hour else "",
                store.close_hour.strftime("%H:%M") if store.close_hour else "",
                f"{store.working_rate:.4f}",
                store.cast_count,
                store.active_cast_count,
                f"{store.avg_rating:.2f}",
                store.last_updated.strftime("%Y-%m-%d %H:%M:%S") if store.last_updated else "",
                "対象" if store.in_scope else "対象外"
            ]
            writer.writerow(row)
        
        # StringIOの内容を取得
        csv_content = output.getvalue()
        output.close()
        
        # StreamingResponseを作成
        def iter_csv():
            yield csv_content.encode('utf-8-sig')  # BOM付きUTF-8でExcelでの文字化けを防ぐ
        
        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}")
        raise

def generate_ranking_csv(stores: List[StoreView], limit: int = 10) -> StreamingResponse:
    """ランキング形式でCSVを生成"""
    try:
        # 稼働率でソート
        sorted_stores = sorted(stores, key=lambda x: x.working_rate, reverse=True)[:limit]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ranking_top{limit}_{timestamp}.csv"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー行
        headers = [
            "順位",
            "店舗名",
            "エリア",
            "業種",
            "稼働率",
            "キャスト数",
            "平均評価"
        ]
        writer.writerow(headers)
        
        # ランキングデータ
        for idx, store in enumerate(sorted_stores, 1):
            row = [
                idx,
                store.name,
                store.area,
                store.business_type,
                f"{store.working_rate:.4f}",
                store.active_cast_count,
                f"{store.avg_rating:.2f}"
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        def iter_csv():
            yield csv_content.encode('utf-8-sig')
        
        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating ranking CSV: {str(e)}")
        raise

def generate_summary_csv(stores: List[StoreView]) -> StreamingResponse:
    """サマリー情報をCSV形式で生成"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stores_summary_{timestamp}.csv"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # サマリー情報を計算
        total_stores = len(stores)
        active_stores = len([s for s in stores if s.working_rate > 0])
        avg_working_rate = sum(s.working_rate for s in stores) / total_stores if total_stores > 0 else 0
        total_casts = sum(s.cast_count for s in stores)
        total_active_casts = sum(s.active_cast_count for s in stores)
        
        # エリア別統計
        area_stats = {}
        for store in stores:
            if store.area not in area_stats:
                area_stats[store.area] = {'count': 0, 'total_rate': 0, 'casts': 0}
            area_stats[store.area]['count'] += 1
            area_stats[store.area]['total_rate'] += store.working_rate
            area_stats[store.area]['casts'] += store.active_cast_count
        
        # 業種別統計
        type_stats = {}
        for store in stores:
            if store.business_type not in type_stats:
                type_stats[store.business_type] = {'count': 0, 'total_rate': 0, 'casts': 0}
            type_stats[store.business_type]['count'] += 1
            type_stats[store.business_type]['total_rate'] += store.working_rate
            type_stats[store.business_type]['casts'] += store.active_cast_count
        
        # 全体サマリー
        writer.writerow(["全体サマリー"])
        writer.writerow(["項目", "値"])
        writer.writerow(["総店舗数", total_stores])
        writer.writerow(["稼働中店舗数", active_stores])
        writer.writerow(["平均稼働率", f"{avg_working_rate:.4f}"])
        writer.writerow(["総キャスト数", total_casts])
        writer.writerow(["アクティブキャスト数", total_active_casts])
        writer.writerow([])
        
        # エリア別サマリー
        writer.writerow(["エリア別サマリー"])
        writer.writerow(["エリア", "店舗数", "平均稼働率", "キャスト数"])
        for area, stats in sorted(area_stats.items()):
            avg_rate = stats['total_rate'] / stats['count'] if stats['count'] > 0 else 0
            writer.writerow([area, stats['count'], f"{avg_rate:.4f}", stats['casts']])
        writer.writerow([])
        
        # 業種別サマリー
        writer.writerow(["業種別サマリー"])
        writer.writerow(["業種", "店舗数", "平均稼働率", "キャスト数"])
        for btype, stats in sorted(type_stats.items()):
            avg_rate = stats['total_rate'] / stats['count'] if stats['count'] > 0 else 0
            writer.writerow([btype, stats['count'], f"{avg_rate:.4f}", stats['casts']])
        
        csv_content = output.getvalue()
        output.close()
        
        def iter_csv():
            yield csv_content.encode('utf-8-sig')
        
        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating summary CSV: {str(e)}")
        raise