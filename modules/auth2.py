import streamlit as st
import hashlib
import json
import os

# ¨?�¥ÎªÌ¨¤¦â©w¸q
USER_ROLES = {
    'admin': '¨t²?�ºÞ²z­û',
    'teacher': '¥Dªv??å®v',
    'resident': '¦í°|??å®v',
    'student': '¹ê²?��?å¾?�¥�?'
}

# ??v­­³]©w
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
        'can_view_analytics': False,
        'can_view_own_data': True
    }
}

def hash_password(password):
    """±N±K½X¶i¦æ??ø´ê³B²z"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """¸ü¤J¨?�¥ÎªÌ¸ê®�?±q JSON ???�®�?"""
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"¸ü¤J¨?�¥ÎªÌ¸ê®�?®?�µo¥?�¿ù»~¡G{str(e)}")
    return {}

def save_users(users):
    """??x¦s¨?�¥ÎªÌ¸ê®�?¨ì JSON ???�®�?"""
    try:
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"??x¦s¨?�¥ÎªÌ¸ê®�?®?�µo¥?�¿ù»~¡G{str(e)}")

def authenticate_user(username, password):
    """??ç???�¨Ï¥ÎªÌµn¤J"""
    users = load_users()
    if username in users and users[username]['password'] == hash_password(password):
        return users[username]['role']
    return None

def create_user(username, password, role, name, student_id=None):
    """³?�«Ø·s¨?�¥ÎªÌ±b¸¹"""
    users = load_users()
    if username in users:
        return False, "¨?�¥ÎªÌ¦Wº?�¤w¦s¦b"
    
    user_data = {
        'password': hash_password(password),  # ??x¦s??ø´ê«áªº±K½X
        'role': role,
        'name': name
    }
    
    # ¦pªG¬O¾?�¥Í¥B¦³¾?�¸¹¡A«h??x¦s¾?�¸�?
    if role == 'student' and student_id:
        user_data['student_id'] = student_id
    
    users[username] = user_data
    save_users(users)
    return True, "¨?�¥ÎªÌµù¥U¦¨¥\"

def delete_user(username):
    """§R°£¨?�¥ÎªÌ±b¸¹"""
    users = load_users()
    if username not in users:
        return False, "¨?�¥ÎªÌ¤£¦s¦b"
    
    del users[username]
    save_users(users)
    return True, "¨?�¥ÎªÌ§R°£¦¨¥\"

def update_user_role(username, new_role):
    """§ó·s¨?�¥ÎªÌ¨¤¦�?"""
    users = load_users()
    if username not in users:
        return False, "¨?�¥ÎªÌ¤£¦s¦b"
    
    users[username]['role'] = new_role
    save_users(users)
    return True, "¨?�¥ÎªÌ¨¤¦â§ó·s¦¨¥\"

def check_permission(role, permission):
    """???�¬d¨?�¥ÎªÌ¬O§_¦³¯S©w??v­­"""
    return PERMISSIONS.get(role, {}).get(permission, False)

def show_login_page():
    """??ã¥?�µn¤J­¶­±"""
    st.title("??{§?�¯à¤Oµû¦ô¨t²?? - ¨?�¥ÎªÌµn¤J")
    
    with st.form("login_form"):
        username = st.text_input("¨?�¥ÎªÌ¦Wº??")
        password = st.text_input("±K½X", type="password")
        submitted = st.form_submit_button("µn¤J")
        
        if submitted:
            role = authenticate_user(username, password)
            if role:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = role
                user = load_users()[username]
                st.session_state['user_name'] = user['name']
                
                # ¦pªG¬O¾?�¥Í¡A??x¦s¾?�¸¹¸ê°T
                if role == 'student':
                    if 'student_id' in user:
                        st.session_state['student_id'] = user['student_id']
                    else:
                        st.error("¾?�¥Í±b¸¹¯?�¤Ö¾Ç¸¹¸ê°T¡A½?��?p??´º?�²z­û¨ó§U³B²z")
                        return False
                
                st.success(f"??wªï¦^¨?�¡A{st.session_state['user_name']}¡I")
                return True
            else:
                st.error("¨?�¥ÎªÌ¦Wº?�©Î±K½X¿ù»~")
    return False

def show_user_management():
    """??ã¥?�¨Ï¥ÎªÌºÞ²z­¶­±"""
    if not check_permission(st.session_state['role'], 'can_manage_users'):
        st.error("±z¨S¦³??v­­º?�²z¨?�¥Îª�?")
        return
    
    st.title("¨?�¥ÎªÌºÞ²z")
    
    # ³?�«Ø¨â­Ó¤�?­¶¡G·s¼W¨?�¥ÎªÌ©Mº?�²z²{¦³¨?�¥Îª�?
    tab1, tab2 = st.tabs(["·s¼W¨?�¥Îª�?", "º?�²z²{¦³¨?�¥Îª�?"])
    
    with tab1:
        # ·s¼W¨?�¥ÎªÌªí³�?
        with st.expander("·s¼W¨?�¥Îª�?"):
            with st.form("add_user_form"):
                new_username = st.text_input("¨?�¥ÎªÌ¦Wº??")
                new_password = st.text_input("±K½X", type="password")
                new_name = st.text_input("©m¦W")
                new_role = st.selectbox("¨¤¦â", options=list(USER_ROLES.keys()), format_func=lambda x: USER_ROLES[x])
                submitted = st.form_submit_button("·s¼W¨?�¥Îª�?")
                
                if submitted:
                    success, message = create_user(new_username, new_password, new_role, new_name)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        # ??ã¥?�²{¦³¨?�¥ÎªÌ¦Cªí
        st.subheader("²{¦³¨?�¥ÎªÌ¦Cªí")
        users = load_users()
        for username, user_data in users.items():
            with st.expander(f"{username} ({USER_ROLES[user_data['role']]})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**©m¦W¡G** {user_data['name']}")
                    st.write(f"**¨¤¦â¡G** {USER_ROLES[user_data['role']]}")
                    if 'student_id' in user_data:
                        st.write(f"**¾?�¸¹¡G** {user_data['student_id']}")
                
                with col2:
                    if st.button(f"§R°£ {username}", key=f"delete_{username}"):
                        success, message = delete_user(username)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    # ¨¤¦â§ó·s
                    new_role = st.selectbox(
                        "§ó·s¨¤¦â",
                        options=list(USER_ROLES.keys()),
                        index=list(USER_ROLES.keys()).index(user_data['role']),
                        format_func=lambda x: USER_ROLES[x],
                        key=f"role_{username}"
                    )
                    
                    if new_role != user_data['role']:
                        if st.button(f"§ó·s {username} ¨¤¦â", key=f"update_role_{username}"):
                            success, message = update_user_role(username, new_role)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

def show_registration_page():
    """??ã¥?�µù¥U­¶­±"""
    st.title("¨?�¥ÎªÌµù¥U")
    
    with st.form("registration_form"):
        username = st.text_input("¨?�¥ÎªÌ¦Wº??")
        password = st.text_input("±K½X", type="password")
        confirm_password = st.text_input("½T»{±K½X", type="password")
        name = st.text_input("©m¦W")
        role = st.selectbox("¨¤¦â", options=list(USER_ROLES.keys()), format_func=lambda x: USER_ROLES[x])
        
        # ¦pªG¬O¾?�¥Í¡A»?�­n¿é¤J¾?�¸�?
        student_id = None
        if role == 'student':
            student_id = st.text_input("¾?�¸�?")
        
        submitted = st.form_submit_button("µù¥U")
        
        if submitted:
            # ??ç???�¿é¤J
            if not all([username, password, confirm_password, name]):
                st.error("½?�¶ñ¼g©?�¦³¥²­n??æ¦ì")
                return False
            
            if password != confirm_password:
                st.error("±K½X»P½T»{±K½X¤£¤@­P")
                return False
            
            if len(password) < 6:
                st.error("±K½Xªø«?�¦Ü¤Ö»Ý­n 6 ­?�¦r¤¸")
                return False
            
            if role == 'student' and not student_id:
                st.error("¾?�¥Í¥²¶·´£¨Ñ¾Ç¸�?")
                return False
            
            # ³?�«Ø¨Ï¥Îª�?
            success, message = create_user(username, password, role, name, student_id)
            if success:
                st.success(message)
                st.info("½?�¨Ï¥Î·s±b¸¹µn¤J¨t²??")
                return True
            else:
                st.error(message)
                return False
    
    return False

def show_change_password_page():
    """??ã¥?�±K½X­?�§ï­¶­�?"""
    st.title("­?�§ï±K½X")
    
    # ???�¬d¬O§_¤wµn¤J
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.error("½?�¥ýµn¤J¨t²??")
        return False
    
    current_username = st.session_state.get('username')
    current_role = st.session_state.get('role')
    
    st.info(f"¥?�«eµn¤J¨?�¥ÎªÌ¡G{current_username} ({USER_ROLES.get(current_role, current_role)})")
    
    with st.form("change_password_form"):
        current_password = st.text_input("¥?�«e±K½X", type="password", help="½?�¿é¤J±z¥?�«eªº±K½X¥H??ç???�¨­¥�?")
        new_password = st.text_input("·s±K½X", type="password", help="½?�¿é¤J·sªº±K½X")
        confirm_password = st.text_input("½T»{·s±K½X", type="password", help="½?�¦A¦¸¿é¤J·s±K½X¥H½T»{")
        
        submitted = st.form_submit_button("­?�§ï±K½X")
        
        if submitted:
            # ??ç???�¿é¤J
            if not all([current_password, new_password, confirm_password]):
                st.error("½?�¶ñ¼g©?�¦³�?æ¦ì")
                return False
            
            if new_password != confirm_password:
                st.error("·s±K½X»P½T»{±K½X¤£¤@­P")
                return False
            
            if len(new_password) < 6:
                st.error("·s±K½Xªø«?�¦Ü¤Ö»Ý­n 6 ­?�¦r¤¸")
                return False
            
            # ??ç???�¥Ø«e±K½X
            if not authenticate_user(current_username, current_password):
                st.error("¥?�«e±K½X¿ù»~")
                return False
            
            # ­?�§ï±K½X
            success, message = change_user_password(current_username, new_password)
            if success:
                st.success(message)
                st.info("½?�¨Ï¥Î·s±K½X­«·sµn¤J")
                # µn¥X¨?�¥Îª�?
                st.session_state['logged_in'] = False
                st.session_state['username'] = None
                st.session_state['role'] = None
                st.session_state['user_name'] = None
                return True
            else:
                st.error(message)
                return False
    
    return False

def change_user_password(username, new_password):
    """­?�§ï¨Ï¥ÎªÌ±K½X"""
    users = load_users()
    if username not in users:
        return False, "¨?�¥ÎªÌ¤£¦s¦b"
    
    # ??ø´ê·s±K½X
    hashed_password = hash_password(new_password)
    
    # §ó·s±K½X
    users[username]['password'] = hashed_password
    save_users(users)
    return True, "±K½X­?�§ï¦¨¥\"

def show_admin_password_management():
    """??ã¥?�ºÞ²z­û±K½Xº?�²z­¶­±"""
    if not check_permission(st.session_state.get('role'), 'can_manage_users'):
        st.error("±z¨S¦³??v­­º?�²z¨?�¥ÎªÌ±K½X")
        return
    
    st.title("±K½Xº?�²z")
    
    users = load_users()
    
    # ¿ï¾?�¨Ï¥Îª�?
    user_options = list(users.keys())
    selected_user = st.selectbox(
        "¿ï¾?�­n­?�§ï±K½Xªº¨?�¥Îª�?",
        options=user_options,
        format_func=lambda x: f"{x} ({USER_ROLES.get(users[x]['role'], users[x]['role'])}) - {users[x]['name']}"
    )
    
    if selected_user:
        st.info(f"¿ï¾?�ªº¨Ï¥ÎªÌ¡G{selected_user}")
        
        with st.form("admin_change_password_form"):
            new_password = st.text_input("·s±K½X", type="password", help="½?�¿é¤J·sªº±K½X")
            confirm_password = st.text_input("½T»{·s±K½X", type="password", help="½?�¦A¦¸¿é¤J·s±K½X¥H½T»{")
            
            submitted = st.form_submit_button("­?�§ï±K½X")
            
            if submitted:
                if not all([new_password, confirm_password]):
                    st.error("½?�¶ñ¼g©?�¦³�?æ¦ì")
                    return
                
                if new_password != confirm_password:
                    st.error("·s±K½X»P½T»{±K½X¤£¤@­P")
                    return
                
                if len(new_password) < 6:
                    st.error("·s±K½Xªø«?�¦Ü¤Ö»Ý­n 6 ­?�¦r¤¸")
                    return
                
                success, message = change_user_password(selected_user, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)
