"""
APIサーバー用統合設定
config/config.yml を使用した設定管理
"""

import sys
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

# shared/config.py を使用
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

try:
    from shared.config import config_manager
    print("✅ 統合設定を読み込みました")
except ImportError as e:
    print(f"⚠️ Warning: shared.config が利用できません: {e}")
    print("デフォルト設定を使用します。")
    config_manager = None

class Settings(BaseSettings):
    """API サーバー設定クラス"""
    
    # デフォルト値を設定
    api_host: str = "localhost"
    api_port: int = 8000
    debug: bool = True
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
