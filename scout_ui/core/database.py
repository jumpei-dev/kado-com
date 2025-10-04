from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create engine with SSL and connection settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,  # 30分に短縮
    pool_timeout=60,
    pool_size=5,  # プールサイズを削減
    max_overflow=10,  # オーバーフローを削減
    connect_args={
        "sslmode": "require",
        "sslcert": None,
        "sslkey": None,
        "sslrootcert": None,  # 証明書検証を無効化
        "connect_timeout": 30,
        "application_name": "scout_ui",
        "keepalives_idle": "600",
        "keepalives_interval": "30",
        "keepalives_count": "3"
    },
    echo=os.getenv("DEBUG", "False").lower() == "true"
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

def get_db():
    """データベースセッションを取得"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def get_db_session():
    """非同期対応のデータベースセッションを取得"""
    return SessionLocal()

def init_db():
    """データベースを初期化"""
    try:
        # Import all models to ensure they are registered with Base
        from scout_ui.models import store  # noqa
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

def check_db_connection():
    """データベース接続をチェック"""
    try:
        logger.info(f"Attempting to connect to database: {DATABASE_URL[:50]}...")
        
        # より簡単な接続テストを試行
        import psycopg2
        from urllib.parse import urlparse
        
        # URLをパース
        parsed = urlparse(DATABASE_URL)
        
        # 直接psycopg2で接続テスト（複数のSSL設定を試行）
        ssl_configs = [
            {'sslmode': 'require', 'sslcert': None, 'sslkey': None, 'sslrootcert': None},
            {'sslmode': 'prefer'},
            {'sslmode': 'disable'}
        ]
        conn = None
        
        for i, ssl_config in enumerate(ssl_configs):
            try:
                logger.info(f"Trying SSL config {i+1}: {ssl_config}")
                conn = psycopg2.connect(
                    host=parsed.hostname,
                    port=parsed.port,
                    database=parsed.path[1:],  # Remove leading '/'
                    user=parsed.username,
                    password=parsed.password,
                    connect_timeout=30,
                    keepalives_idle=600,
                    keepalives_interval=30,
                    keepalives_count=3,
                    **ssl_config
                )
                logger.info(f"Connection successful with SSL config {i+1}")
                break
            except Exception as ssl_error:
                logger.warning(f"SSL config {i+1} failed: {ssl_error}")
                if i == len(ssl_configs) - 1:  # Last attempt
                    raise ssl_error
                continue
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        logger.info(f"Direct psycopg2 connection successful: {result}")
        
        # SQLAlchemyでの接続テスト
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"SQLAlchemy connection successful: {result.fetchone()}")
        
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False