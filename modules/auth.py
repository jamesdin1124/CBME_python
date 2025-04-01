import streamlit as st
import hashlib
import json
import os

# 使用者權限定義
USER_ROLES = {
    'admin': '系統管理員',
    'teacher': '教師',
    'resident': '住院醫師',
    'student': '醫學生'
}

# 權限設定
PERMISSIONS = {
    'admin': {
        'can_view_all': True,
        'can_edit_all': True,
        'can_manage_users': True,
        'can_upload_files': True,
        'can_view_analytics': True
    },
    'teacher': {
        'can_view_all': True,
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': True,
        'can_view_analytics': True
    },
    'resident': {
        'can_view_all': False,
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': False,
        'can_view_analytics': False
    },
    'student': {
        'can_view_all': False,
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': False,
        'can_view_analytics': False
    }
}

def hash_password(password):
    """將密碼進行雜湊處理"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """從檔案載入使用者資料"""
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"載入使用者資料時發生錯誤：{str(e)}")
    return {}

def save_users(users):
    """儲存使用者資料到檔案"""
    try:
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"儲存使用者資料時發生錯誤：{str(e)}")

def authenticate_user(username, password):
    """驗證使用者身份"""
    users = load_users()
    if username in users and users[username]['password'] == hash_password(password):
        return users[username]['role']
    return None

def create_user(username, password, role, name):
    """建立新使用者"""
    users = load_users()
    if username in users:
        return False, "使用者名稱已存在"
    
    users[username] = {
        'password': hash_password(password),
        'role': role,
        'name': name
    }
    save_users(users)
    return True, "使用者建立成功"

def delete_user(username):
    """刪除使用者"""
    users = load_users()
    if username not in users:
        return False, "使用者不存在"
    
    del users[username]
    save_users(users)
    return True, "使用者刪除成功"

def update_user_role(username, new_role):
    """更新使用者權限"""
    users = load_users()
    if username not in users:
        return False, "使用者不存在"
    
    users[username]['role'] = new_role
    save_users(users)
    return True, "使用者權限更新成功"

def check_permission(role, permission):
    """檢查使用者是否有特定權限"""
    return PERMISSIONS.get(role, {}).get(permission, False)

def show_login_page():
    """顯示登入頁面"""
    st.title("臨床教師評核系統 - 登入")
    
    with st.form("login_form"):
        username = st.text_input("使用者名稱")
        password = st.text_input("密碼", type="password")
        submitted = st.form_submit_button("登入")
        
        if submitted:
            role = authenticate_user(username, password)
            if role:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = role
                st.session_state['user_name'] = load_users()[username]['name']
                st.success(f"歡迎回來，{st.session_state['user_name']}！")
                return True
            else:
                st.error("使用者名稱或密碼錯誤")
    return False

def show_user_management():
    """顯示使用者管理介面"""
    if not check_permission(st.session_state['role'], 'can_manage_users'):
        st.error("您沒有權限管理使用者")
        return
    
    st.title("使用者管理")
    
    # 新增使用者表單
    with st.expander("新增使用者"):
        with st.form("add_user_form"):
            new_username = st.text_input("使用者名稱")
            new_password = st.text_input("密碼", type="password")
            new_name = st.text_input("姓名")
            new_role = st.selectbox("權限", options=list(USER_ROLES.keys()), format_func=lambda x: USER_ROLES[x])
            submitted = st.form_submit_button("新增")
            
            if submitted:
                success, message = create_user(new_username, new_password, new_role, new_name)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # 使用者列表
    st.subheader("使用者列表")
    users = load_users()
    for username, user_data in users.items():
        with st.expander(f"{username} ({USER_ROLES[user_data['role']]})"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("刪除", key=f"delete_{username}"):
                    success, message = delete_user(username)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            with col2:
                new_role = st.selectbox(
                    "更新權限",
                    options=list(USER_ROLES.keys()),
                    index=list(USER_ROLES.keys()).index(user_data['role']),
                    key=f"role_{username}"
                )
                if new_role != user_data['role']:
                    success, message = update_user_role(username, new_role)
                    if success:
                        st.success(message)
                    else:
                        st.error(message) 