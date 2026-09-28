# FastAPI + PostgreSQL 後端系統開發：12 週實作課程

> 針對已有全端開發與系統架構背景的學習者設計，跳過基礎語法複習，直接進入後端系統的實務建構。每週包含：學習目標、為什麼這樣安排、實作步驟、本週練習、驗收標準。

## 總覽

| 週次 | 主題 | 產出 |
|---|---|---|
| W01 | FastAPI 專案架構與基礎 API | 可執行的 Hello API 專案骨架 |
| W02 | PostgreSQL 安裝與連線 | 資料庫連線成功、建立第一個 table、加入API |
| W03 | SQLAlchemy ORM + Alembic Migration | Model 定義與版本化的 schema |
| W04 | CRUD API 完整實作 | 一組完整的 RESTful CRUD 端點 |
| W05 | 關聯式設計（一對多、多對多） | 多資料表關聯查詢 |
| W06 | 身份驗證（JWT / OAuth2） | 登入、保護路由 |
| W07 | 測試（pytest） | 自動化測試覆蓋 CRUD + Auth |
| W08 | 非同步與連線池 | Async ORM 操作、效能觀念 |
| W09 | 進階查詢：分頁、篩選、搜尋 | Query 參數化的 API |
| W10 | 錯誤處理、Logging、Middleware | 具生產等級的錯誤回應與紀錄 |
| W11 | Docker 化 | docker-compose 一鍵啟動 API + DB |
| W12 | 部署與整合專題 | 完整可展示的後端專案 |

---

## W01：FastAPI 專案架構與基礎 API

### 學習目標
理解 FastAPI (Python) 的專案結構慣例，以及它跟 (Node.js) Express.js / Spring Boot 這類框架的對應關係。

### 為什麼這樣安排
自學 REST API 設計，不花時間講「什麼是 API」，而是直接建立你之後 12 週都會沿用的專案骨架，這樣後面每週只需要疊加功能。

### 操作步驟

* install Python Install Manager (Windows Market)

```bash
mkdir api
cd api
py -m venv venv
venv\Scripts\activate      # Windows Powershell, Set-ExecutionPolicy
pip install fastapi uvicorn[standard]
```

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

建立專案結構：開始學習與思考自己或團隊習慣的program structures
```
api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   └── __init__.py
│   ├── core/
│   │   └── __init__.py
│   └── models/
│       └── __init__.py
├── requirements.txt
└── venv/
```

`app/main.py`：
```python
from fastapi import FastAPI

app = FastAPI(title="My Backend API")

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

啟動：
```bash
uvicorn app.main:app --reload
```

打開 `http://127.0.0.1:8888/docs`，這是 FastAPI 自動產生的 Swagger UI（對應你熟悉的 Swagger/OpenAPI 概念，但這裡完全自動產生，不用手寫 YAML）。

### 本週練習
1. 新增一個 `/version` 端點，回傳 `{"version": "0.1.0"}`
2. 用 Pydantic 定義一個 `Item` 模型（含 `name: str`、`price: float`），寫一個 `POST /items` 接收並回傳它
3. 執行 `pip freeze > requirements.txt`，理解這個檔案對應 Node.js 的 `package.json` 扮演什麼角色
4. AI：為 py + fastapi + psql 建立 .gitignore
5. Install Git、建立 github repo，並push and commit

```git
# 1. 建立本機第一個 commit
git add .
git commit -m "W1: FastAPI Test"

# 2. 設定 GitHub 遠端 repository
git remote add origin https://github.com/icsie/api.git

# 3. 設定主分支名稱
git branch -M main

# 4. 發現 GitHub 已有 Initial commit，因此先取得遠端歷史
git fetch origin

# 5. 合併本機與 GitHub 的不同歷史
git merge origin/main --allow-unrelated-histories

# 6. 推送到 GitHub
git push -u origin main
```

### 驗收標準
- [x] `/docs` 能正常開啟並看到自訂端點
- [ ] `POST /items` 能正確驗證型別（試著傳錯誤型別，觀察 FastAPI 自動回傳的 422 錯誤）
- [x] 了解建立根目錄的 .gitignore，涵蓋：Python 虛擬環境與快取、pytest、coverage、mypy、ruff 產物、.env 設定檔、FastAPI/Uvicorn log、PostgreSQL 本地資料與備份、VS Code、IDE 與作業系統檔案
- [x] 學會 `.gitignore`：`!` 取消忽略，例如 !.env.example 會保留範例設定檔。
- [x] add .env.example，並commit and push確認出現自github repo。

### Powershell經驗
- AI：let powershell can run .ps1 by default ==> PowerShell can now run local .ps1 scripts by default for your user via `RemoteSigned`. Downloaded scripts must still be signed or unblocked (考慮到資安問題).

### VSCode心得
- 安裝軟體如Git，會寫入環境變數PATH，要完全結束VSCode (close all opened code windows)，reopen vscode才會在powershell環境生效。

### Git心得
- 本機先有 commit 時，GitHub 建立 repository 最好保持完全空白；不要同時勾選建立 README 或 LICENSE，這樣第一次 `git push -u origin main` 最簡單。

---

## W02：PostgreSQL 安裝與連線

### 學習目標
在本機建立 PostgreSQL，並讓 Python 程式成功連線。

### 為什麼這樣安排
先確保「資料庫本身活著、連得上」，再進到 ORM 抽象層。這樣之後如果連線出錯，你能分辨是資料庫問題還是程式碼問題。

### 操作步驟

**安裝 PostgreSQL（Windows Admin）**
1. 到官方下載頁安裝 PostgreSQL（建議 16 版以上）
2. 安裝時會要求設定 `postgres` 超級使用者密碼，記下來
3. 建議一併安裝 pgAdmin（GUI 管理工具，對應你熟悉的 DBeaver / TablePlus 概念）

**安裝 PostgreSQL（Windows Users Permission，電腦教室用此法安裝）**

若目前帳號只有一般 `Users` 權限，建議使用 PostgreSQL ZIP 免安裝版。此方式不建立 Windows Service，也不需要寫入 `Program Files`，可安裝在使用者目錄。

1. 下載與作業系統相容的 PostgreSQL Windows ZIP binary。
2. 將 ZIP 解壓縮至使用者目錄，例如：

```text
C:\Users\<你的帳號>\pgsql
```

3. 建立資料目錄：

```powershell
mkdir "$env:USERPROFILE\pgsql-data"
```

4. 初始化資料庫叢集：

```powershell
cd "$env:USERPROFILE\pgsql"

.\bin\initdb.exe `
  -D "$env:USERPROFILE\pgsql-data" `
  -U postgres `
  -A scram-sha-256 `
  -W
```

執行後依提示設定 `postgres` 使用者密碼。

5. 啟動 PostgreSQL。若 `5432` 已被其他服務使用，可使用 `5433`：

```powershell
.\bin\pg_ctl.exe `
  -D "$env:USERPROFILE\pgsql-data" `
  -o "-p 5433" `
  -l "$env:USERPROFILE\pgsql-data\server.log" `
  start
```

6. 連線測試：

```powershell
.\bin\psql.exe `
  -h localhost `
  -p 5433 `
  -U postgres `
  -d postgres
```

7. 在 `psql` 中建立開發用資料庫與使用者：

```sql
CREATE USER dev_user WITH PASSWORD 'dev_password';
CREATE DATABASE fastapi_dev OWNER dev_user;
\c fastapi_dev
GRANT ALL ON SCHEMA public TO dev_user;
```

檢查是否成功寫入DB：

```sql
SELECT version(); SELECT current_database(), current_user;
```

結束PSQL DB：

```sql
exit
```

8. 修改 `.env`：

```env
DATABASE_URL=postgresql://dev_user:dev_password@localhost:5433/fastapi_dev
```

停止 PostgreSQL：

```powershell
.\bin\pg_ctl.exe `
  -D "$env:USERPROFILE\pgsql-data" `
  stop
```

> ZIP 版本不會自動建立 Windows Service，因此每次使用前需要執行 `pg_ctl start`。若要讓 PostgreSQL 開機自動啟動，通常需要系統管理員協助建立服務。


#### 建立開發用資料庫與使用者
```sql: add file .\psql\createdb.sql
-- 用 psql 或 pgAdmin 執行
CREATE DATABASE fastapi_dev;
CREATE USER dev_user WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE fastapi_dev TO dev_user;

\connect fastapi_dev
GRANT USAGE, CREATE ON SCHEMA public TO dev_user; -- public schema建表權限
```

```pwsh: psql 執行
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' `
  -U postgres `
  -d postgres `
  -f .\psql\createdb.sql
```

**Python 端安裝驅動**
```bash
pip install "psycopg[binary]" python-dotenv
```

`.env`（不要進版控，需加入 `.gitignore`）：
```
DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/fastapi_dev
```

測試連線 `app/core/db_test.py`：
```python
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

def test_connection():
    conn = psycopg.connect(os.getenv("DATABASE_URL"))
    print("連線成功:", conn.info.dbname)
    conn.close()

if __name__ == "__main__":
    test_connection()
```

```pwsh
python .\app\core\db_test.py
```

連線成功: fastapi_dev

### 本週練習
1. 用 `psql` 指令手動建立一個 `notes` table（欄位：`id`, `title`, `content`, `created_at`）；用 `INSERT` 手動塞3筆資料，再用 `SELECT` 查回來
2. New REST api: /note/{id}

### 驗收標準
- [x] Python 程式能成功連上 PostgreSQL
- [x] 能說明為什麼密碼要放在 `.env` 而不是寫死在程式碼裡（對應你熟悉的環境變數管理概念）
    -因為放在程式碼中在git push時會一起被push上去，若有心人士看到則可對資料庫做修改，且放在.env中，若之後密碼有變更只需針對.env做修改，不用一個一個到程式碼中做修改
- [ ] Test API and data format (了解Swagger用法，具備測試API能力)

### 心得
- VScode Extension: SQLTools PostgreSQL/Cockroach Driver，方便VSCode可以執行SQL
- psql: 另外建立db帳號 (postgres權限勿濫用)，須要給予public schema建表權限
- AI coding會建立更清楚的program structures。E.g. routers (REST api path) -> repositories (get data SQL) -> schemas (response model)


---

## W03：Run FastAPI as Web App and API

### 學習目標
用FastAPI做為http server，同時服務web app and api。

root
> Add run.bat to run fastapi with local_IP:7777

app\main.py
> Make fastapi to be a http server with a folder as the root.
- Set public_directory to your webui
- 仔細測試觀察是否有問題？
> Make all api paths correspond to /api/
- 仔細測試觀察是否有問題？
> #sym:StaticFiles: restrict public access to .html and .css only.
- 注意Browser HTTP cache問題
> 另開無痕測試就好了，why? 以後如何注意此問題
- F12 > Network > Disable Cache

### 驗收標準
- [x] local IP可存取
- [x] 上課與TA設定 https://demo.wke.csie.ncnu.edu.tw/studentno 可存取
- [x] 盡量測試，列出問題討論solutions
    - 網頁可透過Ctrl+F5強制重整
    - 網站response status 404但後端terminal顯示200 OK，因為copilot修改路徑後仍忘記加root_path進main.py中
### 心得
- 在VScode中使用copilot AI coding即便給出完整錯誤訊息也不一定能完整解決問題，有時搭配截圖訊息給AI效果更好

---

## W04：CRUD API 完整實作

### RESTful API

RESTful API 是一種以「資源（resource）」為中心設計 HTTP API 的方式。每一種資源都有固定的 URL，例如 `/notes` 代表筆記集合，`/notes/{id}` 代表某一筆筆記；用不同的 HTTP method 表達對資源的操作，而不是為每個動作建立不同的動詞型 URL。

CRUD 分別代表 **Create（新增）**、**Read（查詢）**、**Update（更新）**、**Delete（刪除）**。以下以 `notes` 資源為例：

| CRUD | HTTP method | 範例路徑 | 使用時機 | 請求／回應範例 |
|---|---|---|---|---|
| Create | `POST` | `/notes` | 建立一筆新資源，由伺服器產生 `id` | 請求：`{"title": "學習 REST", "content": "理解 CRUD"}`<br>回應：`201 Created` 與建立後的 note |
| Read（列表） | `GET` | `/notes` | 取得資源集合，可搭配分頁、篩選或搜尋 | 回應：`200 OK` 與 notes 陣列 |
| Read（單筆） | `GET` | `/notes/{id}` | 取得指定 `id` 的資源 | 回應：`200 OK` 與單筆 note；不存在時回傳 `404 Not Found` |
| Update | `PUT` | `/notes/{id}` | 以完整資料取代指定資源 | 請求：`{"title": "更新標題", "content": "更新內容"}`<br>回應：`200 OK` 與更新後的 note |
| Delete | `DELETE` | `/notes/{id}` | 刪除指定資源 | 回應：`204 No Content`；不存在時回傳 `404 Not Found` |

設計 API 時，路徑通常使用名詞而不是動詞，例如使用 `POST /notes`，而不是 `/createNote`。同一個 HTTP method 與 URL 應具有一致且可預期的語意，讓前端、其他服務與 API 文件都容易理解與使用。


### 學習目標
串接API與資料庫，完成一組完整 RESTful CRUD。

### 為什麼這樣安排
這是第一個「垂直切片」（vertical slice）——從 HTTP 請求到資料庫的完整路徑打通，之後每一週都是在這個路徑上疊加功能，而不是零散學習。

### AI coding
> 針對/api/note 加入REST CRUD功能 (需對應慣用HTTP Method)
- 仔細觀察修改的程式碼，另開瀏覽器詢問AI以求理解
- 撰寫學習心得

### 人工操作步驟

#### 分層設計理念：routers → schemas → repositories → core

將 API 拆成不同層次，是為了讓每個檔案只負責一種工作，降低修改時彼此影響的範圍。一次請求大致會依照以下流程處理：

1. **Routers（路由層）**：決定 API 的 URL、HTTP method 與回應狀態，接收請求後呼叫下一層，不直接撰寫大量 SQL 或資料庫連線細節。
2. **Schemas（資料格式層）**：使用 Pydantic 定義請求與回應格式，負責型別驗證、欄位限制，以及避免把資料庫內部欄位直接暴露給前端。
3. **Repositories（資料存取層）**：集中處理 SQL 與資料庫 CRUD，讓 Router 不需要知道資料表查詢的細節。
4. **Core（共用基礎設施層）**：提供資料庫連線、設定、驗證或其他全域共用功能；例如 `core/db.py` 管理 PostgreSQL 連線。

因此，實際的責任關係可以理解為：

```text
HTTP request
    → routers/notes.py       路由與流程控制
    → schemas/notes.py        請求資料驗證
    → repositories/notes.py  SQL 與資料存取
    → core/db.py              PostgreSQL 連線
    → HTTP response
```

相關檔案的使用方式如下：

| 元件 | 目前專案檔案 | 主要用途 |
|---|---|---|
| Router | `app/routers/notes.py` | 定義 `/api/notes` 等端點，處理 HTTP 請求與回應 |
| Schema | `app/schemas/notes.py` | 定義 `NoteCreate`、`NoteResponse` 等輸入輸出模型 |
| Repository | `app/repositories/notes.py` | 封裝 notes 的 SQL 查詢、新增、更新與刪除 |
| Core | `app/core/db.py` | 建立與管理 PostgreSQL 資料庫連線 |
| Core | `app/core/static_files.py` | 集中處理前端靜態檔案的提供方式 |
| Application entrypoint | `app/main.py` | 建立 FastAPI app、註冊 Router 與設定整體服務 |

這種分層方式的重點不是檔案越多越好，而是讓變更容易定位：API 路徑改動主要看 Router，資料格式改動看 Schema，SQL 改動看 Repository，資料庫連線設定則集中在 Core。

#### ORM 技術概念

ORM（Object-Relational Mapping，物件關聯式對映）是把 Python 物件與關聯式資料庫的資料表對應起來的技術。開發者可以操作 `Note` 這類 Python model，ORM 再將操作轉換成 PostgreSQL 能理解的 SQL。

簡單對照如下：

| ORM 概念 | Python / SQLAlchemy 範例 | 資料庫概念 |
|---|---|---|
| Model class | `class Note` | `notes` 資料表 |
| Object attribute | `note.title` | `title` 欄位 |
| Object instance | `note = Note(...)` | 一筆資料（row） |
| Query | `db.query(Note).filter(...)` | `SELECT ... WHERE ...` |
| `db.add()` | 將物件加入 Session | 準備新增一筆資料 |
| `db.commit()` | 提交 Session 的變更 | 真正寫入資料庫 |

例如，以下 ORM 查詢：

```python
note = db.query(Note).filter(Note.id == note_id).first()
```

概念上相當於：

```sql
SELECT * FROM notes WHERE id = :note_id LIMIT 1;
```

其中 `db` 通常是 SQLAlchemy 的 `Session`。Session 可以理解成一次資料庫操作的工作範圍，負責追蹤物件變更、送出查詢，以及透過 `commit()` 確認交易。若發生錯誤，也可以使用 `rollback()` 撤銷尚未提交的變更。

使用 ORM 的好處是可以用 Python model 與型別來表達資料操作，減少手寫 SQL 的數量，並集中處理交易與資料庫連線；但仍然需要理解 SQL，因為 ORM 最後仍會產生 SQL，複雜查詢也可能需要直接使用 SQLAlchemy 的查詢語法。

本節為了讓 CRUD 流程集中，先在 Router 中直接示範 ORM 操作。實際專案可將 `db.query()`、`db.add()` 等資料庫操作移到 `app/repositories/notes.py`，讓 Router 只負責接收請求、呼叫 Repository 與回傳結果。

`app/schemas/note.py`（Pydantic schema，區分「API 輸入輸出」與「資料庫 model」是重要慣例）：
```python
# Schema 只描述 API 收到與回傳的資料格式，不負責執行 SQL。
# import 是匯入其他套件或模組，讓目前檔案可以使用其中的類別與函式。
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# POST /notes 使用的請求格式；content 可省略。
# class 用來定義一個可重複使用的資料結構或物件類別。
class NoteCreate(BaseModel):
    # 冒號後的 str 是型別註記，表示 title 預期是一段文字。
    title: str
    # Optional[str] 表示可以是文字或 None；= None 表示預設值是 None。
    content: Optional[str] = None

# API 回應格式；不直接暴露資料庫 model 給前端。
class NoteResponse(BaseModel):
    # Pydantic 會依照這些型別註記檢查與轉換資料。
    id: int
    title: str
    content: Optional[str]
    created_at: datetime

    # 允許 Pydantic 從 ORM model 的屬性建立回應資料。
    # 內嵌 class Config 是設定這個 Pydantic model 行為的舊版寫法。
    class Config:
        # ORM 物件像 note.title；一般字典則像 {"title": "學習 REST"}。
        # True 允許 Pydantic 讀取 ORM 物件的屬性，轉成 NoteResponse。
        # 若沒有這項設定，通常只能從字典鍵值建立，例如 NoteResponse(**data)。
        from_attributes = True
```

`app/api/notes.py`：
```python
# Router 負責 HTTP 路由與流程控制；資料庫細節可再委派給 repository。
# APIRouter 是 FastAPI 用來集中管理一組相關 API 路由的類別。
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteResponse

# 同一組 notes 資源共用路徑前綴與 OpenAPI 分類。
# 關鍵字參數使用 name=value，讓設定的意義比位置順序更清楚。
router = APIRouter(prefix="/notes", tags=["notes"])

# Create：先由 NoteCreate 驗證請求，再建立資料庫 model。
# @ 是 decorator 語法：把函式註冊成指定 HTTP method 與路徑的 API endpoint。
# response_model 會驗證並限制回傳給前端的欄位格式。
@router.post("/", response_model=NoteResponse)
# note: NoteCreate 是請求 body，db 由 FastAPI 依賴注入，不需手動建立連線。
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    # ** 會把字典的 key/value 展開成函式或類別建構子的關鍵字參數。
    db_note = Note(**note.model_dump())
    # model_dump() 將 Pydantic model 轉成一般 Python 字典。
    db.add(db_note)
    # add、commit、refresh 是 ORM 常見的新增、提交、重新讀取資料流程。
    db.commit()
    db.refresh(db_note)
    return db_note

# Read：回傳所有 notes，response_model 會統一輸出格式。
# list[NoteResponse] 表示回應是一個由 NoteResponse 組成的列表。
@router.get("/", response_model=list[NoteResponse])
# Depends(get_db) 表示呼叫 endpoint 時，由 FastAPI 執行 get_db 並傳入結果。
def list_notes(db: Session = Depends(get_db)):
    # .all() 將查詢結果全部取回；資料量大時應搭配分頁。
    return db.query(Note).all()

# Read：依照 note_id 查詢單筆資源。
@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    # .filter() 加入查詢條件，== 是建立 SQL 條件，不是立即比較 Python 值。
    note = db.query(Note).filter(Note.id == note_id).first()
    # if not 可檢查查詢結果是否為 None 或其他「沒有資料」的狀態。
    if not note:
        # HTTPException 會讓 FastAPI 回傳指定的 HTTP 錯誤狀態與訊息。
        raise HTTPException(status_code=404, detail="Note not found")
    return note

# Update：以 NoteCreate 的完整資料更新指定資源。
@router.put("/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note_data: NoteCreate, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    # for 逐一處理字典內容；key 是欄位名稱，value 是要寫入的新值。
    for key, value in note_data.model_dump().items():
        # setattr(obj, name, value) 依欄位名稱動態設定物件屬性。
        setattr(note, key, value)
    db.commit()
    db.refresh(note)
    return note

# Delete：找不到資源時回傳 404，避免讓呼叫端誤以為刪除成功。
@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    # delete 標記 ORM 物件待刪除，commit 後才會真正寫入資料庫。
    db.delete(note)
    db.commit()
    # return 的字典會被 FastAPI 自動序列化成 JSON 回應。
    return {"detail": "deleted"}
```

在 `app/main.py` 註冊路由：
```python
from app.api import notes
app.include_router(notes.router)
```

### 本週練習
1. 為 `User` 或個人專案會用到的資料表，也做一組完整 CRUD
2. 思考並實作：`DELETE` 時如果 note 不存在，回傳的狀態碼與錯誤訊息是否符合 REST 慣例
3. 用 `/docs` 的 Swagger UI 手動測試所有端點

### 驗收標準
- [ ] 五個 CRUD 端點全部正常運作
- [x] 錯誤情境（找不到資源）回傳正確的 HTTP 狀態碼

### 學習心得
- 

---

## W5：關聯式設計（一對多、多對多）

### 學習目標
用 SQLAlchemy 的 relationship 處理跨表關聯，並理解 N+1 查詢問題。

### 為什麼這樣安排
真實系統幾乎都是多表關聯。這裡會刻意示範「一對多」（User 有多個 Note）與「多對多」（Note 可以有多個 Tag），並點出效能陷阱。

### 操作步驟

`app/models/note.py`（加上外鍵與關聯）：
```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="notes")
```

`app/models/user.py`：
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    notes = relationship("Note", back_populates="owner")
```

多對多需要中介表（association table）：
```python
from sqlalchemy import Table

note_tags = Table(
    "note_tags", Base.metadata,
    Column("note_id", ForeignKey("notes.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    notes = relationship("Note", secondary=note_tags, back_populates="tags")
```

執行 `alembic revision --autogenerate` 產生對應 migration。

### N+1 問題示範
```python
# 有問題的寫法：每個 note 都額外查一次 owner（N+1）
notes = db.query(Note).all()
for note in notes:
    print(note.owner.email)  # 每次都觸發一次 SQL

# 正確寫法：用 joinedload 一次拿完
from sqlalchemy.orm import joinedload
notes = db.query(Note).options(joinedload(Note.owner)).all()
```

### 本週練習
1. 完成 Tag 的 CRUD，並實作「一則 note 新增多個 tag」的端點
2. 用 SQLAlchemy 的 echo 模式（`create_engine(url, echo=True)`）觀察 N+1 實際印出的 SQL 語句數量
3. 改用 `joinedload` 後，再次觀察 SQL 語句數量差異

### 驗收標準
- [ ] 能查詢一個 user 底下所有 notes，以及一則 note 底下所有 tags
- [ ] 能具體說出 N+1 問題發生的原因與解法

---

## W6：身份驗證（JWT / OAuth2）

### 學習目標
實作註冊、登入、JWT 簽發，以及保護需要登入才能存取的端點。

### 操作步驟

```bash
pip install "python-jose[cryptography]" "passlib[bcrypt]"
```

`app/core/security.py`：
```python
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_minutes: int = 60):
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

`app/api/auth.py`（登入端點與保護路由用的 dependency）：
```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, SECRET_KEY, ALGORITHM
from app.models.user import User

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

保護端點：
```python
from app.api.auth import get_current_user

@router.get("/notes/me")
def my_notes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Note).filter(Note.owner_id == current_user.id).all()
```

### 本週練習
1. 實作 `/register` 端點（存密碼前務必用 `hash_password`）
2. 修改所有 note CRUD 端點，加上 `get_current_user`，確保使用者只能操作自己的 note
3. 思考：JWT 存在前端的哪裡比較安全？（localStorage vs httpOnly cookie）並寫下你的判斷理由

### 驗收標準
- [ ] 沒有 token 存取受保護端點會回傳 401
- [ ] 使用者無法刪除/修改別人的 note

---

## W7：測試（pytest）

### 學習目標
用 pytest + FastAPI TestClient 對 CRUD 與 Auth 寫自動化測試。

### 操作步驟

```bash
pip install pytest httpx
```

`tests/conftest.py`（用獨立測試資料庫，避免污染開發資料）：
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, get_db

TEST_DATABASE_URL = "postgresql://dev_user:dev_password@localhost:5432/fastapi_test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
```

`tests/test_notes.py`：
```python
def test_create_note(client):
    response = client.post("/notes/", json={"title": "test", "content": "hello"})
    assert response.status_code == 200
    assert response.json()["title"] == "test"

def test_get_nonexistent_note(client):
    response = client.get("/notes/999")
    assert response.status_code == 404
```

### 本週練習
1. 為 `/register` 與 `/login` 寫測試（含密碼錯誤情境）
2. 為「使用者不能刪除別人的 note」這個規則寫一個測試
3. 執行 `pytest -v`，確保全部通過

### 驗收標準
- [ ] 測試覆蓋所有 CRUD 端點與主要錯誤情境
- [ ] `pytest` 全數通過，且測試資料庫不影響開發資料庫

---

## W8：非同步與連線池

### 學習目標
理解 FastAPI 的 async 支援，並改用 async ORM 操作。

### 為什麼這樣安排
你熟悉 Node.js 的非同步模型，這週會對照講解 Python 的 `async/await` 跟 Node 的 event loop 概念異同，並說明「不是所有東西都要 async」的判斷原則。

### 操作步驟

```bash
pip install asyncpg "sqlalchemy[asyncio]"
```

`app/core/database.py`（改為 async engine）：
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

ASYNC_DATABASE_URL = "postgresql+asyncpg://dev_user:dev_password@localhost:5432/fastapi_dev"
engine = create_async_engine(ASYNC_DATABASE_URL, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

改寫端點為 async：
```python
from sqlalchemy import select

@router.get("/", response_model=list[NoteResponse])
async def list_notes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Note))
    return result.scalars().all()
```

### 本週練習
1. 把 W4-W6 的所有端點改寫為 async 版本
2. 用 `pool_size` 與 `max_overflow` 參數，理解連線池的上限概念（對應你熟悉的資料庫連線池概念，例如 HikariCP）
3. 寫一個簡單的負載測試（可用 `locust` 或手動並發請求），比較 sync 與 async 版本在高並發下的差異

### 驗收標準
- [ ] 所有端點改為 async 且功能不變
- [ ] 能解釋「什麼情境下 async 才真的有幫助」（I/O bound vs CPU bound）

---

## W9：進階查詢：分頁、篩選、搜尋

### 學習目標
實作實務系統必備的分頁、動態篩選、關鍵字搜尋。

### 操作步驟

```python
from fastapi import Query

@router.get("/", response_model=list[NoteResponse])
async def list_notes(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    search: str | None = None,
    is_archived: bool | None = None,
):
    stmt = select(Note)
    if search:
        stmt = stmt.where(Note.title.ilike(f"%{search}%"))
    if is_archived is not None:
        stmt = stmt.where(Note.is_archived == is_archived)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
```

### 本週練習
1. 加上排序參數（`sort_by`, `order`），允許依 `created_at` 或 `title` 排序
2. 回傳分頁時，附上總筆數（`X-Total-Count` header 或包在 response body）
3. 針對 `search` 欄位思考：`ilike` 在大資料量時的效能問題，並研究 PostgreSQL 全文搜尋（`tsvector`）作為進階選項

### 驗收標準
- [ ] 分頁、篩選、搜尋可以同時組合使用
- [ ] `limit` 有上限保護，避免一次撈出過多資料

---

## W10：錯誤處理、Logging、Middleware

### 學習目標
建立統一的錯誤回應格式與結構化 log。

### 操作步驟

`app/core/exceptions.py`：
```python
from fastapi import Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "path": str(request.url)},
    )
```

在 `main.py` 註冊：
```python
from app.core.exceptions import AppException, app_exception_handler
app.add_exception_handler(AppException, app_exception_handler)
```

Logging middleware：
```python
import time, logging
logger = logging.getLogger("app")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} {response.status_code} {duration:.3f}s")
    return response
```

### 本週練習
1. 把所有 `HTTPException` 統一改成自訂的 `AppException`，確保錯誤格式一致
2. 設定 log 同時輸出到 console 與檔案，並區分 `INFO` / `ERROR` 等級
3. 加一個全域的「未預期例外」處理器，避免 500 錯誤時把 stack trace 洩漏給前端

### 驗收標準
- [ ] 所有錯誤回應格式一致
- [ ] Log 能追蹤到每個請求的方法、路徑、狀態碼、耗時

---

## W11：Docker 化

### 學習目標
把 FastAPI + PostgreSQL 用 docker-compose 一鍵啟動。

### 操作步驟

`Dockerfile`：
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.yml`：
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: fastapi_dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build: .
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://dev_user:dev_password@db:5432/fastapi_dev
    ports:
      - "8000:8888"

volumes:
  pgdata:
```

啟動：
```bash
docker compose up --build
```

### 本週練習
1. 確認容器重啟後資料還在（驗證 volume 是否正確掛載）
2. 加入 migration 自動執行的步驟（在 `api` 容器啟動時先跑 `alembic upgrade head`）
3. 研究並寫下：production 環境下，為什麼不建議用 `--reload`，也不建議把資料庫密碼寫死在 `docker-compose.yml`

### 驗收標準
- [ ] `docker compose up` 後，API 與資料庫都能正常運作且互通
- [ ] 重啟容器後資料不遺失

---

## W12：部署與整合專題

### 學習目標
把前 11 週的成果整合成一個完整、可展示的後端專案，並理解基本部署概念。

### 本週任務（作為期末專題，不提供完整程式碼，靠你自己整合）

1. **功能整合**：確認 CRUD、關聯查詢、Auth、分頁搜尋、錯誤處理、Logging 全部串在同一個專案中並能正常運作
2. **文件補齊**：撰寫一份 `README.md`，說明專案架構、如何啟動、API 一覽（可搭配 `/docs` 的 Swagger UI）
3. **CI 基礎**：用 GitHub Actions 設定一個簡單的 workflow，每次 push 自動執行 `pytest`
4. **部署嘗試**（擇一）：
   - 部署到 Render / Railway 等平台的免費方案
   - 或在自己的雲端主機用 docker-compose 跑起來
5. **架構回顧**：以你的 software architect 背景，寫一頁簡短的技術筆記，評估這個專案目前的**架構限制**（例如：沒有 rate limiting、沒有 cache layer、沒有背景任務佇列），並列出如果要正式上線，你會優先補強哪三項

### 驗收標準
- [ ] 專案可以從乾淨環境（新 clone 下來）依照 README 步驟成功啟動
- [ ] CI 能在 push 時自動跑測試並回報結果
- [ ] 完成架構限制評估筆記

---

## 學習方式提醒

每週的「本週練習」請自己動手寫，卡住時可以帶著具體錯誤訊息來討論，而不是直接要完整程式碼——這樣 12 週後你會真正掌握這套技術棧的操作邏輯，而不只是有一份能跑的程式碼。
