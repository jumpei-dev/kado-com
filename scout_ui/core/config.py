import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Settings:
    """アプリケーション設定クラス"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    PASSWORD_SALT: str = os.getenv("PASSWORD_SALT", "default_salt")
    
    # Session
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    
    # CSV Export
    CSV_EXPORT_LIMIT: int = int(os.getenv("CSV_EXPORT_LIMIT", "1000"))
    
    # Admin User (for simple auth)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self.ENVIRONMENT == "production"
    
    def validate(self) -> bool:
        """設定値を検証"""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")
        
        if not self.SECRET_KEY or self.SECRET_KEY == "your-secret-key-here":
            if self.is_production:
                raise ValueError("SECRET_KEY must be set in production")
        
        return True

# グローバル設定インスタンス
settings = Settings()

# 設定検証
settings.validate()