import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re
import json
from modules.utils.data_utils import extract_spreadsheet_id, extract_gid
import pandas as pd
import os
import traceback
from google.oauth2 import service_account
from typing import Optional, Tuple, Dict, Any, List
import base64
import time

# 全局變數控制診斷訊息的顯示
SHOW_DIAGNOSTICS = False

# 常數定義
DEFAULT_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZRYRrsSMNUKoWM32gc5D9FykCHm7IRgcmR1_qXx8_w/edit?resourcekey=&gid=1986457679#gid=1986457679"
GOOGLE_API_SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/cloud-platform'
]
REQUIRED_CREDENTIAL_FIELDS = [
    "type", "project_id", "private_key_id", "private_key",
    "client_email", "client_id", "auth_uri", "token_uri",
    "auth_provider_x509_cert_url", "client_x509_cert_url"
]

def is_base64(s: str, strict: bool = False) -> bool:
    """檢查字符串是否為有效的 Base64 編碼"""
    try:
        # 提取 PEM 格式的核心內容
        lines = s.strip().split('\n')
        if len(lines) < 3:
            return False
        content = ''.join(lines[1:-1]) # 提取 BEGIN 和 END 標記之間的部分
        
        # 檢查 Base64 字符
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")
        padding_count = content.count('=')
        core_content = content.rstrip('=')
        
        if not all(c in valid_chars for c in core_content):
            return False # 包含無效字符
        if padding_count > 2:
            return False # 最多兩個填充符
        if padding_count > 0 and len(content) % 4 != 0:
            return False # 帶填充的長度必須是4的倍數
        if padding_count == 0 and strict and len(content) % 4 != 0:
             # 嚴格模式下，無填充時長度也需檢查 (雖然非必須)
             pass
             
        # 嘗試解碼
        base64.b64decode(content)
        return True
    except Exception:
        return False

def show_diagnostic(message: str, type: str = "info"):
    """顯示診斷訊息的輔助函數
    
    Args:
        message: 要顯示的訊息
        type: 訊息類型 ("info", "success", "warning", "error")
    """
    if SHOW_DIAGNOSTICS:
        if type == "info":
            st.info(message)
        elif type == "success":
            st.success(message)
        elif type == "warning":
            st.warning(message)
        elif type == "error":
            st.error(message)

def fix_private_key_format(private_key: str) -> str:
    """更精確地修復私鑰格式，處理 Base64 填充"""
    try:
        lines = private_key.strip().split('\n')
        if len(lines) < 3 or not lines[0].startswith('-----BEGIN') or not lines[-1].startswith('-----END'):
            show_diagnostic("私鑰 PEM 結構不完整，嘗試基本修復", "warning")
            potential_base64 = ''.join(re.findall(r'[A-Za-z0-9+/=]+', private_key))
        else:
            potential_base64 = ''.join(lines[1:-1])
        
        base64_chars = re.sub(r'[^A-Za-z0-9+/=]', '', potential_base64)
        
        missing_padding = len(base64_chars) % 4
        if missing_padding:
            base64_chars += '=' * (4 - missing_padding)
            show_diagnostic(f"檢測到 Base64 填充不足，已添加 {4 - missing_padding} 個 '='", "info")
        
        try:
            base64.b64decode(base64_chars)
            show_diagnostic("核心 Base64 內容驗證成功", "info")
        except Exception as decode_err:
            show_diagnostic(f"修復後的 Base64 內容解碼失敗: {str(decode_err)}", "error")
            return private_key
            
        formatted_lines = ['-----BEGIN PRIVATE KEY-----']
        for i in range(0, len(base64_chars), 64):
            formatted_lines.append(base64_chars[i:i+64])
        formatted_lines.append('-----END PRIVATE KEY-----')
        
        result = '\n'.join(formatted_lines) + '\n'
        
        show_diagnostic("私鑰格式化後的結構：", "info")
        show_diagnostic(f"- 總行數：{len(formatted_lines)}", "info")
        show_diagnostic(f"- 核心 Base64 長度 (含填充)：{len(base64_chars)}", "info")
        show_diagnostic(f"- 每行長度正確：{all(len(line) <= 64 for line in formatted_lines[1:-1])}", "info")
        
        return result
        
    except Exception as e:
        show_diagnostic(f"修復私鑰格式時發生嚴重錯誤：{str(e)}", "error")
        return private_key

def validate_credentials(credentials: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """驗證憑證的有效性並提供詳細診斷"""
    try:
        missing_fields = [field for field in REQUIRED_CREDENTIAL_FIELDS 
                         if field not in credentials]
        if missing_fields:
            return False, f"缺少必要的憑證欄位：{', '.join(missing_fields)}"
        
        private_key = credentials.get('private_key', '')
        if not private_key:
             return False, "缺少私鑰"
        
        show_diagnostic("驗證前的私鑰診斷信息：", "info")
        show_diagnostic(f"- 包含開始標記：{'-----BEGIN PRIVATE KEY-----' in private_key}", "info")
        show_diagnostic(f"- 包含結束標記：{'-----END PRIVATE KEY-----' in private_key}", "info")
        newline_count = private_key.count('\n')
        show_diagnostic(f"- 換行符數量：{newline_count}", "info")
        show_diagnostic(f"- Base64 驗證：{is_base64(private_key)}", "info")
        
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            return False, "私鑰缺少正確的開始標記"
        if not private_key.strip().endswith('-----END PRIVATE KEY-----'):
            return False, "私鑰缺少正確的結束標記"
        if private_key.count('\n') < 2:
            return False, "私鑰缺少必要的換行符"
            
        if not is_base64(private_key, strict=True):
            return False, "私鑰核心內容 Base64 驗證失敗"
        
        return True, None
    except Exception as e:
        return False, f"驗證憑證時發生錯誤：{str(e)}"

def get_credentials_from_secrets() -> Optional[Dict[str, Any]]:
    """從 Streamlit Secrets 獲取憑證"""
    if not hasattr(st, 'secrets') or not st.secrets:
        st.error("未找到任何 Secrets 設定")
        return None
    
    if "gcp_service_account" not in st.secrets:
        st.error("在 Secrets 中未找到 gcp_service_account 設定")
        return None
    
    try:
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
        
        is_valid, error_msg = validate_credentials(credentials)
        if not is_valid:
            st.error(error_msg)
            return None
            
        return credentials
    except Exception as e:
        st.error(f"處理 Streamlit Secrets 時發生錯誤：{str(e)}")
        return None

def get_credentials_from_file() -> Optional[Dict[str, Any]]:
    """從本地檔案獲取憑證"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        credentials_path = os.path.join(current_dir, 'credentials.json')
        
        if not os.path.exists(credentials_path):
            st.error(f"未找到憑證檔案：{credentials_path}")
            return None
        
        # 顯示檔案信息
        st.info(f"憑證檔案路徑：{credentials_path}")
        st.info(f"檔案大小：{os.path.getsize(credentials_path)} bytes")
        
        try:
            with open(credentials_path, 'r', encoding='utf-8') as f:
                # 讀取原始文件內容
                file_content = f.read()
                st.info(f"檔案原始內容長度：{len(file_content)} 字符")
                
                # 嘗試處理可能的 BOM
                if file_content.startswith('\ufeff'):
                    st.info("檢測到並移除 BOM 標記")
                    file_content = file_content[1:]
                
                # 嘗試解析 JSON
                try:
                    credentials = json.loads(file_content)
                except json.JSONDecodeError as je:
                    st.error(f"JSON 解析錯誤：{str(je)}")
                    st.info("請確保 credentials.json 是有效的 JSON 格式。")
                    return None
                
                # 獲取並修復私鑰
                if 'private_key' not in credentials:
                    st.error("憑證文件中未找到 'private_key' 欄位")
                    return None
                    
                original_key = credentials['private_key']
                st.info("開始修復私鑰格式...")
                fixed_key = fix_private_key_format(original_key)
                
                if fixed_key == original_key:
                    st.info("私鑰格式無需修復或修復失敗")
                else:
                    st.info("私鑰格式已修復")
                    credentials['private_key'] = fixed_key
                
                # 顯示修復後的診斷信息
                st.info("修復後的私鑰診斷信息：")
                st.info("- 包含開始標記：" + str('-----BEGIN PRIVATE KEY-----' in fixed_key))
                st.info("- 包含結束標記：" + str('-----END PRIVATE KEY-----' in fixed_key))
                st.info("- 換行符數量：" + str(fixed_key.count('\n')))
                st.info("- Base64 驗證：" + str(is_base64(fixed_key)))
                
                # 最後驗證整個憑證對象
                st.info("開始驗證最終憑證...")
                is_valid, error_msg = validate_credentials(credentials)
                if not is_valid:
                    st.error(f"最終憑證驗證失敗：{error_msg}")
                    return None
                else:
                    show_diagnostic("憑證驗證成功", "success")
                    return credentials
                    
        except Exception as e:
            st.error(f"讀取或處理憑證檔案時發生錯誤：{str(e)}")
            st.error(f"錯誤詳情：{traceback.format_exc()}")
            return None
            
    except Exception as e:
        st.error(f"處理憑證檔案路徑時發生錯誤：{str(e)}")
        st.error(f"錯誤詳情：{traceback.format_exc()}")
        return None

def test_connection(client: gspread.Client) -> bool:
    """測試 Google API 連接"""
    try:
        test_url = "https://docs.google.com/spreadsheets/d/1I2GzYptiPvhN5dT3_qzVXlIAoPeI8S9MaTVzxfDVjrw/edit?gid=0#gid=0"
        spreadsheet_id = extract_spreadsheet_id(test_url)
        
        if spreadsheet_id:
            test_sheet = client.open_by_key(spreadsheet_id)
            show_diagnostic(f"成功打開試算表: {test_sheet.title}", "success")
            return True
            
        spreadsheets = client.list_spreadsheet_files()
        show_diagnostic(f"Google API 連接成功！找到 {len(spreadsheets)} 個試算表。", "success")
        return True
    except Exception as e:
        st.error(f"連接測試失敗：{str(e)}")
        return False

def setup_google_connection() -> Optional[gspread.Client]:
    """設定與 Google API 的連接"""
    client = None
    credentials = None
    source = ""

    try:
        credentials_secrets = get_credentials_from_secrets()
        if credentials_secrets:
            show_diagnostic("使用 Streamlit Secrets 中的憑證", "info")
            credentials = credentials_secrets
            source = "Secrets"
    except Exception as e:
        show_diagnostic(f"從 Secrets 加載憑證時出錯: {e}", "warning")

    if not credentials:
        try:
            show_diagnostic("嘗試使用本地憑證文件...", "info")
            credentials_file = get_credentials_from_file()
            if credentials_file:
                credentials = credentials_file
                source = "本地文件"
            else:
                show_diagnostic("無法從本地文件加載憑證", "error")
                return None
        except Exception as e:
            show_diagnostic(f"從本地文件加載憑證時發生錯誤: {e}", "error")
            show_diagnostic(f"錯誤詳情: {traceback.format_exc()}", "error")
            return None

    if not credentials:
        show_diagnostic("未能獲取有效的 Google API 憑證", "error")
        return None

    show_diagnostic(f"使用來源 '{source}' 的憑證建立連接...", "info")
    try:
        creds = service_account.Credentials.from_service_account_info(
            credentials, 
            scopes=GOOGLE_API_SCOPES
        )
        client = gspread.authorize(creds)
        show_diagnostic("Google API 認證成功", "success")
        
        if test_connection(client):
            show_diagnostic("Google API 連接測試成功", "success")
            return client
        else:
            show_diagnostic("Google API 連接測試失敗", "error")
            return None
            
    except Exception as e:
        show_diagnostic(f"建立 Google API 認證時發生錯誤：{str(e)}", "error")
        show_diagnostic("這通常由私鑰格式或內容問題引起。請檢查：", "error")
        show_diagnostic("1. credentials.json 是否是從 Google Cloud Console 直接下載的原始文件？", "error")
        show_diagnostic("2. 私鑰內容是否被意外修改或損壞？", "error")
        show_diagnostic("3. 服務帳號是否已啟用並具有所需權限？", "error")
        show_diagnostic(f"詳細錯誤信息: {traceback.format_exc()}", "error")
        return None

def fetch_google_form_data(spreadsheet_url: Optional[str] = None, sheet_title: Optional[str] = None) -> Tuple[Optional[pd.DataFrame], Optional[List[str]]]:
    """從 Google 表單獲取評核資料"""
    try:
        spreadsheet_url = spreadsheet_url or DEFAULT_SPREADSHEET_URL
        client = setup_google_connection()
        
        if client is None:
            return None, None
            
        spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
        if not spreadsheet_id:
            st.error("無法從 URL 提取 spreadsheet ID")
            return None, None
            
        # 設定重試參數
        max_retries = 3
        retry_delay = 2  # 秒
        current_retry = 0
        
        while current_retry < max_retries:
            try:
                spreadsheet = client.open_by_key(spreadsheet_id)
                all_worksheets = spreadsheet.worksheets()
                sheet_titles = [sheet.title for sheet in all_worksheets]
                
                if not sheet_title and sheet_titles:
                    worksheet = all_worksheets[0]
                    sheet_title = sheet_titles[0]
                else:
                    worksheet = spreadsheet.worksheet(sheet_title)
                    
                data = worksheet.get_all_records()
                
                if not data:
                    st.warning(f"工作表 '{sheet_title}' 中沒有資料")
                    return None, sheet_titles
                    
                return pd.DataFrame(data), sheet_titles
                
            except Exception as e:
                error_message = str(e)
                if "Quota exceeded" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                    current_retry += 1
                    if current_retry < max_retries:
                        st.warning(f"遇到 API 速率限制，等待 {retry_delay} 秒後重試... (嘗試 {current_retry}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指數退避
                    else:
                        st.error("已達到最大重試次數，請稍後再試")
                        return None, None
                else:
                    st.error(f"處理試算表時發生錯誤：{error_message}")
                    return None, None
                    
    except Exception as e:
        st.error(f"獲取 Google 表單資料時發生錯誤：{str(e)}")
        return None, None