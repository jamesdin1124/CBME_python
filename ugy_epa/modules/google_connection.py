import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re
import json
from .utils import extract_spreadsheet_id, extract_gid
import pandas as pd

DEFAULT_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZRYRrsSMNUKoWM32gc5D9FykCHm7IRgcmR1_qXx8_w/edit?resourcekey=&gid=1986457679#gid=1986457679"

def extract_gid(url):
    """從 Google 試算表 URL 中提取 gid"""
    # 正則表達式匹配 gid
    match = re.search(r'gid=(\d+)', url)
    if match:
        return int(match.group(1))
    return None

def setup_google_connection():
    """設定與 Google API 的連接"""
    try:
        # 從 Streamlit Secrets 獲取憑證資訊
        if "gcp_service_account" in st.secrets:
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
            
            # 設定 Google API 範圍
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # 建立認證
            creds = Credentials.from_service_account_info(credentials, scopes=scope)
            client = gspread.authorize(creds)
            
            return client
        else:
            # 如果沒有在 secrets 中找到憑證，則使用上傳方式
            st.warning("未找到 Google API 憑證設定，請上傳憑證檔案")
            
            # 檢查是否有上傳憑證檔案
            uploaded_file = st.file_uploader("上傳 Google API 憑證 JSON 檔案", type=['json'])
            
            if uploaded_file is not None:
                # 將上傳的憑證檔案保存到臨時檔案
                credentials_json = uploaded_file.getvalue().decode('utf-8')
                
                # 設定 Google API 範圍
                scope = [
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                
                # 從憑證建立連接
                credentials_dict = json.loads(credentials_json)
                
                # 建立認證
                creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
                client = gspread.authorize(creds)
                
                # 儲存到 session state 以便後續使用
                st.session_state.google_credentials = credentials_dict
                st.session_state.google_client = client
                
                st.success("Google API 連接成功！")
                return client
            
            # 如果已經有憑證，直接使用
            if 'google_client' in st.session_state:
                return st.session_state.google_client
                
            return None
    except Exception as e:
        st.error(f"連接 Google API 時發生錯誤：{str(e)}")
        return None

def fetch_google_form_data(spreadsheet_url=None, sheet_title=None):
    """從 Google 表單獲取評核資料"""
    try:
        # 如果沒有提供 URL，使用預設 URL
        if not spreadsheet_url:
            spreadsheet_url = DEFAULT_SPREADSHEET_URL
        
        client = setup_google_connection()
        if client is None:
            return None, None
        
        # 從 URL 提取 spreadsheet ID
        spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
        if not spreadsheet_id:
            st.error("無法從 URL 提取 spreadsheet ID，請檢查 URL 格式")
            return None, None
        
        # 開啟指定的 Google 試算表
        try:
            spreadsheet = client.open_by_key(spreadsheet_id)
        except Exception as e:
            st.error(f"無法開啟試算表：{str(e)}")
            st.info("請確保您的 Google API 服務帳號有權限訪問此試算表。")
            return None, None
        
        # 獲取所有工作表
        all_worksheets = spreadsheet.worksheets()
        sheet_titles = [sheet.title for sheet in all_worksheets]
        
        # 如果沒有提供工作表標題，使用第一個工作表
        if not sheet_title:
            if sheet_titles:
                worksheet = all_worksheets[0]
                sheet_title = sheet_titles[0]
            else:
                st.error("試算表中沒有工作表")
                return None, sheet_titles
        else:
            try:
                worksheet = spreadsheet.worksheet(sheet_title)
            except Exception as e:
                st.error(f"無法開啟工作表 {sheet_title}：{str(e)}")
                return None, sheet_titles
        
        # 獲取所有資料
        data = worksheet.get_all_records()
        
        if not data:
            st.warning(f"工作表 '{sheet_title}' 中沒有資料或資料格式不正確")
            return None, sheet_titles
        
        # 轉換為 DataFrame
        df = pd.DataFrame(data)
        
        return df, sheet_titles
        
    except Exception as e:
        st.error(f"獲取 Google 表單資料時發生錯誤：{str(e)}")
        return None, None