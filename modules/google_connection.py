import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re
import json
from .utils import extract_spreadsheet_id, extract_gid
import pandas as pd
import os
import traceback
from google.oauth2 import service_account

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
            st.error(f"錯誤詳情: {traceback.format_exc()}")
            return None
            
    except Exception as e:
        st.error(f"連接 Google API 時發生未預期錯誤：{str(e)}")
        st.error(f"錯誤堆疊: {traceback.format_exc()}")
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