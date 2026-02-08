-- =============================================
-- 兒科 CCC 評估系統 Supabase Schema
-- =============================================

-- 1. 統一評核記錄表
CREATE TABLE IF NOT EXISTS pediatric_evaluations (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 共用欄位
    evaluation_type TEXT NOT NULL CHECK (evaluation_type IN ('technical_skill', 'meeting_report', 'epa')),
    evaluator_teacher TEXT NOT NULL,
    evaluation_date DATE NOT NULL,
    evaluated_resident TEXT NOT NULL,
    resident_level TEXT CHECK (resident_level IN ('R1', 'R2', 'R3')),

    -- 會議報告欄位（5 維度 1-5 分）
    evaluation_item TEXT,
    meeting_name TEXT,
    content_sufficient INTEGER CHECK (content_sufficient BETWEEN 1 AND 5),
    data_analysis_ability INTEGER CHECK (data_analysis_ability BETWEEN 1 AND 5),
    presentation_clarity INTEGER CHECK (presentation_clarity BETWEEN 1 AND 5),
    innovative_ideas INTEGER CHECK (innovative_ideas BETWEEN 1 AND 5),
    logical_response INTEGER CHECK (logical_response BETWEEN 1 AND 5),
    meeting_feedback TEXT,

    -- 操作技術欄位
    patient_id TEXT,
    technical_skill_item TEXT,
    sedation_medication TEXT,
    reliability_level NUMERIC(3,1),
    technical_feedback TEXT,
    proficiency_level INTEGER CHECK (proficiency_level BETWEEN 1 AND 5),

    -- EPA 欄位
    epa_item TEXT CHECK (epa_item IS NULL OR epa_item IN ('病人日常照護', '緊急照護處置', '病歷書寫')),
    epa_reliability_level NUMERIC(3,1),
    epa_qualitative_feedback TEXT,

    -- 中繼資料
    submitted_by TEXT,
    form_version TEXT DEFAULT '1.0',
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_ped_eval_type ON pediatric_evaluations(evaluation_type);
CREATE INDEX IF NOT EXISTS idx_ped_eval_date ON pediatric_evaluations(evaluation_date);
CREATE INDEX IF NOT EXISTS idx_ped_eval_resident ON pediatric_evaluations(evaluated_resident);
CREATE INDEX IF NOT EXISTS idx_ped_eval_teacher ON pediatric_evaluations(evaluator_teacher);
CREATE INDEX IF NOT EXISTS idx_ped_eval_not_deleted ON pediatric_evaluations(is_deleted) WHERE is_deleted = FALSE;

-- 2. 教師／住院醫師帳號管理表
CREATE TABLE IF NOT EXISTS pediatric_users (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    user_type TEXT NOT NULL CHECK (user_type IN ('teacher', 'resident', 'admin')),

    -- 住院醫師專屬
    resident_level TEXT CHECK (resident_level IN ('R1', 'R2', 'R3')),
    enrollment_year INTEGER,

    -- 主治醫師專屬
    title TEXT,

    -- 帳號狀態
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,

    -- 科部（全科別通用）
    department TEXT,

    -- 密碼雜湊（供未來全面遷移登入用）
    password_hash TEXT,

    -- 與本地 auth 同步
    synced_from_local_auth BOOLEAN DEFAULT FALSE,
    local_auth_username TEXT
);

CREATE INDEX IF NOT EXISTS idx_ped_users_type ON pediatric_users(user_type);
CREATE INDEX IF NOT EXISTS idx_ped_users_active ON pediatric_users(is_active) WHERE is_active = TRUE;

-- 3. CCC 門檻設定表
CREATE TABLE IF NOT EXISTS pediatric_threshold_settings (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by TEXT,

    -- 技能完成率門檻（百分比）
    technical_green_threshold NUMERIC(5,2) DEFAULT 100.0,
    technical_red_threshold NUMERIC(5,2) DEFAULT 60.0,

    -- EPA / 會議報告均分門檻（1-5 分）
    score_green_threshold NUMERIC(3,1) DEFAULT 3.5,
    score_red_threshold NUMERIC(3,1) DEFAULT 2.5,

    -- 啟用狀態
    is_active BOOLEAN DEFAULT TRUE,
    effective_from TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

-- 確保只有一筆 active 設定
CREATE UNIQUE INDEX IF NOT EXISTS idx_ped_threshold_active
    ON pediatric_threshold_settings(is_active) WHERE is_active = TRUE;

-- 插入預設門檻
INSERT INTO pediatric_threshold_settings
    (technical_green_threshold, technical_red_threshold, score_green_threshold, score_red_threshold, updated_by, notes)
VALUES
    (100.0, 60.0, 3.5, 2.5, 'system', '系統預設門檻值')
ON CONFLICT DO NOTHING;

-- 4. 遷移記錄表
CREATE TABLE IF NOT EXISTS pediatric_migration_log (
    id BIGSERIAL PRIMARY KEY,
    migrated_at TIMESTAMPTZ DEFAULT NOW(),
    google_sheet_timestamp TIMESTAMPTZ,
    record_count INTEGER,
    migration_type TEXT CHECK (migration_type IN ('initial', 'incremental', 'manual')),
    status TEXT CHECK (status IN ('success', 'partial', 'failed')),
    error_details JSONB,
    migrated_by TEXT
);

-- =============================================
-- RLS 政策（可選，依部署需求啟用）
-- =============================================
-- 若使用 Supabase anon key + service_role key 模式，
-- 可在 Streamlit 後端統一用 service_role key 存取，
-- 權限控制由 Streamlit 的 auth.py 負責。
-- 以下 RLS 政策保留供未來需要時啟用。

-- ALTER TABLE pediatric_evaluations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE pediatric_users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE pediatric_threshold_settings ENABLE ROW LEVEL SECURITY;

-- =============================================
-- 欄位擴充（若表已存在，執行 ALTER 新增欄位）
-- =============================================
-- 若你的 pediatric_users 表已建立但缺少 department / password_hash，
-- 請在 Supabase SQL Editor 執行以下兩行：
--
-- ALTER TABLE pediatric_users ADD COLUMN IF NOT EXISTS department TEXT;
-- ALTER TABLE pediatric_users ADD COLUMN IF NOT EXISTS password_hash TEXT;
