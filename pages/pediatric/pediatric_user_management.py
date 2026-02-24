"""
兒科 CCC 評估系統 — 帳號管理
管理小兒科住院醫師與主治醫師帳號，
資料儲存於 Supabase pediatric_users 表。
"""

import streamlit as st
from datetime import datetime


def show_pediatric_user_management(supabase_conn):
    """
    小兒科使用者管理主入口（僅 admin 可存取）。

    Args:
        supabase_conn: SupabaseConnection 實例
    """
    st.markdown("### 👥 小兒科帳號管理")
    st.caption("管理住院醫師與主治醫師帳號，新增的帳號將出現在評核表單的下拉選單中。")

    tab_r, tab_t, tab_sync = st.tabs([
        "🩺 住院醫師管理", "👨‍⚕️ 主治醫師管理", "🔄 同步本地帳號"
    ])

    with tab_r:
        _show_resident_management(supabase_conn)
    with tab_t:
        _show_teacher_management(supabase_conn)
    with tab_sync:
        _show_sync_from_local_auth(supabase_conn)


# ─── 住院醫師管理 ───

def _show_resident_management(supabase_conn):
    """住院醫師 CRUD"""
    st.subheader("住院醫師帳號管理")

    # 新增
    with st.expander("➕ 新增住院醫師", expanded=False):
        with st.form("add_resident_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("帳號（唯一識別碼）", placeholder="例：lin_ys")
                full_name = st.text_input("姓名", placeholder="例：林盈秀")
                email = st.text_input("電子郵件（選填）")
            with col2:
                resident_level = st.selectbox("目前級別", ['R1', 'R2', 'R3'])
                enrollment_year = st.number_input(
                    "入學年度", min_value=2018, max_value=2030,
                    value=datetime.now().year, step=1)

            submitted = st.form_submit_button("新增住院醫師", type="primary")
            if submitted:
                if not username or not full_name:
                    st.error("帳號和姓名為必填")
                else:
                    result = supabase_conn.upsert_pediatric_user({
                        'username': username,
                        'full_name': full_name,
                        'email': email or None,
                        'user_type': 'resident',
                        'resident_level': resident_level,
                        'enrollment_year': enrollment_year,
                        'is_active': True,
                    })
                    if result:
                        st.success(f"✅ 已新增住院醫師：{full_name}")
                        st.rerun()
                    else:
                        st.error("❌ 新增失敗，帳號可能已存在")

    # 列表
    st.markdown("#### 現有住院醫師")
    residents = supabase_conn.fetch_pediatric_users(user_type='resident', active_only=False)

    if not residents:
        st.info("尚無住院醫師帳號")
        return

    # 分為啟用中 / 已停用
    active = [r for r in residents if r.get('is_active', True)]
    inactive = [r for r in residents if not r.get('is_active', True)]

    for r in active:
        _level_badge = {'R1': '🟢', 'R2': '🔵', 'R3': '🟣'}.get(r.get('resident_level', ''), '⚪')
        with st.expander(f"{_level_badge} {r['full_name']}（{r['username']}）— {r.get('resident_level', '?')}"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**帳號**：{r['username']}")
                st.write(f"**級別**：{r.get('resident_level', '未設定')}")
                st.write(f"**入學年度**：{r.get('enrollment_year', '未設定')}")
            with col2:
                st.write(f"**Email**：{r.get('email', '未設定')}")
                st.write(f"**建立時間**：{str(r.get('created_at', ''))[:10]}")
                if r.get('synced_from_local_auth'):
                    st.write("🔗 已同步自本地帳號")

            with col3:
                # 更新級別
                new_level = st.selectbox(
                    "變更級別", ['R1', 'R2', 'R3'],
                    index=['R1', 'R2', 'R3'].index(r.get('resident_level', 'R1')),
                    key=f"level_{r['id']}")
                if new_level != r.get('resident_level'):
                    if st.button("更新級別", key=f"update_level_{r['id']}"):
                        supabase_conn.upsert_pediatric_user({
                            'username': r['username'],
                            'full_name': r['full_name'],
                            'user_type': 'resident',
                            'resident_level': new_level,
                        })
                        st.success(f"已更新 {r['full_name']} 為 {new_level}")
                        st.rerun()

                if st.button("🚫 停用", key=f"deactivate_{r['id']}"):
                    supabase_conn.deactivate_pediatric_user(r['id'])
                    st.warning(f"已停用 {r['full_name']}")
                    st.rerun()

    if inactive:
        with st.expander(f"已停用帳號（{len(inactive)} 位）"):
            for r in inactive:
                st.write(f"~~{r['full_name']}~~ ({r['username']}) — {r.get('resident_level', '?')}")


# ─── 主治醫師管理 ───

def _show_teacher_management(supabase_conn):
    """主治醫師 CRUD"""
    st.subheader("主治醫師帳號管理")

    with st.expander("➕ 新增主治醫師", expanded=False):
        with st.form("add_teacher_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("帳號", placeholder="例：dr_wang")
                full_name = st.text_input("姓名", placeholder="例：王大明")
            with col2:
                email = st.text_input("電子郵件（選填）")
                title = st.text_input("職稱（選填）", placeholder="例：主治醫師 / 教授")

            submitted = st.form_submit_button("新增主治醫師", type="primary")
            if submitted:
                if not username or not full_name:
                    st.error("帳號和姓名為必填")
                else:
                    result = supabase_conn.upsert_pediatric_user({
                        'username': username,
                        'full_name': full_name,
                        'email': email or None,
                        'user_type': 'teacher',
                        'title': title or None,
                        'is_active': True,
                    })
                    if result:
                        st.success(f"✅ 已新增主治醫師：{full_name}")
                        st.rerun()
                    else:
                        st.error("❌ 新增失敗，帳號可能已存在")

    st.markdown("#### 現有主治醫師")
    teachers = supabase_conn.fetch_pediatric_users(user_type='teacher', active_only=False)

    if not teachers:
        st.info("尚無主治醫師帳號")
        return

    active = [t for t in teachers if t.get('is_active', True)]
    inactive = [t for t in teachers if not t.get('is_active', True)]

    for t in active:
        with st.expander(f"👨‍⚕️ {t['full_name']}（{t['username']}）"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**帳號**：{t['username']}")
                st.write(f"**職稱**：{t.get('title', '未設定')}")
                st.write(f"**Email**：{t.get('email', '未設定')}")
                if t.get('synced_from_local_auth'):
                    st.write("🔗 已同步自本地帳號")
            with col2:
                if st.button("🚫 停用", key=f"deactivate_teacher_{t['id']}"):
                    supabase_conn.deactivate_pediatric_user(t['id'])
                    st.warning(f"已停用 {t['full_name']}")
                    st.rerun()

    if inactive:
        with st.expander(f"已停用帳號（{len(inactive)} 位）"):
            for t in inactive:
                st.write(f"~~{t['full_name']}~~ ({t['username']})")


# ─── 從本地 auth 同步 ───

def _show_sync_from_local_auth(supabase_conn):
    """從現有 users.json 同步小兒部帳號到 Supabase"""
    st.subheader("同步本地帳號到 Supabase")
    st.caption("將現有 `users.json` 中小兒部相關的帳號同步到 Supabase `pediatric_users` 表。")

    st.info("""
    **同步規則：**
    - 科別為「小兒部」的帳號會被同步
    - admin 角色的帳號也會被同步（跨科管理）
    - 已存在的帳號（相同 username）不會重複建立
    - 同步後的帳號會標記 `synced_from_local_auth = True`
    """)

    if st.button("🔄 開始同步", type="primary"):
        try:
            from modules.auth import load_users, USER_ROLES
            local_users = load_users()

            if not local_users:
                st.warning("本地 users.json 為空或無法讀取")
                return

            synced_count = 0
            skipped_count = 0

            progress = st.progress(0)
            status_text = st.empty()
            total = len(local_users)

            for idx, (username, user_data) in enumerate(local_users.items()):
                progress.progress((idx + 1) / total)

                department = user_data.get('department', '')
                role = user_data.get('role', '')

                # 只同步小兒部或 admin
                if department != '小兒部' and role != 'admin':
                    skipped_count += 1
                    continue

                # 對應 user_type
                if role == 'admin':
                    user_type = 'admin'
                elif role == 'teacher':
                    user_type = 'teacher'
                elif role == 'resident':
                    user_type = 'resident'
                else:
                    skipped_count += 1
                    continue

                status_text.text(f"同步中：{user_data.get('name', username)}")

                result = supabase_conn.upsert_pediatric_user({
                    'username': username,
                    'full_name': user_data.get('name', username),
                    'email': user_data.get('email'),
                    'user_type': user_type,
                    'resident_level': user_data.get('resident_level'),
                    'is_active': True,
                    'synced_from_local_auth': True,
                    'local_auth_username': username,
                })

                if result:
                    synced_count += 1

            progress.progress(1.0)
            status_text.empty()
            st.success(f"✅ 同步完成！已同步 {synced_count} 個帳號，跳過 {skipped_count} 個帳號。")

        except ImportError:
            st.error("無法載入 modules.auth 模組")
        except Exception as e:
            st.error(f"同步失敗：{str(e)}")
