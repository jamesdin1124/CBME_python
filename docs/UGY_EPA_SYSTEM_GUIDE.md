# UGY EPA 系統內評核 & 學生查成績功能

## 新增檔案

| 檔案 | 功能 |
|------|------|
| `modules/ugy_student_manager.py` | UGY 學生帳號管理（批次建帳、單筆新增、查詢） |
| `pages/ugy/ugy_epa_form.py` | UGY EPA 系統內評核表單（教師端，含批次評核） |
| `pages/ugy/ugy_student_portal.py` | UGY 學生個人成績查詢面板 |
| `sql/create_ugy_epa_records.sql` | Supabase 資料表建立 SQL |

## 修改檔案

| 檔案 | 修改內容 |
|------|----------|
| `new_dashboard.py` | 新增 import、UGY tab 加入「EPA評核表單」「批次評核」「學生帳號管理」、學生角色改用新面板 |

---

## 功能說明

### 1. 學生帳號管理（Admin/科別管理員）

- **批次匯入**：上傳包含「身分證字號」「學號」「姓名」的 Excel/CSV，一鍵批次建帳
  - 帳號 = 身分證字號
  - 密碼 = 學號（SHA-256 加密存儲）
- **單筆新增**：手動輸入單一學生資訊建帳
- **學生清單**：查看所有已建帳的 UGY 學生
- **密碼重設**：可重設學生密碼

### 2. EPA 評核表單（教師端）

#### 單筆評核
- 學員姓名：從已註冊名單選擇 或 手動輸入
- 欄位與 Google 表單完全一致：
  - 階層（C1/C2）
  - 實習科部（內科部/外科部/婦產部/小兒部）
  - EPA 評核項目（病歷紀錄/住院接診/當班處置）
  - 教師評核 EPA 等級（10 級，含即時分數顯示）
  - 學員自評 EPA 等級（選填）
  - 病歷號、病人難度、臨床情境
  - 回饋、給教學部的私下回饋
  - 教師姓名（自動帶入登入者）

#### 批次評核
- 同一臨床情境可一次評核多位學員
- 共用：科部、EPA 項目、地點、病人難度、病歷號、臨床情境
- 個別設定：姓名、階層、EPA 等級、回饋

### 3. 學生成績查詢（學生端）

學生以身分證字號 + 學號登入後可查看：
- 總覽統計（總評核次數、平均分數、最高分數）
- 各 EPA 項目平均分數柱狀圖
- 各科部平均分數
- EPA 分數時間趨勢圖（含趨勢線）
- EPA 能力雷達圖
- 教師回饋紀錄列表

---

## 部署步驟

### Step 1：建立 Supabase 資料表

在 Supabase SQL Editor 執行 `sql/create_ugy_epa_records.sql`

### Step 2：確認 `pediatric_users` 表結構

已有的 `pediatric_users` 表需包含：
- `username` (TEXT) — 身分證字號
- `full_name` (TEXT) — 姓名
- `user_type` (TEXT) — 'student'
- `password_hash` (TEXT) — SHA-256
- `student_id` (TEXT) — 學號
- `is_active` (BOOLEAN)
- `department` (TEXT)
- `extension` (TEXT) — 用於存放梯次
- `email` (TEXT)

### Step 3：匯入學生名冊

1. 準備 Excel/CSV，欄位：身分證字號、學號、姓名（選填：梯次、科部、Email）
2. 以 admin 登入 Dashboard → UGY → 學生帳號管理 → 批次匯入
3. 上傳檔案後確認建立

### Step 4：測試

- 教師登入 → UGY → EPA評核表單 → 填寫提交
- 學生登入（身分證+學號）→ 查看個人成績
