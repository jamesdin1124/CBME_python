# CBME 學生評核系統 - 網站架構圖 (Sitemap)

## 一、系統總覽

本系統為**醫學教育 EPA (Entrustable Professional Activities) 評核平台**，採用雙框架架構：

| 框架 | 用途 | 入口檔案 | 預設埠號 |
|------|------|----------|----------|
| **Streamlit** | 主應用（儀表板、資料分析、使用者管理） | `new_dashboard.py` | 8501 |
| **Flask** | 表單子系統（EPA 評核表單提交） | `epa_form/app.py` | 5001 |

**後端服務：** Supabase (PostgreSQL) + Google Sheets
**部署環境：** Fly.io + GitHub Actions CI/CD

---

## 二、使用者角色與權限矩陣

系統定義 6 種角色，權限由 `modules/auth.py` 中的 `PERMISSIONS` 控制：

| 角色 | 中文名稱 | UGY 資料 | PGY 資料 | 住院醫師資料 | 上傳檔案 | 使用者管理 | 分析報表 |
|------|----------|----------|----------|-------------|----------|-----------|----------|
| `admin` | 系統管理員 | 全部 | 全部 | 全部 | O | O | O |
| `department_admin` | 科別管理員 | 全部 | 本科 | 本科 | O | 本科 | O |
| `teacher` | 主治醫師 | 全部 | 本科 | 本科 | O | X | O |
| `resident` | 住院醫師 | 全部 | X | 僅自己 | X | X | X |
| `pgy` | PGY | X | X | X | X | X | X（僅自己）|
| `student` | UGY | 僅自己 | X | X | X | X | X |

---

## 三、Streamlit 主應用頁面結構

### 入口：`new_dashboard.py`

```
學生評核系統 (new_dashboard.py)
│
├── [未登入] 登入 / 申請帳號
│   ├── 登入頁面 ──── modules/auth.py: show_login_page()
│   └── 申請帳號 ──── new_dashboard.py 內建表單 → Supabase user_applications
│       └── 查詢申請狀態
│
├── [已登入] 側邊欄 (Sidebar)
│   ├── 登出按鈕
│   ├── 科別選擇（依權限限制可選範圍）
│   │   └── 可選科別：小兒部、內科部、外科部、婦產部、神經科、精神部、
│   │       家醫部、急診醫學部、麻醉部、放射部、病理部、復健部、
│   │       皮膚部、眼科、耳鼻喉部、泌尿部、骨部、其他科別
│   ├── 檔案上傳區（需 can_upload_files 權限）
│   │   └── 上傳 Excel → merge_excel_files() 合併 → 下載 CSV/Excel
│   ├── 已上傳科別清單
│   ├── 使用者管理（需 can_manage_users 權限）
│   │   └── modules/auth.py: show_user_management()
│   ├── [管理員] 帳號申請審核入口
│   │   └── pages/admin/user_application_review.py
│   └── 測試系統連結
│       ├── 填寫表單測試
│       └── 查看測試結果
│
└── [已登入] 主內容區 - 動態分頁 (依角色顯示不同 Tab)
    │
    ├── 【UGY 分頁】（admin / department_admin / teacher / resident 可見）
    │   ├── 學生總覽 ─── pages/ugy/ugy_overview.py: show_ugy_student_overview()
    │   ├── 個別學生分析 ── pages/ugy/ugy_individual.py: show_ugy_student_analysis()
    │   └── 老師分析 ──── pages/ugy/ugy_teacher_analysis.py: show_ugy_teacher_analysis()
    │
    ├── 【PGY 分頁】（admin / department_admin / teacher 可見）
    │   └── PGY 分析 ──── pages/pgy/pgy_students.py: show_analysis_section()
    │
    ├── 【住院醫師分頁】（admin / department_admin / teacher / resident 可見）
    │   ├── [小兒部] → pages/pediatric/pediatric_analysis.py: show_pediatric_evaluation_section()
    │   ├── [家醫部] → pages/FAM/fam_residents.py: show_fam_resident_evaluation_section()
    │   ├── [麻醉部] → pages/ANE/anesthesia_residents.py: show_ANE_R_EPA_peer_analysis_section()
    │   └── [其他科別] → pages/residents/residents.py: show_resident_analysis_section()
    │
    └── 【我的評核資料分頁】（student 角色專用）
        ├── 基本資訊（姓名、學號、科別）
        ├── EPA 評分列表
        ├── 評語顯示
        ├── 評分趨勢圖
        └── 能力雷達圖
```

---

## 四、各科別專屬頁面詳細架構

### 4.1 UGY（實習醫學生）模組
```
pages/ugy/
├── ugy_overview.py          # 學生總覽：全體 EPA 統計、分布圖
├── ugy_individual.py        # 個別學生分析：EPA 趨勢、雷達圖
├── ugy_peers.py             # 同儕比較分析
├── ugy_teacher_analysis.py  # 教師評核分析
└── ugy_data/                # 資料處理子模組
    ├── ugy_epa_core.py              # EPA 核心資料處理
    ├── ugy_epa_google_sheets.py     # Google Sheets 資料來源
    ├── migration_tool.py            # 資料遷移工具
    └── supabasetest.py              # Supabase 連線測試
```

### 4.2 PGY（畢業後一般醫學訓練）模組
```
pages/pgy/
└── pgy_students.py          # PGY 學員分析：EPA 評分、趨勢
```

### 4.3 住院醫師模組
```
pages/residents/
└── residents.py             # 一般住院醫師分析
```

### 4.4 小兒部專屬模組
```
pages/pediatric/
├── pediatric_analysis.py            # 主分析頁面（最大模組，115KB）
│   └── show_pediatric_evaluation_section()
├── pediatric_forms.py               # 小兒部評核表單
├── pediatric_resident_forms.py      # 住院醫師評核表單
└── pediatric_user_management.py     # 小兒部使用者管理
```

### 4.5 家醫部專屬模組
```
pages/FAM/
├── fam_residents.py                 # 家醫部住院醫師評核系統
│   └── show_fam_resident_evaluation_section()
├── fam_data_processor.py            # 家醫部資料處理器
├── fam_visualization.py             # 家醫部視覺化
├── emway_data_integration.py        # eMWay 系統資料整合
├── emway_data_converter.py          # eMWay 資料轉換器
└── test_*.py (約 40+ 個測試檔案)    # 各功能單元測試
```

### 4.6 麻醉部專屬模組
```
pages/ANE/
└── anesthesia_residents.py  # 麻醉住院醫師 EPA 同儕分析
    └── show_ANE_R_EPA_peer_analysis_section()
```

### 4.7 教師分析模組
```
pages/teachers/
├── teacher_analysis.py              # 基本教師分析
│   ├── show_teacher_analysis_section()
│   └── fetch_google_form_data()
└── teacher_scoring_analysis.py      # 教師評分模式分析
    ├── show_teacher_scoring_analysis()
    └── show_teacher_comparison()
```

### 4.8 管理功能模組
```
pages/admin/
├── account_management.py            # 帳號管理
└── user_application_review.py       # 帳號申請審核
    └── show_user_application_review()
```

---

## 五、Flask 表單子系統路由

### 入口：`epa_form/app.py`（Port 5001）

| HTTP 方法 | 路由 | 功能說明 | 對應模板/回傳 |
|-----------|------|---------|--------------|
| GET | `/` | 首頁 | `templates/index.html` |
| GET | `/form` | EPA 評核表單頁面 | `templates/form.html` |
| POST | `/submit` | 提交評核資料至 Google Sheets | JSON 回應 |
| POST | `/add_epa_form` | 提交 EPA 評核表單 | JSON 回應 |
| POST | `/enhance_text` | OpenAI 文字修飾 | JSON 回應 |
| GET/POST | `/register` | 使用者註冊 | `templates/register.html` / JSON |

### Flask 模板結構
```
epa_form/
├── app.py                   # Flask 應用主程式
├── credentials.json         # Google API 憑證
├── templates/
│   ├── index.html           # 首頁（Bootstrap 5.3）
│   ├── form.html            # EPA 評核表單（含語音輸入）
│   └── register.html        # 使用者註冊頁面
└── static/
    ├── css/style.css        # 自訂樣式
    └── js/main.js           # 表單驗證、語音錄音、API 呼叫
```

---

## 六、核心模組架構

```
modules/
├── auth.py                  # 認證與權限管理
│   ├── USER_ROLES           # 角色定義（6 種）
│   ├── PERMISSIONS           # 權限矩陣
│   ├── authenticate_user()   # Supabase 身份驗證
│   ├── create_user()         # 建立使用者
│   ├── check_permission()    # 權限檢查
│   ├── filter_data_by_permission()  # 資料過濾
│   ├── show_login_page()     # 登入介面
│   ├── show_user_management() # 使用者管理介面
│   └── show_registration_page() # 註冊介面
│
├── supabase_connection.py   # Supabase 資料庫連線 ORM
│   └── class SupabaseConnection
│       ├── 使用者操作 (CRUD)
│       ├── 評核資料操作
│       └── 申請單操作
│
├── data_processing.py       # EPA 資料處理
│   └── EPA 等級映射、日期處理、梯次分配
│
├── data_analysis.py         # 統計分析
│
├── google_connection.py     # Google Sheets 整合
│
├── visualization/           # 視覺化模組
│   ├── visualization.py     # 核心 Plotly 圖表
│   ├── radar_trend.py       # 雷達圖趨勢分析
│   ├── individual_radar.py  # 個人雷達圖
│   ├── unified_radar.py     # 統一雷達圖
│   └── dept_charts.py       # 科別統計圖表
│
└── utils/                   # 工具模組
    ├── data_sync.py         # 資料同步
    ├── data_utils.py        # 資料處理工具
    ├── google_sheets_fetcher.py  # Google Sheets 進階讀取
    ├── chrome_controller.py # Chrome 瀏覽器控制
    ├── pediatric_migration.py   # 小兒部資料遷移
    └── pediatric_runner.py      # 小兒部任務執行器
```

---

## 七、設定與常數

### `config/epa_constants.py`
- **EPA_LEVEL_MAPPING**：將中文描述轉換為數值等級（1-5 分）
  - Level 1: 不允許學員觀察
  - Level 2: 教師在旁逐步共同操作
  - Level 3: 教師可立即到場協助
  - Level 4: 教師 on call 提供監督
  - Level 5: 學員可對資淺學員進行監督與教學

### `.streamlit/config.toml` & `secrets.toml`
- Streamlit 佈局設定、GCP 服務帳號憑證

### `.env`
- `SUPABASE_URL`、`SUPABASE_KEY`、`OPENAI_API_KEY`

---

## 八、資料庫結構

### 8.1 Supabase (主要)

| 資料表 | 用途 |
|--------|------|
| `pediatric_users` | 使用者帳號（帳號、密碼 hash、角色、科別等）|
| `pediatric_evaluations` | 小兒部評核紀錄 |
| `user_applications` | 帳號申請單（待審核/已核准/已拒絕）|

### 8.2 SQLite (本地備援)

| 資料表 | 用途 | 檔案 |
|--------|------|------|
| `users` | 使用者帳號（本地） | `clinical_evaluation.db` |
| `evaluations` | 評核紀錄（本地） | `clinical_evaluation.db` |
| `test_form_submissions` | 測試表單資料 | `test_form.db` |

### 8.3 Google Sheets (外部資料源)
- EPA 評核原始資料收集
- 帳號申請審核工作表

---

## 九、資料流向圖

```
[臨床教師]                    [學生/住院醫師]
    │                              │
    ▼                              ▼
┌─────────────────┐    ┌─────────────────┐
│ Flask 表單系統    │    │ Streamlit 主應用  │
│ (port 5001)     │    │ (port 8501)     │
│                 │    │                 │
│ - EPA 評核表單   │    │ - 登入/註冊      │
│ - 語音回饋輸入   │    │ - 資料上傳       │
│ - AI 文字修飾   │    │ - 分析儀表板     │
└────────┬────────┘    └───────┬─────────┘
         │                      │
         ▼                      ▼
┌─────────────────────────────────────────┐
│            Google Sheets                 │
│   (EPA 評核資料、帳號申請表)              │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         Supabase (PostgreSQL)            │
│  - pediatric_users (使用者管理)           │
│  - pediatric_evaluations (評核紀錄)       │
│  - user_applications (帳號申請)           │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         Streamlit 分析儀表板              │
│  - Plotly 互動圖表                       │
│  - 雷達圖 / 趨勢圖 / 箱型圖              │
│  - 科別統計 / 同儕比較                    │
└─────────────────────────────────────────┘
```

---

## 十、部署架構

```
┌─────────────┐     push to main    ┌──────────────────┐
│  本地開發     │ ──────────────────► │ GitHub Actions    │
│  (localhost)  │                    │ (fly-deploy.yml)  │
└─────────────┘                     └────────┬─────────┘
                                             │ deploy
                                             ▼
                                    ┌──────────────────┐
                                    │    Fly.io         │
                                    │ (新加坡機房 sin)   │
                                    │ 1 vCPU / 1GB RAM  │
                                    │ Port: 8501        │
                                    │ Auto stop/start   │
                                    └──────────────────┘
```

**部署設定：**
- 設定檔：`fly.toml`（App: `cbme-python-restless-meadow-6491`）
- CI/CD：`.github/workflows/fly-deploy.yml`（push to `main` 自動部署）

---

## 十一、目錄結構總覽

```
CBME_python/
├── new_dashboard.py              # Streamlit 主入口
├── database.py                   # SQLite 資料庫初始化
├── pediatric_form.html           # 獨立小兒部表單
│
├── config/
│   └── epa_constants.py          # EPA 等級常數定義
│
├── modules/                      # 核心後端模組
│   ├── auth.py                   # 認證與權限
│   ├── supabase_connection.py    # Supabase 連線
│   ├── data_processing.py        # 資料處理
│   ├── data_analysis.py          # 統計分析
│   ├── google_connection.py      # Google API
│   ├── visualization/            # 圖表生成
│   └── utils/                    # 工具函式
│
├── pages/                        # Streamlit 頁面模組
│   ├── ugy/                      # UGY 實習醫學生
│   ├── pgy/                      # PGY 訓練
│   ├── residents/                # 住院醫師（通用）
│   ├── pediatric/                # 小兒部專屬
│   ├── FAM/                      # 家醫部專屬
│   ├── ANE/                      # 麻醉部專屬
│   ├── teachers/                 # 教師分析
│   ├── admin/                    # 管理功能
│   └── student/                  # 學生入口
│
├── epa_form/                     # Flask 表單子系統
│   ├── app.py                    # Flask 入口
│   ├── templates/                # HTML 模板
│   └── static/                   # CSS / JS
│
├── data/                         # 資料儲存
│   ├── database/                 # SQLite 資料庫
│   ├── excel/                    # EPA Excel 範例
│   └── csv/                      # CSV 資料
│
├── sql/                          # SQL Schema
│   ├── pediatric_schema.sql
│   ├── user_applications_schema.sql
│   └── migrations/
│
├── tests/                        # 測試套件
│
├── .streamlit/                   # Streamlit 設定
├── .github/workflows/            # CI/CD
├── fly.toml                      # Fly.io 部署設定
├── requirements.txt              # Python 依賴
└── .env                          # 環境變數
```
