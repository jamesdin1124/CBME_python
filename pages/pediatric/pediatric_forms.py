"""
兒科 CCC 評估系統 — 自訂評核表單
提供操作技術、會議報告、EPA 三類評核表單，
資料直接寫入 Supabase。
"""

import streamlit as st
from datetime import date, datetime

# ─── 共用常數（與 pediatric_analysis.py 一致）───

PEDIATRIC_SKILL_REQUIREMENTS = {
    '插氣管內管': {'minimum': 3, 'description': '訓練期間最少3次'},
    '插臍(動靜脈)導管': {'minimum': 1, 'description': '訓練期間最少1次'},
    '腰椎穿刺': {'minimum': 3, 'description': 'PGY2/R1 訓練期間最少3次'},
    '插中心靜脈導管(CVC)': {'minimum': 3, 'description': '訓練期間最少3次'},
    '肋膜液或是腹水抽取': {'minimum': 1, 'description': '訓練期間最少1次'},
    '插胸管': {'minimum': 2, 'description': '訓練期間最少2次'},
    '放置動脈導管': {'minimum': 2, 'description': '訓練期間最少2次'},
    '經皮式中央靜脈導管(PICC)': {'minimum': 3, 'description': '訓練期間最少3次'},
    '腦部超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '心臟超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '腹部超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '腎臟超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    'APLS': {'minimum': 3, 'description': '訓練期間最少3次'},
    'NRP': {'minimum': 5, 'description': '訓練期間最少5次'},
    'CVVH照護': {'minimum': 1, 'description': '訓練期間最少1次'},
    'ECMO照護': {'minimum': 1, 'description': '訓練期間最少1次'},
}

PEDIATRIC_EPA_ITEMS = ['病人日常照護', '緊急照護處置', '病歷書寫']

# 9 級可信賴程度（兒科表單標準選項 1.5–5.0）
RELIABILITY_OPTIONS = {
    '允許住院醫師在旁觀察': 1.5,
    '教師在旁逐步共同操作': 2.0,
    '教師在旁必要時協助': 2.5,
    '教師可立即到場協助，事後逐項確認': 3.0,
    '教師可立即到場協助，事後重點確認': 3.3,
    '教師可稍後到場協助，必要時事後確認': 3.6,
    '教師on call提供監督': 4.0,
    '教師不需on call，事後提供回饋及監督': 4.5,
    '學員可對其他資淺的學員進行監督與教學': 5.0,
}

# 會議報告 5 分制
MEETING_SCORE_OPTIONS = [
    '5 卓越', '4 充分', '3 尚可', '2 稍差', '1 不符合期待'
]

MEETING_SCORE_MAP = {
    '5 卓越': 5, '4 充分': 4, '3 尚可': 3,
    '2 稍差': 2, '1 不符合期待': 1,
}

# 熟練程度 5 分制
PROFICIENCY_OPTIONS = {
    '熟練': 5, '基本熟練': 4, '部分熟練': 3,
    '初學': 2, '不熟練': 1,
}


# ─── 工具函數 ───

def _get_active_residents(supabase_conn):
    """從 Supabase 取得啟用中的住院醫師名單"""
    try:
        residents = supabase_conn.fetch_pediatric_users(user_type='resident', active_only=True)
        return [r['full_name'] for r in residents] if residents else []
    except Exception:
        return []


def _get_resident_level(supabase_conn, resident_name):
    """依住院醫師姓名取得目前級別"""
    try:
        residents = supabase_conn.fetch_pediatric_users(user_type='resident', active_only=True)
        for r in residents:
            if r['full_name'] == resident_name:
                return r.get('resident_level', 'R1')
    except Exception:
        pass
    return 'R1'


def _common_header_fields(supabase_conn, form_key):
    """
    每個表單共用的 header 欄位：評核日期、受評核人員、級職。
    回傳 (evaluation_date, evaluated_resident, resident_level)。
    """
    resident_list = _get_active_residents(supabase_conn)
    if not resident_list:
        st.warning("尚無已註冊的住院醫師，請先至「帳號管理」新增住院醫師。您也可以手動輸入姓名。")
        manual = True
    else:
        manual = False

    col1, col2, col3 = st.columns(3)
    with col1:
        evaluation_date = st.date_input("評核日期", value=date.today(), key=f"date_{form_key}")
    with col2:
        if manual:
            evaluated_resident = st.text_input("受評核人員姓名", key=f"resident_{form_key}")
        else:
            evaluated_resident = st.selectbox(
                "受評核人員", options=resident_list, key=f"resident_{form_key}")
    with col3:
        # 自動帶入級職，但可手動修改
        default_level = 'R1'
        if not manual and evaluated_resident:
            default_level = _get_resident_level(supabase_conn, evaluated_resident)
        level_options = ['R1', 'R2', 'R3']
        resident_level = st.selectbox(
            "評核時級職", options=level_options,
            index=level_options.index(default_level) if default_level in level_options else 0,
            key=f"level_{form_key}")

    return evaluation_date, evaluated_resident, resident_level


# ─── 表單 1：操作技術評核 ───

def show_technical_skill_form(supabase_conn, current_user):
    """操作技術評核表單（16 項技能）"""
    st.subheader("🔧 操作技術評核表單")
    st.caption("評核住院醫師的各項操作技術執行能力")

    with st.form("technical_skill_form", clear_on_submit=True):
        evaluation_date, evaluated_resident, resident_level = \
            _common_header_fields(supabase_conn, 'tech')

        st.markdown("---")

        # 技術項目
        skill_names = list(PEDIATRIC_SKILL_REQUIREMENTS.keys())
        technical_skill = st.selectbox(
            "評核技術項目",
            options=skill_names,
            format_func=lambda x: f"{x}（需 {PEDIATRIC_SKILL_REQUIREMENTS[x]['minimum']} 次）",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            patient_id = st.text_input("病歷號（選填）")
            sedation = st.text_input("鎮靜藥物（選填）")
        with col_b:
            # 9 級可信賴程度
            reliability_label = st.selectbox(
                "可信賴程度",
                options=list(RELIABILITY_OPTIONS.keys()),
                index=2,  # 預設「教師在旁必要時協助」
                help="依觀察到的獨立執行程度選擇"
            )
            # 熟練程度
            proficiency_label = st.selectbox(
                "熟練程度",
                options=list(PROFICIENCY_OPTIONS.keys()),
                index=2,  # 預設「部分熟練」
            )

        feedback = st.text_area("操作技術教師回饋", placeholder="請描述住院醫師的操作表現...")

        submitted = st.form_submit_button("📤 提交技術評核", type="primary")

        if submitted:
            if not evaluated_resident:
                st.error("請選擇或輸入受評核人員")
                return
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
                'proficiency_level': PROFICIENCY_OPTIONS[proficiency_label],
                'technical_feedback': feedback or None,
                'submitted_by': current_user,
            }
            result = supabase_conn.insert_pediatric_evaluation(data)
            if result:
                st.success(f"✅ 已提交 **{evaluated_resident}** 的 **{technical_skill}** 技術評核！")
                st.balloons()
            else:
                st.error("❌ 提交失敗，請檢查網路連線或聯繫管理員")


# ─── 表單 2：會議報告評核 ───

def show_meeting_report_form(supabase_conn, current_user):
    """會議報告評核表單（5 維度 1-5 分）"""
    st.subheader("📑 會議報告評核表單")
    st.caption("評核住院醫師的會議報告表現（五維度評分）")

    with st.form("meeting_report_form", clear_on_submit=True):
        evaluation_date, evaluated_resident, resident_level = \
            _common_header_fields(supabase_conn, 'meeting')

        st.markdown("---")

        meeting_name = st.text_input("會議名稱", placeholder="例：兒科晨會、Case Conference...")

        st.markdown("### 📊 五維度評分")
        st.caption("每個維度 1-5 分，5 = 卓越，1 = 不符合期待")

        # 五維度使用 select_slider 呈現
        score_labels = list(reversed(MEETING_SCORE_OPTIONS))  # 1→5

        content = st.select_slider(
            "1️⃣ 內容是否充分",
            options=score_labels, value='3 尚可')
        analysis = st.select_slider(
            "2️⃣ 辯證資料的能力",
            options=score_labels, value='3 尚可')
        presentation = st.select_slider(
            "3️⃣ 口條、呈現方式是否清晰",
            options=score_labels, value='3 尚可')
        innovative = st.select_slider(
            "4️⃣ 是否具開創、建設性的想法",
            options=score_labels, value='3 尚可')
        logical = st.select_slider(
            "5️⃣ 回答提問是否具邏輯、有條有理",
            options=score_labels, value='3 尚可')

        feedback = st.text_area("會議報告教師回饋", placeholder="請描述住院醫師的報告表現...")

        submitted = st.form_submit_button("📤 提交會議報告評核", type="primary")

        if submitted:
            if not evaluated_resident:
                st.error("請選擇或輸入受評核人員")
                return
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
            }
            result = supabase_conn.insert_pediatric_evaluation(data)
            if result:
                avg = (MEETING_SCORE_MAP[content] + MEETING_SCORE_MAP[analysis] +
                       MEETING_SCORE_MAP[presentation] + MEETING_SCORE_MAP[innovative] +
                       MEETING_SCORE_MAP[logical]) / 5
                st.success(f"✅ 已提交 **{evaluated_resident}** 的會議報告評核！（平均 {avg:.1f} 分）")
                st.balloons()
            else:
                st.error("❌ 提交失敗，請檢查網路連線或聯繫管理員")


# ─── 表單 3：EPA 信賴等級評估 ───

def show_epa_form(supabase_conn, current_user):
    """EPA 信賴等級評估表單（3 項 EPA）"""
    st.subheader("🎯 EPA 信賴等級評估表單")
    st.caption("Entrustable Professional Activities — 可信賴專業活動評估")

    with st.form("epa_form", clear_on_submit=True):
        evaluation_date, evaluated_resident, resident_level = \
            _common_header_fields(supabase_conn, 'epa')

        st.markdown("---")

        # EPA 項目
        epa_item = st.selectbox("EPA 項目", options=PEDIATRIC_EPA_ITEMS)

        # 9 級可信賴程度
        st.markdown("### 可信賴程度")
        reliability_label = st.radio(
            "請選擇該住院醫師在此 EPA 項目的可信賴程度",
            options=list(RELIABILITY_OPTIONS.keys()),
            index=2,  # 預設「教師在旁必要時協助」
            help="依實際觀察選擇最符合的等級"
        )

        # 顯示對應分數
        score = RELIABILITY_OPTIONS[reliability_label]
        if score >= 4.0:
            st.success(f"📊 對應分數：**{score}** 分 — 高度信賴")
        elif score >= 3.0:
            st.info(f"📊 對應分數：**{score}** 分 — 可獨立執行")
        else:
            st.warning(f"📊 對應分數：**{score}** 分 — 需要監督")

        feedback = st.text_area("EPA 質性回饋", placeholder="請描述具體觀察到的行為表現...")

        submitted = st.form_submit_button("📤 提交 EPA 評估", type="primary")

        if submitted:
            if not evaluated_resident:
                st.error("請選擇或輸入受評核人員")
                return
            data = {
                'evaluation_type': 'epa',
                'evaluator_teacher': current_user,
                'evaluation_date': str(evaluation_date),
                'evaluated_resident': evaluated_resident,
                'resident_level': resident_level,
                'evaluation_item': 'EPA',
                'epa_item': epa_item,
                'epa_reliability_level': RELIABILITY_OPTIONS[reliability_label],
                'epa_qualitative_feedback': feedback or None,
                'submitted_by': current_user,
            }
            result = supabase_conn.insert_pediatric_evaluation(data)
            if result:
                st.success(f"✅ 已提交 **{evaluated_resident}** 的 **{epa_item}** EPA 評估！")
                st.balloons()
            else:
                st.error("❌ 提交失敗，請檢查網路連線或聯繫管理員")


# ─── 主入口：顯示所有表單 ───

def show_evaluation_forms_tab(supabase_conn, current_user):
    """
    評核表單 Tab 的主入口。
    以 sub-tabs 呈現三種表單。

    Args:
        supabase_conn: SupabaseConnection 實例
        current_user (str): 當前登入的使用者姓名
    """
    st.markdown("### ✏️ 線上評核表單")
    st.caption("取代 Google Forms，直接在系統內完成評核並即時儲存到資料庫。")

    sub1, sub2, sub3 = st.tabs([
        "🔧 操作技術", "📑 會議報告", "🎯 EPA 評估"
    ])

    with sub1:
        show_technical_skill_form(supabase_conn, current_user)
    with sub2:
        show_meeting_report_form(supabase_conn, current_user)
    with sub3:
        show_epa_form(supabase_conn, current_user)

    # 最近提交記錄（快速確認）
    st.markdown("---")
    with st.expander("📋 最近提交的評核記錄（最新 10 筆）"):
        _show_recent_submissions(supabase_conn, current_user)


def _show_recent_submissions(supabase_conn, current_user):
    """顯示當前教師最近提交的評核記錄"""
    try:
        records = supabase_conn.fetch_pediatric_evaluations(
            filters={'evaluator_teacher': current_user}
        )
        if not records:
            st.info("尚無提交記錄")
            return

        import pandas as pd
        recent = records[:10]
        df = pd.DataFrame(recent)

        # 簡化顯示欄位
        display_cols = ['evaluation_date', 'evaluation_type', 'evaluated_resident']
        extra_cols = []
        if 'technical_skill_item' in df.columns:
            extra_cols.append('technical_skill_item')
        if 'epa_item' in df.columns:
            extra_cols.append('epa_item')
        if 'meeting_name' in df.columns:
            extra_cols.append('meeting_name')

        available = [c for c in display_cols + extra_cols if c in df.columns]
        if available:
            display_df = df[available].copy()
            # 翻譯 evaluation_type
            type_map = {
                'technical_skill': '操作技術',
                'meeting_report': '會議報告',
                'epa': 'EPA'
            }
            if 'evaluation_type' in display_df.columns:
                display_df['evaluation_type'] = display_df['evaluation_type'].map(type_map).fillna(display_df['evaluation_type'])
            display_df.columns = [
                c.replace('evaluation_date', '評核日期')
                 .replace('evaluation_type', '類型')
                 .replace('evaluated_resident', '受評核人員')
                 .replace('technical_skill_item', '技術項目')
                 .replace('epa_item', 'EPA項目')
                 .replace('meeting_name', '會議名稱')
                for c in display_df.columns
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("尚無提交記錄")
    except Exception as e:
        st.warning(f"載入最近記錄時發生錯誤：{str(e)}")
