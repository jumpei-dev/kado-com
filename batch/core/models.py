"""
バッチ処理システムのデータモデル。
"""

from dataclasses import dataclass
from datetime import datetime, time, date
from typing import Optional, List

@dataclass
class Business:
    """店舗エンティティモデル"""
    business_id: int
    name: str
    area: str
    prefecture: str
    type: str
    capacity: int
    open_hour: time
    close_hour: time
    schedule_url: str
    in_scope: bool = True
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Business':
        """データベース行から店舗インスタンスを作成する"""
        return cls(
            business_id=data['business_id'],
            name=data['name'],
            area=data['area'],
            prefecture=data['prefecture'],
            type=data['type'],
            capacity=data['capacity'],
            open_hour=data['open_hour'],
            close_hour=data['close_hour'],
            schedule_url=data['schedule_url'],
            in_scope=data.get('in_scope', True)
        )

@dataclass
class Cast:
    """キャストエンティティモデル"""
    cast_id: str
    business_id: int
    name: str
    profile_url: str
    is_active: bool = True
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Cast':
        """データベース行からキャストインスタンスを作成する"""
        return cls(
            cast_id=data['cast_id'],
            business_id=data['business_id'],
            name=data['name'],
            profile_url=data['profile_url'],
            is_active=data.get('is_active', True)
        )

@dataclass
class Status:
    """ステータスエンティティモデル"""
    cast_id: str
    business_id: int
    is_working: bool
    is_on_shift: bool
    recorded_at: datetime
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Status':
        """データベース行からステータスインスタンスを作成する"""
        return cls(
            cast_id=data['cast_id'],
            business_id=data['business_id'],
            is_working=data['is_working'],
            is_on_shift=data['is_on_shift'],
            recorded_at=data['recorded_at']
        )

@dataclass
class StatusHistory:
    """ステータス履歴エンティティモデル"""
    business_id: int
    biz_date: date
    working_rate: float
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StatusHistory':
        """データベース行からステータス履歴インスタンスを作成する"""
        return cls(
            business_id=data['business_id'],
            biz_date=data['biz_date'],
            working_rate=data['working_rate']
        )

@dataclass
class ScrapingResult:
    """スクレイピング操作の結果"""
    cast_id: str
    is_working: bool
    is_on_shift: bool
    recorded_at: datetime
    success: bool
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """初期化後のデータ検証"""
        if not self.success and not self.error_message:
            raise ValueError("成功フラグがFalseの場合、エラーメッセージが必要です")

@dataclass
class BatchJobResult:
    """バッチジョブ実行の結果"""
    job_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    processed_count: int = 0
    error_count: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """ジョブの実行時間を秒数で計算する"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def add_error(self, error: str):
        """結果にエラーを追加する"""
        self.errors.append(error)
        self.error_count += 1
    
    def add_success(self):
        """成功カウンターを増加させる"""
        self.processed_count += 1
    
    def finalize(self, success: bool = None):
        """ジョブ結果を確定する"""
        self.completed_at = datetime.now()
        if success is not None:
            self.success = success
        else:
            self.success = self.error_count == 0


@dataclass
class CastStatus:
    """キャスト状況データモデル（スクレイピング結果用）"""
    name: str
    is_working: bool
    business_id: str
    cast_id: str = ""
    on_shift: bool = True
    shift_times: str = ""
    working_times: str = ""
    
    def __str__(self):
        working_status = "working" if self.is_working else "not working"
        return f"CastStatus({self.name}, {working_status})"
