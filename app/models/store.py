from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date

class Business(BaseModel):
    """店舗の基本情報モデル"""
    id: int = Field(..., alias="business_id")
    name: str
    blurred_name: Optional[str] = None
    area: str
    prefecture: str
    type: str
    capacity: Optional[int] = None
    open_hour: Optional[datetime] = None
    close_hour: Optional[datetime] = None
    schedule_url: Optional[str] = None
    in_scope: bool = True
    working_type: Optional[str] = None
    cast_type: Optional[str] = None
    shift_type: Optional[str] = None
    media: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True

class Cast(BaseModel):
    """キャストの基本情報モデル"""
    id: int = Field(..., alias="cast_id")
    business_id: int
    profile_url: Optional[str] = None
    is_active: bool = True

class Status(BaseModel):
    """キャストの勤務状態モデル"""
    cast_id: int
    business_id: int
    is_working: bool
    is_on_shift: bool
    recorded_at: datetime
    is_dummy: bool = False

class StatusHistory(BaseModel):
    """店舗の稼働率履歴モデル"""
    business_id: int
    biz_date: date
    working_rate: float

class StoreRanking(BaseModel):
    """ランキング表示用の店舗情報"""
    id: int
    name: str
    blurred_name: str
    prefecture: str
    area: str
    genre: str
    working_rate: float
    rank: int

class RateHistory(BaseModel):
    """稼働率履歴の項目"""
    label: str
    rate: float
    date: date

class StoreDetail(BaseModel):
    """店舗詳細情報"""
    id: int
    name: str
    blurred_name: str
    prefecture: str
    area: str
    genre: str
    current_rate: float
    updated_at: str
    address: Optional[str] = None
    business_hours: Optional[str] = None
    weekly_history: List[RateHistory]
    monthly_history: List[RateHistory]
