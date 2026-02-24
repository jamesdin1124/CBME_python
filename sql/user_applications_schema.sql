-- ==========================================
-- 使用者申請記錄資料表
-- ==========================================
-- 用途：記錄醫師申請帳號的資訊，供管理員審核
-- 建立日期：2026-02-10
-- ==========================================

CREATE TABLE IF NOT EXISTS user_applications (
    id BIGSERIAL PRIMARY KEY,

    -- 申請人基本資訊
    full_name TEXT NOT NULL,
    desired_username TEXT NOT NULL,       -- 申請人自選帳號
    password_hash TEXT NOT NULL,          -- 申請人自設密碼（SHA-256 雜湊）
    email TEXT NOT NULL,
    phone TEXT,                           -- 聯絡電話（公務機）
    user_type TEXT NOT NULL CHECK (user_type IN ('department_admin', 'teacher', 'resident', 'pgy', 'student')),
    resident_level TEXT CHECK (resident_level IN ('R1', 'R2', 'R3')),
    department TEXT,

    -- 附加資訊
    application_reason TEXT,
    supervisor_name TEXT,  -- 指導醫師（若為住院醫師）

    -- 申請狀態
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),

    -- 審核資訊
    reviewed_by TEXT,  -- 審核者姓名
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,  -- 審核備註（拒絕原因或其他說明）

    -- 建立的帳號 ID（核准後記錄）
    created_user_id BIGINT REFERENCES pediatric_users(id),

    -- 時間戳記
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 軟刪除
    is_deleted BOOLEAN DEFAULT FALSE
);

-- ==========================================
-- 索引優化
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_user_applications_status ON user_applications(status) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_user_applications_email ON user_applications(email) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_user_applications_created_at ON user_applications(created_at DESC);

-- ==========================================
-- 更新時間戳記觸發器
-- ==========================================
CREATE OR REPLACE FUNCTION update_user_applications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_applications_updated_at
    BEFORE UPDATE ON user_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_user_applications_updated_at();

-- ==========================================
-- 範例查詢
-- ==========================================

-- 查詢所有待審核申請
-- SELECT * FROM user_applications WHERE status = 'pending' AND is_deleted = FALSE ORDER BY created_at DESC;

-- 查詢特定 Email 的申請狀態
-- SELECT * FROM user_applications WHERE email = 'user@example.com' AND is_deleted = FALSE ORDER BY created_at DESC;

-- 統計各狀態申請數量
-- SELECT status, COUNT(*) FROM user_applications WHERE is_deleted = FALSE GROUP BY status;
