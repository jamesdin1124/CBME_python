-- 創建研究進度和學習反思表
-- 用於住院醫師記錄研究計畫進度和學習反思

-- ========================================
-- 1. 創建 pediatric_research_progress 表
-- ========================================

CREATE TABLE IF NOT EXISTS pediatric_research_progress (
    id BIGSERIAL PRIMARY KEY,

    -- 基本資訊
    resident_name TEXT NOT NULL,
    resident_level TEXT,
    department TEXT,  -- 科別（小兒部、內科部等）

    -- 研究資訊
    research_title TEXT NOT NULL,
    research_type TEXT NOT NULL,  -- 文獻類型（原著論文、個案報告等）
    supervisor_name TEXT,
    current_status TEXT NOT NULL,  -- 目前進度

    -- 詳細資訊
    research_topic TEXT,
    target_journal TEXT,
    submission_date DATE,
    acceptance_date DATE,

    -- 進度說明
    progress_notes TEXT,
    challenges TEXT,
    next_steps TEXT,

    -- 系統欄位
    submitted_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_research_resident_name ON pediatric_research_progress(resident_name);
CREATE INDEX IF NOT EXISTS idx_research_department ON pediatric_research_progress(department);
CREATE INDEX IF NOT EXISTS idx_research_status ON pediatric_research_progress(current_status);
CREATE INDEX IF NOT EXISTS idx_research_created_at ON pediatric_research_progress(created_at);

-- 創建更新時間觸發器
CREATE OR REPLACE FUNCTION update_research_progress_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_research_progress_updated_at ON pediatric_research_progress;
CREATE TRIGGER trigger_update_research_progress_updated_at
    BEFORE UPDATE ON pediatric_research_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_research_progress_updated_at();

-- ========================================
-- 2. 創建 pediatric_learning_reflections 表
-- ========================================

CREATE TABLE IF NOT EXISTS pediatric_learning_reflections (
    id BIGSERIAL PRIMARY KEY,

    -- 基本資訊
    resident_name TEXT NOT NULL,
    resident_level TEXT,
    department TEXT,  -- 科別
    reflection_date DATE NOT NULL,

    -- 反思資訊
    reflection_title TEXT NOT NULL,
    reflection_type TEXT NOT NULL,  -- 反思類型（臨床技能、溝通技巧等）

    -- Gibbs 反思循環
    situation_description TEXT,  -- 情境描述
    thoughts_and_feelings TEXT,  -- 想法與感受
    evaluation TEXT,             -- 評估與分析
    action_plan TEXT,            -- 行動計畫
    learning_outcomes TEXT,      -- 學習成果

    -- 關聯資訊
    related_epa TEXT,
    related_skill TEXT,
    supervising_teacher TEXT,
    tags TEXT[],  -- 標籤陣列

    -- 隱私設定
    is_private BOOLEAN DEFAULT FALSE,

    -- 系統欄位
    submitted_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_reflection_resident_name ON pediatric_learning_reflections(resident_name);
CREATE INDEX IF NOT EXISTS idx_reflection_department ON pediatric_learning_reflections(department);
CREATE INDEX IF NOT EXISTS idx_reflection_date ON pediatric_learning_reflections(reflection_date);
CREATE INDEX IF NOT EXISTS idx_reflection_type ON pediatric_learning_reflections(reflection_type);
CREATE INDEX IF NOT EXISTS idx_reflection_created_at ON pediatric_learning_reflections(created_at);

-- 創建更新時間觸發器
CREATE OR REPLACE FUNCTION update_learning_reflection_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_learning_reflection_updated_at ON pediatric_learning_reflections;
CREATE TRIGGER trigger_update_learning_reflection_updated_at
    BEFORE UPDATE ON pediatric_learning_reflections
    FOR EACH ROW
    EXECUTE FUNCTION update_learning_reflection_updated_at();

-- ========================================
-- 3. 顯示創建結果
-- ========================================

DO $$
BEGIN
    RAISE NOTICE '✅ 表創建完成：';
    RAISE NOTICE '  - pediatric_research_progress';
    RAISE NOTICE '  - pediatric_learning_reflections';
    RAISE NOTICE '';
    RAISE NOTICE '📊 索引已創建，觸發器已設定';
END $$;
