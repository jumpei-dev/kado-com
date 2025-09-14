"""
バッチ処理のためのログユーティリティ。
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

def setup_logging(
    log_level: str = "DEBUG",  # 固定：詳細ログ出力
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    バッチ処理システムの包括的なログ設定を行う。
    
    Args:
        log_level: ログレベル（固定：DEBUG - 詳細ログ出力）
        log_dir: ログファイルを保存するディレクトリ
        max_bytes: ローテーション前の各ログファイルの最大サイズ
        backup_count: 保持するバックアップファイル数
    """
    
    # ログディレクトリが存在しない場合は作成
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # フォーマッターを設定
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # ルートロガー設定（強制的にDEBUGレベルに固定）
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 常にDEBUGレベルに固定
    
    # 既存のハンドラーをクリア
    root_logger.handlers = []
    
    # コンソールハンドラー（DEBUG以上 - 詳細ログ出力）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # DEBUGレベルに固定
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # メインログファイルハンドラー（全ログ）
    main_log_file = log_path / "batch_processing.log"
    main_handler = logging.handlers.RotatingFileHandler(
        main_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    main_handler.setLevel(logging.DEBUG)  # 常にDEBUGレベルに固定
    main_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(main_handler)
    
    # Error log file handler (ERROR and CRITICAL only)
    error_log_file = log_path / "batch_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Job-specific log file handler
    job_log_file = log_path / f"jobs_{datetime.now().strftime('%Y%m%d')}.log"
    job_handler = logging.handlers.RotatingFileHandler(
        job_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    job_handler.setLevel(logging.INFO)
    job_handler.setFormatter(detailed_formatter)
    
    # Create job logger
    job_logger = logging.getLogger('batch.jobs')
    job_logger.addHandler(job_handler)
    job_logger.propagate = True  # Also send to root logger
    
    logging.info(f"Logging initialized - Level: DEBUG (固定), Dir: {log_dir}")

def get_job_logger(job_name: str) -> logging.Logger:
    """Get a logger for a specific job."""
    return logging.getLogger(f'batch.jobs.{job_name}')

def get_scraper_logger() -> logging.Logger:
    """Get a logger for scraping operations."""
    return logging.getLogger('batch.scraper')

def get_database_logger() -> logging.Logger:
    """Get a logger for database operations."""
    return logging.getLogger('batch.database')

def get_logger(name: str) -> logging.Logger:
    """指定した名前でロガーを取得する"""
    return logging.getLogger(name)

class JobLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds job context to log messages."""
    
    def __init__(self, logger: logging.Logger, job_name: str, run_id: str = None):
        self.job_name = job_name
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        super().__init__(logger, {'job_name': job_name, 'run_id': self.run_id})
    
    def process(self, msg, kwargs):
        """Add job context to log messages."""
        return f"[{self.job_name}:{self.run_id}] {msg}", kwargs
    
    def job_started(self):
        """Log job start."""
        self.info("Job started")
    
    def job_completed(self, processed: int, errors: int, duration: float = None):
        """Log job completion."""
        duration_str = f" in {duration:.2f}s" if duration else ""
        self.info(f"Job completed - Processed: {processed}, Errors: {errors}{duration_str}")
    
    def job_failed(self, error: str):
        """Log job failure."""
        self.error(f"Job failed: {error}")
    
    def processing_item(self, item_name: str, item_id: str = None):
        """Log processing of individual item."""
        id_str = f" (ID: {item_id})" if item_id else ""
        self.debug(f"Processing {item_name}{id_str}")
    
    def item_success(self, item_name: str, details: str = None):
        """Log successful processing of item."""
        details_str = f" - {details}" if details else ""
        self.debug(f"Successfully processed {item_name}{details_str}")
    
    def item_error(self, item_name: str, error: str):
        """Log error processing item."""
        self.warning(f"Error processing {item_name}: {error}")
