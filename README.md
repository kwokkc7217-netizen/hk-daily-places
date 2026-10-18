# 每日香港好去處（hk-daily-places）

每日精選香港好去處：行山、購物、睇戲。Phase 1 係公開網站（俾人睇嗰面）。

## Phase 1 範圍

- 公開頁全部 **server-side render（Thymeleaf）**：內容直接喺 HTML 入面，唔行 JS 都睇得晒——呢個係 AdSense 政策要求（唔可以重蹈「無內容版面」覆轍）
- 首頁（最新 12 篇）＋ `/place/{slug}` 詳情頁 ＋ `/category/{hiking|shopping|movie}` 分類頁 ＋ `/api/hello` 健康檢查
- 詳情頁有 Google Map embed（`maps.google.com/maps?q=…&output=embed`，唔使 API key）＋ YouTube 預告片（`youtube-nocookie.com` embed，有 `youtubeId` 先顯示）
- AdSense：頂部廣告位 `6515917749`、文章內廣告位 `2903975795`，`ads.txt` 喺 `/ads.txt`
- DB 用 Neon Postgres（Spring Data JPA，`ddl-auto=update`）
- 第一次起機 DB 係空嘅話，會自動插入 2 篇 sample（龍脊、K11 MUSEA）

## 本地跑（需要 Postgres）

```bash
# 1. 起個本地 Postgres（或用 Neon，見下）
# 2. 設環境變數（JDBC 格式）：
export DATABASE_URL='jdbc:postgresql://localhost:5432/hkdaily'
export DB_USER='postgres'
export DB_PASSWORD='你的密碼'

# 3. 跑
mvn spring-boot:run
# 開 http://localhost:8080
```

## Neon 免費 Postgres 設定

1. 去 [neon.tech](https://neon.tech) 開免費 project，開個 database（例如 `hkdaily`）
2. Neon 俾你嗰條 connection string 係呢個格式：
   `postgresql://USER:PASSWORD@HOST/DB?sslmode=require`
3. 要拆開做三個環境變數（JDBC 格式）：
   - `DATABASE_URL=jdbc:postgresql://HOST:5432/DB?sslmode=require`（加 `jdbc:` 頭，補 `:5432` port）
   - `DB_USER=USER`
   - `DB_PASSWORD=PASSWORD`
4. 唔好將呢三個值入 repo——放 Render 嘅 Environment 設定

## Deploy 上 Render

Render 冇 native Java runtime，所以一定要用 **Docker**（呢個 repo 已有 `Dockerfile`，multi-stage build）：

1. Render → New → Web Service → 連 GitHub repo，Runtime 揀 **Docker**
2. 環境變數加：`DATABASE_URL`、`DB_USER`、`DB_PASSWORD`（見上面 Neon 一節）
3. `PORT` 唔使自己設——Render 會自動派，`application.properties` 已寫 `server.port=${PORT:8080}`
4. JVM 慳 RAM：Dockerfile 已加 `-XX:MaxRAMPercentage=75.0`（免費版得 512MB）
5. Deploy 完開 `/api/hello`，見到 `{"message":"Hello from hk-daily-places","service":"java"}` 即係掂

注意：Render 免費版 15 分鐘冇 request 會瞓，第一次開要等半分鐘到一分鐘，唔係壞咗。

## AdSense 注意事項

- 所有公開內容都係 server-render，crawler 唔行 JS 都睇到全文（之前兩個練習站就係衰喺呢度）
- 每篇內容要有實質文字，唔好得個殼
- 新站要喺 AdSense 後台**獨立加站申請審批**，唔會自動繼承舊站；建議儲夠 8–10 篇先申請
- `ads.txt` 已內建（`src/main/resources/static/ads.txt`）

## Phase 1 冇包嘅嘢（Phase 2 / 3）

- ~~**React CMS 後台**（login、新增／改好去處、Cloudinary 上傳圖片）→ Phase 2~~ ✅ 已完成（見下）
- **每日 cronjob**：每日 AI 準備一篇草稿入 DB（DRAFT），人手喺 CMS 一鍵 publish → Phase 3
- TMDB 電影資料自動同步（而家電影內容要人手入 `youtubeId` 同資料）

## Phase 2：React CMS 後台

CMS 喺 `/admin`：登入後可以新增／編輯／刪除好去處、草稿↔已發佈一鍵切換、上傳圖片去 Cloudinary，仲可以喺「管理員」頁管理登入帳號。

### 管理員帳號（DB-backed）

管理員帳號存喺 `admin_users` 表，密碼用 BCrypt 加密（唔會明文儲存，API 亦唔會洩漏 hash）。

- **第一次 deploy**：`admin_users` 係空，開機會用 `ADMIN_USERNAME`／`ADMIN_PASSWORD` 呢兩個 env 一次性建立第一位管理員，之後可以喺 Render 刪走呢兩個 env。
- **之後**：喺 CMS `/admin` →「管理員」頁新增／刪除管理員、改自己密碼。唔可以刪除自己，亦唔可以刪除最後一位管理員（會鎖死自己）。

### 新增環境變數

| 變數 | 必填？ | 說明 |
|---|---|---|
| `ADMIN_USERNAME` | 首次 deploy 先要 | 一次性 bootstrap：`admin_users` 空嗰陣建立第一位管理員；建立咗之後可以刪走 |
| `ADMIN_PASSWORD` | 首次 deploy 先要 | 同上（唔好 commit 入 repo） |
| `CLOUDINARY_URL` | 選填 | 格式 `cloudinary://API_KEY:API_SECRET@CLOUD_NAME`，去 cloudinary.com console → Dashboard 攞。唔設嘅話上傳 API 會回 503，CMS 可以照用人手貼圖片 URL |

Render 部署時，將需要嘅 env 加喺 Environment（同 `DATABASE_URL`／`DB_USER`／`DB_PASSWORD` 一齊）。

### 登入流程

1. 開 `https://你的站/admin`，會見到登入頁
2. 入第一位管理員嘅帳號密碼（第一次 deploy 時用 `ADMIN_USERNAME`／`ADMIN_PASSWORD` 建立）
3. 登入行 form POST（JSON 回應，唔 redirect），session 用 cookie

### CSRF 注意

前後端同源（`/admin`＋`/api/admin`），CSRF 行 cookie 制：
Spring 派 `XSRF-TOKEN` cookie（HttpOnly=false），React 每次 POST/PUT/DELETE 自動帶 `X-XSRF-TOKEN` header。
唔使人手搞，但唔好閂咗 cookie，否則 login 會 403。

### 架構取捨（老實講）

- 公開頁繼續 **Thymeleaf server-render**（AdSense 政策：crawler 唔行 JS 都要睇到全文）
- React 只做 `/admin` CMS（login wall 入面，唔使廣告）——如果成個站都係 React SPA，就會重蹈之前「無內容版面」嘅覆轍
- `/api/admin/**` 全部要 ADMIN role；其他路徑一律 deny（白名單制）
