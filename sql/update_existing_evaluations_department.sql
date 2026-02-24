-- 更新現有評核記錄的 department 欄位
-- 將所有 department 為 NULL 的記錄設定為「小兒部」

-- 1. 更新 pediatric_evaluations 表
UPDATE pediatric_evaluations
SET department = '小兒部'
WHERE department IS NULL;

-- 2. 更新 pediatric_research_progress 表（如果存在）
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pediatric_research_progress') THEN
        UPDATE pediatric_research_progress
        SET department = '小兒部'
        WHERE department IS NULL;
    END IF;
END $$;

-- 3. 更新 pediatric_learning_reflections 表（如果存在）
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pediatric_learning_reflections') THEN
        UPDATE pediatric_learning_reflections
        SET department = '小兒部'
        WHERE department IS NULL;
    END IF;
END $$;

-- 顯示更新結果
DO $$
DECLARE
    eval_count INTEGER;
    research_count INTEGER := 0;
    reflection_count INTEGER := 0;
BEGIN
    -- 計算 evaluations
    SELECT COUNT(*) INTO eval_count
    FROM pediatric_evaluations
    WHERE department = '小兒部';

    -- 計算 research (如果表存在)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pediatric_research_progress') THEN
        SELECT COUNT(*) INTO research_count
        FROM pediatric_research_progress
        WHERE department = '小兒部';
    END IF;

    -- 計算 reflections (如果表存在)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pediatric_learning_reflections') THEN
        SELECT COUNT(*) INTO reflection_count
        FROM pediatric_learning_reflections
        WHERE department = '小兒部';
    END IF;

    RAISE NOTICE '✅ 更新完成：';
    RAISE NOTICE '  - pediatric_evaluations: % 筆', eval_count;
    RAISE NOTICE '  - pediatric_research_progress: % 筆', research_count;
    RAISE NOTICE '  - pediatric_learning_reflections: % 筆', reflection_count;
END $$;
