from pathlib import Path
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from routers.notes import router as notes_router

app = FastAPI(
    title="My Backend API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    root_path="/s115321529",
)
api_router = APIRouter(prefix="/api")

api_router.include_router(notes_router)
app.include_router(api_router)

# 取得 main.py 的路徑，並往上退三層找到專案根目錄，再指向 webui
# main.py -> app/ -> api/ -> 專案根目錄 -> webui
BASE_DIR = Path(__file__).resolve().parent.parent.parent
webui_dir = BASE_DIR / "webui"


class HtmlCssOnlyStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        if Path(path).suffix.lower() not in {".html", ".css"}:
            return PlainTextResponse("Not Found", status_code=404)
        return await super().get_response(path, scope)


# 明確提供 CSS，確保首頁使用的靜態路徑能找到同層檔案
@app.get("/static/style.css")
async def serve_stylesheet():
    return FileResponse(webui_dir / "style.css", media_type="text/css")

@app.get("/")
async def serve_index():
    return FileResponse(webui_dir / "index.html")


# 掛載其他靜態資源，並限制只提供 HTML 和 CSS
app.mount("/static", HtmlCssOnlyStaticFiles(directory=str(webui_dir)), name="static")


@api_router.get("/health")
def health_check():
    return {"status": "ok"}

@api_router.get("/version")
def version_check():
    return {"version": "0.1.0"}