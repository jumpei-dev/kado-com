"""
稼働.com バッチ処理システム - 風力業界活動トラッカー
"""

__version__ = "1.0.0"
__author__ = "稼働.com チーム"

# コア機能 - 循環インポートを避けるためコメントアウト
# from .core.database import DatabaseManager
# from .core.models import Business, Cast, Status, StatusHistory, ScrapingResult, BatchJobResult
# from .core.scraper import ScraperFactory, CityHavenScraper, DeliherTownScraper, BaseScraper

# バッチジョブ - 循環インポートを避けるためコメントアウト
# from .jobs.status_collection import collect_all_working_status, save_working_status_to_database, run_status_collection
# from .jobs.working_rate_calculation import (
#     WorkingRateCalculationJob, run_working_rate_calculation, WorkingRateResult,
#     run_status_history, get_business_history_summary
# )

# スケジューラー - 循環インポートを避けるためコメントアウト
# from .scheduler.main import BatchScheduler, run_scheduler

# ユーティリティ - 循環インポートを避けるためコメントアウト
# from .utils.logging_utils import setup_logging, get_job_logger, JobLoggerAdapter
# from .utils.datetime_utils import (
#     now_jst, now_jst_naive, to_jst, is_business_hours,
#     get_next_business_day, get_business_days_in_range,
#     should_run_status_collection, should_run_history_calculation
# )
# from .utils.config import (
#     get_config, load_config_from_file, DatabaseConfig, 
#     ScrapingConfig, SchedulingConfig, LoggingConfig, BatchConfig
# )

# __all__ は循環インポート修正後に復活させる
__all__ = []
