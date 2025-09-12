from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.core.config import config_manager

router = APIRouter()

# テンプレートディレクトリを設定
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/data-guide", response_class=HTMLResponse)
async def data_guide_page(request: Request):
    """データの見方ページ"""
    config_data = config_manager.config
    return templates.TemplateResponse(
        "data_guide.html",
        {"request": request, "config": config_data}
    )
