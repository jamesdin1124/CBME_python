"""
UGY 學生總覽
精簡版：資料邏輯委託 ugy_data_service，本檔只負責 UI 和視覺化。
"""

import pandas as pd
import streamlit as st
from datetime import date, timedelta

from pages.ugy import ugy_data_service as ds
from pages.ugy.ugy_chart_helpers import create_peer_comparison_radar, create_peer_comparison_trend
from modules.visualization.dept_charts import create_dept_grade_percentage_chart
from modules.visualization.radar_trend import create_layer_radar_chart, create_epa_trend_charts


# ═══════════════════════════════════════════════════════
# 向後相容：其他模組可能 import 這些
# ═══════════════════════════════════════════════════════
def _fetch_supabase_epa_records():
    return ds.fetch_supabase_records()

def _fix_student_ids(df):
    return ds.fix_student_ids(df)

def _auto_load_supabase_data():
    return ds.load_all_data(include_google_sheets=False)


# ═══════════════════════════════════════════════════════
# 篩選 UI
# ═══════════════════════════════════════════════════════

def _date_range_filter(df: pd.DataFrame) -> pd.DataFrame:
    """用開始/結束日期篩選梯次"""
    if '梯次' not in df.columns:
        return df

    valid_batches = [b for b in df['梯次'].dropna().unique()
                     if b and b != '未知梯次' and b != 'None']
    if not valid_batches:
        return df

    # 解析梯次日期以計算範圍
    try:
        batch_dates = pd.to_datetime(valid_batches, errors='coerce').dropna()
        if batch_dates.empty:
            return df
        min_date = batch_dates.min().date()
        max_date = batch_dates.max().date() + timedelta(days=14)
    except Exception:
        return df

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=min_date, key="overview_start_date")
    with col2:
        end_date = st.date_input("結束日期", value=max_date, key="overview_end_date")

    # 篩選梯次在日期範圍內
    def batch_in_range(batch_str):
        try:
            bd = pd.to_datetime(batch_str)
            return start_date <= bd.date() <= end_date
        except Exception:
            return False

    mask = df['梯次'].apply(batch_in_range)
    return df[mask].copy()


def _multiselect_filter(df: pd.DataFrame, col: str, label: str, key: str,
                        exclude_values=None) -> pd.DataFrame:
    """通用 multiselect 篩選器"""
    if col not in df.columns:
        return df

    exclude = exclude_values or ['未知', '未知梯次', 'None', 'nan', '']
    options = sorted([v for v in df[col].dropna().unique().tolist()
                      if v and str(v) not in exclude])
    if not options:
        return df

    selected = st.multiselect(label, options=options, default=options,
                              format_func=lambda x: f"{x}", key=key)
    if not selected:
        st.warning(f"請選擇至少一個{label}")
        return pd.DataFrame()

    return df[df[col].isin(selected)].copy()


# ═══════════════════════════════════════════════════════
# 視覺化
# ═══════════════════════════════════════════════════════

def _display_overview_charts(df: pd.DataFrame, selected_layers: list):
    """顯示學生總覽的所有圖表"""
    if df.empty:
        st.warning("篩選後無資料可顯示")
        return

    # 1. 科部分布圖
    dept_col = '實習科部' if '實習科部' in df.columns else (
        '訓練科部' if '訓練科部' in df.columns else None
    )
    if dept_col and '教師評核EPA等級_數值' in df.columns:
        st.subheader("各實習科部教師評核等級分布")
        try:
            fig_pct, fig_qty = create_dept_grade_percentage_chart(df, dept_col)
            st.plotly_chart(fig_qty, use_container_width=True, key="overview_dept_qty")
            st.plotly_chart(fig_pct, use_container_width=True, key="overview_dept_pct")
        except Exception as e:
            st.warning(f"科部分布圖繪製失敗：{e}")

    # 2. 各階層雷達圖
    if selected_layers and '階層' in df.columns:
        st.subheader("各階層 EPA 評核雷達圖")
        try:
            radar_fig = create_layer_radar_chart(df, selected_layers)
            st.plotly_chart(radar_fig, use_container_width=True, key="overview_radar")
        except Exception as e:
            st.warning(f"雷達圖繪製失敗：{e}")

    # 3. 各階層趨勢圖
    if selected_layers and '梯次' in df.columns:
        st.subheader("EPA 評核趨勢分析")
        for layer in selected_layers:
            layer_df = df[df['階層'] == layer]
            if layer_df.empty:
                continue
            st.caption(f"階層 {layer} 的 EPA 評核趨勢")
            try:
                # 用同儕趨勢圖展示（整體階層）
                sorted_batches = sorted(layer_df['梯次'].dropna().unique().tolist())
                batch_orders = {layer: sorted_batches}
                trend_figs = create_epa_trend_charts(
                    layer_df, [layer], batch_orders, sorted_batches
                )
                if trend_figs:
                    st.plotly_chart(trend_figs[0], use_container_width=True,
                                   key=f"overview_trend_{layer}")
            except Exception as e:
                st.warning(f"階層 {layer} 趨勢圖繪製失敗：{e}")


# ═══════════════════════════════════════════════════════
# 主函數
# ═══════════════════════════════════════════════════════

def show_ugy_student_overview():
    """顯示 UGY 學生總覽"""
    st.title("UGY EPA 分析")

    # ── 載入資料 ──
    df = ds.get_data()

    # 手動重新載入按鈕
    if st.button("🔄 重新載入資料（系統評核 + Google Sheet）"):
        with st.spinner("載入中..."):
            df = ds.refresh(include_google_sheets=True)
        if df is not None:
            st.success(f"✅ 載入完成，共 {len(df)} 筆資料")
        else:
            st.error("載入失敗")

    if df is None or df.empty:
        st.info("尚無評核資料。請先在 EPA 評核表單提交評核，或按上方按鈕載入 Google Sheet 資料。")
        return

    # ── 只顯示有教師評核的資料 ──
    filter_teacher = st.checkbox("只顯示有教師評核的資料", value=True,
                                  key="overview_filter_teacher")
    if filter_teacher and '教師' in df.columns:
        df = df[df['教師'].notna() & (df['教師'] != '')]

    st.info(f"共 {len(df)} 筆評核資料")

    # ── 篩選 ──
    # 科部
    df = _multiselect_filter(df, '實習科部', '選擇實習科部', 'overview_dept')
    if df.empty:
        return

    # 日期範圍
    df = _date_range_filter(df)
    if df.empty:
        st.warning("所選日期範圍內無資料")
        return

    # 階層
    selected_layers = []
    if '階層' in df.columns:
        valid_layers = sorted([l for l in df['階層'].dropna().unique()
                               if l and l != '未知' and l != 'None'])
        if valid_layers:
            selected_layers = st.multiselect(
                "選擇階層", options=valid_layers, default=valid_layers,
                key="overview_layers"
            )
            if selected_layers:
                df = df[df['階層'].isin(selected_layers)].copy()

    # EPA 項目
    if 'EPA評核項目' in df.columns:
        all_items = sorted(df['EPA評核項目'].dropna().unique().tolist())
        default_items = ['當班處置'] if '當班處置' in all_items else all_items[:1]
        selected_items = st.multiselect(
            "選擇 EPA 評核項目", options=all_items, default=default_items,
            key="overview_epa_items"
        )
        if selected_items:
            df = df[df['EPA評核項目'].isin(selected_items)].copy()

    # ── 資料預覽 ──
    with st.expander("📊 目前分析用資料", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── 圖表 ──
    _display_overview_charts(df, selected_layers)
