# 兒科住院醫師研究進度與學習反思系統 — 功能實作總結

## 📌 專案概述

為兒科住院醫師 CCC 評估系統新增兩大核心功能：
1. **研究進度追蹤系統**：記錄與管理住院醫師的研究計畫（文獻回顧、個案報告、原著論文等）
2. **學習反思記錄系統**：基於 Gibbs 反思循環，記錄臨床學習經驗與專業成長

---

## 🎯 實作目標

### 主要目標
- ✅ 建立完整的研究進度管理機制
- ✅ 提供結構化的學習反思記錄工具
- ✅ 整合到現有 CCC 評估系統
- ✅ 在 CCC 總覽與個人分析頁面顯示資料
- ✅ 提供住院醫師專屬的自填表單介面

### 次要目標
- ✅ 支援隱私權限控制（私人反思）
- ✅ 提供統計分析與視覺化
- ✅ 確保資料完整性（軟刪除機制）
- ✅ 建立完整的使用與部署文件

---

## 📂 檔案結構

```
CBME_python/
├─ sql/
│  └─ pediatric_research_schema.sql          # 資料庫 Schema（研究進度 + 學習反思）
├─ modules/
│  └─ supabase_connection.py                 # 新增 CRUD 方法
└─ pages/pediatric/
   ├─ pediatric_analysis.py                  # 主頁面（已修改，整合顯示功能）
   ├─ pediatric_forms.py                     # 教師評核表單（既有）
   ├─ pediatric_resident_forms.py            # 住院醫師自填表單（新增）
   ├─ pediatric_user_management.py           # 帳號管理（既有）
   ├─ RESEARCH_AND_REFLECTION_GUIDE.md       # 使用指南
   ├─ DEPLOYMENT_CHECKLIST.md                # 部署檢查清單
   └─ FEATURE_SUMMARY.md                     # 本文件
```

---

## 🗄️ 資料庫設計

### 資料表 1：`pediatric_research_progress`

**用途**：記錄住院醫師研究計畫進度

**主要欄位**：
- `resident_name`, `resident_level`：住院醫師資訊
- `research_title`, `research_type`：研究名稱與類型
- `supervisor_name`：指導老師
- `current_status`：構思中 / 撰寫中 / 投稿中 / 接受
- `submission_date`, `acceptance_date`：投稿與接受日期
- `progress_notes`, `challenges`, `next_steps`：進度記錄

**特色**：
- 支援完整研究生命週期追蹤
- 軟刪除機制（`is_deleted`）
- 時間戳記（`created_at`, `updated_at`）

### 資料表 2：`pediatric_learning_reflections`

**用途**：記錄住院醫師學習反思（Gibbs 反思循環）

**主要欄位**：
- `resident_name`, `resident_level`：住院醫師資訊
- `reflection_title`, `reflection_type`：反思標題與類型
- **Gibbs 五階段**：
  - `situation_description`：情境描述
  - `thoughts_and_feelings`：想法與感受
  - `evaluation`：評估與分析
  - `action_plan`：行動計畫
  - `learning_outcomes`：學習成果
- `related_epa`, `related_skill`：關聯 EPA / 技能
- `tags[]`：標籤陣列
- `is_private`：是否為私人記錄

**特色**：
- 結構化反思架構（Gibbs 循環）
- 支援標籤分類
- 隱私權限控制
- 可連結到特定 EPA / 技能項目

---

## 🔧 後端實作

### `supabase_connection.py` 新增方法

#### 研究進度管理
```python
fetch_research_progress(filters)       # 查詢研究進度
insert_research_progress(data)         # 新增記錄
update_research_progress(id, data)     # 更新記錄
delete_research_progress(id)           # 軟刪除
```

#### 學習反思管理
```python
fetch_learning_reflections(filters)    # 查詢反思記錄
insert_learning_reflection(data)       # 新增記錄
update_learning_reflection(id, data)   # 更新記錄
delete_learning_reflection(id)         # 軟刪除
```

**設計特色**：
- 統一的過濾器介面（filters dict）
- 異常處理機制
- 返回標準格式（dict / list / None）

---

## 🎨 前端介面

### 1. 住院醫師自填表單 (`pediatric_resident_forms.py`)

**位置**：「我的表單」分頁（住院醫師專屬）

**子分頁**：
1. **📚 研究進度**
   - 研究名稱、類型、指導老師、進度狀態
   - 詳細資訊：研究主題、目標期刊、投稿日期
   - 進度記錄：進度說明、遭遇困難、下一步計畫
   - 顯示已登記的研究清單（可展開）

2. **💭 學習反思**
   - 反思日期、類型、標題
   - Gibbs 五階段內容（情境、想法、評估、行動、成果）
   - 關聯資訊：EPA、技能、督導教師、標籤
   - 隱私設定：私人記錄開關
   - 顯示最近 5 筆反思記錄（可展開）

**UI 特色**：
- 清晰的表單結構
- 即時驗證（必填欄位）
- 提交後動畫效果（st.balloons()）
- 分離顯示已有記錄（expander）

### 2. CCC 總覽頁面整合 (`pediatric_analysis.py`)

**修改內容**：

#### 摘要卡片（Section B）
- 在每張住院醫師卡片底部顯示最新研究進度
- 格式：`📚 研究進度：X 項` + `[emoji] 研究名稱 — 進度狀態`

#### 研究進度總覽（Section F，新增）
- **統計卡片**：構思中、撰寫中、投稿中、接受（四維度）
- **研究清單表格**：所有住院醫師的研究記錄
  - 欄位：住院醫師、級職、研究名稱、類型、指導老師、進度、更新時間
- **進度分布圖**：圓餅圖（可展開）

### 3. 個別深入分析頁面整合 (`pediatric_analysis.py`)

**新增區塊**：

#### Section F：研究進度
- **統計卡片**：個人的四維度統計
- **研究清單表格**：個人所有研究記錄
- **詳細進度說明**（可展開）：
  - 每筆研究的進度說明、遭遇困難、下一步計畫

#### Section G：學習反思記錄
- **類型統計**：各反思類型的數量
- **反思清單**：最新 10 筆（日期、標題、類型、相關 EPA/技能）
- **詳細反思內容**（可展開）：
  - Gibbs 五階段完整內容
  - 標籤顯示

**顯示邏輯**：
- 僅在有 Supabase 連線時顯示
- 靜默失敗機制（避免影響主功能）
- 私人反思不在此頁面顯示（隱私保護）

---

## 🔐 權限控制

### 角色權限矩陣

| 功能 | 住院醫師 | 教師 | 管理員 |
|------|---------|------|--------|
| 填寫研究進度 | ✅ | ❌ | ❌ |
| 填寫學習反思 | ✅ | ❌ | ❌ |
| 查看自己的研究/反思 | ✅ | ✅ | ✅ |
| 查看他人的研究/反思 | ❌ | ✅ | ✅ |
| 查看私人反思 | 僅自己 | ❌ | ❌ |
| CCC 總覽（研究進度） | ✅ | ✅ | ✅ |
| 個別分析（研究/反思） | ✅ | ✅ | ✅ |

### 實作方式
- 使用 `st.session_state.get('role')` 判斷角色
- 動態建立 Tab 列表（`is_resident` 變數）
- 過濾器控制資料顯示範圍
- `is_private` 欄位控制反思隱私

---

## 📊 資料統計與視覺化

### CCC 總覽頁面
1. **四維度統計卡片**（構思中、撰寫中、投稿中、接受）
2. **研究進度分布圓餅圖**（各狀態比例）
3. **全體研究清單表格**（所有住院醫師）

### 個別分析頁面
1. **個人四維度統計**
2. **研究清單表格**（個人所有研究）
3. **反思類型統計**（臨床反思、學習心得等）
4. **反思清單表格**（最新 10 筆）

### 視覺化特色
- 使用 Plotly 繪製互動式圖表
- 一致的色彩配置
- 響應式設計（`use_container_width=True`）

---

## 🎯 Gibbs 反思循環架構

本系統採用 **Gibbs Reflective Cycle (1988)** 作為學習反思的理論基礎：

```
1. Description (情境描述)
   ↓
2. Feelings (想法與感受)
   ↓
3. Evaluation (評估與分析)
   ↓
4. Analysis (深入分析) ← 合併到 Evaluation
   ↓
5. Conclusion (結論) ← 整合到 Learning Outcomes
   ↓
6. Action Plan (行動計畫)
   ↓
7. Learning Outcomes (學習成果)
```

**簡化為五階段**：
1. 情境描述
2. 想法與感受
3. 評估與分析
4. 行動計畫
5. 學習成果

---

## 🚀 技術特色

### 1. 資料一致性
- 統一命名規範（`resident_name`, `research_title`）
- 標準化狀態選項（構思中、撰寫中、投稿中、接受）
- 軟刪除機制（`is_deleted = FALSE`）

### 2. 效能優化
- Session State 快取（避免重複 API 調用）
- 靜默失敗（不影響主功能）
- 索引優化（資料表建立時自動建立）

### 3. 使用者體驗
- 清晰的表單結構
- 即時驗證與錯誤提示
- 提交成功動畫
- 分類統計一目了然

### 4. 可維護性
- 模組化設計（表單、顯示、資料庫分離）
- 完整的文件（使用指南、部署清單）
- 統一的錯誤處理

---

## 📋 部署流程

### 步驟 1：資料庫設定
```bash
# 在 Supabase SQL Editor 執行
sql/pediatric_research_schema.sql
```

### 步驟 2：確認環境變數
```bash
# .env 檔案
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

### 步驟 3：重啟 Streamlit
```bash
streamlit run main.py
```

### 步驟 4：功能測試
1. 住院醫師填寫表單
2. 確認 CCC 總覽顯示
3. 確認個別分析顯示
4. 測試權限控制

---

## 🔄 整合流程圖

```
使用者登入
    │
    ├─ 住院醫師 (role='resident')
    │  └─ 可見 Tab：CCC 總覽、個別分析、資料概覽、資料管理、我的表單
    │     └─ 我的表單
    │        ├─ 研究進度（填寫 → 提交 → Supabase）
    │        └─ 學習反思（填寫 → 提交 → Supabase）
    │
    └─ 教師/管理員 (role='teacher'/'admin')
       └─ 可見 Tab：CCC 總覽、個別分析、資料概覽、資料管理、評核表單、帳號管理
          ├─ CCC 總覽
          │  ├─ 摘要卡片（顯示最新研究）
          │  └─ 研究進度總覽（統計 + 表格 + 圖表）
          └─ 個別深入分析
             ├─ Section F：研究進度（統計 + 表格 + 詳細說明）
             └─ Section G：學習反思（統計 + 表格 + 詳細內容）
```

---

## 📈 未來擴充方向

### 短期（1-3 個月）
1. 線上編輯功能（研究進度、學習反思）
2. 附件上傳（論文草稿、圖片）
3. 教師回饋機制（針對反思給予回饋）
4. 匯出功能（PDF / Excel）

### 中期（3-6 個月）
1. 研究進度時間軸視覺化
2. 反思詞頻分析（關鍵字雲）
3. 學習成長曲線圖
4. 自動提醒功能（研究截止日期）

### 長期（6-12 個月）
1. AI 輔助反思分析（情感分析、建議生成）
2. 跨科室研究合作追蹤
3. 發表成果統計（Impact Factor、引用次數）
4. 行動版 App 支援

---

## 📚 相關文件

1. **RESEARCH_AND_REFLECTION_GUIDE.md**：使用者使用指南
2. **DEPLOYMENT_CHECKLIST.md**：部署檢查清單
3. **pediatric_research_schema.sql**：資料庫 Schema
4. **本文件 (FEATURE_SUMMARY.md)**：功能實作總結

---

## 🎉 總結

本次實作為兒科住院醫師 CCC 評估系統新增了兩大核心功能：

✅ **研究進度追蹤**：從構思到發表的完整生命週期管理
✅ **學習反思記錄**：基於 Gibbs 反思循環的結構化反思工具
✅ **完整整合**：在 CCC 總覽與個人分析頁面無縫顯示
✅ **權限控制**：住院醫師專屬表單 + 隱私保護機制
✅ **文件完善**：使用指南 + 部署清單 + 技術文件

系統已準備好部署使用，協助住院醫師更有效地追蹤研究進度與記錄學習成長！

---

**文件版本**：v1.0
**更新日期**：2026-02-10
**作者**：Claude Sonnet 4.5
**專案**：兒科住院醫師 CCC 評估系統
