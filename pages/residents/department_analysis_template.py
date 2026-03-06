"""
通用科別分析模板

提供統一的三分頁結構：
  1. 總覽 — 群組趨勢 + 雷達圖
  2. 個別分析 — 個人 vs 群組比較
  3. 評核表單 — 統一評核表單入口

任何尚未建立專屬頁面的科別（如內科部、外科部、婦產部等）
均可直接呼叫此模板。
"""

import streamlit as st
import pandas as pd

from config.department_config import get_department_config, PROFICIENCY_THRESHOLD
from modules.evaluation_forms import show_evaluation_form
from modules.visualization.longitudinal import LongitudinalChart
from modules.visualization.unified_radar import UnifiedRadarVisualization


# ─── 共用工具 ───────────────────────────────────────────

def _get_supabase_conn():
    """取得 Supabase 連線（懶載入）"""
    try:
        from modules.supabase_connection import SupabaseConnection
        return SupabaseConnection()
    except Exception:
        return None


def _load_department_data(department: str) -> pd.DataFrame | None:
    """
    從 Supabase 載入指定科別的評核資料。
    回傳 DataFrame 或 None。
    """
    conn = _get_supabase_conn()
    if not conn:
        return None

    try:
        rows = conn.fetch_evaluations(department=department)
        if rows:
            return pd.DataFrame(rows)
    except Exception as e:
        st.warning(f"載入 {department} 資料時發生錯誤：{e}")
    return None


# ─── 主入口 ─────────────────────────────────────────────

def show_department_analysis(department: str, excel_data: pd.DataFrame | None = None):
    """
    通用科別分析頁面。

    Args:
        department: 科別名稱（如「內科部」）
        excel_data: 從 Excel 上傳並合併的 DataFrame（可選，若無則從 Supabase 載入）
    """
    st.title(f"🏥 {department}住院醫師評核分析")
    st.markdown("---")

    dept_config = get_department_config(department)
    epa_items = dept_config.get('epa_items', [])

    # ── 資料來源 ──
    data_source = st.radio(
        "資料來源",
        options=['supabase', 'excel'],
        format_func=lambda x: {'supabase': '☁️ Supabase 資料庫', 'excel': '📂 上傳 Excel'}[x],
        horizontal=True,
        key=f"{department}_data_source",
    )

    if data_source == 'supabase':
        df = _load_department_data(department)
    else:
        df = excel_data

    # ── 建立分頁 ──
    tab_labels = ["📊 總覽", "📋 個別分析", "📝 評核表單"]
    tabs = st.tabs(tab_labels)

    # ━━━ Tab 1: 總覽 ━━━
    with tabs[0]:
        _show_overview(df, department, epa_items)

    # ━━━ Tab 2: 個別分析 ━━━
    with tabs[1]:
        _show_individual(df, department, epa_items)

    # ━━━ Tab 3: 評核表單 ━━━
    with tabs[2]:
        show_evaluation_form(department=department)


# ─── Tab 1: 總覽 ────────────────────────────────────────

def _show_overview(df: pd.DataFrame | None, department: str, epa_items: list):
    """群組層級分析：基本指標、趨勢圖、雷達圖"""
    st.subheader("群組分析總覽")

    if df is None or df.empty:
        st.info("尚無評核資料。請透過「評核表單」填寫，或切換至 Excel 資料來源。")
        return

    # ── 基本指標 ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("評核總筆數", len(df))
    with col2:
        if 'resident_name' in df.columns:
            st.metric("受評人數", df['resident_name'].nunique())
        elif '受評核人員' in df.columns:
            st.metric("受評人數", df['受評核人員'].nunique())
    with col3:
        if 'evaluator_name' in df.columns:
            st.metric("評核教師數", df['evaluator_name'].nunique())
        elif '評核教師' in df.columns:
            st.metric("評核教師數", df['評核教師'].nunique())
    with col4:
        score_col = _find_score_column(df)
        if score_col:
            avg_score = pd.to_numeric(df[score_col], errors='coerce').mean()
            st.metric("平均信賴等級", f"{avg_score:.2f}" if pd.notna(avg_score) else "N/A")

    st.markdown("---")

    # ── 群組趨勢圖 ──
    time_col = _find_time_column(df)
    score_col = _find_score_column(df)
    group_col = _find_epa_column(df)

    if time_col and score_col:
        st.subheader("📈 群組評分趨勢")
        chart = LongitudinalChart()
        fig = chart.create_group_trend(
            group_data=df,
            time_col=time_col,
            score_col=score_col,
            group_col=group_col,
        )
        st.plotly_chart(fig, width="stretch")

    # ── 群組雷達圖 ──
    if epa_items and score_col and group_col:
        st.subheader("🕸️ EPA 雷達圖")
        radar = UnifiedRadarVisualization()

        # 計算各 EPA 項目平均分數
        epa_scores = {}
        for item in epa_items:
            item_data = df[df[group_col] == item] if group_col else pd.DataFrame()
            if not item_data.empty:
                val = pd.to_numeric(item_data[score_col], errors='coerce').mean()
                epa_scores[item] = round(val, 2) if pd.notna(val) else 0
            else:
                epa_scores[item] = 0

        if any(v > 0 for v in epa_scores.values()):
            fig = radar.create_individual_radar(
                student_scores=epa_scores,
                epa_labels=list(epa_scores.keys()),
                student_name=f"{department} 群組平均",
                max_score=5.0,
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("EPA 項目尚無有效評分資料")


# ─── Tab 2: 個別分析 ────────────────────────────────────

def _show_individual(df: pd.DataFrame | None, department: str, epa_items: list):
    """個人 vs 群組比較分析"""
    st.subheader("個別學員分析")

    if df is None or df.empty:
        st.info("尚無評核資料。")
        return

    # 找出學員欄位
    student_col = _find_student_column(df)
    if not student_col:
        st.warning("資料中找不到學員姓名欄位")
        return

    students = sorted(df[student_col].dropna().unique())
    if not students:
        st.info("無學員資料")
        return

    selected = st.selectbox("選擇學員", students, key=f"{department}_individual_student")
    student_df = df[df[student_col] == selected]

    score_col = _find_score_column(df)
    time_col = _find_time_column(df)
    group_col = _find_epa_column(df)

    # ── 個人 vs 群組趨勢 ──
    if time_col and score_col:
        st.subheader(f"📈 {selected} 個人 vs 群組趨勢")
        chart = LongitudinalChart()
        fig = chart.create_individual_vs_group(
            student_data=student_df,
            group_data=df,
            time_col=time_col,
            score_col=score_col,
            student_name=selected,
        )
        st.plotly_chart(fig, width="stretch")

    # ── 個人 vs 群組雷達 ──
    if epa_items and score_col and group_col:
        st.subheader(f"🕸️ {selected} 個人 vs 群組 EPA 雷達圖")
        radar = UnifiedRadarVisualization()

        # 個人各 EPA 平均
        student_scores = {}
        group_data_dict = {}
        for item in epa_items:
            s_data = student_df[student_df[group_col] == item] if group_col else pd.DataFrame()
            g_data = df[df[group_col] == item] if group_col else pd.DataFrame()

            s_val = pd.to_numeric(s_data[score_col], errors='coerce').mean() if not s_data.empty else 0
            g_val = pd.to_numeric(g_data[score_col], errors='coerce').mean() if not g_data.empty else 0

            student_scores[item] = round(s_val, 2) if pd.notna(s_val) else 0
            group_data_dict[item] = round(g_val, 2) if pd.notna(g_val) else 0

        if any(v > 0 for v in student_scores.values()):
            fig = radar.create_individual_vs_group_radar(
                student_scores=student_scores,
                group_data=group_data_dict,
                epa_labels=list(student_scores.keys()),
                student_name=selected,
                group_name=f"{department} 平均",
                max_score=5.0,
            )
            st.plotly_chart(fig, width="stretch")

    # ── 個人評核紀錄表 ──
    st.subheader(f"📋 {selected} 評核紀錄")
    st.dataframe(student_df, hide_index=True, width="stretch")


# ─── 欄位偵測輔助 ──────────────────────────────────────

def _find_score_column(df: pd.DataFrame) -> str | None:
    """在 DataFrame 中找出分數欄位"""
    candidates = ['reliability_level', '可信賴程度', 'epa_reliability_level', 'score', '分數']
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _find_time_column(df: pd.DataFrame) -> str | None:
    """在 DataFrame 中找出時間欄位"""
    candidates = ['evaluation_date', '評核日期', 'created_at', '時間戳記', 'date']
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _find_student_column(df: pd.DataFrame) -> str | None:
    """在 DataFrame 中找出學員姓名欄位"""
    candidates = ['resident_name', '受評核人員', 'student_name', '姓名', 'name']
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _find_epa_column(df: pd.DataFrame) -> str | None:
    """在 DataFrame 中找出 EPA 項目欄位"""
    candidates = ['evaluation_item', '評核項目', 'epa_item', 'EPA項目', 'item']
    for c in candidates:
        if c in df.columns:
            return c
    return None
