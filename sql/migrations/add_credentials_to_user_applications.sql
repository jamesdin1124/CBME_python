-- ==========================================
-- 遷移腳本：user_applications 新增 desired_username 和 password_hash 欄位
-- 日期：2026-02-11
-- 說明：申請人於註冊時自行設定帳號與密碼，管理員核准後直接建立帳號
-- ==========================================

-- 新增自選帳號欄位
ALTER TABLE user_applications
    ADD COLUMN IF NOT EXISTS desired_username TEXT;

-- 新增密碼 hash 欄位
ALTER TABLE user_applications
    ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- 放寬 user_type 的 CHECK 限制（新增 department_admin, pgy, student）
ALTER TABLE user_applications
    DROP CONSTRAINT IF EXISTS user_applications_user_type_check;

ALTER TABLE user_applications
    ADD CONSTRAINT user_applications_user_type_check
    CHECK (user_type IN ('department_admin', 'teacher', 'resident', 'pgy', 'student'));

-- 移除 department 的預設值（不再強制 '兒科'）
ALTER TABLE user_applications
    ALTER COLUMN department DROP DEFAULT;
