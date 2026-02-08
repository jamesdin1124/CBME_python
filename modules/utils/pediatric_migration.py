"""
兒科 CCC 評估系統 — 資料遷移工具
Google Sheets → Supabase 一次性遷移 + 增量同步。
"""

import streamlit as st
import pandas as pd
from datetime import datetime


def migrate_google_sheets_to_supabase(dry_run=True):
    """
    將 Google Sheets 歷史資料遷移到 Supabase。

    Args:
        dry_run (bool): True = 僅預覽，不實際寫入
    """
    st.markdown("### 📦 Google Sheets → Supabase 資料遷移")

    # 1. 載入 Google Sheets 資料
    from modules.google_connection import fetch_google_form_data
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1n4kc2d3Z-x9SvIDApPCCz2HSDO0wSrrk9Y5jReMhr-M/edit?usp=sharing"

    with st.spinner("正在從 Google Sheets 載入資料..."):
        df, sheet_titles = fetch_google_form_data(spreadsheet_url=spreadsheet_url)

    if df is None or df.empty:
        st.error("❌ 無法從 Google Sheets 載入資料")
        return

    st.success(f"✅ 已從 Google Sheets 載入 {len(df)} 筆資料")

    # 2. 前處理
    from pages.pediatric.pediatric_analysis import process_pediatric_data
    processed_df = process_pediatric_data(df)

    # 3. 分類記錄
    technical_records = []
    meeting_records = []
    epa_records = []
    skipped = 0

    for _, row in processed_df.iterrows():
        eval_item = str(row.get('評核項目', '')).strip()

        if eval_item == '操作技術':
            technical_records.append(_to_technical(row))
        elif eval_item == '會議報告':
            meeting_records.append(_to_meeting(row))
        elif 'EPA' in eval_item:
            epa_records.append(_to_epa(row))
        else:
            skipped += 1

    st.markdown(f"""
    **分類結果：**
    - 操作技術：**{len(technical_records)}** 筆
    - 會議報告：**{len(meeting_records)}** 筆
    - EPA：**{len(epa_records)}** 筆
    - 跳過（無法分類）：{skipped} 筆
    """)

    # 4. Dry run 預覽
    if dry_run:
        st.warning("⚠️ **DRY RUN 模式** — 不會實際寫入資料")

        if technical_records:
            with st.expander(f"預覽操作技術（前 5 筆 / 共 {len(technical_records)} 筆）"):
                st.json(technical_records[:5])
        if meeting_records:
            with st.expander(f"預覽會議報告（前 5 筆 / 共 {len(meeting_records)} 筆）"):
                st.json(meeting_records[:5])
        if epa_records:
            with st.expander(f"預覽 EPA（前 5 筆 / 共 {len(epa_records)} 筆）"):
                st.json(epa_records[:5])
        return

    # 5. 正式遷移
    from modules.supabase_connection import SupabaseConnection
    conn = SupabaseConnection()
    total_inserted = 0
    errors = []

    with st.spinner("正在寫入 Supabase..."):
        # 操作技術
        if technical_records:
            count = conn.insert_pediatric_evaluations_batch(technical_records)
            total_inserted += count
            if count < len(technical_records):
                errors.append(f"操作技術：預期 {len(technical_records)} 筆，實際 {count} 筆")
            st.success(f"✅ 操作技術：{count} 筆")

        # 會議報告
        if meeting_records:
            count = conn.insert_pediatric_evaluations_batch(meeting_records)
            total_inserted += count
            if count < len(meeting_records):
                errors.append(f"會議報告：預期 {len(meeting_records)} 筆，實際 {count} 筆")
            st.success(f"✅ 會議報告：{count} 筆")

        # EPA
        if epa_records:
            count = conn.insert_pediatric_evaluations_batch(epa_records)
            total_inserted += count
            if count < len(epa_records):
                errors.append(f"EPA：預期 {len(epa_records)} 筆，實際 {count} 筆")
            st.success(f"✅ EPA：{count} 筆")

    # 6. 記錄 log
    status = 'success' if not errors else 'partial'
    conn.log_pediatric_migration(
        record_count=total_inserted,
        migration_type='initial',
        status=status,
        migrated_by=st.session_state.get('username', 'system'),
        error_details={'errors': errors} if errors else None
    )

    if errors:
        st.warning(f"⚠️ 部分遷移失敗：{'; '.join(errors)}")
    else:
        st.success(f"🎉 遷移完成！共寫入 {total_inserted} 筆資料")
        st.balloons()


def migrate_test_data_to_supabase():
    """將本地測試資料遷移到 Supabase（開發用）"""
    import os
    test_path = 'pages/pediatric/test_data_pediatric_evaluations.csv'
    if not os.path.exists(test_path):
        st.error(f"❌ 測試資料檔案不存在：{test_path}")
        return

    df = pd.read_csv(test_path, encoding='utf-8-sig')
    st.success(f"✅ 已載入測試資料 {len(df)} 筆")

    from pages.pediatric.pediatric_analysis import process_pediatric_data
    processed_df = process_pediatric_data(df)

    records = []
    for _, row in processed_df.iterrows():
        eval_item = str(row.get('評核項目', '')).strip()
        if eval_item == '操作技術':
            records.append(_to_technical(row))
        elif eval_item == '會議報告':
            records.append(_to_meeting(row))
        elif 'EPA' in eval_item:
            records.append(_to_epa(row))

    if not records:
        st.warning("無可遷移的記錄")
        return

    from modules.supabase_connection import SupabaseConnection
    conn = SupabaseConnection()

    with st.spinner(f"正在寫入 {len(records)} 筆測試資料到 Supabase..."):
        count = conn.insert_pediatric_evaluations_batch(records)

    conn.log_pediatric_migration(
        record_count=count,
        migration_type='manual',
        status='success' if count == len(records) else 'partial',
        migrated_by='test_data_migration'
    )

    st.success(f"✅ 已寫入 {count} / {len(records)} 筆測試資料")


# ─── 轉換函數 ───

def _safe_str(val):
    """安全轉換為字串，None/NaN 回傳 None"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return str(val).strip() or None


def _safe_float(val):
    """安全轉換為 float，失敗回傳 None"""
    if val is None:
        return None
    try:
        v = float(val)
        return v if not pd.isna(v) else None
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    """安全轉換為 int，失敗回傳 None"""
    f = _safe_float(val)
    return int(f) if f is not None else None


def _safe_date(val):
    """安全轉換為日期字串 YYYY-MM-DD"""
    if val is None:
        return str(datetime.now().date())
    try:
        if hasattr(val, 'isoformat'):
            return val.isoformat()
        return str(pd.to_datetime(val).date())
    except Exception:
        return str(datetime.now().date())


def _to_technical(row):
    """DataFrame 行 → 操作技術 Supabase 記錄"""
    return {
        'evaluation_type': 'technical_skill',
        'evaluator_teacher': _safe_str(row.get('評核教師')) or '未知',
        'evaluation_date': _safe_date(row.get('評核日期')),
        'evaluated_resident': _safe_str(row.get('受評核人員')) or '未知',
        'resident_level': _safe_str(row.get('評核時級職')),
        'evaluation_item': '操作技術',
        'patient_id': _safe_str(row.get('病歷號')),
        'technical_skill_item': _safe_str(row.get('評核技術項目')),
        'sedation_medication': _safe_str(row.get('鎮靜藥物')),
        'reliability_level': _safe_float(row.get('可信賴程度_數值')),
        'technical_feedback': _safe_str(row.get('操作技術教師回饋')),
        'proficiency_level': _safe_int(row.get('熟練程度_數值')),
        'submitted_by': 'migration',
        'form_version': '1.0',
    }


def _to_meeting(row):
    """DataFrame 行 → 會議報告 Supabase 記錄"""
    return {
        'evaluation_type': 'meeting_report',
        'evaluator_teacher': _safe_str(row.get('評核教師')) or '未知',
        'evaluation_date': _safe_date(row.get('評核日期')),
        'evaluated_resident': _safe_str(row.get('受評核人員')) or '未知',
        'resident_level': _safe_str(row.get('評核時級職')),
        'evaluation_item': '會議報告',
        'meeting_name': _safe_str(row.get('會議名稱')),
        'content_sufficient': _safe_int(row.get('內容是否充分_數值')),
        'data_analysis_ability': _safe_int(row.get('辯證資料的能力_數值')),
        'presentation_clarity': _safe_int(row.get('口條、呈現方式是否清晰_數值')),
        'innovative_ideas': _safe_int(row.get('是否具開創、建設性的想法_數值')),
        'logical_response': _safe_int(row.get('回答提問是否具邏輯、有條有理_數值')),
        'meeting_feedback': _safe_str(row.get('會議報告教師回饋')),
        'submitted_by': 'migration',
        'form_version': '1.0',
    }


def _to_epa(row):
    """DataFrame 行 → EPA Supabase 記錄"""
    return {
        'evaluation_type': 'epa',
        'evaluator_teacher': _safe_str(row.get('評核教師')) or '未知',
        'evaluation_date': _safe_date(row.get('評核日期')),
        'evaluated_resident': _safe_str(row.get('受評核人員')) or '未知',
        'resident_level': _safe_str(row.get('評核時級職')),
        'evaluation_item': 'EPA',
        'epa_item': _safe_str(row.get('EPA項目')),
        'epa_reliability_level': _safe_float(row.get('EPA可信賴程度_數值')),
        'epa_qualitative_feedback': _safe_str(row.get('EPA質性回饋')),
        'submitted_by': 'migration',
        'form_version': '1.0',
    }
