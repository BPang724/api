from pathlib import Path
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(
    title="My Backend API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    root_path="/s115321529",
)
api_router = APIRouter(prefix="/api")

app.include_router(api_router)

# 取得 main.py 的路徑，並往上退三層找到專案根目錄，再指向 webui
# main.py -> app/ -> api/ -> 專案根目錄 -> webui
BASE_DIR = Path(__file__).resolve().parent.parent.parent
webui_dir = BASE_DIR / "webui"

# 明確提供 CSS，確保首頁使用的靜態路徑能找到同層檔案
@app.get("/static/style.css")
async def serve_stylesheet():
    return FileResponse(webui_dir / "style.css", media_type="text/css")


# 掛載其他靜態資源
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