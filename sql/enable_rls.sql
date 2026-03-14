-- =============================================
-- 啟用 Row Level Security (RLS)
-- 在 Supabase Dashboard → SQL Editor 中執行此腳本
-- =============================================

-- 1. 啟用 RLS（僅對已存在的表執行）
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename IN (
            'pediatric_evaluations',
            'pediatric_users',
            'user_applications',
            'pediatric_research_progress',
            'pediatric_learning_reflections'
          )
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);
        RAISE NOTICE 'RLS enabled on %', tbl;

        -- 建立 deny anon 政策（若尚未存在）
        BEGIN
            EXECUTE format(
                'CREATE POLICY "deny_anon_all" ON %I FOR ALL TO anon USING (false)',
                tbl
            );
            RAISE NOTICE 'Policy created on %', tbl;
        EXCEPTION WHEN duplicate_object THEN
            RAISE NOTICE 'Policy already exists on %, skipped', tbl;
        END;
    END LOOP;
END
$$;

-- 2. 驗證 RLS 狀態
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename LIKE 'pediatric%'
   OR tablename = 'user_applications';
