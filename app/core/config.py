"""
APIサーバー用統合設定
config/config.yml を使用した設定管理
"""

import sys
import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# プロジェクトルートへのパス
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class ConfigManager:
    """統合設定管理クラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.project_root = project_root
        self.config_path = config_path or (self.project_root / "config" / "config.yml")
        
        # 環境変数を読み込み（.envファイルがあれば）
        env_path = self.project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        # 設定ファイルを読み込み
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み、環境変数で上書き"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"設定ファイル読み込み成功: {self.config_path}")
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {str(e)}")
            config = {}
        
        # 環境変数での上書き処理
        config = self._expand_env_vars(config)
        
        # 環境別設定の適用
        env_mode = os.getenv('ENVIRONMENT', config.get('environment', {}).get('mode', 'development'))
        print(f"環境モード: {env_mode}")
        if env_mode == 'production' and 'production' in config:
            config = self._merge_configs(config, config['production'])
        
        return config
    
    def _expand_env_vars(self, config: Any) -> Any:
        """${VAR_NAME}形式の環境変数を展開"""
        if isinstance(config, dict):
            return {key: self._expand_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._expand_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            var_name = config[2:-1]
            return os.getenv(var_name, config)
        else:
            return config
    
    def _merge_configs(self, base: dict, override: dict) -> dict:
        """設定をマージ"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """ドット記法で設定値を取得 (例: 'database.host')"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_database_config(self) -> Dict[str, Any]:
        """データベース設定を取得"""
        return self.get('database', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """API設定を取得"""
        return self.get('api', {})
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """スクレイピング設定を取得"""
        return self.get('scraping', {})
    
    def get_scheduling_config(self) -> Dict[str, Any]:
        """スケジューリング設定を取得"""
        return self.get('scheduling', {})
    
    def get_frontend_config(self) -> Dict[str, Any]:
        """フロントエンド設定を取得"""
        return self.get('frontend', {})
    
    def get_auth_config(self) -> Dict[str, Any]:
        """認証設定を取得"""
        return self.get('auth', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """ログ設定を取得"""
        return self.get('logging', {})
        
    def get_email_config(self) -> Dict[str, Any]:
        """メール設定を取得"""
        return self.get('email', {})

# グローバルインスタンス
config_manager = ConfigManager()

# 便利関数（既存コードとの互換性）
def get_config(key_path: str = None, default: Any = None) -> Any:
    """設定値を取得"""
    if key_path:
        return config_manager.get(key_path, default)
    return config_manager.config

def get_database_url() -> str:
    """データベースURL取得"""
    return config_manager.get('database.url')

def get_database_config() -> Dict[str, Any]:
    """データベース設定取得（batch/との互換性）"""
    return config_manager.get_database_config()

def get_scraping_config() -> Dict[str, Any]:
    """スクレイピング設定取得（batch/との互換性）"""
    return config_manager.get_scraping_config()

def get_scheduling_config() -> Dict[str, Any]:
    """スケジューリング設定取得（batch/との互換性）"""
    return config_manager.get_scheduling_config()

def get_api_settings() -> Dict[str, Any]:
    """API設定取得（server/との互換性）"""
    return config_manager.get_api_config()

class Settings(BaseSettings):
    """API サーバー設定クラス"""
    
    # デフォルト値を設定
    api_host: str = "localhost"
    api_port: int = 8080
    debug: bool = True
    
    # データベース設定
    database_url: str = os.getenv(
        'DATABASE_URL', 
        'postgresql://postgres.hnmbsqydlfemlmsyexrq:Ggzzmmb3@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
    )
    
    # Twitter API設定
    twitter_bearer_token: Optional[str] = os.getenv('TWITTER_BEARER_TOKEN')
    twitter_username: str = os.getenv('TWITTER_USERNAME', 'elonmusk')
    twitter_display_name: str = os.getenv('TWITTER_DISPLAY_NAME', 'Elon Musk')
    title: str = "稼働.com API"
    description: str = "風俗店稼働率管理システムのAPI"
    version: str = "1.0.0"
    database_url: str = ""
    secret_key: str = "fallback-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    magic_link_expire_minutes: int = 15
    frontend_url: str = "http://localhost:5173"
    _allowed_origins: List[str] = ["http://localhost:5173"]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        if config_manager:
            # 統合設定から値を上書き
            api_config = config_manager.get_api_config()
            db_config = config_manager.get_database_config()
            auth_config = config_manager.get_auth_config()
            frontend_config = config_manager.get_frontend_config()
            
            # API設定
            if api_config:
                self.api_host = api_config.get('host', self.api_host)
                self.api_port = api_config.get('port', self.api_port)
                self.debug = api_config.get('debug', self.debug)
                self.title = api_config.get('title', self.title)
                self.description = api_config.get('description', self.description)
                self.version = api_config.get('version', self.version)
                
                # CORS設定
                cors_config = api_config.get('cors', {})
                self._allowed_origins = cors_config.get('origins', self._allowed_origins)
                self.allow_credentials = cors_config.get('allow_credentials', self.allow_credentials)
                self.allow_methods = cors_config.get('allow_methods', self.allow_methods)
                self.allow_headers = cors_config.get('allow_headers', self.allow_headers)
            
            # データベース設定
            if db_config:
                self.database_url = db_config.get('url', self.database_url)
            
            # 認証設定
            if auth_config:
                self.secret_key = auth_config.get('secret_key', self.secret_key)
                self.algorithm = auth_config.get('algorithm', self.algorithm)
                self.access_token_expire_minutes = auth_config.get('access_token_expire_minutes', self.access_token_expire_minutes)
                self.magic_link_expire_minutes = auth_config.get('magic_link_expire_minutes', self.magic_link_expire_minutes)
            
            # フロントエンドURL
            if frontend_config:
                self.frontend_url = frontend_config.get('url', self.frontend_url)
                
                # Twitter設定
                twitter_config = frontend_config.get('twitter', {})
                self.twitter_username = twitter_config.get('username', self.twitter_username)
                self.twitter_display_name = twitter_config.get('display_name', self.twitter_display_name)
        else:
            # フォールバック: 環境変数から読み込み
            self.api_host = os.getenv('API_HOST', self.api_host)
            self.api_port = int(os.getenv('API_PORT', str(self.api_port)))
            self.debug = os.getenv('DEBUG', str(self.debug)).lower() == 'true'
            self.database_url = os.getenv('DATABASE_URL', self.database_url)
            self.secret_key = os.getenv('SECRET_KEY', self.secret_key)
            self.frontend_url = os.getenv('FRONTEND_URL', self.frontend_url)
    
    @property
    def allowed_origins(self) -> List[str]:
        if hasattr(self, '_allowed_origins'):
            return self._allowed_origins
        return [self.frontend_url]
    
    class Config:
        env_file = ".env"

# グローバル設定インスタンス
settings = Settings()

# デバッグ用
if __name__ == "__main__":
    print("🔧 API サーバー設定確認:")
    print(f"  Host: {settings.api_host}:{settings.api_port}")
    print(f"  Debug: {settings.debug}")
    print(f"  Database: {settings.database_url[:50]}..." if settings.database_url else "None")
    print(f"  CORS Origins: {settings.allowed_origins}")
    print("✅ 設定読み込み完了")
