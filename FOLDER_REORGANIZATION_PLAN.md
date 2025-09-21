# 📁 程式檔案重新組織計劃

## 🎯 目標
將程式檔案按照分頁功能重新整理到不同的資料夾中，方便維護和管理。

## 📊 現有分頁分析

### 主要分頁
1. **我的評核資料** - 學生個人資料查看
2. **UGY** - 實習醫學生分析
3. **PGY** - 畢業後一般醫學訓練分析
4. **住院醫師** - 住院醫師分析
5. **老師評分分析** - 教師分析功能

## 🏗️ 新的資料夾結構

```
CBME_python/
├── main_dashboard.py                    # 主儀表板
├── main_login_dashboard.py             # 登入儀表板
├── login.py                            # 登入功能
├── requirements.txt                    # 依賴套件
├── README.md                          # 專案說明
│
├── pages/                             # 分頁功能資料夾
│   ├── __init__.py
│   ├── student/                       # 我的評核資料
│   │   ├── __init__.py
│   │   ├── student_dashboard.py       # 學生個人儀表板
│   │   └── student_analysis.py        # 學生個人分析
│   │
│   ├── ugy/                          # UGY 實習醫學生
│   │   ├── __init__.py
│   │   ├── ugy_overview.py           # 學生總覽
│   │   ├── ugy_individual.py         # 個別學生分析
│   │   ├── ugy_peers.py              # 同儕分析
│   │   └── ugy_data/                 # UGY 相關資料處理
│   │       ├── __init__.py
│   │       ├── ugy_epa_core.py       # UGY EPA 核心功能
│   │       ├── ugy_epa_google_sheets.py # Google Sheets 整合
│   │       └── ugy_epa_supabase.py   # Supabase 整合
│   │
│   ├── pgy/                          # PGY 畢業後一般醫學訓練
│   │   ├── __init__.py
│   │   ├── pgy_students.py           # PGY 學生分析
│   │   └── pgy_data/                 # PGY 相關資料
│   │       └── __init__.py
│   │
│   ├── residents/                     # 住院醫師
│   │   ├── __init__.py
│   │   ├── residents.py              # 住院醫師分析
│   │   ├── anesthesia_residents.py   # 麻醉科住院醫師
│   │   └── residents_data/           # 住院醫師相關資料
│   │       └── __init__.py
│   │
│   └── teachers/                      # 老師評分分析
│       ├── __init__.py
│       ├── teacher_analysis.py       # 教師分析
│       └── teacher_data/             # 教師相關資料
│           └── __init__.py
│
├── modules/                          # 共用模組
│   ├── __init__.py
│   ├── auth.py                      # 權限認證
│   ├── data_processing.py           # 資料處理
│   ├── google_connection.py         # Google 連接
│   ├── supabase_connection.py       # Supabase 連接
│   ├── visualization/               # 視覺化模組
│   │   ├── __init__.py
│   │   ├── radar_charts.py          # 雷達圖
│   │   ├── trend_charts.py          # 趨勢圖
│   │   ├── bar_charts.py            # 長條圖
│   │   └── unified_radar.py         # 統一雷達圖
│   └── utils/                       # 工具模組
│       ├── __init__.py
│       ├── data_utils.py            # 資料工具
│       ├── chrome_controller.py     # Chrome 控制
│       └── google_sheets_fetcher.py # Google Sheets 獲取
│
├── forms/                           # 表單功能
│   ├── __init__.py
│   ├── test_form.py
│   └── pediatric_form.html
│
├── tests/                           # 測試檔案
│   ├── __init__.py
│   └── [所有測試檔案]
│
├── docs/                           # 文檔
│   ├── README.md
│   ├── API_DOCUMENTATION.md
│   └── [所有 .md 文檔]
│
├── data/                           # 資料檔案
│   ├── excel/                      # Excel 檔案
│   ├── csv/                        # CSV 檔案
│   └── database/                   # 資料庫檔案
│
└── config/                         # 配置檔案
    ├── __init__.py
    ├── epa_constants.py            # EPA 常數
    └── settings.py                 # 系統設定
```

## 📋 檔案移動對應表

### 現有檔案 → 新位置

#### 分頁功能檔案
- `analysis_ugy_overview.py` → `pages/ugy/ugy_overview.py`
- `analysis_ugy_individual.py` → `pages/ugy/ugy_individual.py`
- `analysis_ugy_peers.py` → `pages/ugy/ugy_peers.py`
- `analysis_pgy_students.py` → `pages/pgy/pgy_students.py`
- `analysis_residents.py` → `pages/residents/residents.py`
- `analysis_anesthesia_residents.py` → `pages/residents/anesthesia_residents.py`
- `analysis_teachers.py` → `pages/teachers/teacher_analysis.py`
- `analysis_pediatric.py` → `pages/pediatric/pediatric_analysis.py`

#### UGY EPA 相關檔案
- `ugy_epa/ugy_epa_core.py` → `pages/ugy/ugy_data/ugy_epa_core.py`
- `ugy_epa/ugy_epa_google_sheets.py` → `pages/ugy/ugy_data/ugy_epa_google_sheets.py`
- `ugy_epa/ugy_epa_supabase.py` → `pages/ugy/ugy_data/ugy_epa_supabase.py`

#### 視覺化模組
- `modules/visualization.py` → `modules/visualization/visualization.py`
- `modules/radar_trend_visualization.py` → `modules/visualization/radar_trend.py`
- `modules/unified_radar_visualization.py` → `modules/visualization/unified_radar.py`
- `modules/individual_student_radar.py` → `modules/visualization/individual_radar.py`
- `modules/dept_chart_visualization.py` → `modules/visualization/dept_charts.py`

#### 工具模組
- `utils.py` → `modules/utils/data_utils.py`
- `utils_chrome_controller.py` → `modules/utils/chrome_controller.py`
- `utils_google_sheets_fetcher.py` → `modules/utils/google_sheets_fetcher.py`
- `utils_data_sync.py` → `modules/utils/data_sync.py`
- `utils_pediatric_runner.py` → `modules/utils/pediatric_runner.py`

#### 文檔檔案
- `*.md` → `docs/`

#### 資料檔案
- `EXCEL/` → `data/excel/`
- `*.db` → `data/database/`
- `*.csv` → `data/csv/`

## 🔄 重組步驟

1. **創建新資料夾結構**
2. **移動檔案到對應位置**
3. **更新所有 import 路徑**
4. **更新主儀表板的 import**
5. **測試所有功能**
6. **更新文檔**

## ✅ 重組後的優勢

1. **清晰的結構**: 每個分頁功能都有獨立的資料夾
2. **易於維護**: 相關功能集中在同一資料夾
3. **模組化**: 共用功能放在 modules 資料夾
4. **文檔集中**: 所有文檔放在 docs 資料夾
5. **資料分離**: 資料檔案集中在 data 資料夾
6. **測試獨立**: 測試檔案集中在 tests 資料夾

## 🚀 實施計劃

1. 創建新的資料夾結構
2. 逐步移動檔案
3. 更新 import 路徑
4. 測試功能完整性
5. 清理舊檔案
6. 更新文檔
