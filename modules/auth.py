import streamlit as st
import hashlib
import json
import os
import gspread
from google.oauth2.service_account import Credentials
import re
import pandas as pd

# 使用者權限定義
USER_ROLES = {
    'admin': '系統管理員',
    'teacher': '主治醫師',
    'resident': '住院醫師',
    'student': 'UGY'
}

# 權限設定
PERMISSIONS = {
    'admin': {
        'can_view_all': True,           # 管理員可以看到全部資料
        'can_edit_all': True,
        'can_manage_users': True,
        'can_upload_files': True,
        'can_view_analytics': True,
        'can_view_department_data': True,  # 可以查看所有科別資料
        'can_view_ugy_data': True,          # 可以查看所有UGY資料
        'can_view_pgy_data': True,          # 可以查看所有PGY資料
        'can_view_resident_data': True      # 可以查看所有住院醫師資料
    },
    'teacher': {
        'can_view_all': False,          # 主治醫師不能看到全部資料
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': True,
        'can_view_analytics': True,
        'can_view_department_data': True,   # 可以看到自己科住院醫師的資料
        'can_view_ugy_data': True,          # 可以看到所有UGY資料
        'can_view_pgy_data': True,          # 可以看到所有PGY資料
        'can_view_resident_data': True     # 可以看到自己科的住院醫師資料
    },
    'resident': {
        'can_view_all': False,          # 住院醫師不能看到全部資料
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': False,
        'can_view_analytics': False,
        'can_view_department_data': False,  # 不能看到其他科資料
        'can_view_ugy_data': True,          # 可以看到所有UGY資料
        'can_view_pgy_data': False,         # 不能看到PGY資料
        'can_view_resident_data': False    # 修改：住院醫師不能看到住院醫師資料（除非特別授權）
    },
    'student': {
        'can_view_all': False,          # UGY不能看到全部資料
        'can_edit_all': False,
        'can_manage_users': False,
        'can_upload_files': False,
        'can_view_analytics': False,
        'can_view_department_data': False,  # 不能看到科別資料
        'can_view_ugy_data': True,          # 可以看到UGY EPA資料（會過濾為只顯示自己的）
        'can_view_pgy_data': False,         # 不能看到PGY資料
        'can_view_resident_data': False,   # 不能看到住院醫師資料
        'can_view_own_data': True          # 只能看到自己的資料
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

def create_user(username, password, role, name, student_id=None, department=None, extension=None, email=None):
    """建立新使用者"""
    users = load_users()
    if username in users:
        return False, "使用者名稱已存在"
    
    user_data = {
        'password': password,  # 直接使用傳入的密碼雜湊值
        'role': role,
        'name': name
    }
    
    # 如果是學生(UGY)，添加學號
    if role == 'student' and student_id:
        user_data['student_id'] = student_id
    
    # 添加科別資訊
    if department:
        user_data['department'] = department
    
    # 添加其他資訊
    if extension:
        user_data['extension'] = extension
    if email:
        user_data['email'] = email
    
    users[username] = user_data
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

def check_data_access_permission(user_role, user_department, target_data_type, target_department=None):
    """
    檢查使用者是否有權限存取特定類型的資料
    
    Args:
        user_role (str): 使用者角色
        user_department (str): 使用者所屬科別
        target_data_type (str): 目標資料類型 ('ugy', 'pgy', 'resident', 'department')
        target_department (str): 目標科別（僅在存取科別資料時需要）
    
    Returns:
        bool: 是否有權限存取
    """
    # 管理員可以存取所有資料
    if user_role == 'admin':
        return True
    
    # 檢查特定資料類型的權限
    if target_data_type == 'ugy':
        # UGY只能查看自己的資料，這個檢查需要在資料過濾層面處理
        return PERMISSIONS.get(user_role, {}).get('can_view_ugy_data', False)
    elif target_data_type == 'pgy':
        return PERMISSIONS.get(user_role, {}).get('can_view_pgy_data', False)
    elif target_data_type == 'resident':
        # 住院醫師資料需要額外檢查科別
        if user_role == 'teacher':
            # 主治醫師只能看自己科的住院醫師資料
            return user_department == target_department
        elif user_role == 'resident':
            # 住院醫師只能看自己的資料
            return user_department == target_department
        else:
            return PERMISSIONS.get(user_role, {}).get('can_view_resident_data', False)
    elif target_data_type == 'department':
        # 科別資料存取權限
        if user_role == 'teacher':
            # 主治醫師只能看自己科的資料
            return user_department == target_department
        else:
            return PERMISSIONS.get(user_role, {}).get('can_view_department_data', False)
    
    return False

def get_user_department(username):
    """獲取使用者的科別"""
    users = load_users()
    if username in users:
        return users[username].get('department', None)
    return None

def filter_data_by_permission(data, user_role, user_department, data_type):
    """
    根據使用者權限過濾資料
    
    Args:
        data (pd.DataFrame): 原始資料
        user_role (str): 使用者角色
        user_department (str): 使用者科別
        data_type (str): 資料類型
    
    Returns:
        pd.DataFrame: 過濾後的資料
    """
    if data is None or data.empty:
        return data
    
    # 管理員可以看到所有資料
    if user_role == 'admin':
        return data
    
    # 根據資料類型過濾
    if data_type == 'ugy':
        if not PERMISSIONS.get(user_role, {}).get('can_view_ugy_data', False):
            return pd.DataFrame()  # 返回空DataFrame
        # UGY資料：學生只能看自己的，其他人可以看全部
        if user_role == 'student':
            if '學號' in data.columns and 'student_id' in st.session_state:
                return data[data['學號'] == st.session_state['student_id']]
        return data
    
    elif data_type == 'pgy':
        if not PERMISSIONS.get(user_role, {}).get('can_view_pgy_data', False):
            return pd.DataFrame()
        return data
    
    elif data_type == 'resident':
        if not PERMISSIONS.get(user_role, {}).get('can_view_resident_data', False):
            return pd.DataFrame()
        # 住院醫師資料需要根據科別過濾
        if user_role == 'teacher' and user_department:
            # 主治醫師只能看自己科的住院醫師
            if '科別' in data.columns:
                return data[data['科別'] == user_department]
        elif user_role == 'resident' and user_department:
            # 住院醫師只能看自己的資料
            if '姓名' in data.columns and 'user_name' in st.session_state:
                return data[data['姓名'] == st.session_state['user_name']]
        return data
    
    elif data_type == 'department':
        if not PERMISSIONS.get(user_role, {}).get('can_view_department_data', False):
            return pd.DataFrame()
        # 科別資料需要根據科別過濾
        if user_role == 'teacher' and user_department:
            if '科別' in data.columns:
                return data[data['科別'] == user_department]
        return data
    
    return data

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
                user = load_users()[username]
                st.session_state['user_name'] = user['name']
                
                # 儲存科別資訊
                if 'department' in user:
                    st.session_state['user_department'] = user['department']
                else:
                    st.session_state['user_department'] = None
                
                # 如果是學生(UGY)，儲存學號
                if role == 'student':
                    if 'student_id' in user:
                        st.session_state['student_id'] = user['student_id']
                    else:
                        st.error("找不到學號資訊，請聯繫管理員")
                        return False
                
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
    
    # 添加選項卡分別顯示帳號管理和帳號審核
    tab1, tab2 = st.tabs(["帳號管理", "帳號審核"])
    
    with tab1:
        # 新增使用者表單
        with st.expander("新增使用者"):
            with st.form("add_user_form"):
                new_username = st.text_input("使用者名稱")
                new_password = st.text_input("密碼", type="password")
                new_name = st.text_input("姓名")
                new_role = st.selectbox("權限", options=list(USER_ROLES.keys()), format_func=lambda x: USER_ROLES[x])
                
                # 科別選擇
                departments = [
                    "小兒部", "內科", "外科", "婦產科", "神經科", "精神科", 
                    "家醫科", "急診醫學科", "麻醉科", "放射科", "病理科", 
                    "復健科", "皮膚科", "眼科", "耳鼻喉科", "泌尿科", "骨科", "其他科別"
                ]
                new_department = st.selectbox("科別", options=[""] + departments)
                
                # 其他資訊
                new_extension = st.text_input("分機號碼")
                new_email = st.text_input("電子郵件")
                
                # 如果是學生(UGY)，添加學號欄位
                new_student_id = None
                if new_role == 'student':
                    new_student_id = st.text_input("學號")
                
                submitted = st.form_submit_button("新增")
                
                if submitted:
                    success, message = create_user(
                        new_username, 
                        new_password, 
                        new_role, 
                        new_name,
                        student_id=new_student_id,
                        department=new_department if new_department else None,
                        extension=new_extension if new_extension else None,
                        email=new_email if new_email else None
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        # 使用者列表
        st.subheader("使用者列表")
        users = load_users()
        for username, user_data in users.items():
            # 顯示使用者詳細資訊
            role_name = USER_ROLES.get(user_data['role'], user_data['role'])
            department = user_data.get('department', '未設定')
            name = user_data.get('name', '未設定')
            
            with st.expander(f"{name} ({username}) - {role_name} - {department}"):
                # 顯示使用者詳細資訊
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**姓名:** {name}")
                    st.write(f"**使用者名稱:** {username}")
                    st.write(f"**角色:** {role_name}")
                    st.write(f"**科別:** {department}")
                    
                    # 顯示其他資訊
                    if 'student_id' in user_data:
                        st.write(f"**學號:** {user_data['student_id']}")
                    if 'extension' in user_data:
                        st.write(f"**分機:** {user_data['extension']}")
                    if 'email' in user_data:
                        st.write(f"**電子郵件:** {user_data['email']}")
                
                with col2:
                    # 操作按鈕
                    if st.button("刪除", key=f"delete_{username}"):
                        success, message = delete_user(username)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    # 權限更新
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
                            st.rerun()
                        else:
                            st.error(message)
    
    with tab2:
        # 顯示帳號審核界面
        show_user_approval()

def extract_spreadsheet_id(url):
    """從 Google 試算表 URL 中提取 spreadsheet ID"""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return None

def setup_google_connection():
    """設定與 Google API 的連接"""
    try:
        # 驗證 secrets 設定
        if not hasattr(st, 'secrets') or not st.secrets:
            st.error("未找到任何 Secrets 設定")
            st.info("請確保 .streamlit/secrets.toml 檔案存在且包含正確的設定，或在 Streamlit Cloud 中設定 Secrets")
            
            # 如果沒有 secrets，退回到本地文件方式（保留舊方法作為備選）
            st.warning("嘗試使用本地憑證文件...")
            return setup_google_connection_local()
            
        # 檢查 secrets 內容
        if "gcp_service_account" not in st.secrets:
            st.error("在 Secrets 中未找到 gcp_service_account 設定")
            st.info("請確保 Secrets 中包含完整的 Google API 憑證設定")
            
            # 如果沒有正確的 secrets 內容，退回到本地文件方式
            st.warning("嘗試使用本地憑證文件...")
            return setup_google_connection_local()
            
        # 檢查必要的憑證欄位
        required_fields = [
            "type", "project_id", "private_key_id", "private_key",
            "client_email", "client_id", "auth_uri", "token_uri",
            "auth_provider_x509_cert_url", "client_x509_cert_url"
        ]
        
        missing_fields = [field for field in required_fields 
                         if field not in st.secrets.gcp_service_account]
        
        if missing_fields:
            st.error(f"缺少必要的憑證欄位：{', '.join(missing_fields)}")
            st.info("請確保所有必要的憑證欄位都已正確設定")
            
            # 如果缺少必要欄位，退回到本地文件方式
            st.warning("嘗試使用本地憑證文件...")
            return setup_google_connection_local()
            
        try:
            # 構建憑證字典
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
            
            # 顯示服務帳號資訊
            st.info(f"使用服務帳號: {credentials['client_email']}")
            st.info(f"項目 ID: {credentials['project_id']}")
            
            # 設定 Google API 範圍
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/cloud-platform'
            ]
            
            try:
                # 建立認證
                creds = Credentials.from_service_account_info(credentials, scopes=scope)
                client = gspread.authorize(creds)
                
                # 測試連接
                try:
                    test_url = "https://docs.google.com/spreadsheets/d/1I2GzYptiPvhN5dT3_qzVXlIAoPeI8S9MaTVzxfDVjrw/edit?gid=0#gid=0"
                    spreadsheet_id = extract_spreadsheet_id(test_url)
                    
                    if spreadsheet_id:
                        try:
                            test_sheet = client.open_by_key(spreadsheet_id)
                            st.success(f"成功打開試算表: {test_sheet.title}")
                        except Exception as sheet_e:
                            st.warning(f"測試特定試算表時出錯，但 API 連接可能正常: {str(sheet_e)}")
                            st.info(f"請確保將 {credentials['client_email']} 加入試算表的共享列表並給予編輯權限")
                    
                    # 列出所有試算表以確保連接正常
                    spreadsheets = client.list_spreadsheet_files()
                    st.success(f"Google API 連接成功！找到 {len(spreadsheets)} 個試算表。")
                    return client
                except Exception as test_e:
                    st.error(f"連接測試失敗：{str(test_e)}")
                    st.warning("嘗試使用本地憑證文件...")
                    return setup_google_connection_local()
            except Exception as e:
                st.error(f"建立 Google API 認證時發生錯誤：{str(e)}")
                st.warning("嘗試使用本地憑證文件...")
                return setup_google_connection_local()
        except Exception as e:
            st.error(f"處理 Streamlit Secrets 時發生錯誤：{str(e)}")
            st.warning("嘗試使用本地憑證文件...")
            return setup_google_connection_local()
    except Exception as e:
        st.error(f"連接 Google API 時發生錯誤：{str(e)}")
        import traceback
        st.error(f"錯誤堆疊: {traceback.format_exc()}")
        st.warning("嘗試使用本地憑證文件...")
        return setup_google_connection_local()

def setup_google_connection_local():
    """使用本地檔案設定與 Google API 的連接（舊方法）"""
    try:
        # 取得目前檔案的目錄路徑
        current_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(current_dir, 'credentials.json')
        
        # 檢查 credentials.json 檔案是否存在
        if not os.path.exists(credentials_path):
            error_msg = f"未找到 credentials.json 檔案，預期路徑：{credentials_path}"
            st.error(error_msg)
            st.info(f"當前工作目錄: {os.getcwd()}")
            st.info(f"模組目錄: {current_dir}")
            # 嘗試列出模組目錄的檔案
            try:
                files = os.listdir(current_dir)
                st.info(f"模組目錄檔案: {', '.join(files)}")
            except Exception as list_e:
                st.error(f"列出目錄檔案時出錯: {str(list_e)}")
            return None
        
        st.info(f"找到憑證檔案: {credentials_path}")
        # 檢查檔案大小確保不是空檔案
        file_size = os.path.getsize(credentials_path)
        if file_size == 0:
            st.error(f"憑證檔案大小為0，可能是空檔案")
            return None
        st.info(f"憑證檔案大小: {file_size} bytes")
        
        # 嘗試讀取憑證內容以確保它是有效的 JSON
        try:
            with open(credentials_path, 'r') as f:
                cred_content = json.load(f)
                # 檢查關鍵欄位是否存在
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in cred_content]
                if missing_fields:
                    st.error(f"憑證檔案缺少必要欄位: {', '.join(missing_fields)}")
                    return None
                
                # 檢查私鑰格式
                private_key = cred_content.get('private_key', '')
                if not private_key.startswith('-----BEGIN PRIVATE KEY-----') or not private_key.endswith('-----END PRIVATE KEY-----\n'):
                    st.error("私鑰格式不正確，請確保包含正確的頭尾標記和換行符")
                    # 顯示私鑰前後20個字符用於診斷
                    st.error(f"私鑰開頭: {private_key[:20]}...")
                    st.error(f"私鑰結尾: ...{private_key[-20:]}")
                    return None
                
                # 檢查私鑰中是否包含足夠的換行符
                if private_key.count('\n') < 2:
                    st.error("私鑰缺少必要的換行符，可能在複製過程中丟失")
                    return None
                
                st.info(f"憑證檔案格式正確，項目 ID: {cred_content.get('project_id')}")
                st.info(f"服務帳號郵箱: {cred_content.get('client_email')}")
                
                # 檢查時間同步
                import datetime
                import time
                local_time = datetime.datetime.now()
                utc_time = datetime.datetime.utcnow()
                time_diff = abs((local_time - utc_time).total_seconds() - time.timezone)
                if time_diff > 300:  # 如果本地時間與UTC時間差異超過5分鐘(考慮時區)
                    st.warning(f"系統時間可能不同步，當前本地時間: {local_time}，UTC時間: {utc_time}")
                    st.warning("時間不同步可能導致JWT驗證失敗")
        except json.JSONDecodeError as json_e:
            st.error(f"憑證檔案不是有效的 JSON 格式: {str(json_e)}")
            return None
        except Exception as read_e:
            st.error(f"讀取憑證檔案時出錯: {str(read_e)}")
            return None
            
        # 設定 Google API 範圍
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/cloud-platform'
        ]
        
        # 建立認證
        try:
            # 顯示使用內建指令修復私鑰的建議
            st.info("如果持續出現JWT簽名錯誤，請考慮重新下載服務帳號金鑰或修復私鑰格式")
            st.info("可以使用以下命令來查看私鑰是否有正確的換行符: cat modules/credentials.json | grep private_key")
            
            # 嘗試手動構建服務帳號信息，這是主要方法
            from google.oauth2 import service_account
            
            try:
                # 直接從JSON內容構建認證
                st.info("嘗試使用手動方式建立服務帳號...")
                
                # 修復可能的私鑰格式問題
                if 'private_key' in cred_content:
                    # 1. 確保私鑰開頭和結尾有正確的標記
                    pk = cred_content['private_key']
                    if not pk.startswith('-----BEGIN PRIVATE KEY-----\n'):
                        pk = '-----BEGIN PRIVATE KEY-----\n' + pk.lstrip('-----BEGIN PRIVATE KEY-----')
                    if not pk.endswith('\n-----END PRIVATE KEY-----\n'):
                        pk = pk.rstrip('-----END PRIVATE KEY-----\n') + '\n-----END PRIVATE KEY-----\n'
                        
                    # 2. 嘗試確保有足夠的換行符 - RSA私鑰通常每64字符需要一個換行符
                    import re
                    lines = pk.split('\n')
                    new_lines = [lines[0]]  # BEGIN行
                    
                    # 處理中間的BASE64編碼部分
                    body = ''.join([l for l in lines[1:-2] if l])  # 合併所有非BEGIN/END行，移除空行
                    # 每64個字符插入一個換行符
                    chunks = [body[i:i+64] for i in range(0, len(body), 64)]
                    new_lines.extend(chunks)
                    new_lines.append(lines[-2])  # END行
                    new_lines.append('')  # 確保最後有一個空行
                    
                    # 更新私鑰
                    fixed_pk = '\n'.join(new_lines)
                    cred_content['private_key'] = fixed_pk
                    st.info("已嘗試修復私鑰格式")
                
                # 使用修復後的服務帳號信息
                creds = service_account.Credentials.from_service_account_info(
                    cred_content, 
                    scopes=scope
                )
                st.info("使用手動建立的服務帳號成功")
                
            except Exception as manual_error:
                st.error(f"手動建立憑證時出錯: {str(manual_error)}")
                
                # 如果手動方式失敗，退回到使用檔案
                try:
                    st.warning("手動方式失敗，嘗試使用檔案方式...")
                    creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
                    st.info("使用檔案建立服務帳號成功")
                except Exception as file_error:
                    st.error(f"從檔案建立憑證時出錯: {str(file_error)}")
                    return None
            
            client = gspread.authorize(creds)
            
            # 測試連接
            try:
                # 具體測試一個試算表而不是列出所有試算表
                test_url = "https://docs.google.com/spreadsheets/d/1I2GzYptiPvhN5dT3_qzVXlIAoPeI8S9MaTVzxfDVjrw/edit?gid=0#gid=0"
                spreadsheet_id = extract_spreadsheet_id(test_url)
                if spreadsheet_id:
                    try:
                        test_sheet = client.open_by_key(spreadsheet_id)
                        st.info(f"成功打開試算表: {test_sheet.title}")
                        return client
                    except Exception as sheet_e:
                        st.error(f"測試開啟特定試算表時出錯: {str(sheet_e)}")
                        st.info("檢查是否已將服務帳號加入試算表的共享列表")
                        st.info(f"請將 {cred_content.get('client_email')} 加入試算表的共享列表並給予編輯權限")
                        
                # 如果上面失敗，嘗試列出所有試算表
                spreadsheets = client.list_spreadsheet_files()
                st.info(f"成功連接到 Google API，找到 {len(spreadsheets)} 個試算表")
                return client
            except Exception as test_e:
                st.error(f"測試連接時出錯: {str(test_e)}")
                import traceback
                st.error(f"錯誤詳情: {traceback.format_exc()}")
                
                # 提供解決建議
                st.error("JWT簽名無效可能的解決方法:")
                st.info("1. 重新生成新的服務帳號金鑰並下載")
                st.info("2. 確保憑證文件未被修改，直接使用下載的原始文件")
                st.info("3. 檢查系統時間是否正確")
                st.info("4. 確認Google Cloud專案中已啟用必要的API (Google Sheets API, Google Drive API)")
                st.info("5. 確認服務帳號未被停用或撤銷")
                return None
        except Exception as auth_e:
            st.error(f"授權 Google API 時出錯: {str(auth_e)}")
            import traceback
            st.error(f"錯誤詳情: {traceback.format_exc()}")
            return None
            
    except Exception as e:
        st.error(f"連接 Google API 時發生未預期錯誤：{str(e)}")
        import traceback
        st.error(f"錯誤堆疊: {traceback.format_exc()}")
        st.warning("嘗試使用本地憑證文件...")
        return setup_google_connection_local()

def show_registration_page():
    """顯示註冊頁面"""
    st.title("申請帳號")
    
    with st.form("registration_form"):
        username = st.text_input("使用者名稱")
        password = st.text_input("密碼", type="password")
        confirm_password = st.text_input("確認密碼", type="password")
        name = st.text_input("姓名")
        role = st.selectbox("身份", options=['student'], format_func=lambda x: USER_ROLES[x])
        
        # 科別選擇
        departments = [
            "小兒部", "內科", "外科", "婦產科", "神經科", "精神科", 
            "家醫科", "急診醫學科", "麻醉科", "放射科", "病理科", 
            "復健科", "皮膚科", "眼科", "耳鼻喉科", "泌尿科", "骨科", "其他科別"
        ]
        department = st.selectbox("科別", options=[""] + departments)
        
        # 其他資訊
        extension = st.text_input("分機號碼")
        email = st.text_input("電子郵件")
        
        # 如果是學生(UGY)，添加學號欄位
        student_id = None
        if role == 'student':
            student_id = st.text_input("學號")
        
        submitted = st.form_submit_button("申請帳號")
        
        if submitted:
            if not username or not password or not name:
                st.error("請填寫所有必填欄位")
                return False
            
            if password != confirm_password:
                st.error("兩次輸入的密碼不一致")
                return False
            
            # 如果是學生，檢查學號是否填寫
            if role == 'student' and not student_id:
                st.error("請填寫學號")
                return False
            
            # 建立使用者
            success, message = create_user(
                username=username,
                password=hash_password(password),
                role=role,
                name=name,
                student_id=student_id if role == 'student' else None,
                department=department if department else None,
                extension=extension if extension else None,
                email=email if email else None
            )
            
            if success:
                st.success(message)
                return True
            else:
                st.error(message)
                return False
    
    return False

def show_user_approval():
    """顯示帳號審核管理介面"""
    if not check_permission(st.session_state['role'], 'can_manage_users'):
        st.error("您沒有權限管理使用者")
        return
    
    st.subheader("帳號審核管理")
    
    client = setup_google_connection()
    if client is None:
        st.error("無法連接到 Google Sheets")
        return
    
    # 獲取待審核帳號
    try:
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1VZRYRrsSMNUKoWM32gc5D9FykCHm7IRgcmR1_qXx8_w/edit?resourcekey=&gid=1526949290#gid=1526949290"
        spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
        
        if not spreadsheet_id:
            st.error("無法提取 Google Sheet ID")
            return
            
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet("Apply_auth")
            st.info(f"成功連接到帳號申請工作表")
        except Exception as ws_e:
            st.error(f"找不到Apply_auth工作表: {str(ws_e)}")
            return
            
        # 改用 get_all_values 獲取所有數據，並手動處理
        # 這樣可以避免標題行有重複值時的錯誤
        all_values = worksheet.get_all_values()
        
        if not all_values:
            st.info("申請工作表為空")
            return
            
        # 獲取標題行
        headers = all_values[0]
        
        # 顯示標題行，用於診斷
        st.write(f"工作表標題: {headers}")
        
        # 檢查是否存在必要的列
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
            if header == "審核狀態":
                status_col_idx = i
            elif header == "使用者名稱":
                username_col_idx = i
            elif header == "姓名":
                name_col_idx = i
            elif header == "角色":
                role_col_idx = i
            elif header == "申請時間":
                apply_time_col_idx = i
            elif header == "密碼雜湊值":
                password_col_idx = i
            elif header == "學號":
                student_id_col_idx = i
            elif header == "分機":
                extension_col_idx = i
            elif header == "電子郵件":
                email_col_idx = i
        
        # 檢查是否找到必要的列
        if status_col_idx is None or username_col_idx is None or name_col_idx is None or role_col_idx is None:
            st.error("工作表缺少必要的列（審核狀態、使用者名稱、姓名、角色）")
            return
        
        # 將數據轉換為字典列表
        records = []
        for row in all_values[1:]:  # 跳過標題行
            if len(row) <= max(status_col_idx, username_col_idx, name_col_idx, role_col_idx):
                continue  # 跳過資料不完整的行
                
            record = {
                "審核狀態": row[status_col_idx] if status_col_idx < len(row) else "",
                "使用者名稱": row[username_col_idx] if username_col_idx < len(row) else "",
                "姓名": row[name_col_idx] if name_col_idx < len(row) else "",
                "角色": row[role_col_idx] if role_col_idx < len(row) else "",
            }
            
            # 添加可選字段
            if apply_time_col_idx is not None and apply_time_col_idx < len(row):
                record["申請時間"] = row[apply_time_col_idx]
            if password_col_idx is not None and password_col_idx < len(row):
                record["密碼雜湊值"] = row[password_col_idx]
            if student_id_col_idx is not None and student_id_col_idx < len(row):
                record["學號"] = row[student_id_col_idx]
            if extension_col_idx is not None and extension_col_idx < len(row):
                record["分機"] = row[extension_col_idx]
            if email_col_idx is not None and email_col_idx < len(row):
                record["電子郵件"] = row[email_col_idx]
                
            records.append(record)
        
        # 過濾待審核的帳號
        pending_records = [r for r in records if r.get("審核狀態") == "待審核"]
        approved_records = [r for r in records if r.get("審核狀態") == "已審核"]
        rejected_records = [r for r in records if r.get("審核狀態") == "已拒絕"]
        
        # 顯示待審核帳號數量及已審核帳號數量
        st.info(f"有 {len(pending_records)} 個帳號待審核，{len(approved_records)} 個帳號已審核，{len(rejected_records)} 個帳號已拒絕")
        
        if pending_records:
            st.subheader("待審核帳號")
            
            for i, record in enumerate(pending_records):
                with st.expander(f"{record.get('姓名')} ({record.get('使用者名稱')}) - {record.get('角色')}"):
                    col1, col2, col3 = st.columns(3)
                    
                    # 顯示帳號詳細資訊
                    st.write(f"申請時間: {record.get('申請時間', '未記錄')}")
                    st.write(f"身份: {record.get('角色')}")
                    if record.get('學號'):
                        st.write(f"學號: {record.get('學號')}")
                    st.write(f"分機: {record.get('分機', '未填寫')}")
                    st.write(f"電子郵件: {record.get('電子郵件', '未填寫')}")
                    
                    # 審核操作按鈕
                    with col1:
                        if st.button("核准", key=f"approve_{i}"):
                            try:
                                # 1. 更新Google Sheet的狀態
                                found = False
                                for row_idx, row in enumerate(all_values[1:], start=2):
                                    if (username_col_idx < len(row) and 
                                        row[username_col_idx] == record.get('使用者名稱')):
                                        worksheet.update_cell(row_idx, status_col_idx + 1, "已審核")
                                        found = True
                                        break
                                
                                if not found:
                                    st.error(f"無法在工作表中找到使用者名稱為 {record.get('使用者名稱')} 的記錄")
                                    return
                                
                                # 2. 將帳號寫入本地users.json
                                role_code = None
                                for code, name in USER_ROLES.items():
                                    if name == record.get('角色'):
                                        role_code = code
                                        break
                                
                                if not role_code:
                                    role_code = 'student'  # 預設為學生
                                
                                # 直接使用申請時的密碼雜湊值
                                success, message = create_user(
                                    username=record.get('使用者名稱'),
                                    password=record.get('密碼雜湊值'),  # 直接使用申請時的密碼雜湊值
                                    role=role_code,
                                    name=record.get('姓名'),
                                    student_id=record.get('學號')  # 添加學號
                                )
                                
                                if success:
                                    st.success(f"已核准 {record.get('姓名')} 的帳號申請")
                                    st.rerun()
                                else:
                                    st.error(f"帳號建立失敗: {message}")
                                    
                            except Exception as e:
                                st.error(f"核准帳號時發生錯誤: {str(e)}")
                                import traceback
                                st.error(f"錯誤詳情: {traceback.format_exc()}")
                    
                    with col2:
                        if st.button("拒絕", key=f"reject_{i}"):
                            try:
                                # 僅更新Google Sheet的狀態，不寫入本地用戶
                                # 找到該記錄的行
                                found = False
                                for row_idx, row in enumerate(all_values[1:], start=2):  # 從第2行開始，索引從2開始
                                    if (username_col_idx < len(row) and 
                                        row[username_col_idx] == record.get('使用者名稱')):
                                        # 更新狀態
                                        worksheet.update_cell(row_idx, status_col_idx + 1, "已拒絕")  # API索引從1開始
                                        found = True
                                        break
                                
                                if not found:
                                    st.error(f"無法在工作表中找到使用者名稱為 {record.get('使用者名稱')} 的記錄")
                                    return
                                
                                st.success(f"已拒絕 {record.get('姓名')} 的帳號申請")
                                st.rerun()
                            except Exception as e:
                                st.error(f"拒絕帳號時發生錯誤: {str(e)}")
                                import traceback
                                st.error(f"錯誤詳情: {traceback.format_exc()}")
                    
                    with col3:
                        reason = st.text_input("拒絕原因", key=f"reason_{i}")
                        
        else:
            st.info("目前沒有待審核的帳號")
            
        # 顯示已審核帳號歷史
        if st.checkbox("顯示已審核帳號歷史"):
            with st.expander("已審核帳號"):
                if approved_records:
                    for record in approved_records:
                        st.write(f"{record.get('姓名')} ({record.get('使用者名稱')}) - {record.get('角色')} - {record.get('申請時間', '未記錄')}")
                else:
                    st.info("沒有已審核的帳號")
        
        # 顯示已拒絕帳號歷史
        if st.checkbox("顯示已拒絕帳號歷史"):
            with st.expander("已拒絕帳號"):
                if rejected_records:
                    for record in rejected_records:
                        st.write(f"{record.get('姓名')} ({record.get('使用者名稱')}) - {record.get('角色')} - {record.get('申請時間', '未記錄')}")
                else:
                    st.info("沒有已拒絕的帳號")
                
    except Exception as e:
        st.error(f"獲取審核資料時發生錯誤: {str(e)}")
        import traceback
        st.error(f"錯誤詳情: {traceback.format_exc()}") 