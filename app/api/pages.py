from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter()

# テンプレートディレクトリを設定
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/data-guide", response_class=HTMLResponse)
async def data_guide_page(request: Request):
    """データの見方ページ"""
    return templates.TemplateResponse(
        "data_guide.html",
        {"request": request}
    )
