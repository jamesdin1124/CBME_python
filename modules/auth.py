import streamlit as st
import hashlib
import json
import os
import gspread
from google.oauth2.service_account import Credentials
import re

# ä½¿ç”¨???æ¬Šé?å?šç¾©
USER_ROLES = {
    'admin': 'ç³»çµ±ç®¡ç???“¡',
    'teacher': '??™å¸«',
    'resident': 'ä½é™¢??«å¸«',
    'student': '??«å­¸???'
}

# æ¬Šé?è¨­å®?
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
    """å°?å¯?ç¢¼é?²è?Œé?œæ?Šè?•ç??"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """å¾æ?”æ??è¼‰å?¥ä½¿?”¨???è³????"""
    try:
        if os.path.exists('users.json'):
            with open('users.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"è¼‰å?¥ä½¿?”¨???è³???™æ???™¼??ŸéŒ¯èª¤ï?š{str(e)}")
    return {}

def save_users(users):
    """??²å?˜ä½¿?”¨???è³???™å?°æ?”æ??"""
    try:
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"??²å?˜ä½¿?”¨???è³???™æ???™¼??ŸéŒ¯èª¤ï?š{str(e)}")

def authenticate_user(username, password):
    """é©—è?‰ä½¿?”¨???èº«ä»½"""
    users = load_users()
    if username in users and users[username]['password'] == hash_password(password):
        return users[username]['role']
    return None

def create_user(username, password, role, name, student_id=None):
    """å»ºç?‹æ–°ä½¿ç”¨???"""
    users = load_users()
    if username in users:
        return False, "ä½¿ç”¨?????ç¨±å·²å?˜åœ¨"
    
    user_data = {
        'password': password,  # ?›´?¥ä½¿ç”¨??³å?¥ç??å¯?ç¢¼é?œæ?Šå??
        'role': role,
        'name': name
    }
    
    # å¦???œæ˜¯å­¸ç??ï¼Œæ·»?? å­¸???
    if role == 'student' and student_id:
        user_data['student_id'] = student_id
    
    users[username] = user_data
    save_users(users)
    return True, "ä½¿ç”¨???å»ºç?‹æ?å??"

def delete_user(username):
    """?ˆª?™¤ä½¿ç”¨???"""
    users = load_users()
    if username not in users:
        return False, "ä½¿ç”¨???ä¸å?˜åœ¨"
    
    del users[username]
    save_users(users)
    return True, "ä½¿ç”¨????ˆª?™¤??å??"

def update_user_role(username, new_role):
    """?›´?–°ä½¿ç”¨???æ¬Šé??"""
    users = load_users()
    if username not in users:
        return False, "ä½¿ç”¨???ä¸å?˜åœ¨"
    
    users[username]['role'] = new_role
    save_users(users)
    return True, "ä½¿ç”¨???æ¬Šé?æ›´?–°??å??"

def check_permission(role, permission):
    """æª¢æŸ¥ä½¿ç”¨????˜¯?¦??‰ç‰¹å®šæ?Šé??"""
    return PERMISSIONS.get(role, {}).get(permission, False)

def show_login_page():
    """é¡¯ç¤º?™»??¥é???¢"""
    st.title("?‡¨åºŠæ?™å¸«è©•æ ¸ç³»çµ± - ?™»???")
    
    with st.form("login_form"):
        username = st.text_input("ä½¿ç”¨?????ç¨±")
        password = st.text_input("å¯?ç¢?", type="password")
        submitted = st.form_submit_button("?™»???")
        
        if submitted:
            role = authenticate_user(username, password)
            if role:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = role
                user = load_users()[username]
                st.session_state['user_name'] = user['name']
                
                # å¦???œæ˜¯å­¸ç??ï¼???²å?˜å­¸???
                if role == 'student':
                    if 'student_id' in user:
                        st.session_state['student_id'] = user['student_id']
                    else:
                        st.error("?‰¾ä¸å?°å­¸??Ÿè??è¨Šï?Œè?‹è?¯ç¹«ç®¡ç???“¡")
                        return False
                
                st.success(f"æ­¡è?å?ä??ï¼Œ{st.session_state['user_name']}ï¼?")
                return True
            else:
                st.error("ä½¿ç”¨?????ç¨±??–å??ç¢¼éŒ¯èª?")
    return False

def show_user_management():
    """é¡¯ç¤ºä½¿ç”¨???ç®¡ç??ä»‹é¢"""
    if not check_permission(st.session_state['role'], 'can_manage_users'):
        st.error("??¨æ?’æ?‰æ?Šé?ç®¡???ä½¿ç”¨???")
        return
    
    st.title("ä½¿ç”¨???ç®¡ç??")
    
    # æ·»å? é?¸é???¡????ˆ¥é¡¯ç¤ºå¸³è?Ÿç®¡??????å¸³è?Ÿå¯©? ¸
    tab1, tab2 = st.tabs(["å¸³è?Ÿç®¡???", "å¸³è?Ÿå¯©? ¸"])
    
    with tab1:
        # ?–°å¢ä½¿?”¨???è¡¨å–®
        with st.expander("?–°å¢ä½¿?”¨???"):
            with st.form("add_user_form"):
                new_username = st.text_input("ä½¿ç”¨?????ç¨±")
                new_password = st.text_input("å¯?ç¢?", type="password")
                new_name = st.text_input("å§“å??")
                new_role = st.selectbox("æ¬Šé??", options=list(USER_ROLES.keys()), format_func=lambda x: USER_ROLES[x])
                submitted = st.form_submit_button("?–°å¢?")
                
                if submitted:
                    success, message = create_user(new_username, new_password, new_role, new_name)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        # ä½¿ç”¨?????—è¡¨
        st.subheader("ä½¿ç”¨?????—è¡¨")
        users = load_users()
        for username, user_data in users.items():
            with st.expander(f"{username} ({USER_ROLES[user_data['role']]})"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("?ˆª?™¤", key=f"delete_{username}"):
                        success, message = delete_user(username)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                with col2:
                    new_role = st.selectbox(
                        "?›´?–°æ¬Šé??",
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
        # é¡¯ç¤ºå¸³è?Ÿå¯©? ¸??Œé¢
        show_user_approval()

def extract_spreadsheet_id(url):
    """å¾? Google è©¦ç?—è¡¨ URL ä¸­æ?å?? spreadsheet ID"""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return None

def setup_google_connection():
    """è¨­å?šè?? Google API ???????¥"""
    try:
        # é©—è?? secrets è¨­å??
        if not hasattr(st, 'secrets') or not st.secrets:
            st.error("?œª?‰¾??°ä»»ä½? Secrets è¨­å??")
            st.info("è«‹ç¢ºä¿? .streamlit/secrets.toml æª”æ??å­˜åœ¨ä¸”å???«æ­?ç¢ºç??è¨­å?šï?Œæ?–åœ¨ Streamlit Cloud ä¸­è¨­å®? Secrets")
            
            # å¦???œæ?’æ?? secretsï¼Œé????å?°æœ¬?œ°???ä»¶æ–¹å¼ï??ä¿ç?™è?Šæ–¹æ³•ä?œç?ºå?™é?¸ï??
            st.warning("??—è©¦ä½¿ç”¨?œ¬?œ°??‘è?‰æ??ä»?...")
            return setup_google_connection_local()
            
        # æª¢æŸ¥ secrets ??§å®¹
        if "gcp_service_account" not in st.secrets:
            st.error("?œ¨ Secrets ä¸­æœª?‰¾??? gcp_service_account è¨­å??")
            st.info("è«‹ç¢ºä¿? Secrets ä¸­å???«å®Œæ•´??? Google API ??‘è?‰è¨­å®?")
            
            # å¦???œæ?’æ?‰æ­£ç¢ºç?? secrets ??§å®¹ï¼Œé????å?°æœ¬?œ°???ä»¶æ–¹å¼?
            st.warning("??—è©¦ä½¿ç”¨?œ¬?œ°??‘è?‰æ??ä»?...")
            return setup_google_connection_local()
            
        # æª¢æŸ¥å¿?è¦??????‘è?‰æ??ä½?
        required_fields = [
            "type", "project_id", "private_key_id", "private_key",
            "client_email", "client_id", "auth_uri", "token_uri",
            "auth_provider_x509_cert_url", "client_x509_cert_url"
        ]
        
        missing_fields = [field for field in required_fields 
                         if field not in st.secrets.gcp_service_account]
        
        if missing_fields:
            st.error(f"ç¼ºå?‘å??è¦??????‘è?‰æ??ä½ï?š{', '.join(missing_fields)}")
            st.info("è«‹ç¢ºä¿æ????‰å??è¦??????‘è?‰æ??ä½é?½å·²æ­?ç¢ºè¨­å®?")
            
            # å¦???œç¼ºå°‘å??è¦?æ¬?ä½ï?Œé????å?°æœ¬?œ°???ä»¶æ–¹å¼?
            st.warning("??—è©¦ä½¿ç”¨?œ¬?œ°??‘è?‰æ??ä»?...")
            return setup_google_connection_local()
            
        try:
            # æ§‹å»º??‘è?‰å?—å??
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
            
            # é¡¯ç¤º??å?™å¸³??Ÿè??è¨?
            st.info(f"ä½¿ç”¨??å?™å¸³???: {credentials['client_email']}")
            st.info(f"????›® ID: {credentials['project_id']}")
            
            # è¨­å?? Google API ç¯????
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/cloud-platform'
            ]
            
            try:
                # å»ºç?‹è?è??
                creds = Credentials.from_service_account_info(credentials, scopes=scope)
                client = gspread.authorize(creds)
                
                # æ¸¬è©¦????¥
                try:
                    test_url = "https://docs.google.com/spreadsheets/d/1I2GzYptiPvhN5dT3_qzVXlIAoPeI8S9MaTVzxfDVjrw/edit?gid=0#gid=0"
                    spreadsheet_id = extract_spreadsheet_id(test_url)
                    
                    if spreadsheet_id:
                        try:
                            test_sheet = client.open_by_key(spreadsheet_id)
                            st.success(f"??å????“é?‹è©¦ç®—è¡¨: {test_sheet.title}")
                        except Exception as sheet_e:
                            st.warning(f"æ¸¬è©¦?‰¹å®šè©¦ç®—è¡¨????‡º?Œ¯ï¼Œä?? API ????¥?¯??½æ­£å¸?: {str(sheet_e)}")
                            st.info(f"è«‹ç¢ºä¿å {credentials['client_email']}  å¥è©¦ç®—è¡¨±äº«—è¡¨ä¸¦çµ¦äºç·¨è¼¯æ¬Šé")
                    
                    # —å‡º‰è©¦ç®—è¡¨ä»¥ç¢ºä¿é¥æ­å¸
                    spreadsheets = client.list_spreadsheet_files()
                    st.success(f"Google API ¥åï¼‰¾ {len(spreadsheets)} ‹è©¦ç®—è¡¨")
                    return client
                except Exception as test_e:
                    st.error(f"¥æ¸¬è©¦å¤±æ—ïš{str(test_e)}")
                    st.warning("—è©¦ä½¿ç”¨œ¬œ°‘è‰æä»...")
                    return setup_google_connection_local()
            except Exception as e:
                st.error(f"å»ºç Google API èªè‰æ™¼ŸéŒ¯èª¤ïš{str(e)}")
                st.warning("—è©¦ä½¿ç”¨œ¬œ°‘è‰æä»...")
                return setup_google_connection_local()
        except Exception as e:
            st.error(f"•ç Streamlit Secrets ™¼ŸéŒ¯èª¤ïš{str(e)}")
            st.warning("—è©¦ä½¿ç”¨œ¬œ°‘è‰æä»...")
            return setup_google_connection_local()
    except Exception as e:
        st.error(f"¥ Google API ™¼ŸéŒ¯èª¤ïš{str(e)}")
        import traceback
        st.error(f"Œ¯èª¤å: {traceback.format_exc()}")
        st.warning("—è©¦ä½¿ç”¨œ¬œ°‘è‰æä»...")
        return setup_google_connection_local()

def setup_google_connection_local():
    """ä½¿ç”¨œ¬œ°æª”æè¨­åšè Google API ¥ï¼Šæ–¹æ³•ï"""
    try:
        # –å—ç›®æ”æ›®è·¯å
        current_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(current_dir, 'credentials.json')
        
        # æª¢æŸ¥ credentials.json æª”æ˜¯¦å­˜åœ¨
        if not os.path.exists(credentials_path):
            error_msg = f"œª‰¾ credentials.json æª”æï¼ŒéæŸè·¯å¾‘ïš{credentials_path}"
            st.error(error_msg)
            st.info(f"•¶å·¥ä½œç›®: {os.getcwd()}")
            st.info(f"æ¨¡ç›®: {current_dir}")
            # —è©¦—å‡ºæ¨¡ç›®æª”æ
            try:
                files = os.listdir(current_dir)
                st.info(f"æ¨¡ç›®æª”æ: {', '.join(files)}")
            except Exception as list_e:
                st.error(f"—å‡º›®æª”æ‡ºŒ¯: {str(list_e)}")
            return None
        
        st.info(f"‰¾°æ‘è‰æ”æ: {credentials_path}")
        # æª¢æŸ¥æª”æå¤§åç¢ºä¿äæ˜¯ç©ºæ”æ
        file_size = os.path.getsize(credentials_path)
        if file_size == 0:
            st.error(f"‘è‰æ”æå¤§åç0ï¼¯½æ˜¯ç©ºæ”æ")
            return None
        st.info(f"‘è‰æ”æå¤§å: {file_size} bytes")
        
        # —è©¦è®–æ‘è‰å§å®¹ä»¥ç¢ºä¿å˜¯‰æ JSON
        try:
            with open(credentials_path, 'r') as f:
                cred_content = json.load(f)
                # æª¢æŸ¥œéµæ¬ä½æ˜¯¦å­˜åœ¨
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in cred_content]
                if missing_fields:
                    st.error(f"‘è‰æ”æç¼ºå‘åè¦æ¬ä½: {', '.join(missing_fields)}")
                    return None
                
                # æª¢æŸ¥ç§‘° ¼å¼
                private_key = cred_content.get('private_key', '')
                if not private_key.startswith('-----BEGIN PRIVATE KEY-----') or not private_key.endswith('-----END PRIVATE KEY-----\n'):
                    st.error("ç§‘° ¼å¼äæ­£ç¢ºïŒè‹ç¢ºä¿å«æ­ç¢ºç­å°¾æ¨™è˜åŒæ›èŒç¬¦")
                    # é¡¯ç¤ºç§‘°å20‹å—ç¬¦”¨–¼è¨ºæ–·
                    st.error(f"ç§‘°‹é: {private_key[:20]}...")
                    st.error(f"ç§‘°çµå°¾: ...{private_key[-20:]}")
                    return None
                
                # æª¢æŸ¥ç§‘°ä¸­æ˜¯¦«è¶³å ç›èŒç¬¦
                if private_key.count('\n') < 2:
                    st.error("ç§‘°ç¼ºå‘åè¦›èŒç¬¦ï¼¯½åœ¨è¤è£½éç‹ä¸­ä¸Ÿå¤±")
                    return None
                
                st.info(f"‘è‰æ”æ ¼å¼æ­£ç¢ºïŒé›® ID: {cred_content.get('project_id')}")
                st.info(f"å™å¸³Ÿéµç®±: {cred_content.get('client_email')}")
                
                # æª¢æŸ¥“åŒæ­¥
                import datetime
                import time
                local_time = datetime.datetime.now()
                utc_time = datetime.datetime.utcnow()
                time_diff = abs((local_time - utc_time).total_seconds() - time.timezone)
                if time_diff > 300:  # å¦œæœ¬œ°“è‡UTC“å·®•°è¶5(®æ)
                    st.warning(f"ç³»çµ±“å¯½äåŒæ­¥ï¼Œç•¶æœ¬œ°: {local_time}ï¼ŒUTC: {utc_time}")
                    st.warning("“äåŒæ­¥¯½åè‡´JWTé©—è‰å¤±")
        except json.JSONDecodeError as json_e:
            st.error(f"‘è‰æ”æä¸æ˜¯‰æ JSON  ¼å¼: {str(json_e)}")
            return None
        except Exception as read_e:
            st.error(f"è®–æ‘è‰æ”æ‡ºŒ¯: {str(read_e)}")
            return None
            
        # è¨­å Google API ç¯
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/cloud-platform'
        ]
        
        # å»ºç‹èè
        try:
            # é¡¯ç¤ºä½¿ç”¨§å»ºä»¤ä¿®å¾©ç‘°å»ºè­°
            st.info("å¦œæçº‡º¾JWTç°½åéŒ¯èª¤ïŒè‹è®éæ–°ä¸‹è‰æå™å¸³Ÿé‘é‘°–ä¿®å¾©ç‘° ¼å¼")
            st.info("¯ä»¥ä½¿”¨ä»¥ä‹å‘½ä»¤äŸ¥‹ç‘°˜¯¦‰æ­£ç¢ºç›èŒç¬¦: cat modules/credentials.json | grep private_key")
            
            # —è©¦‹å•æ‹å»ºå™å¸³Ÿä¿¡¯ïŒé™æ˜¯ä¸»è–¹æ³
            from google.oauth2 import service_account
            
            try:
                # ›´¥å¾JSON§å®¹æ§‹å»ºèªè
                st.info("—è©¦ä½¿ç”¨‹å•æ–¹å¼å»ºç«‹æå™å¸³...")
                
                # ä¿®å¾©¯½çç§‘° ¼å¼åé
                if 'private_key' in cred_content:
                    # 1. ç¢ºäç‘°‹é­åŒçå°¾‰æ­£ç¢ºçæ¨™è
                    pk = cred_content['private_key']
                    if not pk.startswith('-----BEGIN PRIVATE KEY-----\n'):
                        pk = '-----BEGIN PRIVATE KEY-----\n' + pk.lstrip('-----BEGIN PRIVATE KEY-----')
                    if not pk.endswith('\n-----END PRIVATE KEY-----\n'):
                        pk = pk.rstrip('-----END PRIVATE KEY-----\n') + '\n-----END PRIVATE KEY-----\n'
                        
                    # 2. —è©¦ç¢ºäæ‰è¶³å¤ ç›èŒç¬¦ - RSAç§‘°šå¸¸æ¯64å­—ç¬¦è¦ä¸‹æ›èŒç¬¦
                    import re
                    lines = pk.split('\n')
                    new_lines = [lines[0]]  # BEGINè¡
                    
                    # •çä¸­é“çBASE64ç·¨ç¢¼¨å
                    body = ''.join([l for l in lines[1:-2] if l])  # ä½µæ‰éBEGIN/ENDè¡ŒïŒç§»™¤ç©ºè
                    # æ¯64‹å—ç¬¦’å¥ä‹æ›èŒç¬¦
                    chunks = [body[i:i+64] for i in range(0, len(body), 64)]
                    new_lines.extend(chunks)
                    new_lines.append(lines[-2])  # ENDè¡
                    new_lines.append('')  # ç¢ºäæå¾Œæ‰ä‹ç©ºè¡
                    
                    # ›´–°ç§‘°
                    fixed_pk = '\n'.join(new_lines)
                    cred_content['private_key'] = fixed_pk
                    st.info("å·²å—è©¦ä¿®å¾©ç§‘° ¼å¼")
                
                # ä½¿ç”¨ä¿®å¾©å¾Œçå™å¸³Ÿä¿¡
                creds = service_account.Credentials.from_service_account_info(
                    cred_content, 
                    scopes=scope
                )
                st.info("ä½¿ç”¨‹å•å»ºç«‹çå™å¸³å")
                
            except Exception as manual_error:
                st.error(f"‹å•å»ºç«‹æ‘è‰æ‡ºŒ¯: {str(manual_error)}")
                
                # å¦œæ‹å•æ–¹å¼å¤±—ïŒéå°ä½¿”¨æª”æ
                try:
                    st.warning("‹å•æ–¹å¼å¤±—ï—è©¦ä½¿ç”¨æª”æ–¹å¼...")
                    creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
                    st.info("ä½¿ç”¨æª”æå»ºç‹æå™å¸³å")
                except Exception as file_error:
                    st.error(f"å¾æ”æå»ºç‹æ‘è‰æ‡ºŒ¯: {str(file_error)}")
                    return None
            
            client = gspread.authorize(creds)
            
            # æ¸¬è©¦¥
            try:
                # ·é”æ¸¬è©¦ä‹è©¦ç®—è¡¨Œäæ˜¯—å‡º‰è©¦ç®—è¡¨
                test_url = "https://docs.google.com/spreadsheets/d/1I2GzYptiPvhN5dT3_qzVXlIAoPeI8S9MaTVzxfDVjrw/edit?gid=0#gid=0"
                spreadsheet_id = extract_spreadsheet_id(test_url)
                if spreadsheet_id:
                    try:
                        test_sheet = client.open_by_key(spreadsheet_id)
                        st.info(f"å“é‹è©¦ç®—è¡¨: {test_sheet.title}")
                        return client
                    except Exception as sheet_e:
                        st.error(f"æ¸¬è©¦‹åŸç‰¹å®šè©¦ç®—è¡¨‡ºŒ¯: {str(sheet_e)}")
                        st.info("æª¢æŸ¥˜¯¦å·²åå™å¸³Ÿå å¥è©¦ç®—è¡¨±äº«—è¡¨")
                        st.info(f"è«‹å {cred_content.get('client_email')}  å¥è©¦ç®—è¡¨±äº«—è¡¨ä¸¦çµ¦äºç·¨è¼¯æ¬Šé")
                        
                # å¦œäŠé¢å¤±æ—ï—è©¦—å‡º‰è©¦ç®—è¡¨
                spreadsheets = client.list_spreadsheet_files()
                st.info(f"åŸé¥ Google APIï¼Œæ‰¾ {len(spreadsheets)} ‹è©¦ç®—è¡¨")
                return client
            except Exception as test_e:
                st.error(f"æ¸¬è©¦¥‡ºŒ¯: {str(test_e)}")
                import traceback
                st.error(f"Œ¯èª¤è©³: {traceback.format_exc()}")
                
                # ä›è§£æ±ºå»ºè­
                st.error("JWTç°½åç¡æ¯½çè§æ±ºæ–¹æ³:")
                st.info("1. æ–°æ–°å™å¸³Ÿé‘é‘°ä¸¦ä‹è")
                st.info("2. ç¢ºäæ‘è‰æä»¶æœªè¢«ä¿®”¹ï¼Œç›´¥ä½¿ç”¨ä¸‹è‰çŸå‹æä»")
                st.info("3. æª¢æŸ¥ç³»çµ±“æ˜¯¦æ­ç¢")
                st.info("4. ç¢ºèGoogle Cloudå°æ¡ä¸­å·²Ÿç”¨å¿è¦API (Google Sheets API, Google Drive API)")
                st.info("5. ç¢ºèæå™å¸³œªè¢«åœç”¨–æ’¤Š·")
                return None
        except Exception as auth_e:
            st.error(f"æ¬ Google API ‡ºŒ¯: {str(auth_e)}")
            import traceback
            st.error(f"Œ¯èª¤è©³: {traceback.format_exc()}")
            return None
            
    except Exception as e:
        st.error(f"¥ Google API ™¼œªæŸéŒ¯èª¤ïš{str(e)}")
        import traceback
        st.error(f"Œ¯èª¤å: {traceback.format_exc()}")
        st.warning("—è©¦ä½¿ç”¨œ¬œ°‘è‰æä»...")
        return setup_google_connection_local()

def show_registration_page():
    """é¡¯ç¤ºè¨»åŠé¢"""
    st.title("”³è«‹å¸³")
    
    with st.form("registration_form"):
        username = st.text_input("ä½¿ç”¨ç¨±")
        password = st.text_input("å¯ç¢", type="password")
        confirm_password = st.text_input("ç¢ºèåç¢", type="password")
        name = st.text_input("å§“å")
        role = st.selectbox("èº«ä»½", options=['student'], format_func=lambda x: USER_ROLES[x])
        
        # å¦œæ˜¯å­¸çï¼Œæ·» å­¸æ¬ä½
        student_id = None
        if role == 'student':
            student_id = st.text_input("å­¸è")
        
        submitted = st.form_submit_button("”³è«‹å¸³")
        
        if submitted:
            if not username or not password or not name:
                st.error("è«‹å¡«å¯«æ‰åå¡«æä½")
                return False
            
            if password != confirm_password:
                st.error("©æ¬¡è¼¸å¥çå¯ç¢¼ää‡´")
                return False
            
            # å¦œæ˜¯å­¸çï¼Œæª¢Ÿ¥å­¸è˜¯¦å¡«å¯«
            if role == 'student' and not student_id:
                st.error("è«‹å¡«å¯«å­¸")
                return False
            
            # å»ºç‹ä½¿”¨
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
    """é¡¯ç¤ºå¸³èŸå¯© ¸ç®¡çä»‹é¢"""
    if not check_permission(st.session_state['role'], 'can_manage_users'):
        st.error("¨æ’æ‰æŠéç®¡ä½¿ç”¨")
        return
    
    st.subheader("å¸³èŸå¯© ¸ç®¡ç")
    
    client = setup_google_connection()
    if client is None:
        st.error("¡æ•é¥ Google Sheets")
        return
    
    # ²–åå¯©æ ¸å¸³è
    try:
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1VZRYRrsSMNUKoWM32gc5D9FykCHm7IRgcmR1_qXx8_w/edit?resourcekey=&gid=1526949290#gid=1526949290"
        spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
        
        if not spreadsheet_id:
            st.error("¡æ•æå Google Sheet ID")
            return
            
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet("Apply_auth")
            st.info(f"åŸé¥°å¸³Ÿç”³è«‹å·¥ä½œè¡¨")
        except Exception as ws_e:
            st.error(f"‰¾ä¸å°Apply_authå·¥äœè¡¨: {str(ws_e)}")
            return
            
        # ”¹”¨ get_all_values ²–æ‰æ•¸šïŒä¸¦‹å•è•ç
        # ™æ¨£¯ä»¥é¿åæ™éŒèŒæ‰éè¼æŒ¯èª
        all_values = worksheet.get_all_values()
        
        if not all_values:
            st.info("”³è«‹å·¥ä½œè¡¨ºç©º")
            return
            
        # ²–æ™éŒè
        headers = all_values[0]
        
        # é¡¯ç¤ºæ¨™éŒèŒïŒç”¨–¼è¨ºæ–·
        st.write(f"å·¥äœè¡¨æ¨™é: {headers}")
        
        # æª¢æŸ¥˜¯¦å­˜åœ¨å¿è¦
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
            if header == "å¯©æ ¸":
                status_col_idx = i
            elif header == "ä½¿ç”¨ç¨±":
                username_col_idx = i
            elif header == "å§“å":
                name_col_idx = i
            elif header == "è§’è‰²":
                role_col_idx = i
            elif header == "”³è«‹æ":
                apply_time_col_idx = i
            elif header == "å¯ç¢¼éœæŠå":
                password_col_idx = i
            elif header == "å­¸è":
                student_id_col_idx = i
            elif header == "æ©":
                extension_col_idx = i
            elif header == "›»å­éµä»¶":
                email_col_idx = i
        
        # æª¢æŸ¥˜¯¦‰¾°åè¦
        if status_col_idx is None or username_col_idx is None or name_col_idx is None or role_col_idx is None:
            st.error("å·¥äœè¡¨ç¼ºå‘åè¦—ïå¯©æ ¸‹ãä½¿ç”¨ç¨±å§“åãè§’è‰²ï¼")
            return
        
        # å°•¸šè‰æ›çºå—å¸å—è¡¨
        records = []
        for row in all_values[1:]:  # è·³éæ™éŒè
            if len(row) <= max(status_col_idx, username_col_idx, name_col_idx, role_col_idx):
                continue  # è·³éè™äåŒæ•´è¡
                
            record = {
                "å¯©æ ¸": row[status_col_idx] if status_col_idx < len(row) else "",
                "ä½¿ç”¨ç¨±": row[username_col_idx] if username_col_idx < len(row) else "",
                "å§“å": row[name_col_idx] if name_col_idx < len(row) else "",
                "è§’è‰²": row[role_col_idx] if role_col_idx < len(row) else "",
            }
            
            # æ·»å å¯¸å—æ®µ
            if apply_time_col_idx is not None and apply_time_col_idx < len(row):
                record["”³è«‹æ"] = row[apply_time_col_idx]
            if password_col_idx is not None and password_col_idx < len(row):
                record["å¯ç¢¼éœæŠå"] = row[password_col_idx]
            if student_id_col_idx is not None and student_id_col_idx < len(row):
                record["å­¸è"] = row[student_id_col_idx]
            if extension_col_idx is not None and extension_col_idx < len(row):
                record["æ©"] = row[extension_col_idx]
            if email_col_idx is not None and email_col_idx < len(row):
                record["›»å­éµä»¶"] = row[email_col_idx]
                
            records.append(record)
        
        # æ¿¾å¾å¯©æ ¸å¸³è
        pending_records = [r for r in records if r.get("å¯©æ ¸") == "å¾å¯©æ ¸"]
        approved_records = [r for r in records if r.get("å¯©æ ¸") == "å·²å¯© ¸"]
        rejected_records = [r for r in records if r.get("å¯©æ ¸") == "å·²æ’ç"]
        
        # é¡¯ç¤ºå¾å¯©æ ¸å¸³è•¸åŠå·²å¯©æ ¸å¸³è•¸
        st.info(f" {len(pending_records)} ‹å¸³Ÿåå¯©æ ¸ï¼Œ{len(approved_records)} ‹å¸³Ÿå·²å¯©æ ¸ï¼Œ{len(rejected_records)} ‹å¸³Ÿå·²’ç")
        
        if pending_records:
            st.subheader("å¾å¯©æ ¸å¸³è")
            
            for i, record in enumerate(pending_records):
                with st.expander(f"{record.get('å§“å')} ({record.get('ä½¿ç”¨ç¨±')}) - {record.get('è§’è‰²')}"):
                    col1, col2, col3 = st.columns(3)
                    
                    # é¡¯ç¤ºå¸³èŸè©³ç´°èè¨
                    st.write(f"”³è«‹æ: {record.get('”³è«‹æ', 'œªè¨˜é')}")
                    st.write(f"èº«ä»½: {record.get('è§’è‰²')}")
                    if record.get('å­¸è'):
                        st.write(f"å­¸è: {record.get('å­¸è')}")
                    st.write(f"æ©: {record.get('æ©', 'œªå¡«å¯«')}")
                    st.write(f"›»å­éµä»¶: {record.get('›»å­éµä»¶', 'œªå¡«å¯«')}")
                    
                    # å¯©æ ¸äœæ‰é
                    with col1:
                        if st.button(" ¸", key=f"approve_{i}"):
                            try:
                                # 1. ›´–°Google Sheet
                                found = False
                                for row_idx, row in enumerate(all_values[1:], start=2):
                                    if (username_col_idx < len(row) and 
                                        row[username_col_idx] == record.get('ä½¿ç”¨ç¨±')):
                                        worksheet.update_cell(row_idx, status_col_idx + 1, "å·²å¯© ¸")
                                        found = True
                                        break
                                
                                if not found:
                                    st.error(f"¡æ•åœ¨å·¥äœè¡¨ä¸­æ‰¾°ä½¿”¨ç¨± {record.get('ä½¿ç”¨ç¨±')} è¨˜é")
                                    return
                                
                                # 2. å°å¸³èŸå¯«¥æœ¬œ°users.json
                                role_code = None
                                for code, name in USER_ROLES.items():
                                    if name == record.get('è§’è‰²'):
                                        role_code = code
                                        break
                                
                                if not role_code:
                                    role_code = 'student'  # è¨­ºå­¸
                                
                                # ›´¥ä½¿ç”¨”³è«‹æå¯ç¢¼éœæŠå
                                success, message = create_user(
                                    username=record.get('ä½¿ç”¨ç¨±'),
                                    password=record.get('å¯ç¢¼éœæŠå'),  # ›´¥ä½¿ç”¨”³è«‹æå¯ç¢¼éœæŠå
                                    role=role_code,
                                    name=record.get('å§“å'),
                                    student_id=record.get('å­¸è')  # æ·»å å­¸
                                )
                                
                                if success:
                                    st.success(f"å·²æ ¸ {record.get('å§“å')} å¸³èŸç”³è«")
                                    st.rerun()
                                else:
                                    st.error(f"å¸³èŸå»ºç«‹å¤±: {message}")
                                    
                            except Exception as e:
                                st.error(f" ¸å¸³è™¼ŸéŒ¯èª: {str(e)}")
                                import traceback
                                st.error(f"Œ¯èª¤è©³: {traceback.format_exc()}")
                    
                    with col2:
                        if st.button("’ç", key=f"reject_{i}"):
                            try:
                                # ›´–°Google Sheet‹ïŒäå¯«¥æœ¬œ°”¨
                                # ‰¾°è©²è¨˜éè¡
                                found = False
                                for row_idx, row in enumerate(all_values[1:], start=2):  # å¾ç¬¬2è¡Œé‹å‹ïŒç´¢å¼•å2‹å
                                    if (username_col_idx < len(row) and 
                                        row[username_col_idx] == record.get('ä½¿ç”¨ç¨±')):
                                        # ›´–°
                                        worksheet.update_cell(row_idx, status_col_idx + 1, "å·²æ’ç")  # APIç´¢å•å1‹å
                                        found = True
                                        break
                                
                                if not found:
                                    st.error(f"¡æ•åœ¨å·¥äœè¡¨ä¸­æ‰¾°ä½¿”¨ç¨± {record.get('ä½¿ç”¨ç¨±')} è¨˜é")
                                    return
                                
                                st.success(f"å·²æ’ç {record.get('å§“å')} å¸³èŸç”³è«")
                                st.rerun()
                            except Exception as e:
                                st.error(f"’ç•å¸³™¼ŸéŒ¯èª: {str(e)}")
                                import traceback
                                st.error(f"Œ¯èª¤è©³: {traceback.format_exc()}")
                    
                    with col3:
                        reason = st.text_input("’ç•åŸå", key=f"reason_{i}")
                        
        else:
            st.info("›®æ’æ‰åå¯©æ ¸å¸³è")
            
        # é¡¯ç¤ºå·²å¯© ¸å¸³èæ­·å²
        if st.checkbox("é¡¯ç¤ºå·²å¯© ¸å¸³èæ­·å²"):
            with st.expander("å·²å¯© ¸å¸³è"):
                if approved_records:
                    for record in approved_records:
                        st.write(f"{record.get('å§“å')} ({record.get('ä½¿ç”¨ç¨±')}) - {record.get('è§’è‰²')} - {record.get('”³è«‹æ', 'œªè¨˜é')}")
                else:
                    st.info("æ²’æ‰å·²å¯©æ ¸å¸³è")
        
        # é¡¯ç¤ºå·²æ’ç•å¸³æ­·å²
        if st.checkbox("é¡¯ç¤ºå·²æ’ç•å¸³æ­·å²"):
            with st.expander("å·²æ’ç•å¸³"):
                if rejected_records:
                    for record in rejected_records:
                        st.write(f"{record.get('å§“å')} ({record.get('ä½¿ç”¨ç¨±')}) - {record.get('è§’è‰²')} - {record.get('”³è«‹æ', 'œªè¨˜é')}")
                else:
                    st.info("æ²’æ‰å·²’ç•çå¸³è")
                
    except Exception as e:
        st.error(f"²–å¯© ¸è³™æ™¼ŸéŒ¯èª: {str(e)}")
        import traceback
        st.error(f"Œ¯èª¤è©³: {traceback.format_exc()}") 

def change_user_password(username, new_password):
    """­×§ï¨Ï¥ÎªÌ±K½X"""
    users = load_users()
    if username not in users:
        return False, "¨Ï¥ÎªÌ¤£¦s¦b"
    
    # Âø´ê·s±K½X
    hashed_password = hash_password(new_password)
    
    # §ó·s±K½X
    users[username]['password'] = hashed_password
    save_users(users)
    return True, "±K½X­×§ï¦¨¥\"

def show_change_password_page():
    """Åã¥Ü±K½X­×§ï­¶­±"""
    st.title("­×§ï±K½X")
    
    # ÀË¬d¬O§_¤wµn¤J
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.error("½Ğ¥ıµn¤J¨t²Î")
        return False
    
    current_username = st.session_state.get('username')
    current_role = st.session_state.get('role')
    
    st.info(f"¥Ø«eµn¤J¨Ï¥ÎªÌ¡G{current_username} ({USER_ROLES.get(current_role, current_role)})")
    
    with st.form("change_password_form"):
        current_password = st.text_input("¥Ø«e±K½X", type="password", help="½Ğ¿é¤J±z¥Ø«eªº±K½X¥HÅçÃÒ¨­¥÷")
        new_password = st.text_input("·s±K½X", type="password", help="½Ğ¿é¤J·sªº±K½X")
        confirm_password = st.text_input("½T»{·s±K½X", type="password", help="½Ğ¦A¦¸¿é¤J·s±K½X¥H½T»{")
        
        submitted = st.form_submit_button("­×§ï±K½X")
        
        if submitted:
            # ÅçÃÒ¿é¤J
            if not all([current_password, new_password, confirm_password]):
                st.error("½Ğ¶ñ¼g©Ò¦³Äæ¦ì")
                return False
            
            if new_password != confirm_password:
                st.error("·s±K½X»P½T»{±K½X¤£¤@­P")
                return False
            
            if len(new_password) < 6:
                st.error("·s±K½Xªø«×¦Ü¤Ö»İ­n 6 ­Ó¦r¤¸")
                return False
            
            # ÅçÃÒ¥Ø«e±K½X
            if not authenticate_user(current_username, current_password):
                st.error("¥Ø«e±K½X¿ù»~")
                return False
            
            # ­×§ï±K½X
            success, message = change_user_password(current_username, new_password)
            if success:
                st.success(message)
                st.info("½Ğ¨Ï¥Î·s±K½X­«·sµn¤J")
                # µn¥X¨Ï¥ÎªÌ
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
    """Åã¥ÜºŞ²z­û±K½XºŞ²z­¶­±"""
    if not check_permission(st.session_state.get('role'), 'can_manage_users'):
        st.error("±z¨S¦³Åv­­ºŞ²z¨Ï¥ÎªÌ±K½X")
        return
    
    st.title("±K½XºŞ²z")
    
    users = load_users()
    
    # ¿ï¾Ü¨Ï¥ÎªÌ
    user_options = list(users.keys())
    selected_user = st.selectbox(
        "¿ï¾Ü­n­×§ï±K½Xªº¨Ï¥ÎªÌ",
        options=user_options,
        format_func=lambda x: f"{x} ({USER_ROLES.get(users[x]['role'], users[x]['role'])}) - {users[x]['name']}"
    )
    
    if selected_user:
        st.info(f"¿ï¾Üªº¨Ï¥ÎªÌ¡G{selected_user}")
        
        with st.form("admin_change_password_form"):
            new_password = st.text_input("·s±K½X", type="password", help="½Ğ¿é¤J·sªº±K½X")
            confirm_password = st.text_input("½T»{·s±K½X", type="password", help="½Ğ¦A¦¸¿é¤J·s±K½X¥H½T»{")
            
            submitted = st.form_submit_button("­×§ï±K½X")
            
            if submitted:
                if not all([new_password, confirm_password]):
                    st.error("½Ğ¶ñ¼g©Ò¦³Äæ¦ì")
                    return
                
                if new_password != confirm_password:
                    st.error("·s±K½X»P½T»{±K½X¤£¤@­P")
                    return
                
                if len(new_password) < 6:
                    st.error("·s±K½Xªø«×¦Ü¤Ö»İ­n 6 ­Ó¦r¤¸")
                    return
                
                success, message = change_user_password(selected_user, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message) 