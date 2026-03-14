-- =============================================
-- 啟用 Row Level Security (RLS)
-- 在 Supabase Dashboard → SQL Editor 中執行此腳本
-- =============================================

-- 1. 啟用 RLS
ALTER TABLE pediatric_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE pediatric_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_reflections ENABLE ROW LEVEL SECURITY;

-- 2. Service Role 完全存取（後端 API 使用）
-- service_role key 跳過 RLS，所以 Streamlit 後端仍可正常運作

-- 3. Anon key 預設拒絕所有存取
-- （目前 Streamlit 使用 service_role key，此政策做為額外安全層）

CREATE POLICY "deny_anon_all" ON pediatric_evaluations
    FOR ALL TO anon USING (false);

CREATE POLICY "deny_anon_all" ON pediatric_users
    FOR ALL TO anon USING (false);

CREATE POLICY "deny_anon_all" ON user_applications
    FOR ALL TO anon USING (false);

CREATE POLICY "deny_anon_all" ON research_progress
    FOR ALL TO anon USING (false);

CREATE POLICY "deny_anon_all" ON learning_reflections
    FOR ALL TO anon USING (false);

-- =============================================
-- 驗證 RLS 狀態
-- =============================================
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'pediatric_evaluations',
    'pediatric_users',
    'user_applications',
    'research_progress',
    'learning_reflections'
  );
