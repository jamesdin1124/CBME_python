-- =============================================
-- 兒科住院醫師研究進度與學習反思 Schema
-- =============================================

-- 1. 研究進度追蹤表
CREATE TABLE IF NOT EXISTS pediatric_research_progress (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 住院醫師資訊
    resident_name TEXT NOT NULL,
    resident_level TEXT CHECK (resident_level IN ('R1', 'R2', 'R3')),

    -- 研究基本資訊
    research_title TEXT NOT NULL,
    research_type TEXT NOT NULL CHECK (research_type IN ('個案報告', '原著論文', '系統性回顧', '文獻回顧', '其他')),
    supervisor_name TEXT,  -- 指導老師

    -- 進度狀態
    current_status TEXT NOT NULL CHECK (current_status IN ('構思中', '撰寫中', '投稿中', '接受')),
    status_updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 詳細資訊
    research_topic TEXT,  -- 研究主題／領域
    target_journal TEXT,  -- 目標期刊
    submission_date DATE,  -- 投稿日期
    acceptance_date DATE,  -- 接受日期
    publication_date DATE,  -- 發表日期
    doi TEXT,  -- DOI (若已發表)

    -- 進度記錄
    progress_notes TEXT,  -- 進度說明
    challenges TEXT,  -- 遭遇困難
    next_steps TEXT,  -- 下一步計畫

    -- 附加資訊
    is_deleted BOOLEAN DEFAULT FALSE,
    submitted_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_ped_research_resident ON pediatric_research_progress(resident_name);
CREATE INDEX IF NOT EXISTS idx_ped_research_status ON pediatric_research_progress(current_status);
CREATE INDEX IF NOT EXISTS idx_ped_research_not_deleted ON pediatric_research_progress(is_deleted) WHERE is_deleted = FALSE;

-- 2. 學習反思記錄表
CREATE TABLE IF NOT EXISTS pediatric_learning_reflections (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 住院醫師資訊
    resident_name TEXT NOT NULL,
    resident_level TEXT CHECK (resident_level IN ('R1', 'R2', 'R3')),

    -- 反思基本資訊
    reflection_date DATE NOT NULL,
    reflection_title TEXT NOT NULL,
    reflection_type TEXT CHECK (reflection_type IN ('臨床反思', '學習心得', '個案討論', '技能學習', '其他')),

    -- 反思內容
    situation_description TEXT,  -- 情境描述
    thoughts_and_feelings TEXT,  -- 想法與感受
    evaluation TEXT,  -- 評估與分析
    action_plan TEXT,  -- 行動計畫
    learning_outcomes TEXT,  -- 學習成果

    -- 關聯資訊
    related_epa TEXT,  -- 相關 EPA 項目
    related_skill TEXT,  -- 相關技能項目
    supervising_teacher TEXT,  -- 督導教師

    -- 附加資訊
    tags TEXT[],  -- 標籤（可多選）
    is_private BOOLEAN DEFAULT FALSE,  -- 是否為私人記錄
    is_deleted BOOLEAN DEFAULT FALSE,
    submitted_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_ped_reflection_resident ON pediatric_learning_reflections(resident_name);
CREATE INDEX IF NOT EXISTS idx_ped_reflection_date ON pediatric_learning_reflections(reflection_date);
CREATE INDEX IF NOT EXISTS idx_ped_reflection_type ON pediatric_learning_reflections(reflection_type);
CREATE INDEX IF NOT EXISTS idx_ped_reflection_not_deleted ON pediatric_learning_reflections(is_deleted) WHERE is_deleted = FALSE;

-- =============================================
-- 註解說明
-- =============================================
-- pediatric_research_progress: 追蹤住院醫師的研究計畫進度
--   - 支援從構思到發表的完整生命週期
--   - 記錄指導老師、投稿期刊等資訊
--   - 在 CCC 總覽中顯示研究進度統計
--
-- pediatric_learning_reflections: 住院醫師學習反思記錄
--   - 採用 Gibbs 反思循環架構（情境、想法、評估、行動）
--   - 可連結到特定 EPA 或技能項目
--   - 支援標籤分類與私人記錄設定
