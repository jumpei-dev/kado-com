"""
稼働.com バッチ処理システム - 風力業界活動トラッカー
"""

__version__ = "1.0.0"
__author__ = "稼働.com チーム"

# コア機能
from .core.database import DatabaseManager
from .core.models import Business, Cast, Status, StatusHistory, ScrapingResult, BatchJobResult
from .core.scraper import ScraperFactory, CityHavenScraper, DeliherTownScraper, BaseScraper

# バッチジョブ
from .jobs.status_collection import StatusCollectionJob, run_status_collection
from .jobs.status_history import StatusHistoryJob, run_status_history, get_business_history_summary

# スケジューラー
from .scheduler.main import BatchScheduler, run_scheduler

# ユーティリティ
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
    # コア機能
    'DatabaseManager', 'Business', 'Cast', 'Status', 'StatusHistory', 
    'ScrapingResult', 'BatchJobResult',
    'ScraperFactory', 'CityHavenScraper', 'DeliherTownScraper', 'BaseScraper',
    
    # バッチジョブ
    'StatusCollectionJob', 'run_status_collection',
    'StatusHistoryJob', 'run_status_history', 'get_business_history_summary',
    
    # スケジューラー
    'BatchScheduler', 'run_scheduler',
    
    # ユーティリティ
    'setup_logging', 'get_job_logger', 'JobLoggerAdapter',
    'now_jst', 'now_jst_naive', 'to_jst', 'is_business_hours',
    'get_next_business_day', 'get_business_days_in_range',
    'should_run_status_collection', 'should_run_history_calculation',
    'get_config', 'load_config_from_file', 'DatabaseConfig',
    'ScrapingConfig', 'SchedulingConfig', 'LoggingConfig', 'BatchConfig'
]
