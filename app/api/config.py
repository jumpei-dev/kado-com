"""設定API
フロントエンドから設定値を取得するためのエンドポイント
"""

from fastapi import APIRouter
from app.core.config import config_manager

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("/line")
async def get_line_config():
    """LINE設定を取得"""
    return {
        "url": config_manager.get("line.url", "https://line.me/ti/p/fDpRYZH7C2"),
        "initial_delay_seconds": config_manager.get("line.initial_delay_seconds", 30),
        "reoccurrence_interval_minutes": config_manager.get("line.reoccurrence_interval_minutes", 30)
    }