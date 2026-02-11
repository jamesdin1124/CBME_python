import streamlit as st
from modules.supabase_connection import SupabaseConnection
import pandas as pd
from datetime import datetime

# 全域 Supabase 連線實例
_supabase_conn = None

def get_supabase_connection():
    """獲取 Supabase 連線實例"""
    global _supabase_conn
    if _supabase_conn is not None:
        return _supabase_conn
    try:
        _supabase_conn = SupabaseConnection()
        return _supabase_conn
    except Exception as e:
        st.error(f"無法連線 Supabase：{str(e)}")
        return None

def show_user_application_review():
    """管理員審核使用者申請介面"""

    st.title("👥 帳號申請審核")

    # 權限檢查
    user_role = st.session_state.get('role')
    user_dept = st.session_state.get('user_department')

    if user_role not in ['admin', 'department_admin']:
        st.error("此功能僅限系統管理員或科別管理員使用")
        return

    conn = get_supabase_connection()
    if not conn:
        st.error("無法連線 Supabase，請檢查設定")
        return

    # Tab 分類
    tab1, tab2, tab3 = st.tabs(["⏳ 待審核", "✅ 已核准", "❌ 已拒絕"])

    # ========== Tab 1: 待審核 ==========
    with tab1:
        st.markdown("### 待審核申請列表")

        # 根據角色過濾申請
        if user_role == 'admin':
            pending_apps = conn.fetch_user_applications({'status': 'pending'})
        elif user_role == 'department_admin':
            pending_apps = conn.fetch_user_applications({
                'status': 'pending',
                'department': user_dept
            })

        if not pending_apps:
            st.info("目前無待審核申請")
        else:
            st.write(f"共 **{len(pending_apps)}** 筆待審核申請")

            for app in pending_apps:
                # 使用 USER_ROLES 字典來顯示角色名稱
                from modules.auth import USER_ROLES
                role_display = USER_ROLES.get(app['user_type'], app['user_type'])

                with st.expander(f"📋 {app['full_name']} - {app['email']} ({role_display})"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**基本資料**")
                        st.write(f"- 姓名：{app['full_name']}")
                        st.write(f"- 帳號：`{app.get('desired_username', '未提供')}`")
                        st.write(f"- Email：{app['email']}")
                        st.write(f"- 電話：{app.get('phone', '未提供')}")

                    with col2:
                        st.write("**身份與科別**")
                        st.write(f"- 身份：{role_display}")
                        if app.get('department'):
                            st.write(f"- 科別：{app['department']}")
                        if app.get('resident_level'):
                            st.write(f"- 級職：{app['resident_level']}")
                        if app.get('supervisor_name'):
                            st.write(f"- 指導醫師：{app['supervisor_name']}")
                        st.write(f"- 申請時間：{app['created_at'][:19]}")

                    st.markdown("---")

                    # 審核表單
                    with st.form(key=f"review_form_{app['id']}"):
                        action = st.radio(
                            "審核決定",
                            options=["approve", "reject"],
                            format_func=lambda x: "✅ 核准" if x == "approve" else "❌ 拒絕",
                            horizontal=True
                        )

                        if action == "approve":
                            # 申請人已自行設定帳號密碼，管理員可選擇覆蓋
                            applicant_username = app.get('desired_username', '')
                            st.info(f"申請人自選帳號：**{applicant_username}**（已自設密碼）")
                            override_username = st.text_input(
                                "覆蓋帳號（留空則使用申請人自選帳號）",
                                value="",
                                help="若需修改帳號名稱請填寫，否則留空即可"
                            )
                        else:
                            reason = st.text_area(
                                "拒絕原因 *",
                                placeholder="請說明拒絕原因，此訊息將顯示給申請人",
                                height=100
                            )

                        submit = st.form_submit_button("提交審核結果", use_container_width=True)

                        if submit:
                            reviewer_name = st.session_state.get('username', 'admin')

                            if action == "approve":
                                final_username = override_username.strip() if override_username.strip() else None
                                success, message, user_id = conn.approve_user_application(
                                    app['id'], reviewer_name,
                                    username=final_username,  # None = 使用申請人自選帳號
                                    password=None             # None = 使用申請人自設密碼
                                )
                                if success:
                                    st.success(message)
                                    display_name = final_username if final_username else app.get('desired_username', '')
                                    st.info(f"帳號已建立：**{display_name}**（使用申請人自設密碼）")
                                    st.rerun()
                                else:
                                    st.error(message)

                            else:  # reject
                                if not reason:
                                    st.error("請填寫拒絕原因")
                                else:
                                    success = conn.reject_user_application(app['id'], reviewer_name, reason)
                                    if success:
                                        st.success("已拒絕申請")
                                        st.rerun()
                                    else:
                                        st.error("操作失敗")

    # ========== Tab 2: 已核准 ==========
    with tab2:
        st.markdown("### 已核准申請列表")

        # 根據角色過濾申請
        if user_role == 'admin':
            approved_apps = conn.fetch_user_applications({'status': 'approved'})
        elif user_role == 'department_admin':
            approved_apps = conn.fetch_user_applications({
                'status': 'approved',
                'department': user_dept
            })

        if not approved_apps:
            st.info("目前無已核准申請")
        else:
            df = pd.DataFrame(approved_apps)
            display_cols = ['full_name', 'email', 'user_type', 'resident_level', 'reviewed_by', 'reviewed_at', 'created_at']
            avail_cols = [c for c in display_cols if c in df.columns]

            st.dataframe(
                df[avail_cols].rename(columns={
                    'full_name': '姓名',
                    'email': 'Email',
                    'user_type': '身份',
                    'resident_level': '級職',
                    'reviewed_by': '審核者',
                    'reviewed_at': '審核時間',
                    'created_at': '申請時間'
                }),
                use_container_width=True,
                hide_index=True
            )

    # ========== Tab 3: 已拒絕 ==========
    with tab3:
        st.markdown("### 已拒絕申請列表")

        # 根據角色過濾申請
        if user_role == 'admin':
            rejected_apps = conn.fetch_user_applications({'status': 'rejected'})
        elif user_role == 'department_admin':
            rejected_apps = conn.fetch_user_applications({
                'status': 'rejected',
                'department': user_dept
            })

        if not rejected_apps:
            st.info("目前無已拒絕申請")
        else:
            st.write(f"共 **{len(rejected_apps)}** 筆已拒絕申請")

            for app in rejected_apps:
                from modules.auth import USER_ROLES
                role_display = USER_ROLES.get(app['user_type'], app['user_type'])

                with st.expander(f"📋 {app['full_name']} - {app['email']}"):
                    st.write(f"- 姓名：{app['full_name']}")
                    st.write(f"- Email：{app['email']}")
                    st.write(f"- 身份：{role_display}")
                    if app.get('department'):
                        st.write(f"- 科別：{app['department']}")
                    st.write(f"- 申請時間：{app['created_at'][:19]}")
                    st.write(f"- 審核者：{app.get('reviewed_by', '未記錄')}")
                    st.write(f"- 審核時間：{app.get('reviewed_at', '未記錄')[:19] if app.get('reviewed_at') else '未記錄'}")
                    if app.get('review_notes'):
                        st.warning(f"拒絕原因：{app['review_notes']}")

if __name__ == "__main__":
    show_user_application_review()
