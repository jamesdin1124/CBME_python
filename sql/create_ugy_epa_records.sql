-- UGY EPA 評核紀錄資料表
-- 用於存放系統內填寫的 EPA 評核，欄位與 Google 表單輸出一致

CREATE TABLE IF NOT EXISTS ugy_epa_records (
    id              BIGSERIAL PRIMARY KEY,
    "時間戳記"       TIMESTAMPTZ DEFAULT NOW(),
    "學員姓名"       TEXT NOT NULL,
    "階層"           TEXT,           -- C1, C2
    "實習科部"       TEXT,           -- 內科部, 外科部, 婦產部, 小兒部
    "EPA評核項目"    TEXT NOT NULL,   -- 病歷紀錄, 住院接診, 當班處置
    "地點"           TEXT,
    "教師評核EPA等級" TEXT,
    "教師評核EPA等級_數值" NUMERIC(3,1),
    "學員自評EPA等級" TEXT,
    "病歷號"         TEXT,
    "病人難度"       TEXT,           -- 簡單, 一般, 困難
    "臨床情境"       TEXT,
    "回饋"           TEXT,
    "給教學部的私下回饋" TEXT,
    "教師"           TEXT NOT NULL,
    evaluation_date  DATE DEFAULT CURRENT_DATE,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_ugy_epa_student ON ugy_epa_records ("學員姓名");
CREATE INDEX IF NOT EXISTS idx_ugy_epa_teacher ON ugy_epa_records ("教師");
CREATE INDEX IF NOT EXISTS idx_ugy_epa_date ON ugy_epa_records (evaluation_date);
CREATE INDEX IF NOT EXISTS idx_ugy_epa_dept ON ugy_epa_records ("實習科部");

-- RLS（Row Level Security）- 建議啟用
-- ALTER TABLE ugy_epa_records ENABLE ROW LEVEL SECURITY;
