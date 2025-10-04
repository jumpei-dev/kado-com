from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Time, Text, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from scout_ui.core.database import Base
from datetime import datetime, date, time
from typing import Optional, List

class User(Base):
    """ユーザー認証・認可テーブル"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    can_see_contents = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

class Business(Base):
    """店舗・事業所情報テーブル"""
    __tablename__ = "business"
    
    business_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    area = Column(String(100), nullable=False, index=True)
    prefecture = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    open_hour = Column(Time, nullable=False)
    close_hour = Column(Time, nullable=False)
    schedule_url = Column(Text, nullable=False)
    in_scope = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    casts = relationship("Cast", back_populates="business", cascade="all, delete-orphan")
    status_records = relationship("Status", back_populates="business", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="business", cascade="all, delete-orphan")

class Cast(Base):
    """キャスト情報テーブル"""
    __tablename__ = "casts"
    
    cast_id = Column(String(50), primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.business_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    profile_url = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    business = relationship("Business", back_populates="casts")
    status_records = relationship("Status", back_populates="cast", cascade="all, delete-orphan")

class Status(Base):
    """現在のキャストステータステーブル"""
    __tablename__ = "status"
    
    id = Column(Integer, primary_key=True, index=True)
    cast_id = Column(String(50), ForeignKey("casts.cast_id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("business.business_id", ondelete="CASCADE"), nullable=False, index=True)
    is_working = Column(Boolean, nullable=False)
    is_on_shift = Column(Boolean, nullable=False)
    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    cast = relationship("Cast", back_populates="status_records")
    business = relationship("Business", back_populates="status_records")

class StatusHistory(Base):
    """稼働率履歴テーブル"""
    __tablename__ = "status_history"
    
    business_id = Column(Integer, ForeignKey("business.business_id", ondelete="CASCADE"), nullable=False, index=True, primary_key=True)
    biz_date = Column(Date, nullable=False, index=True, primary_key=True)
    working_rate = Column(DECIMAL(5, 4), nullable=False)
    is_dummy = Column(Boolean, default=False)
    
    # Relationships
    business = relationship("Business", back_populates="status_history")

class BatchJobResult(Base):
    """バッチジョブ結果監視テーブル"""
    __tablename__ = "batch_job_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(255), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime)
    success = Column(Boolean, default=False)
    processed_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    errors = Column(Text)  # JSON文字列として保存
    duration_seconds = Column(DECIMAL(10, 3))
    created_at = Column(DateTime, default=func.current_timestamp())

# ビューモデル用のクラス（店舗一覧表示用）
class StoreView:
    """店舗一覧表示用のビューモデル"""
    
    def __init__(self, business: Business, latest_working_rate: Optional[float] = None, 
                 cast_count: int = 0, active_cast_count: int = 0, last_updated: Optional[datetime] = None):
        self.id = business.business_id
        self.name = business.name
        self.area = business.area
        self.prefecture = business.prefecture
        self.business_type = business.type
        self.capacity = business.capacity
        self.open_hour = business.open_hour
        self.close_hour = business.close_hour
        self.in_scope = business.in_scope
        self.working_rate = latest_working_rate or 0.0
        self.cast_count = cast_count
        self.active_cast_count = active_cast_count
        self.last_updated = last_updated
        self.created_at = business.created_at
        self.updated_at = business.updated_at
    
    @property
    def status_count(self) -> int:
        """ステータス件数（active_cast_countと同じ）"""
        return self.active_cast_count
    
    @property
    def avg_rating(self) -> float:
        """平均評価（稼働率を評価として使用）"""
        return round(self.working_rate * 5, 2)  # 0-1の稼働率を0-5の評価に変換
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "name": self.name,
            "area": self.area,
            "prefecture": self.prefecture,
            "business_type": self.business_type,
            "capacity": self.capacity,
            "open_hour": self.open_hour.strftime("%H:%M") if self.open_hour else None,
            "close_hour": self.close_hour.strftime("%H:%M") if self.close_hour else None,
            "working_rate": self.working_rate,
            "cast_count": self.cast_count,
            "active_cast_count": self.active_cast_count,
            "status_count": self.status_count,
            "avg_rating": self.avg_rating,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "in_scope": self.in_scope
        }

# 後方互換性のためのエイリアス
Store = StoreView