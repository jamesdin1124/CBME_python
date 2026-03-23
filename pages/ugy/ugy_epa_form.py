"""
UGY EPA 系統內評核表單（教師端）

功能：
- 教師登入後可直接在系統內填寫 EPA 評核
- 輸入學生姓名自動查找（支援 Supabase 已註冊學生 + 手動輸入）
- 欄位與 Google 表單一致
- 提交後寫入 Supabase ugy_epa_records 資料表
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from config.epa_constants import EPA_LEVEL_MAPPING
from modules.voice_input import (
    _transcribe_audio, _refine_with_gpt,
    _check_role, _remaining_quota,
    DAILY_TRANSCRIBE_LIMIT, DAILY_REFINE_LIMIT,
)


def _get_supabase_conn():
    from modules.supabase_connection import SupabaseConnection
    return SupabaseConnection()


# ═══════════════════════════════════════════════════════
# EPA 等級選項（與 Google 表單一致）
# ═══════════════════════════════════════════════════════

EPA_LEVEL_OPTIONS = [
    '不允許學員觀察',
    '允許學員在旁觀察',
    '教師在旁逐步共同操作',
    '教師在旁必要時協助',
    '教師可立即到場協助，事後逐項確認',
    '教師可立即到場協助，事後重點確認',
    '教師可稍後到場協助，必要時事後確認',
    '教師on call提供監督',
    '教師不需on call，事後提供回饋及監督',
    '學員可對其他資淺的學員進行監督與教學',
]

EPA_ITEMS = ['病歷紀錄', '住院接診', '當班處置']

DIFFICULTY_OPTIONS = ['簡單', '一般', '困難']

COHORT_OPTIONS = ['C1', 'C2']

DEPARTMENT_OPTIONS = ['內科部', '外科部', '婦產部', '小兒部']


def _get_ugy_student_names():
    """從 Supabase 取得已註冊的 UGY 學生姓名"""
    try:
        from modules.ugy_student_manager import get_ugy_student_names
        return get_ugy_student_names()
    except Exception:
        return []


def _get_ugy_student_options():
    """從 Supabase 取得已註冊的 UGY 學生選項（姓名+學號）"""
    try:
        from modules.ugy_student_manager import get_ugy_student_options
        return get_ugy_student_options()
    except Exception:
        return []


def _submit_ugy_epa(data):
    """寫入 UGY EPA 紀錄到 Supabase"""
    try:
        conn = _get_supabase_conn()
        result = conn.client.table('ugy_epa_records').insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        # 如果 ugy_epa_records 表不存在，fallback 到通用表
        try:
            conn = _get_supabase_conn()
            fallback_data = {
                'evaluation_type': 'ugy_epa',
                'evaluator_teacher': data.get('教師'),
                'evaluation_date': data.get('evaluation_date', str(date.today())),
                'evaluated_resident': data.get('學員姓名'),
                'resident_level': data.get('階層'),
                'department': data.get('實習科部'),
                'epa_item': data.get('EPA評核項目'),
                'epa_reliability_level': EPA_LEVEL_MAPPING.get(data.get('教師評核EPA等級'), 0),
                'epa_qualitative_feedback': data.get('回饋'),
                'submitted_by': data.get('教師'),
            }
            result = conn.client.table('pediatric_evaluations').insert(fallback_data).execute()
            return result.data[0] if result.data else None
        except Exception as e2:
            st.error(f"提交失敗：{str(e2)}")
            return None


# ═══════════════════════════════════════════════════════
# 主要表單 UI
# ═══════════════════════════════════════════════════════

def _show_voice_section(key: str):
    """在表單上方顯示語音輸入區塊（Whisper API），轉錄結果存入 session_state"""
    if not _check_role():
        return

    text_key = f"voice_text_{key}"
    if text_key not in st.session_state:
        st.session_state[text_key] = ""

    trans_left = _remaining_quota('transcribe', DAILY_TRANSCRIBE_LIMIT)
    refine_left = _remaining_quota('refine', DAILY_REFINE_LIMIT)

    with st.expander("🎙️ 語音輸入回饋（Whisper 語音辨識）", expanded=False):
        st.caption(
            f"錄音或上傳音檔，自動辨識中英文醫學用語 → 填入下方回饋欄位　｜　"
            f"今日剩餘：轉錄 **{trans_left}** 次、潤飾 **{refine_left}** 次"
        )

        if trans_left <= 0:
            st.warning(f"⚠️ 今日語音轉錄額度已用完（{DAILY_TRANSCRIBE_LIMIT} 次/天），請直接打字輸入")
        else:
            rec_col, upload_col, action_col = st.columns([1, 2, 1])

            with rec_col:
                try:
                    from audio_recorder_streamlit import audio_recorder
                    audio_bytes = audio_recorder(
                        text="錄音",
                        recording_color="#e74c3c",
                        neutral_color="#6c757d",
                        icon_size="1x",
                        key=f"recorder_{key}",
                    )
                    # 防止重複處理同一段錄音
                    prev_key = f"_prev_audio_{key}"
                    if audio_bytes and audio_bytes != st.session_state.get(prev_key):
                        st.session_state[prev_key] = audio_bytes
                        with st.spinner("🔄 語音辨識中..."):
                            transcribed = _transcribe_audio(audio_bytes)
                        if transcribed:
                            current = st.session_state.get(text_key, "")
                            sep = "\n" if current.strip() else ""
                            st.session_state[text_key] = current + sep + transcribed
                            st.success("✅ 辨識完成")
                except ImportError:
                    st.info("💡 安裝 `audio_recorder_streamlit` 即可使用即時錄音")

            with upload_col:
                uploaded = st.file_uploader(
                    "上傳錄音檔",
                    type=["wav", "mp3", "m4a", "ogg", "webm"],
                    key=f"upload_{key}",
                    label_visibility="collapsed",
                )
                if uploaded and st.button("📝 轉錄音檔", key=f"do_transcribe_{key}"):
                    with st.spinner("🔄 語音辨識中..."):
                        transcribed = _transcribe_audio(uploaded.getvalue())
                    if transcribed:
                        current = st.session_state.get(text_key, "")
                        sep = "\n" if current.strip() else ""
                        st.session_state[text_key] = current + sep + transcribed
                        st.success("✅ 辨識完成")

            with action_col:
                if st.session_state.get(text_key, "").strip() and refine_left > 0:
                    if st.button("✨ AI 潤飾", key=f"refine_{key}", help="修正醫學用語、改善語句"):
                        with st.spinner("🔄 AI 潤飾中..."):
                            refined = _refine_with_gpt(st.session_state[text_key])
                            st.session_state[text_key] = refined
                            st.success("✅ 潤飾完成")

        # 預覽
        if st.session_state.get(text_key, "").strip():
            st.text_area(
                "📋 語音辨識結果（提交時會自動帶入下方回饋欄）",
                value=st.session_state[text_key],
                height=80,
                key=f"preview_{key}",
                disabled=True,
            )


def show_ugy_epa_form():
    """顯示 UGY EPA 評核表單（教師端）"""
    st.subheader("📝 UGY Clerk EPA 評核表單")
    st.caption("教師填寫。欄位與 Google 表單一致，提交後自動儲存至系統資料庫。")

    current_user = st.session_state.get('user_name', st.session_state.get('username', ''))

    # 取得已註冊學生清單（含學號）
    student_options = _get_ugy_student_options()
    # 建立 display → student_option 的對照
    display_list = [opt['display'] for opt in student_options]  # "姓名（學號）"

    # ── 語音輸入（必須放在 form 外面）──
    _show_voice_section('ugy_feedback')

    with st.form("ugy_epa_form", clear_on_submit=True):
        # ── 第一列：學員資訊 ──
        st.markdown("### 學員資訊")
        col1, col2, col3 = st.columns(3)

        with col1:
            # 學生選擇：可輸入部分姓名或學號搜尋
            if student_options:
                selected_display = st.selectbox(
                    "學員姓名/學號 *（可輸入搜尋）",
                    options=[''] + display_list,
                    key='ugy_student_select',
                    help="輸入部分姓名或學號即可搜尋，以學號為唯一辨識"
                )
                # 從選取結果反查學生資訊
                if selected_display:
                    matched = next(
                        (opt for opt in student_options if opt['display'] == selected_display),
                        None
                    )
                    student_name = matched['full_name'] if matched else ''
                    student_id_val = matched['student_id'] if matched else ''
                else:
                    student_name = ''
                    student_id_val = ''
            else:
                st.warning("尚無已註冊學生，請先於帳號管理匯入學生名冊。")
                student_name = ''
                student_id_val = ''

        with col2:
            cohort = st.selectbox("階層 *", options=COHORT_OPTIONS, key='ugy_cohort')

        with col3:
            # 預設選擇該教師所屬科部
            user_dept = st.session_state.get('user_department', '')
            dept_index = 0
            if user_dept and user_dept in DEPARTMENT_OPTIONS:
                dept_index = DEPARTMENT_OPTIONS.index(user_dept)
            department = st.selectbox("實習科部 *", options=DEPARTMENT_OPTIONS, index=dept_index, key='ugy_dept')

        # ── 第二列：EPA 評核 ──
        st.markdown("---")
        st.markdown("### EPA 評核")

        col4, col5, col6_date = st.columns(3)
        with col4:
            epa_item = st.selectbox("EPA 評核項目 *", options=EPA_ITEMS, index=2, key='ugy_epa_item')
        with col5:
            location = st.text_input("地點", key='ugy_location')
        with col6_date:
            eval_date = st.date_input("評核日期 *", value=date.today(), key='ugy_eval_date')
            # 自動計算梯次
            from modules.data_processing import convert_date_to_batch
            batch_label = convert_date_to_batch(str(eval_date))
            st.caption(f"📅 梯次：{batch_label}")

        # 教師評核 EPA 等級
        st.markdown("#### 教師評核 EPA 等級")
        teacher_level = st.radio(
            "請選擇該學員的可信賴程度 *",
            options=EPA_LEVEL_OPTIONS,
            index=3,  # 預設「教師在旁必要時協助」
            key='ugy_teacher_level'
        )

        level_score = EPA_LEVEL_MAPPING.get(teacher_level, 0)

        # 學員自評（選填）
        st.markdown("#### 學員自評 EPA 等級（選填）")
        self_assess = st.selectbox(
            "學員自評",
            options=['不填寫'] + EPA_LEVEL_OPTIONS,
            key='ugy_self_level'
        )

        # ── 第三列：病人/臨床資訊 ──
        st.markdown("---")
        st.markdown("### 臨床情境")

        col6, col7 = st.columns(2)
        with col6:
            patient_id = st.text_input("病歷號 *（純數字）", key='ugy_patient_id',
                                        placeholder="例：12345678")
            difficulty = st.selectbox("病人難度", options=DIFFICULTY_OPTIONS, index=1, key='ugy_difficulty')
        with col7:
            clinical_scenario = st.text_area("臨床情境描述", key='ugy_scenario',
                                             placeholder="例：新病人（COVID, cellulitis）")

        # ── 第四列：回饋 ──
        st.markdown("---")
        st.markdown("### 回饋")
        # 將語音辨識結果同步到表單 widget 的 key
        voice_text = st.session_state.get('voice_text_ugy_feedback', '')
        if voice_text and not st.session_state.get('ugy_feedback'):
            st.session_state['ugy_feedback'] = voice_text
        feedback = st.text_area("回饋 *", key='ugy_feedback',
                                placeholder="請描述學員的表現...",
                                help="可使用上方🎙️語音輸入，辨識結果會自動帶入此欄位")
        private_feedback = st.text_area("給教學部的私下回饋（選填）", key='ugy_private',
                                        placeholder="此回饋僅教學部可見...")

        # ── 教師簽名 ──
        st.text_input("教師姓名", value=current_user, disabled=True, key='ugy_teacher_display')
        teacher_name = current_user

        # ── 提交 ──
        submitted = st.form_submit_button("提交 EPA 評核", type="primary")

        if submitted:
            # 驗證必填
            if not student_name:
                st.error("請輸入或選擇學員姓名")
                return
            if not patient_id:
                st.error("請填寫病歷號")
                return
            if not patient_id.strip().isdigit():
                st.error("病歷號必須為純數字")
                return
            if not feedback:
                st.error("請填寫回饋")
                return
            if not teacher_name:
                st.error("請填寫教師姓名")
                return

            record = {
                '學員姓名': student_name,
                '學號': student_id_val or None,
                '階層': cohort,
                '實習科部': department,
                'EPA評核項目': epa_item,
                '地點': location or None,
                '教師評核EPA等級': teacher_level,
                '教師評核EPA等級_數值': level_score,
                '學員自評EPA等級': self_assess if self_assess != '不填寫' else None,
                '病歷號': patient_id or None,
                '病人難度': difficulty,
                '臨床情境': clinical_scenario or None,
                '回饋': feedback,
                '給教學部的私下回饋': private_feedback or None,
                '教師': teacher_name,
                'evaluation_date': str(eval_date),
                '時間戳記': datetime.combine(eval_date, datetime.now().time()).isoformat(),
            }

            result = _submit_ugy_epa(record)
            if result:
                st.success(f"已提交 **{student_name}**（{student_id_val}）的 **{epa_item}** EPA 評核！")
                st.balloons()
            else:
                st.error("提交失敗，請檢查網路連線或聯繫管理員。")

    # ── 最近提交紀錄 ──
    _show_recent_submissions(current_user)


def _show_recent_submissions(teacher_name, limit=10):
    """在表單下方顯示該教師最近提交的 EPA 評核紀錄（含刪除功能）"""
    st.markdown("---")
    st.subheader("📋 最近提交紀錄")
    try:
        conn = _get_supabase_conn()
        result = conn.client.table('ugy_epa_records').select(
            'id, 時間戳記, 學員姓名, 學號, 階層, 實習科部, EPA評核項目, 病歷號, 教師評核EPA等級_數值, 回饋, 教師'
        ).eq('教師', teacher_name).order('時間戳記', desc=True).limit(limit).execute()

        if result.data:
            import pandas as pd
            records = result.data

            for i, rec in enumerate(records):
                ts = pd.to_datetime(rec.get('時間戳記', '')).strftime('%m/%d %H:%M') if rec.get('時間戳記') else ''
                student = rec.get('學員姓名', '')
                sid = rec.get('學號', '')
                epa_item = rec.get('EPA評核項目', '')
                patient = rec.get('病歷號', '') or ''
                level = rec.get('教師評核EPA等級_數值', '')
                feedback = rec.get('回饋', '') or ''
                if len(feedback) > 25:
                    feedback = feedback[:25] + '...'
                record_id = rec.get('id')

                cols = st.columns([2, 2, 2, 2, 2, 2, 1.5, 3, 1.5])
                cols[0].caption(ts)
                cols[1].caption(student)
                cols[2].caption(sid)
                cols[3].caption(rec.get('實習科部', ''))
                cols[4].caption(epa_item)
                cols[5].caption(patient)
                cols[6].caption(str(level))
                cols[7].caption(feedback)
                if cols[8].button("🗑️", key=f"del_{record_id}_{i}", help="刪除此筆紀錄"):
                    try:
                        conn.client.table('ugy_epa_records').delete().eq('id', record_id).execute()
                        st.success(f"已刪除 {student} 的 {epa_item} 評核")
                        st.rerun()
                    except Exception as e:
                        st.error(f"刪除失敗：{str(e)}")

            # 表頭說明
            st.caption(f"顯示最近 {len(records)} 筆（由您提交）｜點 🗑️ 可刪除錯誤紀錄")
        else:
            st.info("尚無提交紀錄。")
    except Exception as e:
        st.warning(f"無法載入最近紀錄：{str(e)}")


# ═══════════════════════════════════════════════════════
# 批次評核功能（已停用，保留程式碼備用）
# ═══════════════════════════════════════════════════════
# def show_ugy_epa_batch_form():
#     """批次 EPA 評核（同一次評核多位學員）"""
#     st.subheader("📝 批次 UGY EPA 評核")
#     st.caption("一次評核同科同情境的多位學員。")
#
#     current_user = st.session_state.get('user_name', st.session_state.get('username', ''))
#     registered_students = _get_ugy_student_names()
#
#     with st.form("ugy_epa_batch_form", clear_on_submit=True):
#         # 共用欄位
#         st.markdown("### 共用資訊")
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             department = st.selectbox("實習科部", options=DEPARTMENT_OPTIONS)
#             epa_item = st.selectbox("EPA 評核項目", options=EPA_ITEMS)
#         with col2:
#             location = st.text_input("地點")
#             difficulty = st.selectbox("病人難度", options=DIFFICULTY_OPTIONS, index=1)
#         with col3:
#             patient_id = st.text_input("病歷號（選填）")
#             clinical_scenario = st.text_input("臨床情境")
#
#         teacher_name = st.text_input("教師姓名", value=current_user)
#
#         st.markdown("---")
#         st.markdown("### 個別學員評核")
#
#         num_students = st.number_input("評核學員人數", min_value=1, max_value=10, value=3)
#
#         student_entries = []
#         for i in range(int(num_students)):
#             st.markdown(f"**學員 {i+1}**")
#             cols = st.columns([2, 1, 2, 2])
#             with cols[0]:
#                 if registered_students:
#                     sname = st.selectbox(
#                         f"姓名", options=[''] + registered_students,
#                         key=f'batch_name_{i}'
#                     )
#                 else:
#                     sname = st.text_input(f"姓名", key=f'batch_name_{i}')
#             with cols[1]:
#                 scohort = st.selectbox(f"階層", options=COHORT_OPTIONS, key=f'batch_cohort_{i}')
#             with cols[2]:
#                 slevel = st.selectbox(
#                     f"EPA 等級", options=EPA_LEVEL_OPTIONS,
#                     index=3, key=f'batch_level_{i}'
#                 )
#             with cols[3]:
#                 sfeedback = st.text_input(f"回饋", key=f'batch_fb_{i}')
#
#             student_entries.append({
#                 'name': sname, 'cohort': scohort,
#                 'level': slevel, 'feedback': sfeedback
#             })
#
#         submitted = st.form_submit_button("批次提交", type="primary")
#
#         if submitted:
#             if not teacher_name:
#                 st.error("請填寫教師姓名")
#                 return
#
#             success_count = 0
#             for entry in student_entries:
#                 if not entry['name']:
#                     continue
#
#                 level_score = EPA_LEVEL_MAPPING.get(entry['level'], 0)
#                 record = {
#                     '學員姓名': entry['name'],
#                     '階層': entry['cohort'],
#                     '實習科部': department,
#                     'EPA評核項目': epa_item,
#                     '地點': location or None,
#                     '教師評核EPA等級': entry['level'],
#                     '教師評核EPA等級_數值': level_score,
#                     '學員自評EPA等級': None,
#                     '病歷號': patient_id or None,
#                     '病人難度': difficulty,
#                     '臨床情境': clinical_scenario or None,
#                     '回饋': entry['feedback'] or 'Good',
#                     '給教學部的私下回饋': None,
#                     '教師': teacher_name,
#                     'evaluation_date': str(date.today()),
#                     '時間戳記': datetime.now().isoformat(),
#                 }
#                 result = _submit_ugy_epa(record)
#                 if result:
#                     success_count += 1
#
#             if success_count > 0:
#                 st.success(f"成功提交 {success_count} 筆 EPA 評核！")
#                 st.balloons()
#             else:
#                 st.error("提交失敗，請檢查資料。")
