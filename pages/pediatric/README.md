# 兒科住院醫師評核系統 — 研究進度與學習反思模組

## 🚀 快速開始

### 部署（首次使用）

```bash
# 1. 在 Supabase SQL Editor 執行資料庫 Schema
sql/pediatric_research_schema.sql

# 2. 確認 .env 包含 Supabase 連線資訊
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# 3. 重啟 Streamlit
streamlit run main.py
```

### 使用（住院醫師）

1. 登入系統（角色：resident）
2. 點擊 **「📝 我的表單」** 分頁
3. 選擇：
   - **📚 研究進度**：登記研究計畫
   - **💭 學習反思**：記錄學習經驗

### 查看（教師/管理員）

1. **CCC 總覽**：查看所有住院醫師的研究進度統計
2. **個別深入分析**：查看個別住院醫師的詳細研究與反思記錄

---

## 📁 檔案說明

| 檔案 | 說明 |
|------|------|
| `pediatric_resident_forms.py` | 住院醫師自填表單（研究進度 + 學習反思） |
| `pediatric_analysis.py` | 主頁面（已整合顯示功能） |
| `pediatric_research_schema.sql` | 資料庫 Schema（兩個資料表） |
| `RESEARCH_AND_REFLECTION_GUIDE.md` | 📘 詳細使用指南 |
| `DEPLOYMENT_CHECKLIST.md` | ✅ 部署檢查清單 |
| `FEATURE_SUMMARY.md` | 📊 功能實作總結 |
| `README.md` | 📄 本文件（快速參考） |

---

## 🎯 主要功能

### 1️⃣ 研究進度追蹤
- 記錄研究名稱、類型、指導老師
- 追蹤進度：構思中 → 撰寫中 → 投稿中 → 接受
- 記錄投稿期刊、日期、DOI
- 記錄進度說明、遭遇困難、下一步計畫

### 2️⃣ 學習反思記錄
- 基於 **Gibbs 反思循環**架構
- 五階段：情境描述 → 想法感受 → 評估分析 → 行動計畫 → 學習成果
- 可連結到特定 EPA / 技能項目
- 支援標籤分類與私人記錄設定

### 3️⃣ 整合顯示
- **CCC 總覽**：所有住院醫師的研究統計
- **個別分析**：個人研究清單 + 學習反思記錄
- **統計視覺化**：圓餅圖、統計卡片

---

## 🗄️ 資料庫

### 資料表 1：`pediatric_research_progress`
```sql
-- 研究進度記錄
id, resident_name, research_title, research_type,
supervisor_name, current_status, progress_notes...
```

### 資料表 2：`pediatric_learning_reflections`
```sql
-- 學習反思記錄（Gibbs 五階段）
id, resident_name, reflection_title, reflection_type,
situation_description, thoughts_and_feelings, evaluation,
action_plan, learning_outcomes, tags[], is_private...
```

---

## 🔐 權限說明

| 角色 | 研究進度填寫 | 學習反思填寫 | 查看他人資料 | 查看私人反思 |
|------|------------|------------|------------|------------|
| 住院醫師 | ✅ | ✅ | ❌ | 僅自己 |
| 教師 | ❌ | ❌ | ✅ | ❌ |
| 管理員 | ❌ | ❌ | ✅ | ❌ |

---

## 📖 詳細文件

- **使用指南**：[RESEARCH_AND_REFLECTION_GUIDE.md](./RESEARCH_AND_REFLECTION_GUIDE.md)
- **部署清單**：[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
- **功能總結**：[FEATURE_SUMMARY.md](./FEATURE_SUMMARY.md)

---

## ❓ 常見問題

**Q：如何新增研究進度？**
A：住院醫師登入 → 「我的表單」→ 「研究進度」→ 填寫表單 → 提交

**Q：如何查看其他人的研究？**
A：教師/管理員 → 「CCC 總覽」→ 捲動到「研究進度總覽」區塊

**Q：私人反思會被看到嗎？**
A：不會。私人反思僅住院醫師本人在「我的表單」中可見。

**Q：如何修改已提交的記錄？**
A：目前暫不支援線上編輯，請聯繫管理員。

---

## 🐛 問題回報

如有任何問題或建議，請：
1. 檢查 [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) 問題排查章節
2. 聯繫系統管理員
3. 或在 GitHub Issues 回報

---

## 📞 技術支援

- **系統版本**：兒科 CCC 評估系統 v2.0
- **文件版本**：v1.0
- **更新日期**：2026-02-10

---

**祝使用愉快！ 🎉**
