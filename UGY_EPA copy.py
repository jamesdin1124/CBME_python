import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO
import os
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
import scipy.stats as stats

# 預設 Google 試算表連結
DEFAULT_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1VZRYRrsSMNUKoWM32gc5D9FykCHm7IRgcmR1_qXx8_w/edit?resourcekey=&gid=1986457679#gid=1986457679"

# 將 epa_level_mapping 移到全局範圍
epa_level_mapping = {
    # 整合重複的尺規格式
    '不允許學員觀察': 1,
    '學員在旁觀察': 1.5,
    '允許學員在旁觀察': 1.5,
    '教師在旁逐步共同操作': 2,
    '教師在旁必要時協助': 2.5,
    '教師可立即到場協助，事後逐項確認': 3,
    '教師可立即到場協助，事後重點確認': 3.3,
    '教師可稍後到場協助，必要時事後確認': 3.6,
    '教師on call提供監督': 4,
    '教師不需on call，事後提供回饋及監督': 4.5,
    '學員可對其他資淺的學員進行監督與教學': 5,
    
    # 整合重複的 Level 格式
    'Level I': 1, ' Level I': 1, 'Level1': 1, 'Level 1': 1,
    'Level 1&2': 1.5, 'Level1&2': 1.5, 'LevelI&2': 1.5, 'Level&2': 1.5,
    'Level II': 2, ' Level II': 2, 'Level2': 2, 'Level 2': 2,
    'Level2&3': 2.5, 'Level 2&3': 2.5, 'Leve 2&3': 2.5,
    'Level 2a': 2, 'Level2a': 2, 'Level 2b': 2.5, 'Level2b': 2.5,
    'Level III': 3, ' Level III': 3, 'Level3': 3, 'Level 3': 3,
    'Level 3a': 3, 'Level3a': 3, 'Level 3b': 3.3, 'Level3b': 3.3,
    'Level3c': 3.6, 'Level 3c': 3.6,
    'Level 3&4': 3.5, 'Level3&4': 3.5, 'Leve 3&4': 3.5, 'Lvel 3&4': 3.5,
    'Level IV': 4, ' Level IV': 4, 'Level4': 4, 'Level 4': 4,
    'Level4&5': 4.5, 'Level 4&5': 4.5,
    'Level 5': 5, 'Level V': 5, ' Level V': 5, 'Level5': 5
}

def extract_spreadsheet_id(url):
    """從 Google 試算表 URL 中提取 spreadsheet ID"""
    # 正則表達式匹配 spreadsheet ID
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    return None

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

def fetch_google_form_data(spreadsheet_url=None, selected_sheet_title=None):
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
        
        # 從 URL 提取 gid
        gid = extract_gid(spreadsheet_url)
        
        # 開啟指定的 Google 試算表
        try:
            spreadsheet = client.open_by_key(spreadsheet_id)
        except Exception as e:
            st.error(f"無法開啟試算表：{str(e)}")
            st.info("請確保您的 Google API 服務帳號有權限訪問此試算表。您需要在試算表的共享設定中添加服務帳號的電子郵件地址。")
            return None, None
        
        # 獲取所有工作表
        all_worksheets = spreadsheet.worksheets()
        sheet_titles = [sheet.title for sheet in all_worksheets]
        
        # 如果沒有提供工作表標題，則返回工作表標題列表供選擇
        if not selected_sheet_title:
            return None, sheet_titles
        
        # 使用提供的工作表標題
        try:
            worksheet = spreadsheet.worksheet(selected_sheet_title)
            st.info(f"使用工作表：{worksheet.title}")
        except Exception as e:
            st.error(f"無法開啟工作表 {selected_sheet_title}：{str(e)}")
            return None, sheet_titles
        
        # 獲取所有資料
        data = worksheet.get_all_records()
        
        if not data:
            # 嘗試獲取原始資料並顯示
            raw_data = worksheet.get_all_values()
            st.write("試算表內容預覽：")
            st.write(f"總行數：{len(raw_data)}")
            if raw_data:
                st.write("前幾行內容：")
                for i, row in enumerate(raw_data[:5]):  # 顯示前5行
                    st.write(f"第 {i} 行: {row}")
            
            st.warning("試算表中沒有資料或資料格式不正確")
            return None, sheet_titles
        
        # 轉換為 DataFrame
        df = pd.DataFrame(data)
        
        # 轉換為 DataFrame 後立即重置索引
        df = df.reset_index(drop=True)
        
        # 檢查並處理重複列名
        if df.columns.duplicated().any():
            # 找出重複的列名
            dup_cols = df.columns[df.columns.duplicated()].tolist()
            st.warning(f"發現重複的列名：{', '.join(dup_cols)}，將為重複列添加後綴")
            
            # 為重複的列名添加後綴
            new_columns = []
            seen = {}
            for col in df.columns:
                if col in seen:
                    seen[col] += 1
                    new_columns.append(f"{col}_{seen[col]}")
                else:
                    seen[col] = 0
                    new_columns.append(col)
            
            # 使用新的列名
            df.columns = new_columns
        
        # 先顯示原始資料
        st.subheader("原始資料表格")
        st.dataframe(df)
        
        # 處理資料格式
        st.info("正在處理資料格式...")
        try:
            df = process_epa_form_data(df)
        except Exception as e:
            st.error(f"處理數據時發生錯誤：{str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None, None
        
        print("原始等級資料範例：", df['教師評核EPA等級'].head())
        print("教師評核EPA等級列的資料類型：", df['教師評核EPA等級'].dtype)
        print("轉換後教師評核EPA等級數值的資料類型：", df['教師評核EPA等級數值'].dtype)
        
        return df, sheet_titles
    except Exception as e:
        st.error(f"獲取 Google 表單資料時發生錯誤：{str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None, None

def safe_map_level(value):
    """安全地將 EPA 等級字串轉換為數值"""
    if isinstance(value, str):
        cleaned_value = value.strip()
        if cleaned_value in epa_level_mapping:
            return epa_level_mapping[cleaned_value]
    # 嘗試直接轉換為數值
    try:
        return float(value)
    except (ValueError, TypeError):
        return np.nan

def process_epa_form_data(df):
    """處理從 Google 表單獲取的 EPA 評核資料格式"""
    # 首先重置索引以解決重複索引問題
    df = df.reset_index(drop=True)
    
    # 處理重複的欄位名稱
    # 為重複的欄位添加後綴
    new_columns = []
    seen = {}
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            new_columns.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_columns.append(col)
    
    # 使用新的欄位名稱
    df.columns = new_columns
    
    # 輸出除錯資訊
    print("處理後的欄位名稱：")
    print(df.columns.tolist())
    
    # 檢查並處理可能的重複記錄
    if df.duplicated().any():
        dup_count = df.duplicated().sum()
        st.warning(f"發現 {dup_count} 筆重複記錄，將自動去除")
        df = df.drop_duplicates().reset_index(drop=True)
    
    # 檢查並重命名欄位，確保標準化
    column_mapping = {
        # 可能的原始欄位名稱映射到標準欄位名稱
        '學員階層': '學員階層',
        '學生階層': '學員階層',
        '階層': '學員階層',
        '姓名': '姓名',
        '學生姓名': '姓名',
        '學號': '學號',  # 保留映射但不作為必要欄位
        '學生學號': '學號',
        '評核時間': '評核時間',
        '時間': '評核時間',
        '時間戳記': '評核時間',
        '日期': '評核時間',
        'EPA評核項目': 'EPA評核項目',
        'EPA項目': 'EPA評核項目',
        '評核項目': 'EPA評核項目',
        '教師評核EPA等級': '教師評核EPA等級',
        '評核等級': '教師評核EPA等級',
        'EPA等級': '教師評核EPA等級',
        '學員自評EPA等級': '學員自評EPA等級',
        '自評等級': '學員自評EPA等級',
        '學員自評': '學員自評EPA等級',
        '自評': '學員自評EPA等級',
        '評語': '評語',
        '回饋': '評語',
        '電子郵件地址': '評核老師',
        '梯次': '梯次',
        '學員梯次': '梯次',
        '實習梯次': '梯次',
        '訓練梯次': '梯次'
    }
    
    # 重命名欄位 - 修改為處理重複欄位的情況
    renamed_columns = {}
    for col in df.columns:
        base_col = col.split('_')[0]  # 取得基本欄位名稱（不含後綴）
        for original, standard in column_mapping.items():
            if original.lower() in base_col.lower():
                # 如果是重複欄位，保留後綴
                suffix = col[len(base_col):] if len(col) > len(base_col) else ''
                renamed_columns[col] = standard + suffix
                break
    
    # 應用重命名
    df = df.rename(columns=renamed_columns)
    
    # 選擇要保留的欄位（使用第一個出現的欄位）
    columns_to_keep = []
    seen_columns = set()
    for col in df.columns:
        base_col = col.split('_')[0]  # 取得基本欄位名稱
        if base_col not in seen_columns:
            columns_to_keep.append(col)
            seen_columns.add(base_col)
    
    # 只保留選定的欄位
    df = df[columns_to_keep]
    
    # 確保必要欄位存在 (修改了等級欄位名稱)
    required_columns = ['學員階層', '姓名', '評核時間', 'EPA評核項目', '教師評核EPA等級', '評語', '評核老師']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.warning(f"表單中缺少以下必要欄位：{', '.join(missing_columns)}")
        # 為缺少的欄位添加空值
        for col in missing_columns:
            df[col] = None
    
    # 如果沒有學員自評EPA等級欄位，創建一個空的
    if '學員自評EPA等級' not in df.columns:
        df['學員自評EPA等級'] = None
    
    # 處理評核時間格式
    if '評核時間' in df.columns:
        try:
            # 嘗試轉換為日期時間格式
            df['評核時間'] = pd.to_datetime(df['評核時間'])
        except:
            # 如果轉換失敗，保持原樣
            pass
    
    # 處理 EPA 等級轉換 - 分別處理教師評核和學員自評
    # 注意：不需要再次定義 epa_level_mapping，因為現在它是全局變量
    
    # 處理教師評核EPA等級 - 改用向量化操作避免 apply 引發的重索引問題
    if '教師評核EPA等級' in df.columns:
        # 將等級欄位轉為字串，並確保處理 NaN 值
        df['教師評核EPA等級'] = df['教師評核EPA等級'].fillna('').astype(str)
        
        # 輸出除錯資訊
        print("原始教師評核EPA等級值：")
        print(df['教師評核EPA等級'].values)
        print("教師評核EPA等級列的資料類型：", df['教師評核EPA等級'].dtypes)  # 修改這裡，使用 dtypes
        
        # 創建一個新列來存儲數值結果，確保長度匹配
        values = []
        for level in df['教師評核EPA等級'].values:
            mapped_value = safe_map_level(level)
            values.append(mapped_value)
            print(f"處理等級 '{level}' -> {mapped_value}")  # 除錯輸出
        
        print(f"處理後的值列表長度：{len(values)}")
        print(f"資料框索引長度：{len(df.index)}")
        
        # 確保值的數量與資料框列數相同
        if len(values) == len(df.index):
            df['教師評核EPA等級數值'] = values
            print("教師評核EPA等級數值列的資料類型：", df['教師評核EPA等級數值'].dtypes)  # 修改這裡，使用 dtypes
            print("教師評核EPA等級數值的唯一值：", df['教師評核EPA等級數值'].unique())
        else:
            st.error(f"值的數量（{len(values)}）與資料列數（{len(df.index)}）不匹配")
            # 如果數量不匹配，填充為 NaN
            df['教師評核EPA等級數值'] = np.nan
    
    # 處理學員自評EPA等級 - 同樣避免使用 apply
    if '學員自評EPA等級' in df.columns and not df['學員自評EPA等級'].isna().all():
        # 將自評等級欄位轉為字串
        df['學員自評EPA等級'] = df['學員自評EPA等級'].astype(str)
        
        # 使用相同的方法處理學員自評
        values = []
        for level in df['學員自評EPA等級']:
            values.append(safe_map_level(level))
        
        df['學員自評EPA等級數值'] = values
        
        # 輸出除錯資訊
        print("學員自評EPA等級列的資料類型：", df['學員自評EPA等級'].dtypes)  # 修改這裡，使用 dtypes
        print("學員自評EPA等級數值列的資料類型：", df['學員自評EPA等級數值'].dtypes)  # 修改這裡，使用 dtypes
        print("學員自評EPA等級數值的唯一值：", df['學員自評EPA等級數值'].unique())
    else:
        # 如果沒有學員自評資料，創建空的數值欄位
        df['學員自評EPA等級數值'] = np.nan
    
    # 為向下兼容，保留原始等級數值欄位，使用教師評核EPA等級數值
    df['等級數值'] = df['教師評核EPA等級數值']
    
    # 如果沒有梯次欄位，嘗試從評核時間生成梯次
    if '梯次' not in df.columns and '評核時間' in df.columns and pd.api.types.is_datetime64_any_dtype(df['評核時間']):
        # 使用年份和月份組合作為梯次
        df['梯次'] = df['評核時間'].dt.strftime('%Y-%m')
        st.info("未找到梯次欄位，已根據評核時間自動生成梯次 (年-月格式)")
    
    # 加入資料來源標記
    df['資料來源'] = 'Google表單EPA評核'
    
    # 加入匯入時間
    df['匯入時間'] = datetime.now()
    
    # 在 groupby 操作之前，確保索引是唯一的
    if df.index.duplicated().any():
        df = df.reset_index(drop=True)
    
    # 顯示處理後的資料表格，以便檢查轉換結果
    st.subheader("資料處理後表格")
    st.dataframe(df)
    
    return df

def show_google_form_import_section():
    """顯示 Google 表單 EPA 評核資料匯入區域"""
    st.title("UGY EPA分析")
    
    # 自動載入預設連結的資料
    with st.spinner("正在自動載入預設試算表資料..."):
        # 首先獲取工作表列表
        df, sheet_titles = fetch_google_form_data(DEFAULT_SPREADSHEET_URL)
        
        if sheet_titles:
            # 直接使用第一個工作表
            selected_sheet = sheet_titles[0]
            st.info(f"自動使用第一個工作表：{selected_sheet}")
            
            # 使用第一個工作表獲取資料
            df, _ = fetch_google_form_data(DEFAULT_SPREADSHEET_URL, selected_sheet)
            
            if df is not None and not df.empty:
                st.success(f"成功匯入 {len(df)} 筆 EPA 評核資料！")
                
                # 顯示處理後的資料預覽
                st.subheader("處理後資料預覽")
                st.dataframe(df)
                
                # 加入篩選器
                st.write("### 資料篩選")
                
                # 篩選梯次
                if '梯次' in df.columns:
                    all_batches = sorted(df['梯次'].unique().tolist())
                    selected_batches = st.multiselect("選擇梯次", all_batches, default=all_batches)
                else:
                    selected_batches = None
                
                # 應用篩選條件
                filtered_df = df.copy()
                
                if selected_batches:
                    filtered_df = filtered_df[filtered_df['梯次'].isin(selected_batches)]
                
                # 顯示篩選後的資料
                st.write(f"篩選後資料：{len(filtered_df)} 筆")
                st.dataframe(filtered_df)
                
                # 將資料存入 session state
                if 'epa_form_data' not in st.session_state:
                    st.session_state.epa_form_data = df
                else:
                    # 如果已有資料，則合併
                    st.session_state.epa_form_data = pd.concat([st.session_state.epa_form_data, df], ignore_index=True)
                
                # 提供下載選項
                st.write("### 下載資料")
                
                # 提供選項下載原始資料或篩選後的資料
                download_option = st.radio("選擇要下載的資料", ["原始資料", "篩選後的資料"])
                
                download_df = df if download_option == "原始資料" else filtered_df
                
                csv = download_df.to_csv(index=False)
                excel_buffer = BytesIO()
                download_df.to_excel(excel_buffer, index=False)
                excel_data = excel_buffer.getvalue()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="下載 CSV 檔案",
                        data=csv,
                        file_name="epa_evaluation_data.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    st.download_button(
                        label="下載 Excel 檔案",
                        data=excel_data,
                        file_name="epa_evaluation_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                # 分析按鈕 - 改為用按鈕觸發，而不是自動分析
                if st.button("分析篩選後的資料"):
                    st.subheader("篩選後資料分析")
                    analyze_epa_data(filtered_df)
                
                # 合併到主資料選項
                st.subheader("合併到主資料")
                data_type = st.radio("選擇要合併的資料類型", ["CEPO 評核資料", "住院醫師評核資料"])
                
                if st.button("合併到選定的資料類型"):
                    if data_type == "CEPO 評核資料":
                        if 'ugy_data' in st.session_state:
                            st.session_state.ugy_data = pd.concat([st.session_state.ugy_data, df], ignore_index=True)
                            st.success("已成功合併到 CEPO 評核資料！")
                        else:
                            st.session_state.ugy_data = df
                            st.success("已建立新的 CEPO 評核資料！")
                    else:  # 住院醫師評核資料
                        if 'resident_data' in st.session_state:
                            st.session_state.resident_data = pd.concat([st.session_state.resident_data, df], ignore_index=True)
                            st.success("已成功合併到住院醫師評核資料！")
                        else:
                            st.session_state.resident_data = df
                            st.success("已建立新的住院醫師評核資料！")
        else:
            st.error("無法獲取試算表工作表列表，請檢查權限設定。")
    
    # 選擇是否使用其他連結
    use_other_link = st.checkbox("使用其他連結", value=False)
    
    if use_other_link:
        # 輸入 Google 表單網址
        other_spreadsheet_url = st.text_input("請輸入 Google 表單回應試算表網址", 
                                       placeholder="例如：https://docs.google.com/spreadsheets/d/xxxx/edit")
        
        if st.button("載入資料") and other_spreadsheet_url:
            with st.spinner("正在載入資料..."):
                df, sheet_titles = fetch_google_form_data(other_spreadsheet_url)
                
                if sheet_titles:
                    # 直接使用第一個工作表
                    selected_sheet = sheet_titles[0]
                    st.info(f"自動使用第一個工作表：{selected_sheet}")
                    
                    # 使用第一個工作表獲取資料
                    df, _ = fetch_google_form_data(other_spreadsheet_url, selected_sheet)
                    
                    if df is not None and not df.empty:
                        st.success(f"成功匯入 {len(df)} 筆 EPA 評核資料！")
                        
                        # 顯示處理後的資料預覽
                        st.subheader("處理後資料預覽")
                        st.dataframe(df)
                        
                        # 加入篩選器
                        st.write("### 資料篩選")
                        
                        # 篩選梯次
                        if '梯次' in df.columns:
                            all_batches = sorted(df['梯次'].unique().tolist())
                            selected_batches = st.multiselect("選擇梯次", all_batches, default=all_batches, key="other_batches")
                        else:
                            selected_batches = None
                        
                        # 應用篩選條件
                        filtered_df = df.copy()
                        
                        if selected_batches:
                            filtered_df = filtered_df[filtered_df['梯次'].isin(selected_batches)]
                        
                        if selected_students and len(selected_students) > 0:
                            filtered_df = filtered_df[filtered_df['姓名'].isin(selected_students)]
                        
                        # 顯示篩選後的資料
                        st.write(f"篩選後資料：{len(filtered_df)} 筆")
                        st.dataframe(filtered_df)
                        
                        # 將資料存入 session state
                        if 'epa_form_data' not in st.session_state:
                            st.session_state.epa_form_data = df
                        else:
                            # 如果已有資料，則合併
                            st.session_state.epa_form_data = pd.concat([st.session_state.epa_form_data, df], ignore_index=True)
                        
                        # 提供下載選項
                        st.write("### 下載資料")
                        
                        # 提供選項下載原始資料或篩選後的資料
                        download_option = st.radio("選擇要下載的資料", ["原始資料", "篩選後的資料"], key="other_download")
                        
                        download_df = df if download_option == "原始資料" else filtered_df
                        
                        csv = download_df.to_csv(index=False)
                        excel_buffer = BytesIO()
                        download_df.to_excel(excel_buffer, index=False)
                        excel_data = excel_buffer.getvalue()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="下載 CSV 檔案",
                                data=csv,
                                file_name="epa_evaluation_data.csv",
                                mime="text/csv"
                            )
                        
                        with col2:
                            st.download_button(
                                label="下載 Excel 檔案",
                                data=excel_data,
                                file_name="epa_evaluation_data.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        # 分析按鈕 - 改為用按鈕觸發，而不是自動分析
                        if st.button("分析篩選後的資料"):
                            st.subheader("篩選後資料分析")
                            analyze_epa_data(filtered_df)
                        
                        # 合併到主資料選項
                        st.subheader("合併到主資料")
                        data_type = st.radio("選擇要合併的資料類型", ["CEPO 評核資料", "住院醫師評核資料"])
                        
                        if st.button("合併到選定的資料類型"):
                            if data_type == "CEPO 評核資料":
                                if 'ugy_data' in st.session_state:
                                    st.session_state.ugy_data = pd.concat([st.session_state.ugy_data, df], ignore_index=True)
                                    st.success("已成功合併到 CEPO 評核資料！")
                                else:
                                    st.session_state.ugy_data = df
                                    st.success("已建立新的 CEPO 評核資料！")
                            else:  # 住院醫師評核資料
                                if 'resident_data' in st.session_state:
                                    st.session_state.resident_data = pd.concat([st.session_state.resident_data, df], ignore_index=True)
                                    st.success("已成功合併到住院醫師評核資料！")
                                else:
                                    st.session_state.resident_data = df
                                    st.success("已建立新的住院醫師評核資料！")
                    else:
                        st.error("無法獲取工作表列表，請檢查網址是否正確以及權限設定。")
    
    # 顯示已匯入的資料
    if 'epa_form_data' in st.session_state and not st.session_state.epa_form_data.empty:
        with st.expander("查看已匯入的所有 EPA 評核資料"):
            st.dataframe(st.session_state.epa_form_data)
            
            # 分析所有已匯入的 EPA 評核資料
            if st.button("分析所有已匯入的 EPA 評核資料"):
                analyze_epa_data(st.session_state.epa_form_data)
            
            if st.button("清除已匯入的 EPA 評核資料"):
                del st.session_state.epa_form_data
                st.experimental_rerun()

def analyze_epa_data(df):
    """分析 EPA 評核資料"""
    if df is None or df.empty:
        st.warning("沒有可分析的資料")
        return
    
    # 確保不會有重複的索引
    df = df.reset_index(drop=True)
    
    # 1. 基本統計資訊
    st.write("# 基本統計資訊")
    
    # 計算評核總數
    total_assessments = len(df)
    
    # 計算不同學員階層的評核數量
    if '學員階層' in df.columns:
        level_counts = df['學員階層'].value_counts()
        
        # 顯示評核總數和各階層評核數量
        col1, col2 = st.columns(2)
        with col1:
            st.metric("評核總數", total_assessments)
        
        with col2:
            st.write("各階層評核數量")
            st.dataframe(level_counts)
    else:
        st.metric("評核總數", total_assessments)
    
    # 2. EPA 項目分析
    if 'EPA評核項目' in df.columns:
        st.write("# EPA 項目分析")
        
        # 計算各 EPA 項目的評核數量
        epa_item_counts = df['EPA評核項目'].value_counts()
    
    # 3. EPA 等級分析 - 同時分析教師評核和學員自評（如果有）
    if '教師評核EPA等級數值' in df.columns:
        # 使用雷達圖呈現 EPA 項目平均等級
        if 'EPA評核項目' in df.columns:
            st.write("### EPA 整體趨勢")
            
            # 創建兩欄布局
            col1, col2 = st.columns([1, 1])
            
            # 計算每個 EPA 項目的整體平均等級（教師評核）
            epa_item_avg_teacher = df.groupby('EPA評核項目')['教師評核EPA等級數值'].mean().reset_index(name='平均值')
            
            # 如果有學員自評資料，也計算其平均值
            has_self_evaluation = '學員自評EPA等級數值' in df.columns and not df['學員自評EPA等級數值'].isna().all()
            if has_self_evaluation:
                epa_item_avg_self = df.groupby('EPA評核項目')['學員自評EPA等級數值'].mean().reset_index(name='平均值')
            
            # 在左欄顯示雷達圖
            with col1:
                # 檢查是否有足夠的資料繪製雷達圖
                if len(epa_item_avg_teacher) >= 3:  # 雷達圖至少需要3個點
                    # 準備雷達圖資料
                    categories = epa_item_avg_teacher['EPA評核項目'].tolist()
                    values_teacher = epa_item_avg_teacher['平均值'].tolist()
                    
                    # 如果有學員自評資料，為雷達圖準備學員自評資料
                    if has_self_evaluation:
                        values_self = []
                        for item in categories:
                            if item in epa_item_avg_self['EPA評核項目'].tolist():
                                values_self.append(epa_item_avg_self[epa_item_avg_self['EPA評核項目'] == item]['平均值'].values[0])
                            else:
                                values_self.append(0)
                    
                    # 確保資料是閉合的（首尾相連）
                    categories.append(categories[0])
                    values_teacher.append(values_teacher[0])
                    if has_self_evaluation:
                        values_self.append(values_self[0])
                    
                    # 計算角度 - 確保與類別數量一致
                    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=True)
                    
                    # 設定中文字型
                    plt.rcParams['font.sans-serif'] = ['sans-serif']
                    plt.rcParams['axes.unicode_minus'] = False
                    
                    # 創建雷達圖
                    fig = plt.figure(figsize=(8, 8))
                    ax = fig.add_subplot(111, polar=True)
                    
                    # 繪製教師評核整體平均雷達圖 - 使用黑色粗線
                    ax.plot(angles, values_teacher, 'o-', linewidth=3, color='black', label='教師評核整體平均')
                    ax.fill(angles, values_teacher, alpha=0.25, color='gray')
                    
                    # 如果有學員自評資料，繪製學員自評整體平均
                    if has_self_evaluation:
                        ax.plot(angles, values_self, 'o-', linewidth=2, color='blue', label='學員自評整體平均')
                        ax.fill(angles, values_self, alpha=0.1, color='blue')
                    
                    # 如果有學員階層欄位，繪製不同階層的平均
                    if '學員階層' in df.columns:
                        # 獲取所有階層
                        all_levels = sorted(df['學員階層'].unique())
                        
                        # 定義不同階層的顏色
                        colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan']
                        
                        # 為每個階層繪製雷達圖
                        for i, level in enumerate(all_levels):
                            # 篩選該階層的資料
                            level_data = df[df['學員階層'] == level]
                            
                            # 計算該階層每個 EPA 項目的平均等級（教師評核）
                            level_epa_avg = level_data.groupby('EPA評核項目')['教師評核EPA等級數值'].mean().reset_index(name='平均值')
                            
                            # 獲取與整體相同的 EPA 項目
                            level_values = []
                            for item in categories[:-1]:  # 不包括閉合點
                                if item in level_epa_avg['EPA評核項目'].tolist():
                                    level_values.append(level_epa_avg[level_epa_avg['EPA評核項目'] == item]['平均值'].values[0])
                                else:
                                    level_values.append(0)
                            
                            # 閉合階層資料
                            level_values.append(level_values[0])
                            
                            # 選擇顏色
                            color = colors[i % len(colors)]
                            
                            # 繪製階層雷達圖
                            ax.plot(angles, level_values, 'o-', linewidth=2, color=color, label=f'{level} 教師評核')
                            ax.fill(angles, level_values, alpha=0.1, color=color)
                    
                    # 設定刻度和標籤
                    ax.set_thetagrids(np.degrees(angles[:-1]), categories[:-1], fontsize=9)
                    ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                    ax.set_yticks([1, 2, 3, 4, 5])
                    ax.set_yticklabels(['1', '2', '3', '4', '5'])
                    ax.set_rlabel_position(0)
                    
                    # 添加標題和圖例
                    plt.title('各 EPA 項目平均等級雷達圖', size=14)
                    plt.legend(loc='upper right', fontsize='small')
                    
                    # 調整布局，確保標籤不被裁剪
                    plt.tight_layout()
                    
                    # 顯示雷達圖
                    st.pyplot(fig)
                else:
                    st.warning("EPA 項目數量不足，無法繪製雷達圖（至少需要3個不同項目）")
            
            # 在右欄顯示每個梯次各個 EPA 項目的平均等級
            with col2:
                if '梯次' in df.columns:
                    st.write("##### 各梯次 EPA 項目平均等級")
                    
                    # 計算每個梯次每個 EPA 項目的平均等級
                    batch_epa_avg = df.groupby(['梯次', 'EPA評核項目'])['教師評核EPA等級數值'].mean().reset_index()
                    batch_epa_pivot = batch_epa_avg.pivot(index='梯次', columns='EPA評核項目', values='教師評核EPA等級數值')
                    
                    # 檢查是否有資料
                    if not batch_epa_pivot.empty:
                        # 顯示表格
                        st.dataframe(batch_epa_pivot.style.background_gradient(cmap='YlGnBu', axis=None))
                        
                        # 繪製折線圖，顯示各 EPA 項目隨梯次的變化趨勢
                        st.write("##### EPA 項目隨梯次變化趨勢")
                        
                        # 創建折線圖
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # 為每個 EPA 項目繪製一條折線及其 95% 信賴區間
                        for item in batch_epa_pivot.columns:
                            # 獲取該 EPA 項目在每個梯次的平均值
                            means = batch_epa_pivot[item]
                            
                            # 計算每個梯次該 EPA 項目的標準差和樣本數
                            std_devs = df[df['EPA評核項目'] == item].groupby('梯次')['教師評核EPA等級數值'].std()
                            counts = df[df['EPA評核項目'] == item].groupby('梯次')['教師評核EPA等級數值'].count()
                            
                            # 計算 95% 信賴區間
                            # 信賴區間 = 平均值 ± 1.96 * (標準差 / sqrt(樣本數))
                            ci_lower = []
                            ci_upper = []
                            
                            for idx in means.index:
                                if idx in std_devs.index and idx in counts.index:
                                    std = std_devs[idx]
                                    count = counts[idx]
                                    
                                    # 處理可能的 NaN 值或樣本數為 1 的情況
                                    if pd.isna(std) or count <= 1:
                                        # 如果標準差為 NaN 或樣本數為 1，則使用平均值作為上下限
                                        ci_lower.append(means[idx])
                                        ci_upper.append(means[idx])
                                    else:
                                        # 計算 95% 信賴區間
                                        margin = 1.96 * (std / np.sqrt(count))
                                        ci_lower.append(max(0, means[idx] - margin))  # 確保下限不小於 0
                                        ci_upper.append(min(5, means[idx] + margin))  # 確保上限不大於 5
                                else:
                                    # 如果沒有標準差或樣本數資料，則使用平均值作為上下限
                                    ci_lower.append(means[idx])
                                    ci_upper.append(means[idx])
                            
                            # 繪製平均值折線
                            ax.plot(means.index, means.values, 'o-', linewidth=2, label=item)
                            
                            # 繪製 95% 信賴區間（半透明區域）
                            ax.fill_between(means.index, ci_lower, ci_upper, alpha=0.2)
                        
                        # 設定圖表屬性
                        ax.set_xlabel('梯次', fontsize=12)
                        ax.set_ylabel('EPA 等級', fontsize=12)
                        ax.set_title('EPA 項目隨梯次變化趨勢 (含 95% 信賴區間)', fontsize=14)
                        ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                        ax.grid(True, linestyle='--', alpha=0.7)
                        
                        # 如果項目太多，將圖例放在圖表下方
                        if len(batch_epa_pivot.columns) > 5:
                            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize='small')
                        else:
                            ax.legend(loc='best', fontsize='small')
                        
                        # 調整布局，確保標籤不被裁剪
                        plt.tight_layout()
                        
                        # 顯示折線圖
                        st.pyplot(fig)
                    else:
                        st.warning("沒有足夠的資料來顯示各梯次 EPA 項目平均等級")
                else:
                    st.warning("資料中缺少梯次欄位，無法顯示各梯次 EPA 項目平均等級")
    
    # 4. 學員雷達圖分析 - 直接呈現所有學生資料
    if '姓名' in df.columns:
        st.write("### 個別學員 EPA 項目雷達圖分析")
        
        # 獲取所有學員姓名
        all_students = sorted(df['姓名'].unique().tolist())
        
        # 計算整體平均
        overall_epa_avg = df.groupby('EPA評核項目')['教師評核EPA等級數值'].mean().reset_index(name='平均值')
        
        # 檢查是否有足夠的資料繪製雷達圖
        if len(overall_epa_avg) >= 3:  # 雷達圖至少需要3個點
            # 準備雷達圖資料
            overall_categories = overall_epa_avg['EPA評核項目'].tolist()
            overall_values = overall_epa_avg['平均值'].tolist()
            
            # 確保資料是閉合的（首尾相連）
            overall_categories.append(overall_categories[0])
            overall_values.append(overall_values[0])
            
            # 計算角度 - 確保與類別數量一致
            angles = np.linspace(0, 2*np.pi, len(overall_categories), endpoint=True)
            
            # 設定中文字型
            plt.rcParams['font.sans-serif'] = ['sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 為每個學員創建雷達圖和資料表格
            for student in all_students:
                # 篩選該學員的資料
                student_data = df[df['姓名'] == student]
                
                # 獲取學員階層（如果存在）
                student_level = "未知階層"
                if '學員階層' in student_data.columns and not student_data['學員階層'].empty:
                    # 獲取該學員最常見的階層
                    student_level = student_data['學員階層'].mode()[0]
                
                # 顯示學員階層+姓名
                st.write(f"#### {student_level} {student}")
                
                # 創建兩欄布局
                col1, col2 = st.columns([1, 1])
                
                # 計算該學員每個 EPA 項目的平均等級
                student_epa_avg = student_data.groupby('EPA評核項目')['教師評核EPA等級數值'].mean().reset_index(name='平均值')
                
                # 在左欄顯示雷達圖
                with col1:
                    # 檢查是否有足夠的資料繪製雷達圖
                    if len(student_epa_avg) >= 3:  # 雷達圖至少需要3個點
                        # 獲取與整體相同的 EPA 項目
                        student_values = []
                        for item in overall_categories[:-1]:  # 不包括閉合點
                            if item in student_epa_avg['EPA評核項目'].tolist():
                                student_values.append(student_epa_avg[student_epa_avg['EPA評核項目'] == item]['平均值'].values[0])
                            else:
                                student_values.append(0)
                        
                        # 閉合學員資料
                        student_values.append(student_values[0])
                        
                        # 創建學員雷達圖
                        fig = plt.figure(figsize=(6, 6))
                        ax = fig.add_subplot(111, polar=True)
                        
                        # 繪製學員雷達圖 - 黑色粗線
                        ax.plot(angles, student_values, 'o-', linewidth=3, color='black', label=f'{student_level} {student}')
                        #ax.fill(angles, student_values, alpha=0.25, color='gray')
                        
                        # 計算該學員階層的平均值
                        if '學員階層' in df.columns and student_level != "未知階層":
                            # 篩選相同階層的資料
                            level_data = df[df['學員階層'] == student_level]
                            level_epa_avg = level_data.groupby('EPA評核項目')['教師評核EPA等級數值'].mean().reset_index(name='平均值')
                            
                            # 獲取與整體相同的 EPA 項目
                            level_values = []
                            for item in overall_categories[:-1]:  # 不包括閉合點
                                if item in level_epa_avg['EPA評核項目'].tolist():
                                    level_values.append(level_epa_avg[level_epa_avg['EPA評核項目'] == item]['平均值'].values[0])
                                else:
                                    level_values.append(0)
                            
                            # 閉合階層資料
                            level_values.append(level_values[0])
                            
                            # 繪製該階層平均值 - 淺藍色細線
                            ax.plot(angles, level_values, 'o-', linewidth=1, color='lightblue', label=f'{student_level}平均')
                            ax.fill(angles, level_values, alpha=0.1, color='lightblue')
                        else:
                            # 如果沒有階層資訊，則使用整體平均
                            ax.plot(angles, overall_values, 'o-', linewidth=1, color='lightblue', label='整體平均')
                        
                        # 設定刻度和標籤
                        ax.set_thetagrids(np.degrees(angles[:-1]), overall_categories[:-1], fontsize=9)
                        ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                        ax.set_yticks([1, 2, 3, 4, 5])
                        ax.set_yticklabels(['1', '2', '3', '4', '5'])
                        ax.set_rlabel_position(0)
                        
                        # 添加標題和圖例
                        plt.title(f'{student_level} {student} EPA 項目評核雷達圖', size=14)
                        plt.legend(loc='upper right', fontsize='small')
                        
                        # 調整布局，確保標籤不被裁剪
                        plt.tight_layout()
                        
                        # 顯示雷達圖
                        st.pyplot(fig)
                    else:
                        st.warning(f"{student_level} {student} 的 EPA 項目數量不足，無法繪製雷達圖（至少需要3個不同項目）")
                
                # 在右欄顯示評語（可收合）
                with col2:
                    if '評語' in student_data.columns and '評核老師' in student_data.columns and 'EPA評核項目' in student_data.columns:
                        # 檢查是否有評語資料
                        if not student_data['評語'].isna().all():
                            # 創建一個可收合的區域顯示評語
                            with st.expander("查看評核評語", expanded=False):
                                # 準備評語資料表格
                                comments_data = student_data[['EPA評核項目', '評語', '評核老師']].copy()
                                
                                # 過濾掉空值或 NaN 評語
                                comments_data = comments_data[comments_data['評語'].notna() & (comments_data['評語'].str.strip() != '')]
                                
                                if not comments_data.empty:
                                    # 重新命名欄位以便於顯示
                                    comments_data = comments_data.rename(columns={
                                        'EPA評核項目': '項目',
                                        '評語': '評語',
                                        '評核老師': '老師'
                                    })
                                    
                                    # 使用 st.table 顯示評語表格，提供更好的固定格式呈現
                                    st.dataframe(comments_data)
                                else:
                                    st.info("此學員沒有有效的評語資料")
                        else:
                            st.info("此學員沒有評語資料")
                    else:
                        st.info("資料中缺少必要欄位（評語、評核老師或EPA評核項目）")
                
                # 新增：顯示學員在不同梯次各 EPA 項目的趨勢折線圖
                st.write("##### 各 EPA 項目隨時間變化趨勢")
                
                # 檢查是否有梯次欄位
                if '梯次' in student_data.columns:
                    # 按梯次和 EPA 項目分組計算平均等級
                    trend_data = student_data.groupby(['梯次', 'EPA評核項目'])['教師評核EPA等級數值'].mean().unstack()
                    
                    # 檢查是否有足夠的資料繪製趨勢圖
                    if not trend_data.empty and len(trend_data) > 1:  # 至少需要兩個時間點
                        # 繪製趨勢折線圖
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # 為每個 EPA 項目繪製一條折線及其 95% 信賴區間
                        for item in trend_data.columns:
                            # 獲取該 EPA 項目在每個梯次的平均值
                            means = trend_data[item]
                            
                            # 計算整體平均的標準差和樣本數（而非學生個人的）
                            overall_std_devs = df[df['EPA評核項目'] == item].groupby('梯次')['教師評核EPA等級數值'].std()
                            overall_counts = df[df['EPA評核項目'] == item].groupby('梯次')['教師評核EPA等級數值'].count()
                            
                            # 計算整體平均的 95% 信賴區間
                            # 信賴區間 = 整體平均值 ± 1.96 * (標準差 / sqrt(樣本數))
                            overall_means = df[df['EPA評核項目'] == item].groupby('梯次')['教師評核EPA等級數值'].mean()
                            ci_lower = []
                            ci_upper = []
                            
                            for idx in means.index:
                                if idx in overall_std_devs.index and idx in overall_counts.index and idx in overall_means.index:
                                    std = overall_std_devs[idx]
                                    count = overall_counts[idx]
                                    overall_mean = overall_means[idx]
                                    
                                    # 處理可能的 NaN 值或樣本數為 1 的情況
                                    if pd.isna(std) or count <= 1:
                                        # 如果標準差為 NaN 或樣本數為 1，則使用平均值作為上下限
                                        ci_lower.append(overall_mean)
                                        ci_upper.append(overall_mean)
                                    else:
                                        # 計算 95% 信賴區間
                                        margin = 1.96 * (std / np.sqrt(count))
                                        ci_lower.append(max(0, overall_mean - margin))  # 確保下限不小於 0
                                        ci_upper.append(min(5, overall_mean + margin))  # 確保上限不大於 5
                                else:
                                    # 如果沒有標準差或樣本數資料，則使用平均值作為上下限
                                    if idx in overall_means.index:
                                        ci_lower.append(overall_means[idx])
                                        ci_upper.append(overall_means[idx])
                                    else:
                                        ci_lower.append(means[idx])
                                        ci_upper.append(means[idx])
                            
                            # 繪製學生平均值折線
                            ax.plot(means.index, means.values, 'o-', linewidth=2, label=item)
                            
                            # 繪製整體平均的 95% 信賴區間（半透明區域）
                            ax.fill_between(means.index, ci_lower, ci_upper, alpha=0.2)
                        
                        # 設定圖表屬性
                        ax.set_xlabel('梯次', fontsize=12)
                        ax.set_ylabel('EPA 等級', fontsize=12)
                        ax.set_title(f'{student_level} {student} 各 EPA 項目隨時間變化趨勢 (含整體平均 95% 信賴區間)', fontsize=14)
                        ax.set_ylim(0, 6)  # EPA 等級範圍為 0-5
                        ax.grid(True, linestyle='--', alpha=0.7)
                        
                        # 如果項目太多，將圖例放在圖表下方
                        if len(trend_data.columns) > 5:
                            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize='small')
                        else:
                            ax.legend(loc='best', fontsize='small')
                        
                        # 調整布局，確保標籤不被裁剪
                        plt.tight_layout()
                        
                        # 顯示趨勢折線圖
                        st.pyplot(fig)
                    else:
                        st.info(f"{student_level} {student} 在不同梯次的資料不足，無法繪製趨勢圖（至少需要兩個不同梯次的資料）")
                elif '評核時間' in student_data.columns:
                    # 如果沒有梯次欄位但有評核時間，可以按月份分組
                    student_data['月份'] = student_data['評核時間'].dt.strftime('%Y-%m')
                    
                    # 按月份和 EPA 項目分組計算平均等級
                    trend_data = student_data.groupby(['月份', 'EPA評核項目'])['教師評核EPA等級數值'].mean().unstack()
                    
                    # 檢查是否有足夠的資料繪製趨勢圖
                    if not trend_data.empty and len(trend_data) > 1:  # 至少需要兩個時間點
                        # 繪製趨勢折線圖
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # 為每個 EPA 項目繪製一條折線及其 95% 信賴區間
                        for item in trend_data.columns:
                            # 獲取該 EPA 項目在每個梯次的平均值
                            means = trend_data[item]
                            
                            # 計算整體平均的標準差和樣本數（而非學生個人的）
                            overall_std_devs = df[df['EPA評核項目'] == item].groupby('梯次')['教師評核EPA等級數值'].std()
                            overall_counts = df[df['EPA評核項目'] == item].groupby('梯次')['教師評核EPA等級數值'].count()
                            
                            # 計算整體平均的 95% 信賴區間
                            # 信賴區間 = 整體平均值 ± 1.96 * (標準差 / sqrt(樣本數))
                            overall_means = df[df['EPA評核項目'] == item].groupby('梯次')['教師評核EPA等級數值'].mean()
                            ci_lower = []
                            ci_upper = []
                            
                            for idx in means.index:
                                if idx in overall_std_devs.index and idx in overall_counts.index and idx in overall_means.index:
                                    std = overall_std_devs[idx]
                                    count = overall_counts[idx]
                                    overall_mean = overall_means[idx]
                                    
                                    # 處理可能的 NaN 值或樣本數為 1 的情況
                                    if pd.isna(std) or count <= 1:
                                        # 如果標準差為 NaN 或樣本數為 1，則使用平均值作為上下限
                                        ci_lower.append(overall_mean)
                                        ci_upper.append(overall_mean)
                                    else:
                                        # 計算 95% 信賴區間
                                        margin = 1.96 * (std / np.sqrt(count))
                                        ci_lower.append(max(0, overall_mean - margin))  # 確保下限不小於 0
                                        ci_upper.append(min(5, overall_mean + margin))  # 確保上限不大於 5
                                else:
                                    # 如果沒有標準差或樣本數資料，則使用平均值作為上下限
                                    if idx in overall_means.index:
                                        ci_lower.append(overall_means[idx])
                                        ci_upper.append(overall_means[idx])
                                    else:
                                        ci_lower.append(means[idx])
                                        ci_upper.append(means[idx])
                            
                            # 繪製學生平均值折線
                            ax.plot(means.index, means.values, 'o-', linewidth=2, label=item)
                            
                            # 繪製整體平均的 95% 信賴區間（半透明區域）
                            ax.fill_between(means.index, ci_lower, ci_upper, alpha=0.2)
                        
                        # 設定圖表屬性
                        ax.set_xlabel('月份', fontsize=12)
                        ax.set_ylabel('EPA 等級', fontsize=12)
                        ax.set_title(f'{student_level} {student} 各 EPA 項目隨時間變化趨勢 (含整體平均 95% 信賴區間)', fontsize=14)
                        ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                        ax.grid(True, linestyle='--', alpha=0.7)
                        
                        # 如果項目太多，將圖例放在圖表下方
                        if len(trend_data.columns) > 5:
                            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize='small')
                        else:
                            ax.legend(loc='best', fontsize='small')
                        
                        # 調整布局，確保標籤不被裁剪
                        plt.tight_layout()
                        
                        # 顯示趨勢折線圖
                        st.pyplot(fig)
                    else:
                        st.info(f"{student_level} {student} 在不同時間的資料不足，無法繪製趨勢圖（至少需要兩個不同時間點的資料）")
                else:
                    st.warning("缺少梯次或評核時間欄位，無法繪製時間趨勢圖")
                
                # 添加分隔線
                st.markdown("---")


