"""
バッチ処理の設定管理。
YAML形式の設定ファイルと環境変数をサポート。
"""

import os
import yaml
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path

@dataclass
class DatabaseConfig:
    """データベース設定"""
    connection_string: str
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    user: str = "postgres"
    password: str = ""
    sslmode: str = "prefer"
    url: str = ""
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """環境変数から設定を作成する"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL環境変数が設定されていません")
        
        return cls(
            connection_string=database_url,
            pool_size=int(os.getenv('DB_POOL_SIZE', 5)),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 10)),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', 30)),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            sslmode=os.getenv('DB_SSLMODE', 'prefer'),
            url=os.getenv('DB_URL', '')
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'DatabaseConfig':
        """設定辞書から設定を作成する"""
        db_config = config_dict
        
        # secret.ymlから機密情報を読み込み
        project_root = Path(__file__).parent.parent.parent
        secret_file = project_root / 'config' / 'secret.yml'
        
        secret_config = {}
        if secret_file.exists():
            try:
                with open(secret_file, 'r', encoding='utf-8') as f:
                    secret_data = yaml.safe_load(f)
                    # secret.ymlの構造: database.url の形式に対応
                    secret_config = secret_data.get('database', {})
            except Exception as e:
                print(f"secret.yml読み込みエラー: {e}")
        
        # 接続文字列の優先順位: 1. secret.yml database.url, 2. 環境変数, 3. エラー
        if secret_config.get('url'):
            # secret.ymlのdatabase.urlが記載されている場合
            connection_string = secret_config['url']
        else:
            # 環境変数を確認
            env_url = os.getenv('DATABASE_URL')
            if env_url:
                connection_string = env_url
            else:
                raise ValueError("データベース接続情報が見つかりません。secret.ymlのdatabase.urlまたはDATABASE_URL環境変数を設定してください。")
        
        return cls(
            connection_string=connection_string,
            pool_size=db_config.get('pool_size', 5),
            max_overflow=db_config.get('max_overflow', 10),
            pool_timeout=db_config.get('pool_timeout', 30),
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            database=db_config.get('database', 'postgres'),
            user=db_config.get('user', 'postgres'),
            password=secret_config.get('password', db_config.get('password', '')),
            sslmode=db_config.get('sslmode', 'prefer'),
            url=secret_config.get('url', db_config.get('url', ''))
        )

@dataclass
class ScrapingConfig:
    """スクレイピング設定"""
    timeout: int = 30
    max_concurrent: int = 10
    max_concurrent_businesses: int = 5  # 店舗並行処理数
    retry_attempts: int = 3
    retry_delay: float = 1.0
    delay_between_requests: float = 1.0
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    user_agents: list = None
    max_parallel_businesses: int = 3
    min_delay: float = 0.5
    max_delay: float = 2.0
    request_interval: float = 1.0
    use_aiohttp: bool = True
    connection_pooling: bool = True
    keep_alive: bool = True
    compress: bool = True
    session_rotation: bool = True  # セッションローテーション有効
    session_lifetime: int = 1800  # セッション有効期間（秒）30分
    cookie_persistence: bool = True  # Cookie永続化
    random_intervals: bool = True  # 完全ランダム間隔
    interval_base_minutes: int = 60  # ベース間隔（分）
    interval_variance_percent: int = 50  # 変動幅（±50%）
    random_headers: bool = True  # ヘッダーランダム化
    random_referer: bool = True  # リファラーランダム化
    
    @classmethod
    def from_env(cls) -> 'ScrapingConfig':
        """環境変数から設定を作成する"""
        return cls(
            timeout=int(os.getenv('SCRAPING_TIMEOUT', 30)),
            max_concurrent=int(os.getenv('SCRAPING_MAX_CONCURRENT', 10)),
            max_concurrent_businesses=int(os.getenv('SCRAPING_MAX_CONCURRENT_BUSINESSES', 5)),
            retry_attempts=int(os.getenv('SCRAPING_RETRY_ATTEMPTS', 3)),
            retry_delay=float(os.getenv('SCRAPING_RETRY_DELAY', 1.0)),
            delay_between_requests=float(os.getenv('SCRAPING_DELAY_BETWEEN_REQUESTS', 1.0)),
            user_agent=os.getenv('SCRAPING_USER_AGENT', cls.user_agent),
            user_agents=None,
            max_parallel_businesses=int(os.getenv('SCRAPING_MAX_PARALLEL_BUSINESSES', 3)),
            min_delay=float(os.getenv('SCRAPING_MIN_DELAY', 0.5)),
            max_delay=float(os.getenv('SCRAPING_MAX_DELAY', 2.0)),
            request_interval=float(os.getenv('SCRAPING_REQUEST_INTERVAL', 1.0)),
            use_aiohttp=os.getenv('SCRAPING_USE_AIOHTTP', 'true').lower() == 'true',
            connection_pooling=os.getenv('SCRAPING_CONNECTION_POOLING', 'true').lower() == 'true',
            keep_alive=os.getenv('SCRAPING_KEEP_ALIVE', 'true').lower() == 'true',
            compress=os.getenv('SCRAPING_COMPRESS', 'true').lower() == 'true',
            session_rotation=os.getenv('SCRAPING_SESSION_ROTATION', 'true').lower() == 'true',
            session_lifetime=int(os.getenv('SCRAPING_SESSION_LIFETIME', 1800)),
            cookie_persistence=os.getenv('SCRAPING_COOKIE_PERSISTENCE', 'true').lower() == 'true',
            random_intervals=os.getenv('SCRAPING_RANDOM_INTERVALS', 'true').lower() == 'true',
            interval_base_minutes=int(os.getenv('SCRAPING_INTERVAL_BASE_MINUTES', 60)),
            interval_variance_percent=int(os.getenv('SCRAPING_INTERVAL_VARIANCE_PERCENT', 50)),
            random_headers=os.getenv('SCRAPING_RANDOM_HEADERS', 'true').lower() == 'true',
            random_referer=os.getenv('SCRAPING_RANDOM_REFERER', 'true').lower() == 'true'
        )

@dataclass
class SchedulingConfig:
    """スケジューリング設定"""
    status_collection_interval: int = 120  # 分（2時間間隔）
    history_calculation_hour: int = 12    # 稼働率計算実行時刻
    history_calculation_minute: int = 0   # 稼働率計算実行分
    max_concurrent_businesses: int = 5        # 店舗並行処理数
    max_concurrent_working_rate: int = 10     # 稼働率計算並行処理数
    health_check_interval: int = 15       # 分
    cleanup_time_hour: int = 2            # 午前2時
    cleanup_time_minute: int = 0
    misfire_grace_time_status: int = 300  # ステータス収集の猶予時間（秒）
    misfire_grace_time_history: int = 600 # 履歴計算の猶予時間（秒）
    max_log_retention_days: int = 30      # ログ保持日数
    business_hours_buffer: int = 0        # 営業時間バッファ（分）
    
    @classmethod
    def from_env(cls) -> 'SchedulingConfig':
        """環境変数から設定を作成する"""
        return cls(
            status_collection_interval=int(os.getenv('STATUS_COLLECTION_INTERVAL', 30)),
            history_calculation_hour=int(os.getenv('HISTORY_CALCULATION_HOUR', 12)),
            history_calculation_minute=int(os.getenv('HISTORY_CALCULATION_MINUTE', 0)),
            max_concurrent_businesses=int(os.getenv('MAX_CONCURRENT_BUSINESSES', 5)),
            max_concurrent_working_rate=int(os.getenv('MAX_CONCURRENT_WORKING_RATE', 10)),
            health_check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', 15)),
            cleanup_time_hour=int(os.getenv('CLEANUP_TIME_HOUR', 2)),
            cleanup_time_minute=int(os.getenv('CLEANUP_TIME_MINUTE', 0)),
            misfire_grace_time_status=int(os.getenv('MISFIRE_GRACE_TIME_STATUS', 300)),
            misfire_grace_time_history=int(os.getenv('MISFIRE_GRACE_TIME_HISTORY', 600)),
            max_log_retention_days=int(os.getenv('MAX_LOG_RETENTION_DAYS', 30)),
            business_hours_buffer=int(os.getenv('BUSINESS_HOURS_BUFFER', 0))
        )

@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    log_dir: str = "logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create configuration from environment variables."""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            log_dir=os.getenv('LOG_DIR', 'logs'),
            max_file_size=int(os.getenv('LOG_MAX_FILE_SIZE', 10 * 1024 * 1024)),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT', 5)),
            format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        
        # schedulingの特別な処理
        scheduling_data = data.get('scheduling', {})
        if 'misfire_grace_time' in scheduling_data:
            misfire_grace_time = scheduling_data['misfire_grace_time']
            scheduling_data['misfire_grace_time_status'] = misfire_grace_time.get('status_collection', 300)
            scheduling_data['misfire_grace_time_history'] = misfire_grace_time.get('status_history', 600)
            del scheduling_data['misfire_grace_time']
        
        return cls(
            database=DatabaseConfig.from_dict(data.get('database', {})),
            scraping=ScrapingConfig(**data.get('scraping', {})),
            scheduling=SchedulingConfig(**scheduling_data),
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
                'max_concurrent_businesses': self.scraping.max_concurrent_businesses,
                'retry_attempts': self.scraping.retry_attempts,
                'retry_delay': self.scraping.retry_delay,
                'user_agent': self.scraping.user_agent
            },
            'scheduling': {
                'status_collection_interval': self.scheduling.status_collection_interval,
                'history_calculation_hour': self.scheduling.history_calculation_hour,
                'history_calculation_minute': self.scheduling.history_calculation_minute,
                'max_concurrent_businesses': self.scheduling.max_concurrent_businesses,
                'max_concurrent_working_rate': self.scheduling.max_concurrent_working_rate,
                'health_check_interval': self.scheduling.health_check_interval,
                'cleanup_time_hour': self.scheduling.cleanup_time_hour,
                'cleanup_time_minute': self.scheduling.cleanup_time_minute
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
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式に変換"""
        return asdict(self)

# グローバル設定インスタンス
_config: Optional[BatchConfig] = None

def get_config() -> BatchConfig:
    """グローバル設定インスタンスを取得"""
    global _config
    if _config is None:
        _config = load_config_for_environment()
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
    """統合設定ファイルから設定を読み込む"""
    # プロジェクトルートの設定ディレクトリから config.yml を読み込み
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / 'config' / 'config.yml'
    
    if config_file.exists():
        return BatchConfig.from_yaml(str(config_file))
    else:
        # フォールバック: 環境変数から設定
        return BatchConfig.from_env()

# レガシー互換性のためのエイリアス
Config = BatchConfig

def get_scheduling_config():
    """既存のget_config()を活用してスケジューリング設定を取得"""
    config = get_config()
    config_dict = config.to_dict()
    scheduling = config_dict.get('scheduling', {})
    
    return {
        'status_cron': f"*/{scheduling.get('status_collection_interval', 30)} * * * *",
        'working_rate_cron': f"{scheduling.get('history_calculation_minute', 0)} {scheduling.get('history_calculation_hour', 12)} * * *",
        'timezone': 'Asia/Tokyo'
    }

def get_database_config():
    """設定ファイルからデータベース設定を取得"""
    try:
        # secret.ymlから直接読み込み
        project_root = Path(__file__).parent.parent.parent
        secret_file = project_root / 'config' / 'secret.yml'
        
        if secret_file.exists():
            with open(secret_file, 'r', encoding='utf-8') as f:
                secret_data = yaml.safe_load(f)
                database_config = secret_data.get('database', {})
                
                if database_config.get('url'):
                    return DatabaseConfig(
                        connection_string=database_config['url'],
                        password=database_config.get('password', ''),
                        url=database_config['url']
                    )
                else:
                    raise ValueError("secret.ymlにdatabase.urlが設定されていません")
        else:
            # フォールバック: 環境変数
            return DatabaseConfig.from_env()
    except Exception as e:
        print(f"設定ファイル読み込みエラー: データベース接続情報が見つかりません。secret.ymlのdatabase.urlまたはDATABASE_URL環境変数を設定してください。")
        # フォールバック: 環境変数
        return DatabaseConfig.from_env()

def get_scraping_config():
    """スクレイピング設定を取得"""
    try:
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / 'config' / 'config.yml'
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            
            scraping_config = config_dict.get('scraping', {})
            
            # デフォルト値を設定
            return {
                'timeout': scraping_config.get('timeout', 30),
                'retry_attempts': scraping_config.get('retry_attempts', 3),
                'user_agents': scraping_config.get('user_agents', [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ]),
                'max_parallel_businesses': scraping_config.get('max_parallel_businesses', 3),
                'min_delay': scraping_config.get('min_delay', 0.5),
                'max_delay': scraping_config.get('max_delay', 2.0),
                'request_interval': scraping_config.get('request_interval', 1.0),
                'retry_delay': scraping_config.get('retry_delay', 3.0),
                'use_aiohttp': scraping_config.get('use_aiohttp', True),
                'connection_pooling': scraping_config.get('connection_pooling', True),
                'keep_alive': scraping_config.get('keep_alive', True),
                'compress': scraping_config.get('compress', True)
            }
        else:
            # フォールバック: デフォルト設定
            return {
                'timeout': 30,
                'retry_attempts': 3,
                'user_agents': [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ],
                'max_parallel_businesses': 3,
                'min_delay': 0.5,
                'max_delay': 2.0,
                'request_interval': 1.0,
                'retry_delay': 3.0,
                'use_aiohttp': True,
                'connection_pooling': True,
                'keep_alive': True,
                'compress': True
            }
    except Exception as e:
        print(f"スクレイピング設定読み込みエラー: {e}")
        # エラー時のフォールバック
        return {
            'timeout': 30,
            'retry_attempts': 3,
            'user_agents': [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ],
            'max_parallel_businesses': 1,  # 安全のため並行処理を無効
            'min_delay': 1.0,
            'max_delay': 3.0,
            'request_interval': 2.0,
            'retry_delay': 5.0,
            'use_aiohttp': False,  # 安全のためaiohttp無効
            'connection_pooling': False,
            'keep_alive': False,
            'compress': False
        }
