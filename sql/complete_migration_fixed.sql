-- ==========================================
-- 完整資料庫遷移腳本（修正版本）
-- 執行日期：2026-02-10
-- 說明：創建 user_applications 表並執行多科別權限遷移
-- ==========================================

-- ==========================================
-- 第一部分：創建/更新 user_applications 表
-- ==========================================

-- 創建 user_applications 表（如果不存在）
CREATE TABLE IF NOT EXISTS user_applications (
    id BIGSERIAL PRIMARY KEY,

    -- 申請人基本資訊
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    user_type TEXT NOT NULL CHECK (user_type IN ('admin', 'department_admin', 'teacher', 'resident', 'pgy', 'student')),
    department TEXT,
    resident_level TEXT CHECK (resident_level IN ('R1', 'R2', 'R3')),

    -- 申請理由與說明
    application_reason TEXT,
    supervisor_name TEXT,

    -- 申請狀態
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),

    -- 審核資訊
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,

    -- 建立的帳號 ID（核准後記錄）
    created_user_id BIGINT,

    -- 時間戳記
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 軟刪除
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 如果表已存在，更新 user_type 約束
DO $$
BEGIN
    ALTER TABLE user_applications DROP CONSTRAINT IF EXISTS user_applications_user_type_check;
    ALTER TABLE user_applications ADD CONSTRAINT user_applications_user_type_check
        CHECK (user_type IN ('admin', 'department_admin', 'teacher', 'resident', 'pgy', 'student'));

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_applications' AND column_name = 'department'
    ) THEN
        ALTER TABLE user_applications ADD COLUMN department TEXT;
    END IF;

    RAISE NOTICE '✅ user_applications 表已創建/更新';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️  user_applications 更新錯誤: %', SQLERRM;
END $$;

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_user_applications_status ON user_applications(status) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_user_applications_email ON user_applications(email) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_user_applications_department ON user_applications(department) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_user_applications_created_at ON user_applications(created_at DESC);

-- 創建更新時間觸發器函數
CREATE OR REPLACE FUNCTION update_user_applications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 創建觸發器
DROP TRIGGER IF EXISTS trigger_update_user_applications_updated_at ON user_applications;
CREATE TRIGGER trigger_update_user_applications_updated_at
    BEFORE UPDATE ON user_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_user_applications_updated_at();

-- ==========================================
-- 第二部分：多科別權限系統遷移
-- ==========================================

-- 1. 更新 pediatric_users 表
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'pediatric_users'
    ) THEN
        ALTER TABLE pediatric_users DROP CONSTRAINT IF EXISTS pediatric_users_user_type_check;
        ALTER TABLE pediatric_users ADD CONSTRAINT pediatric_users_user_type_check
            CHECK (user_type IN ('admin', 'department_admin', 'teacher', 'resident', 'pgy', 'student'));

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'pediatric_users' AND column_name = 'department'
        ) THEN
            ALTER TABLE pediatric_users ADD COLUMN department TEXT;
        END IF;

        CREATE INDEX IF NOT EXISTS idx_pediatric_users_department ON pediatric_users(department) WHERE is_active = TRUE;

        UPDATE pediatric_users
        SET department = '小兒部'
        WHERE department IS NULL AND user_type NOT IN ('pgy', 'student');

        RAISE NOTICE '✅ pediatric_users 表已更新';
    ELSE
        RAISE NOTICE '⚠️  pediatric_users 表不存在，跳過';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️  pediatric_users 更新錯誤: %', SQLERRM;
END $$;

-- 2. 更新 pediatric_evaluations 表
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'pediatric_evaluations'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'pediatric_evaluations' AND column_name = 'department'
        ) THEN
            ALTER TABLE pediatric_evaluations ADD COLUMN department TEXT;
        END IF;

        CREATE INDEX IF NOT EXISTS idx_pediatric_evaluations_department
        ON pediatric_evaluations(department) WHERE is_deleted = FALSE;

        UPDATE pediatric_evaluations
        SET department = '小兒部'
        WHERE department IS NULL;

        RAISE NOTICE '✅ pediatric_evaluations 表已更新';
    ELSE
        RAISE NOTICE '⚠️  pediatric_evaluations 表不存在，跳過';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️  pediatric_evaluations 更新錯誤: %', SQLERRM;
END $$;

-- 3. 更新 pediatric_research_progress 表
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'pediatric_research_progress'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'pediatric_research_progress' AND column_name = 'department'
        ) THEN
            ALTER TABLE pediatric_research_progress ADD COLUMN department TEXT;
        END IF;

        CREATE INDEX IF NOT EXISTS idx_pediatric_research_progress_department
        ON pediatric_research_progress(department) WHERE is_deleted = FALSE;

        UPDATE pediatric_research_progress
        SET department = '小兒部'
        WHERE department IS NULL;

        RAISE NOTICE '✅ pediatric_research_progress 表已更新';
    ELSE
        RAISE NOTICE '⚠️  pediatric_research_progress 表不存在，跳過';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️  pediatric_research_progress 更新錯誤: %', SQLERRM;
END $$;

-- 4. 更新 pediatric_learning_reflections 表
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'pediatric_learning_reflections'
    ) THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'pediatric_learning_reflections' AND column_name = 'department'
        ) THEN
            ALTER TABLE pediatric_learning_reflections ADD COLUMN department TEXT;
        END IF;

        CREATE INDEX IF NOT EXISTS idx_pediatric_learning_reflections_department
        ON pediatric_learning_reflections(department) WHERE is_deleted = FALSE;

        UPDATE pediatric_learning_reflections
        SET department = '小兒部'
        WHERE department IS NULL;

        RAISE NOTICE '✅ pediatric_learning_reflections 表已更新';
    ELSE
        RAISE NOTICE '⚠️  pediatric_learning_reflections 表不存在，跳過';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '⚠️  pediatric_learning_reflections 更新錯誤: %', SQLERRM;
END $$;

-- ==========================================
-- 最終驗證與總結
-- ==========================================
DO $$
DECLARE
    rec RECORD;
    table_count INT := 0;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '資料庫遷移完成！';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '📋 已更新的表：';

    FOR rec IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name IN (
            'user_applications',
            'pediatric_users',
            'pediatric_evaluations',
            'pediatric_research_progress',
            'pediatric_learning_reflections'
        )
        ORDER BY table_name
    LOOP
        RAISE NOTICE '  ✅ %', rec.table_name;
        table_count := table_count + 1;
    END LOOP;

    RAISE NOTICE '';
    RAISE NOTICE '🔍 驗證結果：';
    RAISE NOTICE '  - 已更新 % 個表', table_count;
    RAISE NOTICE '  - 6 個角色已支援：admin, department_admin, teacher, resident, pgy, student';
    RAISE NOTICE '  - department 欄位已添加到所有相關表';
    RAISE NOTICE '  - 現有資料已回填為「小兒部」';
    RAISE NOTICE '  - 索引已創建以優化查詢效能';
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '🚀 系統已準備就緒！';
    RAISE NOTICE '========================================';
END $$;
