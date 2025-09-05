"""
Jobs package - バッチジョブ実行モジュール群（統合版）

Available modules:
- status_collection: 稼働ステータス収集ジョブ（モジュラー構造）
- working_rate_calculation: 稼働率計算ジョブ（モジュラー構造）

このパッケージは両方のジョブタイプに統一されたAPIを提供します。
内部的にはそれぞれモジュラー構造を採用しており、
複雑な処理を適切に分離しています。
"""

# モジュラー構造対応インポート - 直接各モジュールから取得
from .status_collection.collector import collect_all_working_status, collect_status_for_business
from .working_rate_calculation import (
    run_working_rate_calculation, WorkingRateCalculator as WorkingRateCalculationJob, WorkingRateResult,
    run_status_history, get_business_history_summary
)

__version__ = "4.0.0"  # 統合モジュラー構造版
__all__ = [
    # Status Collection API (from modular structure)
    'collect_all_working_status',
    'collect_status_for_business',
    
    # Working Rate Calculation API
    'run_working_rate_calculation', 
    'WorkingRateCalculationJob', 
    'WorkingRateResult',
    'run_status_history', 
    'get_business_history_summary'
]
