"""
UGY 學生個人成績查詢入口

功能：
- 學生以身分證字號+學號登入
- 查看自己的 EPA 評核紀錄
- 各 EPA 項目分數趨勢圖
- 科部別分析
- 教師回饋彙整
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config.epa_constants import EPA_LEVEL_MAPPING


def _get_supabase_conn():
    from modules.supabase_connection import SupabaseConnection
    return SupabaseConnection()


def _fetch_student_epa_records(student_name):
    """查詢某位學生的所有 EPA 紀錄"""
    try:
        conn = _get_supabase_conn()
        # 先嘗試 ugy_epa_records 表
        try:
            result = conn.client.table('ugy_epa_records').select('*').eq(
                '學員姓名', student_name
            ).order('時間戳記', desc=True).execute()
            if result.data:
                return pd.DataFrame(result.data)
        except Exception:
            pass

        # Fallback: 從 pediatric_evaluations 查 ugy_epa 類型
        try:
            result = conn.client.table('pediatric_evaluations').select('*').eq(
                'evaluated_resident', student_name
            ).eq('evaluation_type', 'ugy_epa').order('evaluation_date', desc=True).execute()
            if result.data:
                df = pd.DataFrame(result.data)
                # 欄位轉換以相容
                col_map = {
                    'evaluated_resident': '學員姓名',
                    'epa_item': 'EPA評核項目',
                    'epa_reliability_level': '教師評核EPA等級_數值',
                    'epa_qualitative_feedback': '回饋',
                    'evaluator_teacher': '教師',
                    'department': '實習科部',
                    'resident_level': '階層',
                    'evaluation_date': 'evaluation_date',
                }
                df = df.rename(columns=col_map)
                return df
        except Exception:
            pass

        return pd.DataFrame()

    except Exception as e:
        st.error(f"查詢失敗：{str(e)}")
        return pd.DataFrame()


def _level_to_score(level_str):
    """將文字等級轉為數值"""
    if pd.isna(level_str):
        return None
    if isinstance(level_str, (int, float)):
        return float(level_str)
    return EPA_LEVEL_MAPPING.get(str(level_str).strip(), None)


# ═══════════════════════════════════════════════════════
# 個人成績面板
# ═══════════════════════════════════════════════════════

def _show_student_dashboard(student_name, student_info=None):
    """顯示學生個人 EPA 成績面板"""
    st.markdown(f"### 📊 {student_name} 的 EPA 評核紀錄")

    df = _fetch_student_epa_records(student_name)

    if df.empty:
        st.info("目前尚無 EPA 評核紀錄。")
        return

    # 確保有數值欄位
    if '教師評核EPA等級_數值' not in df.columns and '教師評核EPA等級' in df.columns:
        df['教師評核EPA等級_數值'] = df['教師評核EPA等級'].apply(_level_to_score)

    score_col = '教師評核EPA等級_數值'
    if score_col not in df.columns:
        st.warning("缺少分數資料。")
        st.dataframe(df)
        return

    df[score_col] = pd.to_numeric(df[score_col], errors='coerce')

    # ── 總覽統計 ──
    st.markdown("#### 總覽")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總評核次數", len(df))
    valid_scores = df[score_col].dropna()
    col2.metric("平均分數", f"{valid_scores.mean():.2f}" if len(valid_scores) > 0 else "N/A")
    col3.metric("最高分數", f"{valid_scores.max():.1f}" if len(valid_scores) > 0 else "N/A")

    if 'EPA評核項目' in df.columns:
        col4.metric("評核項目數", df['EPA評核項目'].nunique())

    # ── 各 EPA 項目平均分數 ──
    if 'EPA評核項目' in df.columns:
        st.markdown("#### 各 EPA 項目平均分數")
        epa_avg = df.groupby('EPA評核項目')[score_col].agg(['mean', 'count']).reset_index()
        epa_avg.columns = ['EPA項目', '平均分數', '次數']
        epa_avg = epa_avg.sort_values('平均分數', ascending=False)

        fig_bar = px.bar(
            epa_avg, x='EPA項目', y='平均分數',
            text='次數', color='平均分數',
            color_continuous_scale='Blues',
            labels={'平均分數': '平均 EPA 分數', '次數': '評核次數'}
        )
        fig_bar.update_traces(texttemplate='n=%{text}', textposition='outside')
        fig_bar.update_layout(yaxis_range=[0, 5.5], height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── 科部別分析 ──
    if '實習科部' in df.columns:
        st.markdown("#### 各科部平均分數")
        dept_avg = df.groupby('實習科部')[score_col].agg(['mean', 'count']).reset_index()
        dept_avg.columns = ['科部', '平均分數', '次數']

        fig_dept = px.bar(
            dept_avg, x='科部', y='平均分數',
            text='次數', color='科部',
        )
        fig_dept.update_traces(texttemplate='n=%{text}', textposition='outside')
        fig_dept.update_layout(yaxis_range=[0, 5.5], height=350, showlegend=False)
        st.plotly_chart(fig_dept, use_container_width=True)

    # ── 時間趨勢圖 ──
    date_col = None
    for c in ['evaluation_date', '時間戳記', '評核日期']:
        if c in df.columns:
            date_col = c
            break

    if date_col:
        st.markdown("#### EPA 分數趨勢")
        df_trend = df.copy()
        df_trend[date_col] = pd.to_datetime(df_trend[date_col], errors='coerce')
        df_trend = df_trend.dropna(subset=[date_col, score_col])
        df_trend = df_trend.sort_values(date_col)

        if not df_trend.empty:
            if 'EPA評核項目' in df_trend.columns:
                fig_trend = px.scatter(
                    df_trend, x=date_col, y=score_col,
                    color='EPA評核項目',
                    trendline='lowess',
                    labels={score_col: 'EPA 等級分數', date_col: '日期'},
                )
            else:
                fig_trend = px.scatter(
                    df_trend, x=date_col, y=score_col,
                    trendline='lowess',
                    labels={score_col: 'EPA 等級分數', date_col: '日期'},
                )
            fig_trend.update_layout(yaxis_range=[0, 5.5], height=400)
            st.plotly_chart(fig_trend, use_container_width=True)

    # ── 雷達圖（如果有多項 EPA） ──
    if 'EPA評核項目' in df.columns and df['EPA評核項目'].nunique() >= 3:
        st.markdown("#### EPA 能力雷達圖")
        radar_data = df.groupby('EPA評核項目')[score_col].mean().reset_index()
        radar_data.columns = ['EPA項目', '平均分數']

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_data['平均分數'].tolist() + [radar_data['平均分數'].iloc[0]],
            theta=radar_data['EPA項目'].tolist() + [radar_data['EPA項目'].iloc[0]],
            fill='toself',
            name=student_name
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            height=400
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # ── 教師回饋列表 ──
    st.markdown("#### 教師回饋紀錄")
    feedback_cols = []
    for c in ['evaluation_date', '時間戳記', 'EPA評核項目', '教師評核EPA等級',
              score_col, '回饋', '教師', '實習科部', '病人難度']:
        if c in df.columns:
            feedback_cols.append(c)

    if feedback_cols:
        st.dataframe(
            df[feedback_cols].sort_values(
                feedback_cols[0], ascending=False
            ),
            use_container_width=True,
            height=400
        )


# ═══════════════════════════════════════════════════════
# 學生登入入口（獨立使用時）
# ═══════════════════════════════════════════════════════

def show_student_login_and_portal():
    """
    學生登入 + 成績查詢（可在 student role 下直接使用）。
    若學生已登入（session_state 中有資料），直接顯示面板。
    """
    # 檢查是否已登入
    if st.session_state.get('role') == 'student' and st.session_state.get('user_name'):
        _show_student_dashboard(st.session_state['user_name'])
        return

    # 未登入：顯示登入表單
    st.subheader("🔑 UGY 學生成績查詢")
    st.info("請使用 **身分證字號** 和 **學號** 登入查看個人 EPA 成績。")

    with st.form("student_login_form"):
        nid = st.text_input("身分證字號（帳號）")
        sid = st.text_input("學號（密碼）", type="password")
        login_btn = st.form_submit_button("登入查詢", type="primary")

    if login_btn:
        if not nid or not sid:
            st.error("請輸入身分證字號和學號")
            return

        from modules.auth import authenticate_user
        user_info = authenticate_user(nid, sid)

        if user_info and user_info.get('role') == 'student':
            st.session_state['role'] = 'student'
            st.session_state['user_name'] = user_info['name']
            st.session_state['username'] = nid
            st.session_state['student_id'] = user_info.get('student_id')
            st.rerun()
        elif user_info:
            # 非學生角色也允許查看（教師等）
            st.session_state['temp_student_view'] = user_info['name']
            _show_student_dashboard(user_info['name'])
        else:
            st.error("登入失敗：帳號或密碼錯誤。請確認身分證字號和學號是否正確。")


def show_student_portal_for_logged_in():
    """
    已登入的學生角色直接查看成績（整合到 dashboard 用）
    """
    student_name = st.session_state.get('user_name')
    if student_name:
        _show_student_dashboard(student_name)
    else:
        st.warning("無法取得學生姓名，請重新登入。")
