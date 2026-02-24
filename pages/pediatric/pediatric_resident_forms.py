"""
兒科住院醫師自填表單
提供研究進度、學習反思兩類表單，資料直接寫入 Supabase。
"""

import streamlit as st
from datetime import date, datetime

# ─── 共用常數 ───

RESEARCH_TYPES = ['個案報告', '原著論文', '系統性回顧', '文獻回顧', '其他']
RESEARCH_STATUS = ['構思中', '撰寫中', '投稿中', '接受']

REFLECTION_TYPES = ['臨床反思', '學習心得', '個案討論', '技能學習', '其他']

# EPA 項目（與 pediatric_forms.py 一致）
PEDIATRIC_EPA_ITEMS = ['病人日常照護', '緊急照護處置', '病歷書寫']

# 技能項目（16 項）
PEDIATRIC_SKILL_ITEMS = [
    '插氣管內管', '插臍(動靜脈)導管', '腰椎穿刺', '插中心靜脈導管(CVC)',
    '肋膜液或是腹水抽取', '插胸管', '放置動脈導管', '經皮式中央靜脈導管(PICC)',
    '腦部超音波', '心臟超音波', '腹部超音波', '腎臟超音波',
    'APLS', 'NRP', 'CVVH照護', 'ECMO照護'
]

# 反思標籤選項
REFLECTION_TAGS = [
    '溝通技巧', '臨床決策', '團隊合作', '病人安全',
    '醫病關係', '情緒管理', '壓力調適', '專業成長'
]


# ─── 工具函數 ───

def _get_current_resident_info(supabase_conn, current_user):
    """
    取得目前登入住院醫師的資訊（姓名、級別）

    Args:
        supabase_conn: Supabase 連線
        current_user (str): 登入使用者名稱

    Returns:
        dict: {'name': str, 'level': str} 或 None
    """
    try:
        residents = supabase_conn.fetch_pediatric_users(user_type='resident', active_only=True)
        for r in residents:
            if r.get('username') == current_user or r.get('full_name') == current_user:
                return {
                    'name': r['full_name'],
                    'level': r.get('resident_level', 'R1')
                }
    except Exception:
        pass
    return None


def _get_teacher_list(supabase_conn):
    """取得教師名單（供指導老師/督導教師選擇）"""
    try:
        teachers = supabase_conn.fetch_pediatric_users(user_type='teacher', active_only=True)
        return [t['full_name'] for t in teachers] if teachers else []
    except Exception:
        return []


# ─── 表單 1：研究進度 ───

def show_research_progress_form(supabase_conn, current_user):
    """住院醫師研究進度填寫表單"""
    st.subheader("📚 研究進度登記")
    st.caption("記錄您的研究計畫進度，包含文獻回顧、個案報告、原著論文等。")

    resident_info = _get_current_resident_info(supabase_conn, current_user)
    if not resident_info:
        st.warning("⚠️ 無法取得您的住院醫師資料，請聯繫管理員或確認您的帳號設定。")
        return

    resident_name = resident_info['name']
    resident_level = resident_info['level']

    # 顯示目前已登記的研究（可編輯）
    with st.expander("📋 我的研究清單", expanded=False):
        _show_my_research_list(supabase_conn, resident_name)

    st.markdown("---")
    st.markdown("### 新增研究進度")

    with st.form("research_progress_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            research_title = st.text_input("研究名稱 *", placeholder="例：新生兒敗血症之臨床分析")
            research_type = st.selectbox("文獻類型 *", options=RESEARCH_TYPES)
        with col2:
            teacher_list = _get_teacher_list(supabase_conn)
            if teacher_list:
                supervisor_name = st.selectbox("指導老師", options=[''] + teacher_list)
            else:
                supervisor_name = st.text_input("指導老師", placeholder="請輸入指導老師姓名")
            current_status = st.selectbox("目前進度 *", options=RESEARCH_STATUS, index=0)

        st.markdown("#### 詳細資訊（選填）")

        col_a, col_b = st.columns(2)
        with col_a:
            research_topic = st.text_input("研究主題/領域", placeholder="例：小兒感染")
            target_journal = st.text_input("目標期刊", placeholder="例：Taiwan Journal of Pediatrics")
        with col_b:
            submission_date = st.date_input("投稿日期（若已投稿）", value=None)
            acceptance_date = st.date_input("接受日期（若已接受）", value=None)

        progress_notes = st.text_area(
            "進度說明",
            placeholder="請描述目前進度，例：已完成文獻回顧，正在撰寫方法章節...",
            height=100
        )
        challenges = st.text_area(
            "遭遇困難（選填）",
            placeholder="研究過程中遇到的問題或挑戰...",
            height=80
        )
        next_steps = st.text_area(
            "下一步計畫（選填）",
            placeholder="接下來預計進行的工作...",
            height=80
        )

        submitted = st.form_submit_button("📤 提交研究進度", type="primary")

        if submitted:
            if not research_title or not research_type:
                st.error("❌ 請填寫必填欄位（研究名稱、文獻類型）")
                return

            # 取得當前使用者的科別（用於科別過濾）
            user_department = st.session_state.get('user_department', '小兒部')

            data = {
                'resident_name': resident_name,
                'resident_level': resident_level,
                'research_title': research_title,
                'research_type': research_type,
                'supervisor_name': supervisor_name if supervisor_name else None,
                'current_status': current_status,
                'research_topic': research_topic if research_topic else None,
                'target_journal': target_journal if target_journal else None,
                'submission_date': str(submission_date) if submission_date else None,
                'acceptance_date': str(acceptance_date) if acceptance_date else None,
                'progress_notes': progress_notes if progress_notes else None,
                'challenges': challenges if challenges else None,
                'next_steps': next_steps if next_steps else None,
                'submitted_by': current_user,
                'department': user_department,  # ✅ 新增：設定科別
            }

            result = supabase_conn.insert_research_progress(data)
            if result:
                st.success(f"✅ 研究進度已登記：**{research_title}**")
                st.balloons()
            else:
                st.error("❌ 提交失敗，請檢查網路連線或聯繫管理員")


def _show_my_research_list(supabase_conn, resident_name):
    """顯示住院醫師的研究清單（可編輯/刪除）"""
    try:
        records = supabase_conn.fetch_research_progress(
            filters={'resident_name': resident_name}
        )
        if not records:
            st.info("尚無研究記錄")
            return

        import pandas as pd
        df = pd.DataFrame(records)

        # 顯示簡化表格
        display_cols = ['research_title', 'research_type', 'supervisor_name', 'current_status', 'updated_at']
        available = [c for c in display_cols if c in df.columns]
        if available:
            display_df = df[available].copy()
            display_df.columns = [
                c.replace('research_title', '研究名稱')
                 .replace('research_type', '類型')
                 .replace('supervisor_name', '指導老師')
                 .replace('current_status', '進度')
                 .replace('updated_at', '更新時間')
                for c in display_df.columns
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # 編輯/刪除功能（可選）
            st.caption("💡 如需修改或刪除研究記錄，請聯繫管理員或在系統中新增編輯功能。")
    except Exception as e:
        st.warning(f"載入研究清單時發生錯誤：{str(e)}")


# ─── 表單 2：學習反思 ───

def show_learning_reflection_form(supabase_conn, current_user):
    """住院醫師學習反思填寫表單（Gibbs 反思循環）"""
    st.subheader("💭 學習反思記錄")
    st.caption("記錄您的臨床學習經驗與反思，幫助自我成長與專業發展。")

    resident_info = _get_current_resident_info(supabase_conn, current_user)
    if not resident_info:
        st.warning("⚠️ 無法取得您的住院醫師資料，請聯繫管理員或確認您的帳號設定。")
        return

    resident_name = resident_info['name']
    resident_level = resident_info['level']

    # 顯示最近的反思記錄
    with st.expander("📖 我的反思記錄（最新 5 筆）", expanded=False):
        _show_my_reflection_list(supabase_conn, resident_name)

    st.markdown("---")
    st.markdown("### 新增學習反思")

    with st.form("learning_reflection_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            reflection_date = st.date_input("反思日期 *", value=date.today())
        with col2:
            reflection_type = st.selectbox("反思類型 *", options=REFLECTION_TYPES)
        with col3:
            is_private = st.checkbox("設為私人記錄", value=False, help="私人記錄僅自己可見")

        reflection_title = st.text_input(
            "反思標題 *",
            placeholder="例：第一次獨立執行腰椎穿刺的經驗"
        )

        st.markdown("#### 📝 反思內容（Gibbs 反思循環）")
        st.caption("依循反思架構，幫助您深入思考學習經驗")

        situation_description = st.text_area(
            "1️⃣ 情境描述 — 發生了什麼事？",
            placeholder="描述當時的情境、時間、地點、涉及的人物...",
            height=100
        )

        thoughts_and_feelings = st.text_area(
            "2️⃣ 想法與感受 — 當時您的想法與感受是什麼？",
            placeholder="描述您當時的情緒、想法、擔憂...",
            height=100
        )

        evaluation = st.text_area(
            "3️⃣ 評估與分析 — 什麼做得好？什麼可以改進？",
            placeholder="評估這次經驗的優點與缺點...",
            height=100
        )

        action_plan = st.text_area(
            "4️⃣ 行動計畫 — 下次遇到類似情況，您會怎麼做？",
            placeholder="具體的改進計畫或行動方案...",
            height=100
        )

        learning_outcomes = st.text_area(
            "5️⃣ 學習成果 — 從這次經驗中學到了什麼？",
            placeholder="總結您的學習收穫...",
            height=100
        )

        st.markdown("#### 🔗 關聯資訊（選填）")
        col_x, col_y, col_z = st.columns(3)
        with col_x:
            related_epa = st.selectbox("相關 EPA", options=[''] + PEDIATRIC_EPA_ITEMS)
        with col_y:
            related_skill = st.selectbox("相關技能", options=[''] + PEDIATRIC_SKILL_ITEMS)
        with col_z:
            teacher_list = _get_teacher_list(supabase_conn)
            if teacher_list:
                supervising_teacher = st.selectbox("督導教師", options=[''] + teacher_list)
            else:
                supervising_teacher = st.text_input("督導教師")

        tags = st.multiselect("標籤", options=REFLECTION_TAGS, help="選擇相關標籤分類")

        submitted = st.form_submit_button("📤 提交學習反思", type="primary")

        if submitted:
            if not reflection_title:
                st.error("❌ 請填寫反思標題")
                return

            # 取得當前使用者的科別（用於科別過濾）
            user_department = st.session_state.get('user_department', '小兒部')

            data = {
                'resident_name': resident_name,
                'resident_level': resident_level,
                'reflection_date': str(reflection_date),
                'reflection_title': reflection_title,
                'reflection_type': reflection_type,
                'situation_description': situation_description if situation_description else None,
                'thoughts_and_feelings': thoughts_and_feelings if thoughts_and_feelings else None,
                'evaluation': evaluation if evaluation else None,
                'action_plan': action_plan if action_plan else None,
                'learning_outcomes': learning_outcomes if learning_outcomes else None,
                'related_epa': related_epa if related_epa else None,
                'related_skill': related_skill if related_skill else None,
                'supervising_teacher': supervising_teacher if supervising_teacher else None,
                'tags': tags if tags else None,
                'is_private': is_private,
                'submitted_by': current_user,
                'department': user_department,  # ✅ 新增：設定科別
            }

            result = supabase_conn.insert_learning_reflection(data)
            if result:
                st.success(f"✅ 學習反思已記錄：**{reflection_title}**")
                st.balloons()
            else:
                st.error("❌ 提交失敗，請檢查網路連線或聯繫管理員")


def _show_my_reflection_list(supabase_conn, resident_name):
    """顯示住院醫師最近的反思記錄"""
    try:
        records = supabase_conn.fetch_learning_reflections(
            filters={'resident_name': resident_name, 'include_private': True}
        )
        if not records:
            st.info("尚無反思記錄")
            return

        import pandas as pd
        recent = records[:5]  # 最新 5 筆
        df = pd.DataFrame(recent)

        display_cols = ['reflection_date', 'reflection_title', 'reflection_type', 'is_private']
        available = [c for c in display_cols if c in df.columns]
        if available:
            display_df = df[available].copy()
            # 將 is_private 轉為圖示
            if 'is_private' in display_df.columns:
                display_df['is_private'] = display_df['is_private'].apply(lambda x: '🔒' if x else '🌐')
            display_df.columns = [
                c.replace('reflection_date', '日期')
                 .replace('reflection_title', '標題')
                 .replace('reflection_type', '類型')
                 .replace('is_private', '隱私')
                for c in display_df.columns
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"載入反思記錄時發生錯誤：{str(e)}")


# ─── 主入口：顯示所有表單 ───

def show_resident_forms_tab(supabase_conn, current_user):
    """
    住院醫師自填表單 Tab 的主入口。
    以 sub-tabs 呈現研究進度、學習反思兩種表單。

    Args:
        supabase_conn: SupabaseConnection 實例
        current_user (str): 當前登入的使用者名稱
    """
    st.markdown("### 📝 住院醫師自填表單")
    st.caption("記錄您的研究進度與學習反思，系統將自動整合到您的學習歷程檔案。")

    sub1, sub2 = st.tabs(["📚 研究進度", "💭 學習反思"])

    with sub1:
        show_research_progress_form(supabase_conn, current_user)

    with sub2:
        show_learning_reflection_form(supabase_conn, current_user)
