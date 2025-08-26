"""
バッチ処理の設定管理。
YAML形式の設定ファイルと環境変数をサポート。
"""

import os
import yaml
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path

@dataclass
class DatabaseConfig:
    """データベース設定"""
    connection_string: str
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """環境変数から設定を作成する"""
        return cls(
            connection_string=os.getenv(
                'DATABASE_URL',
                'postgresql://postgres.hnmbsqydlfemlmsyexrq:Ggzzmmb3@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
            ),
            pool_size=int(os.getenv('DB_POOL_SIZE', 5)),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 10)),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', 30))
        )

@dataclass
class ScrapingConfig:
    """スクレイピング設定"""
    timeout: int = 30
    max_concurrent: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.0
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    @classmethod
    def from_env(cls) -> 'ScrapingConfig':
        """環境変数から設定を作成する"""
        return cls(
            timeout=int(os.getenv('SCRAPING_TIMEOUT', 30)),
            max_concurrent=int(os.getenv('SCRAPING_MAX_CONCURRENT', 10)),
            retry_attempts=int(os.getenv('SCRAPING_RETRY_ATTEMPTS', 3)),
            retry_delay=float(os.getenv('SCRAPING_RETRY_DELAY', 1.0)),
            user_agent=os.getenv('SCRAPING_USER_AGENT', cls.user_agent)
        )

@dataclass
class SchedulingConfig:
    """ジョブスケジューリング設定"""
    status_collection_interval: int = 30  # 分
    history_calculation_interval: int = 360  # 分（6時間）
    business_hours_buffer: int = 30  # 営業時間前後のバッファ分数
    
    @classmethod
    def from_env(cls) -> 'SchedulingConfig':
        """Create configuration from environment variables."""
        return cls(
            status_collection_interval=int(os.getenv('STATUS_COLLECTION_INTERVAL', 30)),
            history_calculation_interval=int(os.getenv('HISTORY_CALCULATION_INTERVAL', 360)),
            business_hours_buffer=int(os.getenv('BUSINESS_HOURS_BUFFER', 30))
        )

@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    log_dir: str = "logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create configuration from environment variables."""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            log_dir=os.getenv('LOG_DIR', 'logs'),
            max_file_size=int(os.getenv('LOG_MAX_FILE_SIZE', 10 * 1024 * 1024)),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT', 5))
        )

@dataclass
class BatchConfig:
    """メインバッチ処理設定"""
    database: DatabaseConfig
    scraping: ScrapingConfig
    scheduling: SchedulingConfig
    logging: LoggingConfig
    environment: str = "development"
    
    @classmethod
    def from_env(cls) -> 'BatchConfig':
        """環境変数から設定を作成する"""
        return cls(
            database=DatabaseConfig.from_env(),
            scraping=ScrapingConfig.from_env(),
            scheduling=SchedulingConfig.from_env(),
            logging=LoggingConfig.from_env(),
            environment=os.getenv('BATCH_ENVIRONMENT', 'development')
        )
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'BatchConfig':
        """YAMLファイルから設定を読み込む"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 環境変数の展開
        data = cls._expand_env_vars(data)
        
        return cls(
            database=DatabaseConfig(**data.get('database', {})),
            scraping=ScrapingConfig(**data.get('scraping', {})),
            scheduling=SchedulingConfig(**data.get('scheduling', {})),
            logging=LoggingConfig(**data.get('logging', {})),
            environment=data.get('environment', 'development')
        )
    
    @classmethod
    def from_file(cls, config_path: str) -> 'BatchConfig':
        """設定ファイルから読み込み（YAML形式）"""
        return cls.from_yaml(config_path)
    
    @classmethod 
    def _expand_env_vars(cls, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """設定内の環境変数を展開する（${VAR_NAME}形式）"""
        if isinstance(config_dict, dict):
            return {
                key: cls._expand_env_vars(value)
                for key, value in config_dict.items()
            }
        elif isinstance(config_dict, list):
            return [cls._expand_env_vars(item) for item in config_dict]
        elif isinstance(config_dict, str):
            # ${VAR_NAME}形式の環境変数を展開
            import re
            def replace_env_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))
            return re.sub(r'\$\{([^}]+)\}', replace_env_var, config_dict)
        else:
            return config_dict
    
    def to_yaml(self, config_path: str):
        """設定をYAMLファイルに保存"""
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            'database': {
                'host': getattr(self.database, 'host', 'localhost'),
                'port': getattr(self.database, 'port', 5432),
                'database': getattr(self.database, 'database', 'kado'),
                'user': getattr(self.database, 'user', 'postgres'),
                'password': getattr(self.database, 'password', 'password'),
            },
            'scraping': {
                'timeout': self.scraping.timeout,
                'max_concurrent': self.scraping.max_concurrent,
                'retry_attempts': self.scraping.retry_attempts,
                'retry_delay': self.scraping.retry_delay,
                'user_agent': self.scraping.user_agent
            },
            'scheduling': {
                'status_collection_interval': self.scheduling.status_collection_interval,
                'history_calculation_interval': self.scheduling.history_calculation_interval,
                'business_hours_buffer': self.scheduling.business_hours_buffer
            },
            'logging': {
                'level': self.logging.level,
                'log_dir': self.logging.log_dir,
                'max_file_size': self.logging.max_file_size,
                'backup_count': self.logging.backup_count
            },
            'environment': self.environment
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)
    
    @property
    def is_development(self) -> bool:
        """開発環境かどうかチェック"""
        return self.environment.lower() == 'development'
    
    @property
    def is_production(self) -> bool:
        """本番環境かどうかチェック"""
        return self.environment.lower() == 'production'

# グローバル設定インスタンス
_config: Optional[BatchConfig] = None

def get_config() -> BatchConfig:
    """グローバル設定インスタンスを取得"""
    global _config
    if _config is None:
        _config = BatchConfig.from_env()
    return _config

def set_config(config: BatchConfig):
    """グローバル設定インスタンスを設定"""
    global _config
    _config = config

def load_config_from_file(config_path: str):
    """ファイルから設定を読み込みグローバルインスタンスに設定"""
    global _config
    _config = BatchConfig.from_file(config_path)

def load_config_for_environment(environment: str = None) -> BatchConfig:
    """環境に応じた設定ファイルを読み込む"""
    if environment is None:
        environment = os.getenv('BATCH_ENVIRONMENT', 'development')
    
    # プロジェクトルートの設定ディレクトリを検索
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / 'config' / f'{environment}.yaml'
    
    if config_file.exists():
        return BatchConfig.from_yaml(str(config_file))
    else:
        # フォールバック: 環境変数から設定
        return BatchConfig.from_env()
