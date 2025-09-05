"""
稼働.com バッチ処理システム - 統合版

主要機能:
- 稼働ステータス収集 (jobs.status_collection) - モジュラー構造
- 稼働率計算 (jobs.working_rate_calculation) - モジュラー構造  
- スケジューラー (schedulers) - 統合済み
- ユーティリティ (utils) - 共通機能

このパッケージは全てのバッチ処理機能への統一されたアクセスポイントを提供します。
内部的にはモジュラー構造を採用しており、保守性と拡張性を確保しています。
"""

__version__ = "4.0.0"  # 統合モジュラー構造版
__author__ = "稼働.com チーム"

# モジュラー構造での安全なインポート
try:
    # Core functionality
    from .core.database import DatabaseManager
    from .core.models import Business, Cast, Status, StatusHistory, ScrapingResult, BatchJobResult
    
    # Jobs API - モジュラー版（直接インポート）
    from .jobs.status_collection.collector import collect_all_working_status, collect_status_for_business
    from .jobs.working_rate_calculation import (
        run_working_rate_calculation, WorkingRateCalculator as WorkingRateCalculationJob, WorkingRateResult,
        run_status_history, get_business_history_summary
    )
    
    # Schedulers
    from .schedulers import (
        StatusCollectionScheduler, WorkingRateScheduler,
        run_status_collection_scheduler, run_working_rate_scheduler,
        BatchScheduler, run_batch_scheduler
    )
    
    # Utilities
    from .utils.logging_utils import setup_logging, get_job_logger, JobLoggerAdapter
    from .utils.datetime_utils import (
        now_jst, now_jst_naive, to_jst, is_business_hours,
        get_next_business_day, get_business_days_in_range,
        should_run_status_collection, should_run_history_calculation
    )
    from .utils.config import (
        get_config, load_config_from_file, DatabaseConfig,
        ScrapingConfig, SchedulingConfig, LoggingConfig, BatchConfig
    )
    
    __all__ = [
        # Core
        'DatabaseManager', 'Business', 'Cast', 'Status', 'StatusHistory', 
        'ScrapingResult', 'BatchJobResult',
        
        # Jobs API
        'collect_all_working_status', 'collect_status_for_business',
        'run_working_rate_calculation', 'WorkingRateCalculationJob', 'WorkingRateResult',
        'run_status_history', 'get_business_history_summary',
        
        # Schedulers
        'StatusCollectionScheduler', 'WorkingRateScheduler',
        'run_status_collection_scheduler', 'run_working_rate_scheduler',
        'BatchScheduler', 'run_batch_scheduler',
        
        # Utilities
        'setup_logging', 'get_job_logger', 'JobLoggerAdapter',
        'now_jst', 'now_jst_naive', 'to_jst', 'is_business_hours',
        'get_next_business_day', 'get_business_days_in_range',
        'should_run_status_collection', 'should_run_history_calculation',
        'get_config', 'load_config_from_file', 'DatabaseConfig',
        'ScrapingConfig', 'SchedulingConfig', 'LoggingConfig', 'BatchConfig'
    ]

except ImportError as e:
    # 開発中は一部インポートエラーを許可
    import warnings
    warnings.warn(f"Some modules could not be imported: {e}", ImportWarning)
    __all__ = []
