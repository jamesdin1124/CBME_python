# 兒科研究進度與學習反思功能部署檢查清單

## ✅ 部署前檢查

### 1. 資料庫設定
- [ ] 在 Supabase SQL Editor 執行 `sql/pediatric_research_schema.sql`
- [ ] 確認兩個資料表已建立：
  - [ ] `pediatric_research_progress`
  - [ ] `pediatric_learning_reflections`
- [ ] 檢查索引是否正確建立（執行完 SQL 後自動建立）

### 2. 環境變數
- [ ] `.env` 檔案包含正確的 Supabase 連線資訊
  ```
  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_KEY=your-service-role-key
  ```

### 3. 程式碼檔案確認
- [ ] `modules/supabase_connection.py`：已新增研究進度與反思相關方法
- [ ] `pages/pediatric/pediatric_resident_forms.py`：住院醫師自填表單
- [ ] `pages/pediatric/pediatric_analysis.py`：已整合顯示功能
- [ ] `sql/pediatric_research_schema.sql`：資料庫 Schema

---

## 🧪 功能測試

### 測試 1：住院醫師填寫研究進度
1. 以住院醫師身份登入（`role='resident'`）
2. 進入「我的表單」分頁
3. 切換到「研究進度」子分頁
4. 填寫並提交一筆研究進度
5. 確認提交成功且顯示成功訊息

### 測試 2：住院醫師填寫學習反思
1. 在「我的表單」→「學習反思」
2. 填寫完整的 Gibbs 反思內容
3. 選擇相關 EPA、技能、標籤
4. 測試「私人記錄」功能（勾選與不勾選）
5. 確認提交成功

### 測試 3：CCC 總覽頁面顯示
1. 以教師或管理員身份登入
2. 進入「CCC 總覽」分頁
3. 確認摘要卡片底部顯示最新研究進度
4. 捲動到底部，確認「研究進度總覽」區塊顯示
5. 檢查統計數字與表格是否正確

### 測試 4：個別分析頁面顯示
1. 在「個別深入分析」分頁
2. 選擇一位住院醫師
3. 捲動到「研究進度」區塊，確認資料正確顯示
4. 捲動到「學習反思記錄」區塊
5. 展開「詳細反思內容」，確認 Gibbs 五階段完整顯示

### 測試 5：權限控制
1. 確認住院醫師無法看到「評核表單」分頁（教師專用）
2. 確認教師無法看到「我的表單」分頁（住院醫師專用）
3. 確認私人反思不在個別分析頁面顯示
4. 確認住院醫師可在「我的表單」中看到自己的私人反思

---

## 🔧 問題排查

### 問題 1：無法連線 Supabase
**症狀**：頁面顯示「無法連線 Supabase」錯誤

**解決方案**：
1. 檢查 `.env` 檔案中的 `SUPABASE_URL` 和 `SUPABASE_KEY`
2. 確認 Supabase 專案狀態正常
3. 檢查網路連線

### 問題 2：表單提交失敗
**症狀**：按下提交後顯示「提交失敗」

**解決方案**：
1. 檢查 Supabase 資料表結構是否正確
2. 確認欄位名稱與資料類型一致
3. 查看 Supabase Dashboard → Logs 中的錯誤訊息

### 問題 3：資料不顯示
**症狀**：填寫後資料沒有在頁面顯示

**解決方案**：
1. 重新整理頁面
2. 檢查 `is_deleted` 欄位是否為 `FALSE`
3. 確認 `resident_name` 欄位與住院醫師姓名完全一致
4. 檢查過濾條件是否正確

### 問題 4：住院醫師看不到「我的表單」分頁
**症狀**：住院醫師登入後沒有「我的表單」選項

**解決方案**：
1. 檢查 `st.session_state.get('role')` 是否為 `'resident'`
2. 確認 `pediatric_analysis.py` 中的 Tab 邏輯正確
3. 確認 `is_resident` 變數計算正確

---

## 📊 資料驗證

### 資料庫查詢（Supabase SQL Editor）

```sql
-- 檢查研究進度記錄數
SELECT COUNT(*) FROM pediatric_research_progress WHERE is_deleted = FALSE;

-- 檢查學習反思記錄數
SELECT COUNT(*) FROM pediatric_learning_reflections WHERE is_deleted = FALSE;

-- 查看最新 5 筆研究進度
SELECT resident_name, research_title, current_status, updated_at
FROM pediatric_research_progress
WHERE is_deleted = FALSE
ORDER BY updated_at DESC
LIMIT 5;

-- 查看最新 5 筆學習反思
SELECT resident_name, reflection_title, reflection_type, reflection_date
FROM pediatric_learning_reflections
WHERE is_deleted = FALSE
ORDER BY reflection_date DESC
LIMIT 5;

-- 檢查私人記錄統計
SELECT is_private, COUNT(*)
FROM pediatric_learning_reflections
WHERE is_deleted = FALSE
GROUP BY is_private;
```

---

## 📝 上線後監控

### 每日檢查
- [ ] 檢查是否有新的研究進度/反思記錄提交
- [ ] 確認資料顯示正常
- [ ] 檢查 Supabase 使用量（避免超過免費額度）

### 每週檢查
- [ ] 查看使用者回饋
- [ ] 檢查錯誤日誌
- [ ] 評估系統效能

### 每月檢查
- [ ] 資料備份
- [ ] 使用統計報告
- [ ] 功能優化建議

---

## 🚀 未來擴充建議

1. **研究進度**
   - 新增線上編輯功能
   - 支援附件上傳（論文草稿、投稿證明）
   - 自動提醒截止日期

2. **學習反思**
   - 教師可針對反思給予回饋
   - 反思統計分析（詞頻分析、情感分析）
   - 匯出個人反思集錦

3. **權限管理**
   - 更細緻的隱私權限控制
   - 教師可設定是否可查看私人反思
   - 住院醫師可選擇分享對象

4. **資料視覺化**
   - 研究進度時間軸
   - 反思類型趨勢圖
   - 學習成長曲線

---

**檢查清單版本**：v1.0
**更新日期**：2026-02-10
**檢查人員**：________
**檢查日期**：________
