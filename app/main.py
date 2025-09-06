from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI(title="稼働.com")

# 静的ファイルの設定
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# テンプレートの設定
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページを表示"""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "稼働.com"}
    )

# ダミーデータ（後でDBから取得するように変更）
STORES = [
    {
        "id": 1, 
        "name": "チュチュバナナ", 
        "genre": "ソープランド", 
        "area": "東京",
        "working_rate": 85.5, 
        "previous_rate": 82.0, 
        "weekly_rate": 80.2
    },
    {
        "id": 2, 
        "name": "クラブA", 
        "genre": "キャバクラ", 
        "area": "大阪",
        "working_rate": 75.0, 
        "previous_rate": 78.5, 
        "weekly_rate": 76.3
    },
    {
        "id": 3, 
        "name": "レモネード", 
        "genre": "ピンサロ", 
        "area": "名古屋",
        "working_rate": 68.8, 
        "previous_rate": 65.5, 
        "weekly_rate": 70.1
    }
]

@app.get("/api/stores", response_class=HTMLResponse)
async def get_stores(request: Request):
    """店舗一覧をHTMLとして返す（HTMX用）"""
    return templates.TemplateResponse(
        "components/stores_list.html", 
        {"request": request, "stores": STORES}
    )

@app.get("/api/stores/{store_id}", response_class=HTMLResponse)
async def get_store(request: Request, store_id: int):
    """店舗詳細をHTMLとして返す（HTMX用）"""
    store = next((s for s in STORES if s["id"] == store_id), None)
    if not store:
        return {"error": "Store not found"}
    return templates.TemplateResponse(
        "components/store_detail.html", 
        {"request": request, "store": store}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
