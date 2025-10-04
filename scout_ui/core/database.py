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

# Create engine with stable SSL settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,  # 30分に短縮
    pool_timeout=20,
    pool_size=2,  # さらに小さく
    max_overflow=3,
    connect_args={
        "sslmode": "prefer",  # requireからpreferに変更
        "connect_timeout": 15,
        "application_name": "scout_ui",
        "keepalives_idle": "600",
        "keepalives_interval": "30",
        "keepalives_count": "3"
    },
    echo=os.getenv("DEBUG", "False").lower() == "true",
    use_native_hstore=False
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
        logger.info("Checking database connection...")
        
        # シンプルなSQLAlchemy接続テスト
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False