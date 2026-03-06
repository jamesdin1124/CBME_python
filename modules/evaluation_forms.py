"""
統一評核表單模組

根據科別配置動態渲染評核表單。所有科別共用統一的可信賴程度量表，
但 EPA 項目、評核類型、技能清單依科別而異。

使用方式：
    from modules.evaluation_forms import show_evaluation_form
    show_evaluation_form(department='小兒部')
"""

import streamlit as st
from datetime import date, datetime

from config.department_config import (
    RELIABILITY_OPTIONS, PROFICIENCY_THRESHOLD,
    MEETING_SCORE_OPTIONS, MEETING_SCORE_MAP,
    get_department_config,
)


# ═══════════════════════════════════════════════════════
# 工具函數
# ═══════════════════════════════════════════════════════

def _get_supabase_conn():
    """取得 Supabase 連線實例"""
    from modules.supabase_connection import SupabaseConnection
    return SupabaseConnection()


def _get_active_residents(department=None):
    """從 Supabase 取得啟用中的住院醫師名單"""
    try:
        conn = _get_supabase_conn()
        residents = conn.fetch_pediatric_users(user_type='resident', active_only=True)
        if not residents:
            return []
        if department:
            residents = [r for r in residents if r.get('department') == department]
        return [r['full_name'] for r in residents]
    except Exception:
        return []


def _get_resident_level(resident_name):
    """依住院醫師姓名取得目前級別"""
    try:
        conn = _get_supabase_conn()
        residents = conn.fetch_pediatric_users(user_type='resident', active_only=True)
        for r in residents:
            if r['full_name'] == resident_name:
                return r.get('resident_level', 'R1')
    except Exception:
        pass
    return 'R1'


def _render_header_fields(form_key, department=None):
    """
    共用 header 欄位：評核日期、受評核人員、級職。

    Returns:
        tuple: (evaluation_date, evaluated_resident, resident_level)
    """
    resident_list = _get_active_residents(department)
    manual = not resident_list

    if manual:
        st.warning("尚無已註冊的住院醫師，請先至「帳號管理」新增。您也可以手動輸入姓名。")

    col1, col2, col3 = st.columns(3)
    with col1:
        evaluation_date = st.date_input(
            "評核日期", value=date.today(), key=f"date_{form_key}")
    with col2:
        if manual:
            evaluated_resident = st.text_input(
                "受評核人員姓名", key=f"resident_{form_key}")
        else:
            evaluated_resident = st.selectbox(
                "受評核人員", options=resident_list, key=f"resident_{form_key}")
    with col3:
        default_level = 'R1'
        if not manual and evaluated_resident:
            default_level = _get_resident_level(evaluated_resident)
        level_options = ['R1', 'R2', 'R3']
        resident_level = st.selectbox(
            "評核時級職", options=level_options,
            index=level_options.index(default_level) if default_level in level_options else 0,
            key=f"level_{form_key}")

    return evaluation_date, evaluated_resident, resident_level


def _submit_to_supabase(data):
    """
    統一寫入 Supabase。使用通用的 insert_evaluation()，
    若不存在則 fallback 到 insert_pediatric_evaluation()。

    Returns:
        dict | None: 新增成功回傳記錄
    """
    try:
        conn = _get_supabase_conn()
        # 優先使用通用方法
        if hasattr(conn, 'insert_evaluation'):
            return conn.insert_evaluation(data)
        else:
            return conn.insert_pediatric_evaluation(data)
    except Exception as e:
        st.error(f"提交失敗：{str(e)}")
        return None


# ═══════════════════════════════════════════════════════
# EPA 評估表單
# ═══════════════════════════════════════════════════════

def _show_epa_form(department, dept_config, current_user):
    """EPA 信賴等級評估表單（依科別動態渲染 EPA 項目）"""
    st.subheader("EPA 信賴等級評估表單")

    epa_items = dept_config.get('epa_items', ['病歷紀錄', '當班處置', '住院接診'])
    has_dual = dept_config.get('has_dual_assessment', False)
    min_reqs = dept_config.get('epa_min_requirements', {})

    with st.form(f"epa_form_{department}", clear_on_submit=True):
        evaluation_date, evaluated_resident, resident_level = \
            _render_header_fields(f'epa_{department}', department)

        st.markdown("---")

        # EPA 項目選擇
        if min_reqs:
            epa_item = st.selectbox(
                "EPA 項目", options=epa_items,
                format_func=lambda x: f"{x}（需 {min_reqs.get(x, '?')} 次）" if x in min_reqs else x,
            )
        else:
            epa_item = st.selectbox("EPA 項目", options=epa_items)

        # 教師評量 — 9 級可信賴程度
        st.markdown("### 教師評量 — 可信賴程度")
        reliability_label = st.radio(
            "請選擇該住院醫師在此 EPA 項目的可信賴程度",
            options=list(RELIABILITY_OPTIONS.keys()),
            index=2,
            help="依實際觀察選擇最符合的等級",
            key=f"teacher_rel_{department}",
        )
        score = RELIABILITY_OPTIONS[reliability_label]
        if score >= 4.0:
            st.success(f"對應分數：**{score}** 分 — 高度信賴")
        elif score >= 3.0:
            st.info(f"對應分數：**{score}** 分 — 可獨立執行")
        else:
            st.warning(f"對應分數：**{score}** 分 — 需要監督")

        # 學員自評（雙向評量科別）
        self_score = None
        if has_dual:
            st.markdown("### 學員自評 — 可信賴程度")
            self_label = st.radio(
                "學員自評的可信賴程度（若由學員自行填寫）",
                options=['不適用'] + list(RELIABILITY_OPTIONS.keys()),
                index=0,
                key=f"self_rel_{department}",
            )
            if self_label != '不適用':
                self_score = RELIABILITY_OPTIONS[self_label]

        feedback = st.text_area("EPA 質性回饋", placeholder="請描述具體觀察到的行為表現...")

        submitted = st.form_submit_button("提交 EPA 評估", type="primary")

        if submitted:
            if not evaluated_resident:
                st.error("請選擇或輸入受評核人員")
                return

            user_department = st.session_state.get('user_department', department)
            data = {
                'evaluation_type': 'epa',
                'evaluator_teacher': current_user,
                'evaluation_date': str(evaluation_date),
                'evaluated_resident': evaluated_resident,
                'resident_level': resident_level,
                'evaluation_item': 'EPA',
                'epa_item': epa_item,
                'epa_reliability_level': score,
                'epa_qualitative_feedback': feedback or None,
                'submitted_by': current_user,
                'department': user_department,
            }
            if self_score is not None:
                data['self_assessment_score'] = self_score

            result = _submit_to_supabase(data)
            if result:
                st.success(f"已提交 **{evaluated_resident}** 的 **{epa_item}** EPA 評估！")
                st.balloons()
            else:
                st.error("提交失敗，請檢查網路連線或聯繫管理員")


# ═══════════════════════════════════════════════════════
# 操作技術評核表單
# ═══════════════════════════════════════════════════════

def _show_technical_skill_form(department, dept_config, current_user):
    """操作技術評核表單（依科別載入技能項目）"""
    st.subheader("操作技術評核表單")

    skill_items = dept_config.get('skill_items', {})
    if not skill_items:
        st.info("此科別未設定操作技術項目")
        return

    with st.form(f"tech_form_{department}", clear_on_submit=True):
        evaluation_date, evaluated_resident, resident_level = \
            _render_header_fields(f'tech_{department}', department)

        st.markdown("---")

        skill_names = list(skill_items.keys())
        technical_skill = st.selectbox(
            "評核技術項目",
            options=skill_names,
            format_func=lambda x: f"{x}（需 {skill_items[x]['minimum']} 次）",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            patient_id = st.text_input("病歷號（選填）")
            sedation = st.text_input("鎮靜藥物（選填）")
        with col_b:
            reliability_label = st.selectbox(
                "可信賴程度",
                options=list(RELIABILITY_OPTIONS.keys()),
                index=2,
                help="依觀察到的獨立執行程度選擇",
            )
            _rel_score = RELIABILITY_OPTIONS[reliability_label]
            if _rel_score >= PROFICIENCY_THRESHOLD:
                st.success(f"可信賴分數 **{_rel_score}** — 熟練")
            else:
                st.warning(f"可信賴分數 **{_rel_score}** — 不熟練")

        feedback = st.text_area("操作技術教師回饋", placeholder="請描述住院醫師的操作表現...")

        submitted = st.form_submit_button("提交技術評核", type="primary")

        if submitted:
            if not evaluated_resident:
                st.error("請選擇或輸入受評核人員")
                return

            user_department = st.session_state.get('user_department', department)
            data = {
                'evaluation_type': 'technical_skill',
                'evaluator_teacher': current_user,
                'evaluation_date': str(evaluation_date),
                'evaluated_resident': evaluated_resident,
                'resident_level': resident_level,
                'evaluation_item': '操作技術',
                'patient_id': patient_id or None,
                'technical_skill_item': technical_skill,
                'sedation_medication': sedation or None,
                'reliability_level': RELIABILITY_OPTIONS[reliability_label],
                'proficiency_level': 5 if RELIABILITY_OPTIONS[reliability_label] >= PROFICIENCY_THRESHOLD else 2,
                'technical_feedback': feedback or None,
                'submitted_by': current_user,
                'department': user_department,
            }
            result = _submit_to_supabase(data)
            if result:
                st.success(f"已提交 **{evaluated_resident}** 的 **{technical_skill}** 技術評核！")
                st.balloons()
            else:
                st.error("提交失敗，請檢查網路連線或聯繫管理員")


# ═══════════════════════════════════════════════════════
# 會議報告評核表單
# ═══════════════════════════════════════════════════════

def _show_meeting_report_form(department, current_user):
    """會議報告評核表單（5 維度 1-5 分，全科別通用）"""
    st.subheader("會議報告評核表單")
    st.caption("評核住院醫師的會議報告表現（五維度評分）")

    with st.form(f"meeting_form_{department}", clear_on_submit=True):
        evaluation_date, evaluated_resident, resident_level = \
            _render_header_fields(f'meeting_{department}', department)

        st.markdown("---")

        meeting_name = st.text_input("會議名稱", placeholder="例：晨會、Case Conference...")

        st.markdown("### 五維度評分")
        st.caption("每個維度 1-5 分，5 = 卓越，1 = 不符合期待")

        score_labels = list(reversed(MEETING_SCORE_OPTIONS))

        content = st.select_slider(
            "1. 內容是否充分", options=score_labels, value='3 尚可')
        analysis = st.select_slider(
            "2. 辯證資料的能力", options=score_labels, value='3 尚可')
        presentation = st.select_slider(
            "3. 口條、呈現方式是否清晰", options=score_labels, value='3 尚可')
        innovative = st.select_slider(
            "4. 是否具開創、建設性的想法", options=score_labels, value='3 尚可')
        logical = st.select_slider(
            "5. 回答提問是否具邏輯、有條有理", options=score_labels, value='3 尚可')

        feedback = st.text_area("會議報告教師回饋", placeholder="請描述住院醫師的報告表現...")

        submitted = st.form_submit_button("提交會議報告評核", type="primary")

        if submitted:
            if not evaluated_resident:
                st.error("請選擇或輸入受評核人員")
                return

            user_department = st.session_state.get('user_department', department)
            data = {
                'evaluation_type': 'meeting_report',
                'evaluator_teacher': current_user,
                'evaluation_date': str(evaluation_date),
                'evaluated_resident': evaluated_resident,
                'resident_level': resident_level,
                'evaluation_item': '會議報告',
                'meeting_name': meeting_name or None,
                'content_sufficient': MEETING_SCORE_MAP[content],
                'data_analysis_ability': MEETING_SCORE_MAP[analysis],
                'presentation_clarity': MEETING_SCORE_MAP[presentation],
                'innovative_ideas': MEETING_SCORE_MAP[innovative],
                'logical_response': MEETING_SCORE_MAP[logical],
                'meeting_feedback': feedback or None,
                'submitted_by': current_user,
                'department': user_department,
            }
            result = _submit_to_supabase(data)
            if result:
                avg = (MEETING_SCORE_MAP[content] + MEETING_SCORE_MAP[analysis] +
                       MEETING_SCORE_MAP[presentation] + MEETING_SCORE_MAP[innovative] +
                       MEETING_SCORE_MAP[logical]) / 5
                st.success(f"已提交 **{evaluated_resident}** 的會議報告評核！（平均 {avg:.1f} 分）")
                st.balloons()
            else:
                st.error("提交失敗，請檢查網路連線或聯繫管理員")


# ═══════════════════════════════════════════════════════
# 最近提交記錄
# ═══════════════════════════════════════════════════════

def _show_recent_submissions(department, current_user):
    """顯示當前教師最近提交的評核記錄"""
    try:
        conn = _get_supabase_conn()
        filters = {
            'evaluator_teacher': current_user,
            'department': department,
        }
        if hasattr(conn, 'fetch_evaluations'):
            records = conn.fetch_evaluations(department=department, filters=filters)
        else:
            records = conn.fetch_pediatric_evaluations(filters=filters)

        if not records:
            st.info("尚無提交記錄")
            return

        import pandas as pd
        recent = records[:10]
        df = pd.DataFrame(recent)

        display_cols = ['evaluation_date', 'evaluation_type', 'evaluated_resident']
        extra_cols = ['technical_skill_item', 'epa_item', 'meeting_name']
        available = [c for c in display_cols + extra_cols if c in df.columns]

        if available:
            display_df = df[available].copy()
            type_map = {
                'technical_skill': '操作技術',
                'meeting_report': '會議報告',
                'epa': 'EPA',
            }
            if 'evaluation_type' in display_df.columns:
                display_df['evaluation_type'] = display_df['evaluation_type'].map(type_map).fillna(
                    display_df['evaluation_type'])

            col_rename = {
                'evaluation_date': '評核日期',
                'evaluation_type': '類型',
                'evaluated_resident': '受評核人員',
                'technical_skill_item': '技術項目',
                'epa_item': 'EPA項目',
                'meeting_name': '會議名稱',
            }
            display_df = display_df.rename(columns=col_rename)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("尚無提交記錄")

    except Exception as e:
        st.warning(f"載入最近記錄時發生錯誤：{str(e)}")


# ═══════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════

def show_evaluation_form(department=None):
    """
    統一評核表單入口。
    依科別配置動態渲染可用的表單類型（EPA / 操作技術 / 會議報告）。

    Args:
        department (str, optional): 科別名稱。
            若為 None，會使用 session_state 中的 user_department，
            或讓使用者從下拉選單選擇。
    """
    # 確定科別
    if department is None:
        department = st.session_state.get('user_department')

    if department is None:
        from config.department_config import ALL_DEPARTMENTS
        department = st.selectbox("選擇科別", options=ALL_DEPARTMENTS,
                                  key="eval_form_dept_selector")

    # 確定當前使用者
    current_user = st.session_state.get('user_name', st.session_state.get('username', '未知'))

    # 取得科別配置
    dept_config = get_department_config(department)
    eval_types = dept_config.get('evaluation_types', ['epa'])

    st.markdown(f"### 線上評核表單 — {department}")
    st.caption(f"評核者：{current_user}")

    # 動態建立 tabs
    tab_labels = []
    tab_funcs = []

    if 'epa' in eval_types:
        tab_labels.append("EPA 評估")
        tab_funcs.append(('epa', dept_config))
    if 'technical_skill' in eval_types:
        tab_labels.append("操作技術")
        tab_funcs.append(('tech', dept_config))
    if 'meeting_report' in eval_types:
        tab_labels.append("會議報告")
        tab_funcs.append(('meeting', None))

    if len(tab_labels) == 0:
        st.info("此科別尚未設定評核表單")
        return

    tabs = st.tabs(tab_labels)

    for i, (form_type, config) in enumerate(tab_funcs):
        with tabs[i]:
            if form_type == 'epa':
                _show_epa_form(department, config, current_user)
            elif form_type == 'tech':
                _show_technical_skill_form(department, config, current_user)
            elif form_type == 'meeting':
                _show_meeting_report_form(department, current_user)

    # 最近提交記錄
    st.markdown("---")
    with st.expander("最近提交的評核記錄（最新 10 筆）"):
        _show_recent_submissions(department, current_user)
