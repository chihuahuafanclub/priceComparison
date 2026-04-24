# PriceComparison 比價網站

一個使用 Django + React 的多平台商品比價專案。  
目前可從多個購物平台抓取搜尋結果，統一顯示價格、原價、商品圖與連結。

## 功能特色

- 多來源比價：PChome、露天、momo、Yahoo（穩定）
- 搜尋排序：相關度、價格低到高、價格高到低
- 來源多選：可切換比價來源
- 統一資料格式：同一張卡片顯示來源、價格、原價、折扣、圖片、連結
- API 化後端：前端透過 `/api/search/` 呼叫資料

## 技術棧

- Backend: Django, requests
- Frontend: React (Create React App)
- DB: SQLite（Django 預設）

## 專案結構

```text
priceComparison/
├─ backend/               # Django app，包含比價邏輯與 API
├─ frontend/              # React 前端
├─ priceComparison/       # Django settings / urls
├─ manage.py
├─ requirements.txt
└─ db.sqlite3
```

## 快速啟動（Windows）

### 1) 安裝後端套件

```powershell
cd "C:\Users\howard.tseng\Desktop\Vibe Coding\priceComparison"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) 安裝前端套件

```powershell
cd "C:\Users\howard.tseng\Desktop\Vibe Coding\priceComparison\frontend"
npm install
```

### 3) 開發模式（前後端分開跑）

Terminal A（Django API）:

```powershell
cd "C:\Users\howard.tseng\Desktop\Vibe Coding\priceComparison"
.\.venv\Scripts\python.exe manage.py runserver 8000
```

Terminal B（React）:

```powershell
cd "C:\Users\howard.tseng\Desktop\Vibe Coding\priceComparison\frontend"
npm start
```

- 前端網址: `http://localhost:3000`
- 後端 API: `http://localhost:8000/api/search/`

## 部署模式（Django 直接服務前端）

```powershell
cd "C:\Users\howard.tseng\Desktop\Vibe Coding\priceComparison\frontend"
npm run build

cd "C:\Users\howard.tseng\Desktop\Vibe Coding\priceComparison"
.\.venv\Scripts\python.exe manage.py runserver 8000
```

打開 `http://localhost:8000`。

## API 說明

### `GET /api/search/`

Query 參數:

- `keyword` (必填): 搜尋關鍵字
- `providers` (選填): 來源清單，以逗號分隔  
  可用值: `pchome,ruten,momo,yahoo,shopee,taobao`
- `sort` (選填): `relevance` / `price_asc` / `price_desc`
- `page` (選填): 頁碼，預設 `1`
- `limit` (選填): 每頁筆數，預設 `24`，上限 `120`

範例:

```bash
curl "http://localhost:8000/api/search/?keyword=iphone&providers=pchome,ruten,momo,yahoo&sort=price_asc&limit=24"
```

回傳重點欄位:

- `results[]`
  - `id`, `source`, `title`
  - `price`, `original_price`, `discount_amount`
  - `image_url`, `product_url`
- `warnings[]`: 平台限制或解析失敗訊息
- `provider_counts`: 各來源抓到幾筆

## 來源支援現況

- 穩定可用：`pchome`, `ruten`, `momo`, `yahoo`
- 受平台限制：`shopee`, `taobao`
  - Shopee 常見代碼：`90309999`
  - Taobao 常見情況：僅回傳骨架頁/驗證頁

> 前端已將受限來源標示為「受限」，避免日常使用被干擾。

## 蝦皮 / 淘寶強化模式（瀏覽器備援）

專案已內建 Playwright 備援流程。當 API 被擋時，後端可改用瀏覽器流量擷取資料。

### 步驟 1：先建立登入 Session（一次即可）

```powershell
cd "C:\Users\howard.tseng\Desktop\Vibe Coding\priceComparison"
.\.venv\Scripts\python.exe manage.py open_browser_session --provider all --user-data-dir ".browser-profile"
```

會開瀏覽器，請完成蝦皮/淘寶登入與驗證，回終端機按 Enter 儲存。

### 步驟 2：啟用後端備援

```powershell
$env:ENABLE_BROWSER_FALLBACK="1"
$env:BROWSER_USER_DATA_DIR=".browser-profile"
$env:BROWSER_CHANNEL="msedge"
.\.venv\Scripts\python.exe manage.py runserver 8000
```

可選參數：

- `BROWSER_HEADLESS=0`：除錯時顯示瀏覽器視窗
- `BROWSER_TIMEOUT_MS=60000`：延長頁面等待時間

## 測試

後端:

```powershell
cd "C:\Users\howard.tseng\Desktop\Vibe Coding\priceComparison"
.\.venv\Scripts\python.exe manage.py test
```

前端（可選）:

```powershell
cd "C:\Users\howard.tseng\Desktop\Vibe Coding\priceComparison\frontend"
npm test
```

## 常見問題

### 1) `No module named 'django'`

代表你還沒裝後端套件，或沒啟用虛擬環境。請先執行「安裝後端套件」段落。

### 2) `npm ENOENT ... package.json`（在專案根目錄執行 npm）

請進 `frontend` 目錄再跑 `npm install` / `npm start`。

### 3) 圖片沒顯示

- 部分平台圖片連結會失效或擋外站引用
- 前端已內建圖片失敗 fallback（顯示「暫無圖片」）

### 4) Shopee / Taobao 一直出現限制訊息

這是目標站反爬機制造成，非程式崩潰。建議先以穩定來源比價。
