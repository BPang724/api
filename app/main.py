from fastapi import FastAPI

app = FastAPI(title="My Backend API")

import os
from pathlib import Path
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
api_router = APIRouter(prefix="/api")

# 取得 main.py 的路徑，並往上退三層找到專案根目錄，再指向 webui
# main.py -> app/ -> api/ -> 專案根目錄 -> webui
BASE_DIR = Path(__file__).resolve().parent.parent.parent
webui_dir = BASE_DIR / "webui"

# 掛載靜態資源與首頁
app.mount("/static", StaticFiles(directory=str(webui_dir)), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(webui_dir / "index.html")


@api_router.get("/health")
def health_check():
    return {"status": "ok"}

@api_router.get("/version")
def version_check():
    return {"version": "0.1.0"}

app.include_router(api_router)