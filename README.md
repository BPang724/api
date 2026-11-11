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

### 3. 安裝並啟動

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