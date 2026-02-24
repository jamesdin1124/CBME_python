-- =========================================================
-- 多科別、多層級權限管理系統 - 資料庫遷移腳本
-- =========================================================
-- 版本：v1.0
-- 日期：2026-02-10
-- 說明：擴展權限系統支援 6 層級角色與多科別管理
-- =========================================================

-- =========================================================
-- Part 1: 擴展 pediatric_users 表的角色支援
-- =========================================================

-- 1.1 刪除舊的 user_type 約束
ALTER TABLE pediatric_users
DROP CONSTRAINT IF EXISTS pediatric_users_user_type_check;

-- 1.2 新增支援 6 層級角色的約束
ALTER TABLE pediatric_users
ADD CONSTRAINT pediatric_users_user_type_check
CHECK (user_type IN ('admin', 'department_admin', 'teacher', 'resident', 'pgy', 'student'));

-- 1.3 確保非 admin 角色必須有科別（PGY/UGY 除外）
ALTER TABLE pediatric_users
DROP CONSTRAINT IF EXISTS pediatric_users_department_required;

ALTER TABLE pediatric_users
ADD CONSTRAINT pediatric_users_department_required
CHECK (
    (user_type = 'admin') OR
    (user_type IN ('pgy', 'student')) OR
    (user_type IN ('department_admin', 'teacher', 'resident') AND department IS NOT NULL)
);

-- =========================================================
-- Part 2: 擴展 user_applications 表的角色與科別支援
-- =========================================================

-- 2.1 刪除舊的 user_type 約束
ALTER TABLE user_applications
DROP CONSTRAINT IF EXISTS user_applications_user_type_check;

-- 2.2 新增支援 5 層級角色的約束（不含 admin，admin 不需申請）
ALTER TABLE user_applications
ADD CONSTRAINT user_applications_user_type_check
CHECK (user_type IN ('department_admin', 'teacher', 'resident', 'pgy', 'student'));

-- 2.3 移除 department 的預設值
ALTER TABLE user_applications
ALTER COLUMN department DROP DEFAULT;

-- 2.4 確保非 PGY/UGY 角色必須填寫科別
ALTER TABLE user_applications
DROP CONSTRAINT IF EXISTS user_applications_department_required;

ALTER TABLE user_applications
ADD CONSTRAINT user_applications_department_required
CHECK (
    (user_type IN ('pgy', 'student')) OR
    (user_type IN ('department_admin', 'teacher', 'resident') AND department IS NOT NULL)
);

-- =========================================================
-- Part 3: 為評核記錄表新增科別欄位
-- =========================================================

-- 3.1 pediatric_evaluations 表新增 department 欄位
ALTER TABLE pediatric_evaluations
ADD COLUMN IF NOT EXISTS department TEXT;

-- 3.2 pediatric_research_progress 表新增 department 欄位
ALTER TABLE pediatric_research_progress
ADD COLUMN IF NOT EXISTS department TEXT;

-- 3.3 pediatric_learning_reflections 表新增 department 欄位
ALTER TABLE pediatric_learning_reflections
ADD COLUMN IF NOT EXISTS department TEXT;

-- =========================================================
-- Part 4: 回填現有資料為「小兒部」
-- =========================================================

-- 4.1 回填評核記錄
UPDATE pediatric_evaluations
SET department = '小兒部'
WHERE department IS NULL;

-- 4.2 回填研究進度
UPDATE pediatric_research_progress
SET department = '小兒部'
WHERE department IS NULL;

-- 4.3 回填學習反思
UPDATE pediatric_learning_reflections
SET department = '小兒部'
WHERE department IS NULL;

-- =========================================================
-- Part 5: 建立索引以提升查詢效能
-- =========================================================

-- 5.1 評核記錄表索引
CREATE INDEX IF NOT EXISTS idx_pediatric_evaluations_department
ON pediatric_evaluations(department) WHERE department IS NOT NULL;

-- 5.2 研究進度表索引
CREATE INDEX IF NOT EXISTS idx_research_progress_department
ON pediatric_research_progress(department) WHERE department IS NOT NULL;

-- 5.3 學習反思表索引
CREATE INDEX IF NOT EXISTS idx_learning_reflections_department
ON pediatric_learning_reflections(department) WHERE department IS NOT NULL;

-- 5.4 使用者表科別索引
CREATE INDEX IF NOT EXISTS idx_pediatric_users_department
ON pediatric_users(department) WHERE department IS NOT NULL;

-- 5.5 使用者申請表科別索引
CREATE INDEX IF NOT EXISTS idx_user_applications_department
ON user_applications(department) WHERE department IS NOT NULL;

-- =========================================================
-- Part 6: 驗證遷移結果
-- =========================================================

-- 6.1 檢查 pediatric_users 表結構
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'pediatric_users' AND column_name IN ('user_type', 'department');

-- 6.2 檢查評核記錄是否已回填
-- SELECT department, COUNT(*) as count
-- FROM pediatric_evaluations
-- GROUP BY department;

-- 6.3 檢查索引是否建立
-- SELECT indexname, tablename
-- FROM pg_indexes
-- WHERE tablename IN ('pediatric_evaluations', 'pediatric_research_progress', 'pediatric_learning_reflections', 'pediatric_users', 'user_applications')
-- AND indexname LIKE '%department%';

-- =========================================================
-- 遷移完成
-- =========================================================
-- 執行此腳本後，系統將支援：
-- 1. 6 層級角色：admin, department_admin, teacher, resident, pgy, student
-- 2. 科別隔離：各科別資料自動過濾
-- 3. PGY/UGY 跨科訓練：個人資料無科別，評核記錄有科別
-- 4. 回填完成：所有現有資料歸屬「小兒部」
-- =========================================================
