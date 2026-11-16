# 啟動虛擬環境
venv\Scripts\activate

啟動：
```bash
uvicorn app.main:app --reload
```

## W6 Google 登入與 JWT

本週的登入流程是：Google OIDC 驗證使用者身分，API 將 Google `sub`
對應到本地 `member.id`，再簽發本系統的 JWT。JWT 以 HttpOnly cookie
保存；Notes API 會在每次請求驗證 token，並確認會員仍存在且啟用中。

### 1. 設定環境變數

將 `.env.example` 的設定項目加到 `.env`；若 `.env` 已有
`DATABASE_URL`，請保留原值，不要用範例覆蓋。填入 Google OAuth Web client
的 ID、secret 和 callback URI。Google Cloud Console 的 Authorized redirect URI 必須與
`GOOGLE_REDIRECT_URI` 完全相同。本機 HTTP 開發才使用
`AUTH_COOKIE_SECURE=false`；正式 HTTPS 環境必須改為 `true`。

`JWT_SECRET_KEY` 與 `SESSION_SECRET_KEY` 請使用不同的隨機密鑰，各至少
32 個字元。可以用 PowerShell 分別產生：

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

不要提交 `.env` 或將真實密鑰貼到程式碼、文件或前端。

若要限制實驗區僅供單一 Google 帳戶使用，請在 `.env` 設定
`EXPERIMENTS_OWNER_EMAIL` 為該帳戶的信箱。未設定時，所有帳戶（包含已登入
帳戶）都只能使用影片觀看區；其他已登入帳戶也只會看到影片觀看區。

### 2. 建立會員表

在應用程式使用的 PostgreSQL 資料庫中執行 `psql/create_member.sql`。
此 SQL 使用 `CREATE TABLE IF NOT EXISTS`，不會刪除現有 Notes 資料。
資料庫帳號需有建立資料表及使用 identity sequence 的權限。
若由管理員建立、API 使用另一個資料庫角色，請將下方 `dev_user` 換成
`DATABASE_URL` 中實際使用的角色，再由 owner/admin 執行：

```sql
GRANT SELECT, INSERT, UPDATE ON public.member TO dev_user;
GRANT USAGE, SELECT ON SEQUENCE public.member_id_seq TO dev_user;
```

### 3. 建立 Dataset 資料表

在與 `DATABASE_URL` 相同的 PostgreSQL 資料庫中執行
`psql/create_dataset_tables.sql`。此腳本會建立 Dataset、Video、多對多關聯
及 Ground Truth 時間點資料表；使用 `CREATE TABLE IF NOT EXISTS` 和
`CREATE INDEX IF NOT EXISTS`，不會刪除或修改既有資料。

```powershell
psql -d <database_name> -v ON_ERROR_STOP=1 -f psql/create_dataset_tables.sql
```

請將 `<database_name>` 換成 API `DATABASE_URL` 指向的資料庫名稱。執行帳號
需要建立資料表、索引及使用 identity sequence 的權限；若 API 使用不同角色，
請由資料庫管理者授予該角色對新資料表及其 identity sequences 的所需權限。

`ground_truth_timestamps.video_id` 直接參照 `videos.id`，因此同一支影片在
不同 Dataset 中共用同一份標註。刪除 Dataset 會刪除其
`dataset_videos` 關聯，但不會刪除影片或 Ground Truth；刪除 Video 則會
清除相關 Dataset 關聯及該影片的時間點。

### Dataset 查詢 API

已登入且符合 `EXPERIMENTS_OWNER_EMAIL` 的帳戶可以使用唯讀端點：

- `GET /api/datasets`：回傳 Dataset 清單及各自影片數。
- `GET /api/datasets/{dataset_id}`：回傳 Dataset、影片及各影片共用的
  Ground Truth 秒數。

例如 Dataset 詳細資料的影片會包含：

```json
{
  "id": 81,
  "youtube_id": "abcdefghijk",
  "url": "https://www.youtube.com/watch?v=abcdefghijk",
  "title": null,
  "duration_seconds": null,
  "ground_truth_timestamps": [205, 431]
}
```

查詢結果不會快取；不存在的 Dataset 回傳 `404`，未登入回傳 `401`，
沒有實驗資料權限回傳 `403`。

### Dataset 寫入 API

以下端點同樣要求登入且帳戶符合 `EXPERIMENTS_OWNER_EMAIL`：

- `POST /api/datasets`，body `{"name":"course-slides"}`：建立 Dataset。
- `PATCH /api/datasets/{dataset_id}`，body `{"name":"updated-name"}`：修改名稱。
- `DELETE /api/datasets/{dataset_id}`：刪除 Dataset 及其關聯，不刪除共用影片。
- `POST /api/datasets/{dataset_id}/videos`，body
  `{"url":"https://www.youtube.com/watch?v=abcdefghijk"}`：將影片加入 Dataset；
  後端會透過 `yt-dlp` 讀取標題與影片長度（不下載影片），相同影片會重用
  同一筆 Video。
- `DELETE /api/datasets/{dataset_id}/videos/{video_id}`：只移除這筆 Dataset 關聯。
- `GET /api/videos/{video_id}/timestamps`：讀取影片共用的 Ground Truth 秒數。
- `PUT /api/videos/{video_id}/timestamps`，body `{"timestamps":[205,431]}`：
  整批取代影片標註；傳空陣列可清空。時間點必須是非負、不重複整數，
  且不能超過已知影片長度。

名稱重複時回傳 `409`；同一影片重複加入同一 Dataset 時回傳既有影片資料
及 `200`，讓重試或重複送出不會被誤報為失敗。無效 URL、
時間點或超過影片長度的標註回傳 `422`；找不到指定 Dataset 或影片時回傳
`404`。若 `yt-dlp` 無法取得影片資訊，加入影片會回傳 `422` 並說明原因；
移除影片關聯不會刪除影片或其 Ground Truth。

### 4. 安裝並啟動

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

登入入口為 `/api/auth/google/login`，Google callback 為
`/api/auth/google/callback`。登入後 `/api/auth/me` 回傳目前會員；
`POST /api/auth/logout` 清除登入 cookie。沒有有效 token 時，`/api/notes`
端點回傳 `401`。
`/api/auth/me` 另會回傳 `can_access_experiments`，供前端控制實驗區顯示。

目前 Notes 尚未歸屬特定會員；此階段只限制必須登入，登入會員之間仍共用
同一組 Notes。若要讓每人只能存取自己的資料，需再為 Notes 加入 `member_id`
欄位並將所有查詢限制在目前會員。