"""
稼働.com 統合設定管理ユーティリティ
config/config.yml から全モジュールの設定を一元管理
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class ConfigManager:
    """統合設定管理クラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or (self.project_root / "config" / "config.yml")
        
        # 環境変数を読み込み（.envファイルがあれば）
        env_path = self.project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        # 設定ファイルを読み込み
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み、環境変数で上書き"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 環境変数での上書き処理
        config = self._expand_env_vars(config)
        
        # 環境別設定の適用
        env_mode = os.getenv('NODE_ENV', config.get('environment', {}).get('mode', 'development'))
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
