"""
認證與權限管理模組（純 Supabase 版本）

提供：
- 使用者角色定義與權限矩陣
- Supabase 身份驗證
- 使用者 CRUD 操作
- 登入介面
- 使用者管理介面
"""

import streamlit as st
import hashlib
import pandas as pd


# ═══════════════════════════════════════════════════════
# 使用者角色與權限定義
# ═══════════════════════════════════════════════════════

USER_ROLES = {
    'admin': '系統管理員',
    'department_admin': '科別管理員',
    'teacher': '主治醫師',
    'resident': '住院醫師',
    'pgy': 'PGY',
    'student': 'UGY'
}

PERMISSIONS = {
    'admin': {
        'can_view_all': True,
        'can_edit_all': True,
        'can_manage_users': True,
        'can_upload_files': True,
        'can_view_analytics': True,
        'can_view_department_data': True,
        'can_view_ugy_data': True,
        'can_view_pgy_data': True,
        'can_view_resident_data': True,
        'can_approve_all_departments': True,
        'can_manage_department_admins': True,
    },
    'department_admin': {
        'can_view_all': False,
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': True,
        'can_view_analytics': True,
        'can_view_department_data': True,
        'can_view_ugy_data': True,
        'can_view_pgy_data': True,
        'can_view_resident_data': True,
        'can_manage_department_users': True,
        'can_approve_department_applications': True,
    },
    'teacher': {
        'can_view_all': False,
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': True,
        'can_view_analytics': True,
        'can_view_department_data': True,
        'can_view_ugy_data': True,
        'can_view_pgy_data': True,
        'can_view_resident_data': True,
    },
    'resident': {
        'can_view_all': False,
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': False,
        'can_view_analytics': False,
        'can_view_department_data': False,
        'can_view_ugy_data': True,
        'can_view_pgy_data': False,
        'can_view_resident_data': True,
        'can_view_own_data': True,
    },
    'pgy': {
        'can_view_all': False,
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': False,
        'can_view_analytics': False,
        'can_view_department_data': False,
        'can_view_ugy_data': False,
        'can_view_pgy_data': False,
        'can_view_resident_data': False,
        'can_view_own_data': True,
    },
    'student': {
        'can_view_all': False,
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': False,
        'can_view_analytics': False,
        'can_view_department_data': False,
        'can_view_ugy_data': True,
        'can_view_pgy_data': False,
        'can_view_resident_data': False,
        'can_view_own_data': True,
    }
}


# ═══════════════════════════════════════════════════════
# 密碼工具
# ═══════════════════════════════════════════════════════

def hash_password(password):
    """將密碼進行 SHA-256 雜湊處理"""
    return hashlib.sha256(password.encode()).hexdigest()


# ═══════════════════════════════════════════════════════
# Supabase 認證與使用者管理
# ═══════════════════════════════════════════════════════

def _get_supabase_conn():
    """取得 Supabase 連線實例"""
    from modules.supabase_connection import SupabaseConnection
    return SupabaseConnection()


def authenticate_user(username, password):
    """
    驗證使用者身份（純 Supabase）

    Returns:
        dict: 包含 role, name, department, email, student_id, user_id
        None: 驗證失敗
    """
    try:
        conn = _get_supabase_conn()
        result = conn.client.table('pediatric_users').select('*').eq(
            'username', username
        ).eq('is_active', True).execute()

        if not result.data or len(result.data) == 0:
            return None

        user = result.data[0]
        password_hash = hash_password(password)

        if user.get('password_hash') == password_hash:
            return {
                'role': user.get('user_type', 'resident'),
                'name': user.get('full_name', username),
                'department': user.get('department'),
                'email': user.get('email'),
                'student_id': user.get('student_id'),
                'user_id': user.get('id'),
            }
        return None

    except Exception as e:
        st.error(f"認證失敗：{str(e)}")
        return None


def create_user(username, password, role, name,
                student_id=None, department=None, extension=None, email=None):
    """
    建立新使用者（純 Supabase）

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        conn = _get_supabase_conn()

        # 檢查使用者是否已存在
        existing = conn.client.table('pediatric_users').select('username').eq(
            'username', username
        ).execute()
        if existing.data and len(existing.data) > 0:
            return False, "使用者名稱已存在"

        # 確保密碼是 hash（SHA-256 hash 長度為 64）
        password_hash = password if len(password) == 64 else hash_password(password)

        user_data = {
            'username': username,
            'full_name': name,
            'user_type': role,
            'password_hash': password_hash,
            'is_active': True,
            'department': department,
            'email': email,
            'student_id': student_id,
        }

        result = conn.client.table('pediatric_users').insert(user_data).execute()

        if result.data:
            return True, "使用者建立成功"
        else:
            return False, "建立失敗"

    except Exception as e:
        return False, f"建立失敗：{str(e)}"


def change_password(username, old_password, new_password):
    """
    修改使用者密碼

    Args:
        username: 使用者帳號
        old_password: 舊密碼（明文）
        new_password: 新密碼（明文）

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        conn = _get_supabase_conn()

        # 先驗證舊密碼
        result = conn.client.table('pediatric_users').select('password_hash').eq(
            'username', username
        ).eq('is_active', True).execute()

        if not result.data or len(result.data) == 0:
            return False, "找不到該使用者"

        old_hash = hash_password(old_password)
        if result.data[0].get('password_hash') != old_hash:
            return False, "舊密碼不正確"

        # 更新密碼
        new_hash = hash_password(new_password)
        update_result = conn.client.table('pediatric_users').update(
            {'password_hash': new_hash}
        ).eq('username', username).execute()

        if update_result.data:
            return True, "密碼修改成功"
        return False, "密碼修改失敗"

    except Exception as e:
        return False, f"密碼修改失敗：{str(e)}"


def deactivate_user(username):
    """停用使用者（軟刪除）"""
    try:
        conn = _get_supabase_conn()
        result = conn.client.table('pediatric_users').update(
            {'is_active': False}
        ).eq('username', username).execute()

        if result.data:
            return True, "使用者已停用"
        return False, "找不到該使用者"
    except Exception as e:
        return False, f"停用失敗：{str(e)}"


def update_user_role(username, new_role):
    """更新使用者角色"""
    try:
        conn = _get_supabase_conn()
        result = conn.client.table('pediatric_users').update(
            {'user_type': new_role}
        ).eq('username', username).execute()

        if result.data:
            return True, "使用者權限更新成功"
        return False, "找不到該使用者"
    except Exception as e:
        return False, f"更新失敗：{str(e)}"


# ═══════════════════════════════════════════════════════
# 權限檢查
# ═══════════════════════════════════════════════════════

def check_permission(role, permission):
    """檢查使用者是否有特定權限"""
    return PERMISSIONS.get(role, {}).get(permission, False)


def check_data_access_permission(user_role, user_department, target_data_type, target_department=None):
    """
    檢查使用者是否有權限存取特定類型的資料

    Args:
        user_role: 使用者角色
        user_department: 使用者所屬科別
        target_data_type: 目標資料類型 ('ugy', 'pgy', 'resident', 'department')
        target_department: 目標科別
    """
    if user_role == 'admin':
        return True

    if target_data_type == 'ugy':
        return PERMISSIONS.get(user_role, {}).get('can_view_ugy_data', False)
    elif target_data_type == 'pgy':
        return PERMISSIONS.get(user_role, {}).get('can_view_pgy_data', False)
    elif target_data_type == 'resident':
        if user_role == 'teacher':
            return user_department == target_department
        elif user_role == 'resident':
            return user_department == target_department
        else:
            return PERMISSIONS.get(user_role, {}).get('can_view_resident_data', False)
    elif target_data_type == 'department':
        if user_role == 'teacher':
            return user_department == target_department
        else:
            return PERMISSIONS.get(user_role, {}).get('can_view_department_data', False)

    return False


def get_user_department(username):
    """取得使用者的科別"""
    try:
        conn = _get_supabase_conn()
        result = conn.client.table('pediatric_users').select('department').eq(
            'username', username
        ).eq('is_active', True).execute()

        if result.data and len(result.data) > 0:
            return result.data[0].get('department')
        return None
    except Exception:
        return None


def filter_data_by_permission(data, user_role, user_department, data_type):
    """
    根據使用者權限過濾資料

    Args:
        data: 原始 DataFrame
        user_role: 使用者角色
        user_department: 使用者科別
        data_type: 資料類型 ('ugy', 'pgy', 'resident', 'department')
    """
    if data is None or data.empty:
        return data

    # 管理員可以看到所有資料
    if user_role == 'admin':
        return data

    # PGY 和 UGY 只能看自己的資料
    if user_role in ['pgy', 'student']:
        username = st.session_state.get('username')
        if '姓名' in data.columns:
            return data[data['姓名'] == username]
        elif 'resident_name' in data.columns:
            return data[data['resident_name'] == username]
        elif '學號' in data.columns and 'student_id' in st.session_state:
            return data[data['學號'] == st.session_state['student_id']]
        return pd.DataFrame()

    if data_type == 'ugy':
        if not PERMISSIONS.get(user_role, {}).get('can_view_ugy_data', False):
            return pd.DataFrame()
        return data

    elif data_type == 'pgy':
        if not PERMISSIONS.get(user_role, {}).get('can_view_pgy_data', False):
            return pd.DataFrame()
        if user_role in ['department_admin', 'teacher'] and user_department:
            if '科別' in data.columns:
                return data[data['科別'] == user_department]
        return data

    elif data_type == 'resident':
        if not PERMISSIONS.get(user_role, {}).get('can_view_resident_data', False):
            return pd.DataFrame()
        if user_role in ['department_admin', 'teacher'] and user_department:
            if '科別' in data.columns:
                return data[data['科別'] == user_department]
        elif user_role == 'resident':
            username = st.session_state.get('username')
            if '姓名' in data.columns:
                return data[data['姓名'] == username]
            elif 'resident_name' in data.columns:
                return data[data['resident_name'] == username]
        return data

    elif data_type == 'department':
        if not PERMISSIONS.get(user_role, {}).get('can_view_department_data', False):
            return pd.DataFrame()
        if user_role in ['department_admin', 'teacher'] and user_department:
            if '科別' in data.columns:
                return data[data['科別'] == user_department]
        return data

    return data


# ═══════════════════════════════════════════════════════
# UI 介面
# ═══════════════════════════════════════════════════════

def show_login_page():
    """顯示登入頁面"""
    st.title("臨床教師評核系統 - 登入")

    with st.form("login_form"):
        username = st.text_input("使用者名稱")
        password = st.text_input("密碼", type="password")
        submitted = st.form_submit_button("登入")

        if submitted:
            user_info = authenticate_user(username, password)
            if user_info:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = user_info['role']
                st.session_state['user_name'] = user_info['name']
                st.session_state['user_department'] = user_info.get('department')
                st.session_state['user_id'] = user_info.get('user_id')

                if user_info['role'] == 'student':
                    if user_info.get('student_id'):
                        st.session_state['student_id'] = user_info['student_id']
                    else:
                        st.error("找不到學號資訊，請聯繫管理員")
                        return False

                st.success(f"歡迎回來，{st.session_state['user_name']}！")
                return True
            else:
                st.error("使用者名稱或密碼錯誤")
    return False


def show_user_management():
    """顯示使用者管理介面（純 Supabase 版本）"""
    if not check_permission(st.session_state['role'], 'can_manage_users'):
        st.error("您沒有權限管理使用者")
        return

    st.title("使用者管理")

    # ── 新增使用者 ──
    with st.expander("新增使用者"):
        with st.form("add_user_form"):
            new_username = st.text_input("使用者名稱")
            new_password = st.text_input("密碼", type="password")
            new_name = st.text_input("姓名")
            new_role = st.selectbox(
                "權限",
                options=list(USER_ROLES.keys()),
                format_func=lambda x: USER_ROLES[x],
            )

            departments = [
                "小兒部", "內科部", "外科部", "婦產部", "神經科", "精神部",
                "家醫部", "急診醫學部", "麻醉部", "放射部", "病理部",
                "復健部", "皮膚部", "眼科", "耳鼻喉部", "泌尿部", "骨部", "其他科別"
            ]
            new_department = st.selectbox("科別", options=[""] + departments)
            new_email = st.text_input("電子郵件")

            new_student_id = None
            if new_role == 'student':
                new_student_id = st.text_input("學號")

            submitted = st.form_submit_button("新增")

            if submitted:
                if not new_username or not new_password or not new_name:
                    st.error("請填寫帳號、密碼、姓名")
                else:
                    success, message = create_user(
                        new_username, new_password, new_role, new_name,
                        student_id=new_student_id,
                        department=new_department if new_department else None,
                        email=new_email if new_email else None,
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    # ── 使用者列表（從 Supabase 讀取）──
    st.subheader("使用者列表")
    try:
        conn = _get_supabase_conn()
        users_data = conn.fetch_all_users()

        if not users_data:
            st.info("目前沒有使用者")
            return

        for user in users_data:
            username = user.get('username', '')
            name = user.get('full_name', '未設定')
            role = user.get('user_type', 'resident')
            department = user.get('department', '未設定')
            is_active = user.get('is_active', True)
            role_name = USER_ROLES.get(role, role)

            status_icon = "✅" if is_active else "❌"
            with st.expander(f"{status_icon} {name} ({username}) - {role_name} - {department or '未設定'}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**姓名:** {name}")
                    st.write(f"**帳號:** {username}")
                    st.write(f"**角色:** {role_name}")
                    st.write(f"**科別:** {department or '未設定'}")
                    st.write(f"**狀態:** {'啟用中' if is_active else '已停用'}")
                    if user.get('email'):
                        st.write(f"**Email:** {user['email']}")
                    if user.get('student_id'):
                        st.write(f"**學號:** {user['student_id']}")

                with col2:
                    if is_active:
                        if st.button("停用帳號", key=f"deactivate_{username}"):
                            success, message = deactivate_user(username)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

                        new_role = st.selectbox(
                            "更新權限",
                            options=list(USER_ROLES.keys()),
                            index=list(USER_ROLES.keys()).index(role) if role in USER_ROLES else 0,
                            format_func=lambda x: USER_ROLES[x],
                            key=f"role_{username}",
                        )
                        if new_role != role:
                            if st.button("確認更新權限", key=f"update_role_{username}"):
                                success, message = update_user_role(username, new_role)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)

    except Exception as e:
        st.error(f"讀取使用者列表失敗：{str(e)}")


def show_change_password_form():
    """顯示修改密碼表單"""
    st.subheader("🔑 修改密碼")

    with st.form("change_password_form"):
        old_password = st.text_input("目前密碼", type="password")
        new_password = st.text_input("新密碼", type="password")
        confirm_password = st.text_input("確認新密碼", type="password")
        submitted = st.form_submit_button("確認修改", type="primary")

        if submitted:
            if not old_password or not new_password or not confirm_password:
                st.error("請填寫所有欄位")
            elif new_password != confirm_password:
                st.error("新密碼與確認密碼不一致")
            elif len(new_password) < 4:
                st.error("新密碼長度至少 4 個字元")
            elif old_password == new_password:
                st.error("新密碼不能與舊密碼相同")
            else:
                username = st.session_state.get('username')
                success, message = change_password(username, old_password, new_password)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")


# ── 向後相容的匯出（供 new_dashboard.py 等匯入使用）──
def show_registration_page():
    """已棄用：註冊功能已整合至 new_dashboard.py 的申請帳號頁面"""
    st.warning("此功能已整合至主頁的「申請帳號」頁面")
