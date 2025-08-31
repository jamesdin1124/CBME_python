import streamlit as st
import hashlib
import json
import os
import gspread
from google.oauth2.service_account import Credentials
import re

# 使用???權�?��?�義
USER_ROLES = {
    'admin': '系統管�???��',
    'teacher': '??�師',
    'resident': '住院??�師',
    'student': '??�學???'
}

# 權�?�設�?
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
    """�?�?碼�?��?��?��?��?��??"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """從�?��??載�?�使?��???�????"""
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"載�?�使?��???�???��???��??�錯誤�?�{str(e)}")
    return {}

def save_users(users):
    """??��?�使?��???�???��?��?��??"""
    try:
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"??��?�使?��???�???��???��??�錯誤�?�{str(e)}")

def authenticate_user(username, password):
    """驗�?�使?��???身份"""
    users = load_users()
    if username in users and users[username]['password'] == hash_password(password):
        return users[username]['role']
    return None

def create_user(username, password, role, name, student_id=None):
    """建�?�新使用???"""
    users = load_users()
    if username in users:
        return False, "使用?????�稱已�?�在"
    
    user_data = {
        'password': password,  # ?��?��使用??��?��??�?碼�?��?��??
        'role': role,
        'name': name
    }
    
    # �???�是學�??，添??�學???
    if role == 'student' and student_id:
        user_data['student_id'] = student_id
    
    users[username] = user_data
    save_users(users)
    return True, "使用???建�?��?��??"

def delete_user(username):
    """?��?��使用???"""
    users = load_users()
    if username not in users:
        return False, "使用???不�?�在"
    
    del users[username]
    save_users(users)
    return True, "使用????��?��??��??"

def update_user_role(username, new_role):
    """?��?��使用???權�??"""
    users = load_users()
    if username not in users:
        return False, "使用???不�?�在"
    
    users[username]['role'] = new_role
    save_users(users)
    return True, "使用???權�?�更?��??��??"

def check_permission(role, permission):
    """檢查使用????��?��??�特定�?��??"""
    return PERMISSIONS.get(role, {}).get(permission, False)

def show_login_page():
    """顯示?��??��???��"""
    st.title("?��床�?�師評核系統 - ?��???")
    
    with st.form("login_form"):
        username = st.text_input("使用?????�稱")
        password = st.text_input("�?�?", type="password")
        submitted = st.form_submit_button("?��???")
        
        if submitted:
            role = authenticate_user(username, password)
            if role:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = role
                user = load_users()[username]
                st.session_state['user_name'] = user['name']
                
                # �???�是學�??�???��?�學???
                if role == 'student':
                    if 'student_id' in user:
                        st.session_state['student_id'] = user['student_id']
                    else:
                        st.error("?��不�?�學??��??訊�?��?��?�繫管�???��")
                        return False
                
                st.success(f"歡�?��?��??，{st.session_state['user_name']}�?")
                return True
            else:
                st.error("使用?????�稱??��??碼錯�?")
    return False

def show_user_management():
    """顯示使用???管�??介面"""
    if not check_permission(st.session_state['role'], 'can_manage_users'):
        st.error("??��?��?��?��?�管???使用???")
        return
    
    st.title("使用???管�??")
    
    # 添�?��?��???��????��顯示帳�?�管??????帳�?�審?��
    tab1, tab2 = st.tabs(["帳�?�管???", "帳�?�審?��"])
    
    with tab1:
        # ?��增使?��???表單
        with st.expander("?��增使?��???"):
            with st.form("add_user_form"):
                new_username = st.text_input("使用?????�稱")
                new_password = st.text_input("�?�?", type="password")
                new_name = st.text_input("姓�??")
                new_role = st.selectbox("權�??", options=list(USER_ROLES.keys()), format_func=lambda x: USER_ROLES[x])
                submitted = st.form_submit_button("?���?")
                
                if submitted:
                    success, message = create_user(new_username, new_password, new_role, new_name)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        # 使用?????�表
        st.subheader("使用?????�表")
        users = load_users()
        for username, user_data in users.items():
            with st.expander(f"{username} ({USER_ROLES[user_data['role']]})"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("?��?��", key=f"delete_{username}"):
                        success, message = delete_user(username)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                with col2:
                    new_role = st.selectbox(
                        "?��?��權�??",
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
    
    with tab2:
        # 顯示帳�?�審?��??�面
        show_user_approval()

def extract_spreadsheet_id(url):
    """�? Google 試�?�表 URL 中�?��?? spreadsheet ID"""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return None

def setup_google_connection():
    """設�?��?? Google API ???????��"""
    try:
        # 驗�?? secrets 設�??
        if not hasattr(st, 'secrets') or not st.secrets:
            st.error("?��?��??�任�? Secrets 設�??")
            st.info("請確�? .streamlit/secrets.toml 檔�??存在且�???���?確�??設�?��?��?�在 Streamlit Cloud 中設�? Secrets")
            
            # �???��?��?? secrets，�????��?�本?��???件方式�??保�?��?�方法�?��?��?��?��??
            st.warning("??�試使用?��?��??��?��??�?...")
            return setup_google_connection_local()
            
        # 檢查 secrets ??�容
        if "gcp_service_account" not in st.secrets:
            st.error("?�� Secrets 中未?��??? gcp_service_account 設�??")
            st.info("請確�? Secrets 中�???��完整??? Google API ??��?�設�?")
            
            # �???��?��?�正確�?? secrets ??�容，�????��?�本?��???件方�?
            st.warning("??�試使用?��?��??��?��??�?...")
            return setup_google_connection_local()
            
        # 檢查�?�??????��?��??�?
        required_fields = [
            "type", "project_id", "private_key_id", "private_key",
            "client_email", "client_id", "auth_uri", "token_uri",
            "auth_provider_x509_cert_url", "client_x509_cert_url"
        ]
        
        missing_fields = [field for field in required_fields 
                         if field not in st.secrets.gcp_service_account]
        
        if missing_fields:
            st.error(f"缺�?��??�??????��?��??位�?�{', '.join(missing_fields)}")
            st.info("請確保�????��??�??????��?��??位�?�已�?確設�?")
            
            # �???�缺少�??�?�?位�?��????��?�本?��???件方�?
            st.warning("??�試使用?��?��??��?��??�?...")
            return setup_google_connection_local()
            
        try:
            # 構建??��?��?��??
            credentials = {
                "type": st.secrets["gcp_service_account"]["type"],
                "project_id": st.secrets["gcp_service_account"]["project_id"],
                "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
                "private_key": st.secrets["gcp_service_account"]["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["gcp_service_account"]["client_email"],
                "client_id": st.secrets["gcp_service_account"]["client_id"],
                "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
                "token_uri": st.secrets["gcp_service_account"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
            }
            
            # 顯示??��?�帳??��??�?
            st.info(f"使用??��?�帳???: {credentials['client_email']}")
            st.info(f"????�� ID: {credentials['project_id']}")
            
            # 設�?? Google API �????
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/cloud-platform'
            ]
            
            try:
                # 建�?��?��??
                creds = Credentials.from_service_account_info(credentials, scopes=scope)
                client = gspread.authorize(creds)
                
                # 測試????��
                try:
                    test_url = "https://docs.google.com/spreadsheets/d/1I2GzYptiPvhN5dT3_qzVXlIAoPeI8S9MaTVzxfDVjrw/edit?gid=0#gid=0"
                    spreadsheet_id = extract_spreadsheet_id(test_url)
                    
                    if spreadsheet_id:
                        try:
                            test_sheet = client.open_by_key(spreadsheet_id)
                            st.success(f"??��????��?�試算表: {test_sheet.title}")
                        except Exception as sheet_e:
                            st.warning(f"測試?��定試算表????��?��，�?? API ????��?��??�正�?: {str(sheet_e)}")
                            st.info(f"請確保� {credentials['client_email']} ��試算表�享�表並給�編輯權�")
                    
                    # �出�試算表以確保鎥��
                    spreadsheets = client.list_spreadsheet_files()
                    st.success(f"Google API ����）� {len(spreadsheets)} �試算表")
                    return client
                except Exception as test_e:
                    st.error(f"��測試失��{str(test_e)}")
                    st.warning("�試使用��������...")
                    return setup_google_connection_local()
            except Exception as e:
                st.error(f"建� Google API 認�晼�錯誤�{str(e)}")
                st.warning("�試使用��������...")
                return setup_google_connection_local()
        except Exception as e:
            st.error(f"�� Streamlit Secrets ���錯誤�{str(e)}")
            st.warning("�試使用��������...")
            return setup_google_connection_local()
    except Exception as e:
        st.error(f"�� Google API ���錯誤�{str(e)}")
        import traceback
        st.error(f"��誤�: {traceback.format_exc()}")
        st.warning("�試使用��������...")
        return setup_google_connection_local()

def setup_google_connection_local():
    """使用����檔�設�� Google API ��＊方法�"""
    try:
        # ��目��曮路�
        current_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(current_dir, 'credentials.json')
        
        # 檢查 credentials.json 檔是��存在
        if not os.path.exists(credentials_path):
            error_msg = f"���� credentials.json 檔�，��路徑�{credentials_path}"
            st.error(error_msg)
            st.info(f"���工作目: {os.getcwd()}")
            st.info(f"模目: {current_dir}")
            # �試�出模目檔�
            try:
                files = os.listdir(current_dir)
                st.info(f"模目檔�: {', '.join(files)}")
            except Exception as list_e:
                st.error(f"�出��檔懺��: {str(list_e)}")
            return None
        
        st.info(f"�������: {credentials_path}")
        # 檢查檔�大�確保�是空��
        file_size = os.path.getsize(credentials_path)
        if file_size == 0:
            st.error(f"����大��0／��是空��")
            return None
        st.info(f"����大�: {file_size} bytes")
        
        # �試讖���容以確保嘯�� JSON
        try:
            with open(credentials_path, 'r') as f:
                cred_content = json.load(f)
                # 檢查�鍵�位是��存在
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in cred_content]
                if missing_fields:
                    st.error(f"����缺�����: {', '.join(missing_fields)}")
                    return None
                
                # 檢查科����
                private_key = cred_content.get('private_key', '')
                if not private_key.startswith('-----BEGIN PRIVATE KEY-----') or not private_key.endswith('-----END PRIVATE KEY-----\n'):
                    st.error("科���式�正確��確保含�確�尾標����符")
                    # 顯示科���20��符����診斷
                    st.error(f"科���: {private_key[:20]}...")
                    st.error(f"科�結尾: ...{private_key[-20:]}")
                    return None
                
                # 檢查科�中是����足���符
                if private_key.count('\n') < 2:
                    st.error("科�缺��覛�符／��在�製��中丟失")
                    return None
                
                st.info(f"���格式正確�雮 ID: {cred_content.get('project_id')}")
                st.info(f"��帳��箱: {cred_content.get('client_email')}")
                
                # 檢查��步
                import datetime
                import time
                local_time = datetime.datetime.now()
                utc_time = datetime.datetime.utcnow()
                time_diff = abs((local_time - utc_time).total_seconds() - time.timezone)
                if time_diff > 300:  # 妜本����UTC�差���5(��)
                    st.warning(f"系統�可���步，當�本��: {local_time}，UTC: {utc_time}")
                    st.warning("���步����致JWT驗�失")
        except json.JSONDecodeError as json_e:
            st.error(f"����不是�� JSON ���: {str(json_e)}")
            return None
        except Exception as read_e:
            st.error(f"讖���懺��: {str(read_e)}")
            return None
            
        # 設� Google API �
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/cloud-platform'
        ]
        
        # 建���
        try:
            # 顯示使用�建令修復瑰建議
            st.info("妜�纇���JWT簽�錯誤����新下���帳��鑰�修復瑰���")
            st.info("��以使��以�命令䟥�瑰�����正確��符: cat modules/credentials.json | grep private_key")
            
            # �試���建��帳�信���是主薹�
            from google.oauth2 import service_account
            
            try:
                # ����從JSON�容構建認�
                st.info("�試使用��方式建立��帳...")
                
                # 修復����科���式��
                if 'private_key' in cred_content:
                    # 1. 確�瑰����尾�正確�標�
                    pk = cred_content['private_key']
                    if not pk.startswith('-----BEGIN PRIVATE KEY-----\n'):
                        pk = '-----BEGIN PRIVATE KEY-----\n' + pk.lstrip('-----BEGIN PRIVATE KEY-----')
                    if not pk.endswith('\n-----END PRIVATE KEY-----\n'):
                        pk = pk.rstrip('-----END PRIVATE KEY-----\n') + '\n-----END PRIVATE KEY-----\n'
                        
                    # 2. �試確��足夠��符 - RSA科��常�64字符�下��符
                    import re
                    lines = pk.split('\n')
                    new_lines = [lines[0]]  # BEGIN�
                    
                    # ��中��BASE64編碼��
                    body = ''.join([l for l in lines[1:-2] if l])  # 併��BEGIN/END行�移��空�
                    # �64��符�����符
                    chunks = [body[i:i+64] for i in range(0, len(body), 64)]
                    new_lines.extend(chunks)
                    new_lines.append(lines[-2])  # END�
                    new_lines.append('')  # 確��後��空�
                    
                    # ����科�
                    fixed_pk = '\n'.join(new_lines)
                    cred_content['private_key'] = fixed_pk
                    st.info("已�試修復科����")
                
                # 使用修復後��帳�信
                creds = service_account.Credentials.from_service_account_info(
                    cred_content, 
                    scopes=scope
                )
                st.info("使用��建立��帳��")
                
            except Exception as manual_error:
                st.error(f"��建立��懺��: {str(manual_error)}")
                
                # 妜��方式失����使��檔�
                try:
                    st.warning("��方式失��試使用檔方�...")
                    creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
                    st.info("使用檔�建���帳��")
                except Exception as file_error:
                    st.error(f"從��建���懺��: {str(file_error)}")
                    return None
            
            client = gspread.authorize(creds)
            
            # 測試��
            try:
                # ��測試�試算表��是�出�試算表
                test_url = "https://docs.google.com/spreadsheets/d/1I2GzYptiPvhN5dT3_qzVXlIAoPeI8S9MaTVzxfDVjrw/edit?gid=0#gid=0"
                spreadsheet_id = extract_spreadsheet_id(test_url)
                if spreadsheet_id:
                    try:
                        test_sheet = client.open_by_key(spreadsheet_id)
                        st.info(f"���試算表: {test_sheet.title}")
                        return client
                    except Exception as sheet_e:
                        st.error(f"測試��特定試算表����: {str(sheet_e)}")
                        st.info("檢查����已��帳���試算表�享�表")
                        st.info(f"請� {cred_content.get('client_email')} ��試算表�享�表並給�編輯權�")
                        
                # 妜�面失��試�出�試算表
                spreadsheets = client.list_spreadsheet_files()
                st.info(f"��鎥 Google API，找 {len(spreadsheets)} �試算表")
                return client
            except Exception as test_e:
                st.error(f"測試������: {str(test_e)}")
                import traceback
                st.error(f"��誤詳: {traceback.format_exc()}")
                
                # ��解決建�
                st.error("JWT簽��揯���決方�:")
                st.info("1. �新�新��帳��鑰並��")
                st.info("2. 確����件未被修��，直��使用下�����")
                st.info("3. 檢查系統�是����")
                st.info("4. 確�Google Cloud��中已�用��API (Google Sheets API, Google Drive API)")
                st.info("5. 確���帳��被�用�撤��")
                return None
        except Exception as auth_e:
            st.error(f"� Google API ����: {str(auth_e)}")
            import traceback
            st.error(f"��誤詳: {traceback.format_exc()}")
            return None
            
    except Exception as e:
        st.error(f"�� Google API ������錯誤�{str(e)}")
        import traceback
        st.error(f"��誤�: {traceback.format_exc()}")
        st.warning("�試使用��������...")
        return setup_google_connection_local()

def show_registration_page():
    """顯示註�面"""
    st.title("��請帳")
    
    with st.form("registration_form"):
        username = st.text_input("使用�稱")
        password = st.text_input("��", type="password")
        confirm_password = st.text_input("確���", type="password")
        name = st.text_input("姓�")
        role = st.selectbox("身份", options=['student'], format_func=lambda x: USER_ROLES[x])
        
        # 妜是學�，添�學��
        student_id = None
        if role == 'student':
            student_id = st.text_input("學�")
        
        submitted = st.form_submit_button("��請帳")
        
        if submitted:
            if not username or not password or not name:
                st.error("請填寫��填��")
                return False
            
            if password != confirm_password:
                st.error("�次輸���碼�䇴")
                return False
            
            # 妜是學�，檢��學蘯��填寫
            if role == 'student' and not student_id:
                st.error("請填寫學")
                return False
            
            # 建�使��
            success, message = create_user(
                username=username,
                password=hash_password(password),
                role=role,
                name=name,
                student_id=student_id if role == 'student' else None
            )
            
            if success:
                st.success(message)
                return True
            else:
                st.error(message)
                return False
    
    return False

def show_user_approval():
    """顯示帳�審��管�介面"""
    if not check_permission(st.session_state['role'], 'can_manage_users'):
        st.error("�����管使用")
        return
    
    st.subheader("帳�審��管�")
    
    client = setup_google_connection()
    if client is None:
        st.error("��鎥 Google Sheets")
        return
    
    # ����審核帳�
    try:
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1VZRYRrsSMNUKoWM32gc5D9FykCHm7IRgcmR1_qXx8_w/edit?resourcekey=&gid=1526949290#gid=1526949290"
        spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
        
        if not spreadsheet_id:
            st.error("���� Google Sheet ID")
            return
            
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet("Apply_auth")
            st.info(f"��鎥�帳�申請工作表")
        except Exception as ws_e:
            st.error(f"��不�Apply_auth工�表: {str(ws_e)}")
            return
            
        # ���� get_all_values ����數��並����
        # �樣��以��������振�
        all_values = worksheet.get_all_values()
        
        if not all_values:
            st.info("��請工作表�空")
            return
            
        # ������
        headers = all_values[0]
        
        # 顯示標���用��診斷
        st.write(f"工�表標�: {headers}")
        
        # 檢查����存在��
        status_col_idx = None
        username_col_idx = None
        name_col_idx = None
        role_col_idx = None
        apply_time_col_idx = None
        password_col_idx = None
        student_id_col_idx = None
        extension_col_idx = None
        email_col_idx = None
        
        for i, header in enumerate(headers):
            if header == "審核":
                status_col_idx = i
            elif header == "使用�稱":
                username_col_idx = i
            elif header == "姓�":
                name_col_idx = i
            elif header == "角色":
                role_col_idx = i
            elif header == "��請�":
                apply_time_col_idx = i
            elif header == "�碼���":
                password_col_idx = i
            elif header == "學�":
                student_id_col_idx = i
            elif header == "�":
                extension_col_idx = i
            elif header == "��子�件":
                email_col_idx = i
        
        # 檢查���������
        if status_col_idx is None or username_col_idx is None or name_col_idx is None or role_col_idx is None:
            st.error("工�表缺��覗�審核��使用�稱姓��角色�")
            return
        
        # 尕��������表
        records = []
        for row in all_values[1:]:  # 跳����
            if len(row) <= max(status_col_idx, username_col_idx, name_col_idx, role_col_idx):
                continue  # 跳����整�
                
            record = {
                "審核": row[status_col_idx] if status_col_idx < len(row) else "",
                "使用�稱": row[username_col_idx] if username_col_idx < len(row) else "",
                "姓�": row[name_col_idx] if name_col_idx < len(row) else "",
                "角色": row[role_col_idx] if role_col_idx < len(row) else "",
            }
            
            # 添�可��段
            if apply_time_col_idx is not None and apply_time_col_idx < len(row):
                record["��請�"] = row[apply_time_col_idx]
            if password_col_idx is not None and password_col_idx < len(row):
                record["�碼���"] = row[password_col_idx]
            if student_id_col_idx is not None and student_id_col_idx < len(row):
                record["學�"] = row[student_id_col_idx]
            if extension_col_idx is not None and extension_col_idx < len(row):
                record["�"] = row[extension_col_idx]
            if email_col_idx is not None and email_col_idx < len(row):
                record["��子�件"] = row[email_col_idx]
                
            records.append(record)
        
        # �濾�審核帳�
        pending_records = [r for r in records if r.get("審核") == "�審核"]
        approved_records = [r for r in records if r.get("審核") == "已審��"]
        rejected_records = [r for r in records if r.get("審核") == "已��"]
        
        # 顯示�審核帳蕸��已審核帳蕸
        st.info(f" {len(pending_records)} �帳��審核，{len(approved_records)} �帳�已審核，{len(rejected_records)} �帳�已��")
        
        if pending_records:
            st.subheader("�審核帳�")
            
            for i, record in enumerate(pending_records):
                with st.expander(f"{record.get('姓�')} ({record.get('使用�稱')}) - {record.get('角色')}"):
                    col1, col2, col3 = st.columns(3)
                    
                    # 顯示帳�詳細��
                    st.write(f"��請�: {record.get('��請�', '��記�')}")
                    st.write(f"身份: {record.get('角色')}")
                    if record.get('學�'):
                        st.write(f"學�: {record.get('學�')}")
                    st.write(f"�: {record.get('�', '��填寫')}")
                    st.write(f"��子�件: {record.get('��子�件', '��填寫')}")
                    
                    # 審核����
                    with col1:
                        if st.button("��", key=f"approve_{i}"):
                            try:
                                # 1. ����Google Sheet
                                found = False
                                for row_idx, row in enumerate(all_values[1:], start=2):
                                    if (username_col_idx < len(row) and 
                                        row[username_col_idx] == record.get('使用�稱')):
                                        worksheet.update_cell(row_idx, status_col_idx + 1, "已審��")
                                        found = True
                                        break
                                
                                if not found:
                                    st.error(f"��在工�表中找�使���稱 {record.get('使用�稱')} 記�")
                                    return
                                
                                # 2. �帳�寫�本��users.json
                                role_code = None
                                for code, name in USER_ROLES.items():
                                    if name == record.get('角色'):
                                        role_code = code
                                        break
                                
                                if not role_code:
                                    role_code = 'student'  # �設�學
                                
                                # ����使用��請��碼���
                                success, message = create_user(
                                    username=record.get('使用�稱'),
                                    password=record.get('�碼���'),  # ����使用��請��碼���
                                    role=role_code,
                                    name=record.get('姓�'),
                                    student_id=record.get('學�')  # 添�學
                                )
                                
                                if success:
                                    st.success(f"已核 {record.get('姓�')} 帳�申�")
                                    st.rerun()
                                else:
                                    st.error(f"帳�建立失: {message}")
                                    
                            except Exception as e:
                                st.error(f"��帳虼�錯�: {str(e)}")
                                import traceback
                                st.error(f"��誤詳: {traceback.format_exc()}")
                    
                    with col2:
                        if st.button("��", key=f"reject_{i}"):
                            try:
                                # ����Google Sheet���寫�本����
                                # ���該記��
                                found = False
                                for row_idx, row in enumerate(all_values[1:], start=2):  # 從第2行���索引�2��
                                    if (username_col_idx < len(row) and 
                                        row[username_col_idx] == record.get('使用�稱')):
                                        # ����
                                        worksheet.update_cell(row_idx, status_col_idx + 1, "已��")  # API索��1��
                                        found = True
                                        break
                                
                                if not found:
                                    st.error(f"��在工�表中找�使���稱 {record.get('使用�稱')} 記�")
                                    return
                                
                                st.success(f"已�� {record.get('姓�')} 帳�申�")
                                st.rerun()
                            except Exception as e:
                                st.error(f"��帳���錯�: {str(e)}")
                                import traceback
                                st.error(f"��誤詳: {traceback.format_exc()}")
                    
                    with col3:
                        reason = st.text_input("����", key=f"reason_{i}")
                        
        else:
            st.info("������審核帳�")
            
        # 顯示已審��帳�歷史
        if st.checkbox("顯示已審��帳�歷史"):
            with st.expander("已審��帳�"):
                if approved_records:
                    for record in approved_records:
                        st.write(f"{record.get('姓�')} ({record.get('使用�稱')}) - {record.get('角色')} - {record.get('��請�', '��記�')}")
                else:
                    st.info("沒�已審核帳�")
        
        # 顯示已��帳歷史
        if st.checkbox("顯示已��帳歷史"):
            with st.expander("已��帳"):
                if rejected_records:
                    for record in rejected_records:
                        st.write(f"{record.get('姓�')} ({record.get('使用�稱')}) - {record.get('角色')} - {record.get('��請�', '��記�')}")
                else:
                    st.info("沒�已���帳�")
                
    except Exception as e:
        st.error(f"���審��賙晼�錯�: {str(e)}")
        import traceback
        st.error(f"��誤詳: {traceback.format_exc()}") 

def change_user_password(username, new_password):
    """�ק�ϥΪ̱K�X"""
    users = load_users()
    if username not in users:
        return False, "�ϥΪ̤��s�b"
    
    # ����s�K�X
    hashed_password = hash_password(new_password)
    
    # ��s�K�X
    users[username]['password'] = hashed_password
    save_users(users)
    return True, "�K�X�ק令�\"

def show_change_password_page():
    """��ܱK�X�קﭶ��"""
    st.title("�ק�K�X")
    
    # �ˬd�O�_�w�n�J
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.error("�Х��n�J�t��")
        return False
    
    current_username = st.session_state.get('username')
    current_role = st.session_state.get('role')
    
    st.info(f"�ثe�n�J�ϥΪ̡G{current_username} ({USER_ROLES.get(current_role, current_role)})")
    
    with st.form("change_password_form"):
        current_password = st.text_input("�ثe�K�X", type="password", help="�п�J�z�ثe���K�X�H���Ҩ���")
        new_password = st.text_input("�s�K�X", type="password", help="�п�J�s���K�X")
        confirm_password = st.text_input("�T�{�s�K�X", type="password", help="�ЦA����J�s�K�X�H�T�{")
        
        submitted = st.form_submit_button("�ק�K�X")
        
        if submitted:
            # ���ҿ�J
            if not all([current_password, new_password, confirm_password]):
                st.error("�ж�g�Ҧ����")
                return False
            
            if new_password != confirm_password:
                st.error("�s�K�X�P�T�{�K�X���@�P")
                return False
            
            if len(new_password) < 6:
                st.error("�s�K�X���צܤֻݭn 6 �Ӧr��")
                return False
            
            # ���ҥثe�K�X
            if not authenticate_user(current_username, current_password):
                st.error("�ثe�K�X���~")
                return False
            
            # �ק�K�X
            success, message = change_user_password(current_username, new_password)
            if success:
                st.success(message)
                st.info("�Шϥηs�K�X���s�n�J")
                # �n�X�ϥΪ�
                st.session_state['logged_in'] = False
                st.session_state['username'] = None
                st.session_state['role'] = None
                st.session_state['user_name'] = None
                return True
            else:
                st.error(message)
                return False
    
    return False

def show_admin_password_management():
    """��ܺ޲z���K�X�޲z����"""
    if not check_permission(st.session_state.get('role'), 'can_manage_users'):
        st.error("�z�S���v���޲z�ϥΪ̱K�X")
        return
    
    st.title("�K�X�޲z")
    
    users = load_users()
    
    # ��ܨϥΪ�
    user_options = list(users.keys())
    selected_user = st.selectbox(
        "��ܭn�ק�K�X���ϥΪ�",
        options=user_options,
        format_func=lambda x: f"{x} ({USER_ROLES.get(users[x]['role'], users[x]['role'])}) - {users[x]['name']}"
    )
    
    if selected_user:
        st.info(f"��ܪ��ϥΪ̡G{selected_user}")
        
        with st.form("admin_change_password_form"):
            new_password = st.text_input("�s�K�X", type="password", help="�п�J�s���K�X")
            confirm_password = st.text_input("�T�{�s�K�X", type="password", help="�ЦA����J�s�K�X�H�T�{")
            
            submitted = st.form_submit_button("�ק�K�X")
            
            if submitted:
                if not all([new_password, confirm_password]):
                    st.error("�ж�g�Ҧ����")
                    return
                
                if new_password != confirm_password:
                    st.error("�s�K�X�P�T�{�K�X���@�P")
                    return
                
                if len(new_password) < 6:
                    st.error("�s�K�X���צܤֻݭn 6 �Ӧr��")
                    return
                
                success, message = change_user_password(selected_user, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message) 