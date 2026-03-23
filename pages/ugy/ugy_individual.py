"""
UGY 個別學生分析
精簡版：資料從 ugy_data_service 取得，圖表用 ugy_chart_helpers 統一繪製。
核心概念：自己 vs 同儕比較。
"""

import pandas as pd
import streamlit as st

from pages.ugy import ugy_data_service as ds
from pages.ugy.ugy_chart_helpers import (
    create_peer_comparison_radar,
    create_peer_comparison_trend,
)


# ═══════════════════════════════════════════════════════
# 個別學生顯示
# ═══════════════════════════════════════════════════════

def _show_student_detail(student_data: pd.DataFrame, all_data: pd.DataFrame,
                         student_name: str):
    """顯示單一學生的完整分析"""
    if student_data.empty:
        st.warning("沒有找到該學生的資料")
        return

    # ── 標題 ──
    student_id = ''
    if '學號' in student_data.columns:
        sid = student_data['學號'].iloc[0]
        if pd.notna(sid) and str(sid) != student_name:
            student_id = str(sid)

    if student_id:
        st.subheader(f"學生: {student_name} ({student_id})")
    else:
        st.subheader(f"學生: {student_name}")

    # ── 基本統計 ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("總評核數", len(student_data))
    with col2:
        n_items = student_data['EPA評核項目'].nunique() if 'EPA評核項目' in student_data.columns else 0
        st.metric("EPA 項目數", n_items)
    with col3:
        n_batches = student_data['梯次'].nunique() if '梯次' in student_data.columns else 0
        st.metric("梯次數", n_batches)
    with col4:
        if '教師評核EPA等級_數值' in student_data.columns:
            avg = student_data['教師評核EPA等級_數值'].mean()
            st.metric("平均分數", f"{avg:.2f}")
        else:
            st.metric("平均分數", "N/A")

    # ── 評核資料表格 ──
    with st.expander("📋 學生評核資料", expanded=True):
        display_cols = [c for c in [
            '學號', '學員姓名', '階層', '實習科部', 'EPA評核項目',
            '教師評核EPA等級', '教師評核EPA等級_數值', '病歷號',
            '地點', '回饋', '教師', '梯次'
        ] if c in student_data.columns]
        if display_cols:
            st.dataframe(student_data[display_cols], use_container_width=True, hide_index=True)
        else:
            st.dataframe(student_data, use_container_width=True, hide_index=True)

    # ── 圖表：自己 vs 同儕 ──
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.caption("🎯 EPA 雷達圖（個人 vs 同儕）")
        radar_fig = create_peer_comparison_radar(student_data, all_data, student_name)
        st.plotly_chart(radar_fig, use_container_width=True,
                        key=f"individual_radar_{student_name}")

    with chart_col2:
        st.caption("📈 EPA 趨勢圖（個人 vs 同儕）")
        trend_fig = create_peer_comparison_trend(student_data, all_data, student_name)
        st.plotly_chart(trend_fig, use_container_width=True,
                        key=f"individual_trend_{student_name}")

    # ── 評核回饋詳情 ──
    with st.expander("💬 評核回饋詳情", expanded=False):
        feedback_cols = [c for c in ['梯次', 'EPA評核項目', '教師評核EPA等級',
                                      '回饋', '教師', '實習科部']
                         if c in student_data.columns]
        if feedback_cols:
            fb_df = student_data[feedback_cols].sort_values(
                '梯次' if '梯次' in feedback_cols else feedback_cols[0]
            )
            st.dataframe(fb_df, use_container_width=True, hide_index=True)

    # ── 各項目統計 ──
    if 'EPA評核項目' in student_data.columns and '教師評核EPA等級_數值' in student_data.columns:
        with st.expander("📊 各項目評核統計", expanded=False):
            stats = student_data.groupby('EPA評核項目')['教師評核EPA等級_數值'].agg(
                平均分='mean', 最高分='max', 最低分='min', 評核數='count'
            ).round(2).reset_index().sort_values('評核數', ascending=False)
            st.dataframe(stats, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════
# 主函數
# ═══════════════════════════════════════════════════════

def show_individual_student_analysis(df: pd.DataFrame):
    """顯示個別學生分析（接收已篩選的 DataFrame）"""
    st.markdown("<h1 style='color:#1E90FF; font-size:32px;'>個別學生分析</h1>",
                unsafe_allow_html=True)

    if df.empty:
        st.warning("沒有可用的資料")
        return

    # 判斷姓名欄位
    name_col = '學員姓名' if '學員姓名' in df.columns else (
        '姓名' if '姓名' in df.columns else None
    )
    if not name_col:
        st.error("資料中找不到學生姓名欄位")
        return

    all_students = sorted(df[name_col].dropna().unique().tolist())
    if not all_students:
        st.warning("沒有找到學生資料")
        return

    st.info(f"共 {len(df)} 筆資料，{len(all_students)} 位學生")

    # ── 學生選擇 ──
    user_role = st.session_state.get('role')
    logged_in_name = st.session_state.get('user_name')

    if user_role == 'student':
        # 學生只能看自己
        if logged_in_name and logged_in_name in all_students:
            selected_student = logged_in_name
            st.info(f"學生帳號：已自動選擇 {selected_student}")
        else:
            st.warning(f"找不到您的資料（{logged_in_name}）")
            return
    else:
        # 教師/管理員可搜尋選擇
        search = st.text_input("搜尋學生姓名", placeholder="輸入姓名搜尋...",
                                key="individual_search")
        if search:
            filtered = [s for s in all_students if search.lower() in s.lower()]
        else:
            filtered = all_students

        if not filtered:
            st.warning("沒有找到符合搜尋條件的學生")
            return

        selected_student = st.selectbox(
            "選擇學生", options=filtered, key="individual_select",
            help=f"共 {len(filtered)} 位學生"
        )

    # ── 顯示該學生 ──
    student_data = df[df[name_col] == selected_student].copy()
    _show_student_detail(student_data, df, selected_student)


def show_ugy_student_analysis():
    """主要入口：從 data_service 取得資料，顯示個別學生分析"""
    df = ds.get_data()

    if df is None or df.empty:
        st.warning("尚無評核資料。請先在 EPA 評核表單提交評核。")
        return

    show_individual_student_analysis(df)
