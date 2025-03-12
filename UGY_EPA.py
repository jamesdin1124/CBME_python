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
        
        # 處理資料格式
        df = process_epa_form_data(df)
        
        return df, sheet_titles
    except Exception as e:
        st.error(f"獲取 Google 表單資料時發生錯誤：{str(e)}")
        return None, None

def process_epa_form_data(df):
    """處理從 Google 表單獲取的 EPA 評核資料格式"""
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
        '等級': '等級',
        '評核等級': '等級',
        'EPA等級': '等級',
        '評語': '評語',
        '回饋': '評語',
        '電子郵件地址': '評核老師',  # 將電子郵件地址映射為評核老師
        '梯次': '梯次',
        '學員梯次': '梯次',
        '實習梯次': '梯次',
        '訓練梯次': '梯次'
    }
    
    # 重命名欄位
    for col in df.columns:
        for original, standard in column_mapping.items():
            if original.lower() in col.lower():
                df = df.rename(columns={col: standard})
                break
    
    # 確保必要欄位存在 (移除了學號欄位)
    required_columns = ['學員階層', '姓名', '評核時間', 'EPA評核項目', '等級', '評語', '評核老師']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.warning(f"表單中缺少以下必要欄位：{', '.join(missing_columns)}")
        # 為缺少的欄位添加空值
        for col in missing_columns:
            df[col] = None
    
    # 處理評核時間格式
    if '評核時間' in df.columns:
        try:
            # 嘗試轉換為日期時間格式
            df['評核時間'] = pd.to_datetime(df['評核時間'])
        except:
            # 如果轉換失敗，保持原樣
            pass
    
    # 處理 EPA 等級轉換
    if '等級' in df.columns:
        # 定義轉換對照表
        epa_level_mapping = {
            'Level I': 1,
            ' Level I': 1,
            'Level1': 1,
            'Level 1': 1,
            'Level 1&2': 1.5,
            'Level1&2': 1.5,
            'LevelI&2': 1.5,
            'Level&2': 1.5,
            'Level II': 2,
            ' Level II': 2,
            'Level2': 2,
            'Level 2': 2,
            'Level2&3': 2.5,
            'Level 2&3': 2.5,
            'Leve 2&3': 2.5,
            'Level 2a': 2,
            'Level2a': 2,
            'Level 2b': 2.5,
            'Level2b': 2.5,
            'Level III': 3,
            ' Level III': 3,
            'Level3': 3,
            'Level 3': 3,
            'Level 3a': 3,
            'Level3a': 3,
            'Level 3b': 3.3,
            'Level3b': 3.3,
            'Level3c': 3.6,
            'Level 3c': 3.6,
            'Level 3&4': 3.5,
            'Level3&4': 3.5,
            'Leve 3&4': 3.5,
            'Lvel 3&4': 3.5,
            'Level IV': 4,
            ' Level IV': 4, 
            'Level4': 4,
            'Level 4': 4,
            'Level4&5': 4.5,
            'Level 4&5': 4.5,
            'Level 5': 5,
            'Level V': 5,
            ' Level V': 5,
            'Level5': 5
        }
        
        # 轉換等級文字為數值
        df['等級數值'] = df['等級'].apply(lambda x: epa_level_mapping.get(str(x).strip(), x))
        df['等級數值'] = pd.to_numeric(df['等級數值'], errors='coerce')
    
    # 如果沒有梯次欄位，嘗試從評核時間生成梯次
    if '梯次' not in df.columns and '評核時間' in df.columns and pd.api.types.is_datetime64_any_dtype(df['評核時間']):
        # 使用年份和月份組合作為梯次
        df['梯次'] = df['評核時間'].dt.strftime('%Y-%m')
        st.info("未找到梯次欄位，已根據評核時間自動生成梯次 (年-月格式)")
    
    # 加入資料來源標記
    df['資料來源'] = 'Google表單EPA評核'
    
    # 加入匯入時間
    df['匯入時間'] = datetime.now()
    
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
                
                # 顯示資料預覽
                st.subheader("資料預覽")
                
                # 加入篩選器
                st.write("### 資料篩選")
                
                # 篩選梯次
                if '梯次' in df.columns:
                    all_batches = sorted(df['梯次'].unique().tolist())
                    selected_batches = st.multiselect("選擇梯次", all_batches, default=all_batches)
                else:
                    selected_batches = None
                
                # 篩選個人
                if '姓名' in df.columns:
                    all_students = sorted(df['姓名'].unique().tolist())
                    selected_students = st.multiselect("選擇學員", all_students, default=[])
                else:
                    selected_students = None
                
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
                
                # 直接分析篩選後的資料，不需要按鈕
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
                        
                        # 顯示資料預覽
                        st.subheader("資料預覽")
                        
                        # 加入篩選器
                        st.write("### 資料篩選")
                        
                        # 篩選梯次
                        if '梯次' in df.columns:
                            all_batches = sorted(df['梯次'].unique().tolist())
                            selected_batches = st.multiselect("選擇梯次", all_batches, default=all_batches, key="other_batches")
                        else:
                            selected_batches = None
                        
                        # 篩選個人
                        if '姓名' in df.columns:
                            all_students = sorted(df['姓名'].unique().tolist())
                            selected_students = st.multiselect("選擇學員", all_students, default=[], key="other_students")
                        else:
                            selected_students = None
                        
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
                        
                        # 直接分析篩選後的資料，不需要按鈕
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
        
    
    # 3. EPA 等級分析
    if '等級數值' in df.columns:
        
        
        # 使用雷達圖呈現 EPA 項目平均等級
        if 'EPA評核項目' in df.columns:
            st.write("### EPA 梯次平均雷達圖")
            
            # 創建兩欄布局
            col1, col2 = st.columns([1, 1])
            
            # 計算每個 EPA 項目的整體平均等級
            epa_item_avg = df.groupby('EPA評核項目')['等級數值'].mean()
            
            # 在左欄顯示雷達圖
            with col1:
                # 檢查是否有足夠的資料繪製雷達圖
                if len(epa_item_avg) >= 3:  # 雷達圖至少需要3個點
                    # 準備雷達圖資料
                    categories = epa_item_avg.index.tolist()
                    values = epa_item_avg.values.tolist()
                    
                    # 確保資料是閉合的（首尾相連）
                    categories.append(categories[0])
                    values.append(values[0])
                    
                    # 計算角度 - 確保與類別數量一致
                    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=True)
                    
                    # 設定中文字型
                    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
                    plt.rcParams['axes.unicode_minus'] = False
                    
                    # 創建雷達圖
                    fig = plt.figure(figsize=(8, 8))
                    ax = fig.add_subplot(111, polar=True)
                    
                    # 繪製整體平均雷達圖 - 使用黑色粗線
                    ax.plot(angles, values, 'o-', linewidth=3, color='black', label='整體平均')
                    ax.fill(angles, values, alpha=0.25, color='gray')
                    
                    # 如果有學員階層欄位，繪製不同階層的平均
                    if '學員階層' in df.columns:
                        # 獲取所有階層
                        all_levels = sorted(df['學員階層'].unique())
                        
                        # 定義不同階層的顏色
                        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan']
                        
                        # 為每個階層繪製雷達圖
                        for i, level in enumerate(all_levels):
                            # 篩選該階層的資料
                            level_data = df[df['學員階層'] == level]
                            
                            # 計算該階層每個 EPA 項目的平均等級
                            level_epa_avg = level_data.groupby('EPA評核項目')['等級數值'].mean()
                            
                            # 獲取與整體相同的 EPA 項目
                            level_values = []
                            for item in categories[:-1]:  # 不包括閉合點
                                if item in level_epa_avg:
                                    level_values.append(level_epa_avg[item])
                                else:
                                    level_values.append(0)
                            
                            # 閉合階層資料
                            level_values.append(level_values[0])
                            
                            # 選擇顏色
                            color = colors[i % len(colors)]
                            
                            # 繪製階層雷達圖
                            ax.plot(angles, level_values, 'o-', linewidth=2, color=color, label=f'{level}')
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
                    batch_epa_avg = df.groupby(['梯次', 'EPA評核項目'])['等級數值'].mean().unstack()
                    
                    # 檢查是否有資料
                    if not batch_epa_avg.empty:
                        # 顯示表格
                        st.dataframe(batch_epa_avg.style.background_gradient(cmap='YlGnBu', axis=None))
                        
                        # 繪製折線圖，顯示各 EPA 項目隨梯次的變化趨勢
                        st.write("##### EPA 項目隨梯次變化趨勢")
                        
                        # 創建折線圖
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # 為每個 EPA 項目繪製一條折線及其 95% 信賴區間
                        for item in batch_epa_avg.columns:
                            # 獲取該 EPA 項目在每個梯次的平均值
                            means = batch_epa_avg[item]
                            
                            # 計算每個梯次該 EPA 項目的標準差和樣本數
                            std_devs = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].std()
                            counts = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].count()
                            
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
                        if len(batch_epa_avg.columns) > 5:
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
        st.write("### 所有學員 EPA 項目雷達圖分析")
        
        # 獲取所有學員姓名
        all_students = sorted(df['姓名'].unique().tolist())
        
        # 計算整體平均
        overall_epa_avg = df.groupby('EPA評核項目')['等級數值'].mean()
        
        # 檢查是否有足夠的資料繪製雷達圖
        if len(overall_epa_avg) >= 3:  # 雷達圖至少需要3個點
            # 準備雷達圖資料
            overall_categories = overall_epa_avg.index.tolist()
            overall_values = overall_epa_avg.values.tolist()
            
            # 確保資料是閉合的（首尾相連）
            overall_categories.append(overall_categories[0])
            overall_values.append(overall_values[0])
            
            # 計算角度 - 確保與類別數量一致
            angles = np.linspace(0, 2*np.pi, len(overall_categories), endpoint=True)
            
            # 設定中文字型
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 為每個學員創建雷達圖和資料表格
            for student in all_students:
                st.write(f"#### {student}")
                
                # 創建兩欄布局
                col1, col2 = st.columns([1, 1])
                
                # 篩選該學員的資料
                student_data = df[df['姓名'] == student]
                
                # 計算該學員每個 EPA 項目的平均等級
                student_epa_avg = student_data.groupby('EPA評核項目')['等級數值'].mean()
                
                # 在左欄顯示雷達圖
                with col1:
                    # 檢查是否有足夠的資料繪製雷達圖
                    if len(student_epa_avg) >= 3:  # 雷達圖至少需要3個點
                        # 獲取與整體相同的 EPA 項目
                        student_values = []
                        for item in overall_categories[:-1]:  # 不包括閉合點
                            if item in student_epa_avg:
                                student_values.append(student_epa_avg[item])
                            else:
                                student_values.append(0)
                        
                        # 閉合學員資料
                        student_values.append(student_values[0])
                        
                        # 創建學員雷達圖
                        fig = plt.figure(figsize=(6, 6))
                        ax = fig.add_subplot(111, polar=True)
                        
                        # 繪製學員雷達圖 - 黑色粗線
                        ax.plot(angles, student_values, 'o-', linewidth=3, color='black', label=f'{student}')
                        ax.fill(angles, student_values, alpha=0.25, color='gray')
                        
                        # 繪製整體平均雷達圖進行比較
                        ax.plot(angles, overall_values, 'o-', linewidth=1, color='red', label='整體平均')
                        ax.fill(angles, overall_values, alpha=0.1, color='red')
                        
                        # 設定刻度和標籤
                        ax.set_thetagrids(np.degrees(angles[:-1]), overall_categories[:-1], fontsize=8)
                        ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                        ax.set_yticks([1, 2, 3, 4, 5])
                        ax.set_yticklabels(['1', '2', '3', '4', '5'])
                        ax.set_rlabel_position(0)
                        
                        # 添加標題和圖例
                        plt.title(f'{student} EPA 項目評核', size=12)
                        plt.legend(loc='upper right', fontsize='small')
                        
                        # 調整布局，確保標籤不被裁剪
                        plt.tight_layout()
                        
                        # 顯示學員雷達圖
                        st.pyplot(fig)
                    else:
                        st.warning(f"{student} 的 EPA 項目數量不足，無法繪製雷達圖（至少需要3個不同項目）")
                
                # 在右欄顯示表格資料（可展開）
                with col2:
                    # 準備顯示的資料表格
                    if '評語' in student_data.columns and 'EPA評核項目' in student_data.columns and '等級' in student_data.columns:
                        # 選擇要顯示的欄位
                        display_df = student_data[['EPA評核項目', '評語', '等級', '評核老師']]
                        
                        # 使用 expander 讓表格可展開
                        with st.expander("點擊展開詳細評核資料", expanded=False):
                            st.dataframe(display_df)
                    else:
                        st.warning("缺少必要欄位，無法顯示完整評核資料")
                
                # 新增：顯示學員在不同梯次各 EPA 項目的趨勢折線圖
                st.write("##### 各 EPA 項目隨時間變化趨勢")
                
                # 檢查是否有梯次欄位
                if '梯次' in student_data.columns:
                    # 按梯次和 EPA 項目分組計算平均等級
                    trend_data = student_data.groupby(['梯次', 'EPA評核項目'])['等級數值'].mean().unstack()
                    
                    # 檢查是否有足夠的資料繪製趨勢圖
                    if not trend_data.empty and len(trend_data) > 1:  # 至少需要兩個時間點
                        # 繪製趨勢折線圖
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # 為每個 EPA 項目繪製一條折線及其 95% 信賴區間
                        for item in trend_data.columns:
                            # 獲取該 EPA 項目在每個梯次的平均值
                            means = trend_data[item]
                            
                            # 計算每個梯次該 EPA 項目的標準差和樣本數
                            std_devs = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].std()
                            counts = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].count()
                            
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
                        ax.set_title(f'{student} 各 EPA 項目隨時間變化趨勢', fontsize=14)
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
                        st.info(f"{student} 在不同梯次的資料不足，無法繪製趨勢圖（至少需要兩個不同梯次的資料）")
                elif '評核時間' in student_data.columns:
                    # 如果沒有梯次欄位但有評核時間，可以按月份分組
                    student_data['月份'] = student_data['評核時間'].dt.strftime('%Y-%m')
                    
                    # 按月份和 EPA 項目分組計算平均等級
                    trend_data = student_data.groupby(['月份', 'EPA評核項目'])['等級數值'].mean().unstack()
                    
                    # 檢查是否有足夠的資料繪製趨勢圖
                    if not trend_data.empty and len(trend_data) > 1:  # 至少需要兩個時間點
                        # 繪製趨勢折線圖
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # 為每個 EPA 項目繪製一條折線及其 95% 信賴區間
                        for item in trend_data.columns:
                            # 獲取該 EPA 項目在每個梯次的平均值
                            means = trend_data[item]
                            
                            # 計算每個梯次該 EPA 項目的標準差和樣本數
                            std_devs = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].std()
                            counts = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].count()
                            
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
                        ax.set_xlabel('月份', fontsize=12)
                        ax.set_ylabel('EPA 等級', fontsize=12)
                        ax.set_title(f'{student} 各 EPA 項目隨時間變化趨勢', fontsize=14)
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
                        st.info(f"{student} 在不同時間的資料不足，無法繪製趨勢圖（至少需要兩個不同時間點的資料）")
                else:
                    st.warning("缺少梯次或評核時間欄位，無法繪製時間趨勢圖")
                
                # 添加分隔線
                st.markdown("---")

    # 5. 老師與同儕評分差異分析
    st.write("# 老師評分差異分析")

    # 檢查必要欄位是否存在
    required_cols = ['評核老師', '等級數值', 'EPA評核項目']
    if all(col in df.columns for col in required_cols):
        # 選擇要顯示的欄位並建立表格
        display_df = df[required_cols].copy()
        

    else:
        # 如果缺少必要欄位則顯示警告
        missing_cols = [col for col in required_cols if col not in df.columns]
        st.warning(f"缺少以下必要欄位，無法顯示評分明細：{', '.join(missing_cols)}")

    # 老師個別評分分析
    st.write("### 個別老師評分分析")
    
    # 檢查是否有評核老師欄位
    if '評核老師' in df.columns:
        # 取得所有老師列表
        teachers = df['評核老師'].unique().tolist()
        
        # 讓使用者選擇要分析的老師
        selected_teacher = st.selectbox(
            "選擇要分析的老師",
            teachers,
            key="teacher_select"
        )
        
        # 篩選選定老師的資料
        teacher_data = df[df['評核老師'] == selected_teacher]
        
        if not teacher_data.empty:
            st.write(f"#### {selected_teacher} 的評分分布")
            
            # 使用 matplotlib 和 seaborn 繪製箱型圖 - 將老師的評分與整體評分放在一起比較
            st.write("##### EPA 項目評分分布比較 (老師 vs 整體)")
            
            # 設定中文字型
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 創建圖形 - 使用更大的尺寸以容納更多資料
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # 創建一個新的DataFrame，添加來源標籤
            teacher_plot_data = teacher_data.copy()
            teacher_plot_data['來源'] = f'{selected_teacher}'
            
            all_plot_data = df.copy()
            all_plot_data['來源'] = '所有老師'
            
            # 合併資料
            plot_data = pd.concat([teacher_plot_data, all_plot_data])
            
            # 使用 seaborn 繪製箱型圖，按來源分組
            sns.boxplot(x='EPA評核項目', y='等級數值', hue='來源', data=plot_data, 
                       palette={'所有老師': 'lightgray', f'{selected_teacher}': 'steelblue'}, ax=ax)
            
            # 設定圖表屬性
            ax.set_title(f'{selected_teacher} vs 所有老師的 EPA 項目評分分布比較', fontsize=16)
            ax.set_xlabel('EPA評核項目', fontsize=12)
            ax.set_ylabel('評分等級', fontsize=12)
            ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
            
            # 旋轉 x 軸標籤以避免重疊
            plt.xticks(rotation=45, ha='right')
            
            # 添加網格線以便於閱讀
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
            
            # 調整圖例位置
            ax.legend(loc='upper right', fontsize='medium')
            
            # 調整布局
            plt.tight_layout()
            
            # 顯示圖表
            st.pyplot(fig)
            
            # 顯示統計資訊比較表格
            st.write("#### 評分統計資訊比較")
            
            # 計算老師的統計資訊
            teacher_stats = teacher_data.groupby('EPA評核項目')['等級數值'].agg([
                ('老師平均分數', 'mean'),
                ('老師中位數', 'median'),
                ('老師標準差', 'std'),
                ('老師評分次數', 'count')
            ]).round(2)
            
            # 計算整體的統計資訊
            all_stats = df.groupby('EPA評核項目')['等級數值'].agg([
                ('整體平均分數', 'mean'),
                ('整體中位數', 'median'),
                ('整體標準差', 'std'),
                ('整體評分次數', 'count')
            ]).round(2)
            
            # 合併統計資訊
            combined_stats = pd.concat([teacher_stats, all_stats], axis=1)
            
            # 計算差異
            if not combined_stats.empty:
                combined_stats['平均分數差異'] = combined_stats['老師平均分數'] - combined_stats['整體平均分數']
                combined_stats['中位數差異'] = combined_stats['老師中位數'] - combined_stats['整體中位數']
                
                # 新增：進行統計顯著性檢定
                st.write("#### 統計顯著性檢定")
                
                # 創建結果DataFrame
                significance_results = pd.DataFrame(index=teacher_stats.index, 
                                                  columns=['t檢定p值', 't檢定結果', 'Mann-Whitney U檢定p值', 'Mann-Whitney U檢定結果'])
                
                # 對每個EPA項目進行檢定
                for epa_item in teacher_stats.index:
                    # 獲取該EPA項目的老師評分和整體評分
                    teacher_scores = teacher_data[teacher_data['EPA評核項目'] == epa_item]['等級數值']
                    all_scores = df[df['EPA評核項目'] == epa_item]['等級數值']
                    
                    # 只有當樣本數足夠時才進行檢定
                    if len(teacher_scores) >= 5 and len(all_scores) >= 5:
                        # 進行t檢定（假設兩組數據有不同的方差）
                        try:
                            t_stat, p_value_t = stats.ttest_ind(teacher_scores, all_scores, equal_var=False)
                            significance_results.loc[epa_item, 't檢定p值'] = round(p_value_t, 4)
                            significance_results.loc[epa_item, 't檢定結果'] = "顯著差異" if p_value_t < 0.05 else "無顯著差異"
                        except:
                            significance_results.loc[epa_item, 't檢定p值'] = "計算錯誤"
                            significance_results.loc[epa_item, 't檢定結果'] = "無法判定"
                        
                        # 進行Mann-Whitney U檢定（非參數檢定，不假設正態分布）
                        try:
                            u_stat, p_value_u = stats.mannwhitneyu(teacher_scores, all_scores, alternative='two-sided')
                            significance_results.loc[epa_item, 'Mann-Whitney U檢定p值'] = round(p_value_u, 4)
                            significance_results.loc[epa_item, 'Mann-Whitney U檢定結果'] = "顯著差異" if p_value_u < 0.05 else "無顯著差異"
                        except:
                            significance_results.loc[epa_item, 'Mann-Whitney U檢定p值'] = "計算錯誤"
                            significance_results.loc[epa_item, 'Mann-Whitney U檢定結果'] = "無法判定"
                    else:
                        significance_results.loc[epa_item, 't檢定p值'] = "樣本不足"
                        significance_results.loc[epa_item, 't檢定結果'] = "無法檢定"
                        significance_results.loc[epa_item, 'Mann-Whitney U檢定p值'] = "樣本不足"
                        significance_results.loc[epa_item, 'Mann-Whitney U檢定結果'] = "無法檢定"
                
                # 顯示檢定結果
                st.dataframe(significance_results)
                
                # 解釋檢定結果
                st.write("##### 統計檢定說明")
                st.write("""
                - **t檢定**：比較兩組數據的平均值是否有顯著差異，假設數據近似正態分布。
                - **Mann-Whitney U檢定**：非參數檢定，比較兩組數據的分布是否有顯著差異，不要求數據正態分布。
                - **p值 < 0.05**：表示有95%的信心認為兩組數據存在顯著差異。
                - **樣本不足**：表示老師的評分樣本數少於5，不足以進行可靠的統計檢定。
                """)
                
                # 計算效應量 (Cohen's d)
                st.write("#### 效應量分析 (Cohen's d)")
                
                effect_size_results = pd.DataFrame(index=teacher_stats.index, 
                                                 columns=['效應量(Cohen\'s d)', '效應大小解釋'])
                
                for epa_item in teacher_stats.index:
                    teacher_scores = teacher_data[teacher_data['EPA評核項目'] == epa_item]['等級數值']
                    all_scores = df[df['EPA評核項目'] == epa_item]['等級數值']
                    
                    if len(teacher_scores) >= 5 and len(all_scores) >= 5:
                        try:
                            # 計算Cohen's d
                            teacher_mean = teacher_scores.mean()
                            all_mean = all_scores.mean()
                            teacher_std = teacher_scores.std()
                            all_std = all_scores.std()
                            
                            # 計算合併標準差
                            n1 = len(teacher_scores)
                            n2 = len(all_scores)
                            pooled_std = np.sqrt(((n1-1)*teacher_std**2 + (n2-1)*all_std**2) / (n1+n2-2))
                            
                            # 計算Cohen's d
                            d = abs(teacher_mean - all_mean) / pooled_std
                            effect_size_results.loc[epa_item, '效應量(Cohen\'s d)'] = round(d, 2)
                            
                            # 解釋效應大小
                            if d < 0.2:
                                effect_size_results.loc[epa_item, '效應大小解釋'] = "微小差異"
                            elif d < 0.5:
                                effect_size_results.loc[epa_item, '效應大小解釋'] = "小差異"
                            elif d < 0.8:
                                effect_size_results.loc[epa_item, '效應大小解釋'] = "中等差異"
                            else:
                                effect_size_results.loc[epa_item, '效應大小解釋'] = "大差異"
                        except:
                            effect_size_results.loc[epa_item, '效應量(Cohen\'s d)'] = "計算錯誤"
                            effect_size_results.loc[epa_item, '效應大小解釋'] = "無法判定"
                    else:
                        effect_size_results.loc[epa_item, '效應量(Cohen\'s d)'] = "樣本不足"
                        effect_size_results.loc[epa_item, '效應大小解釋'] = "無法計算"
                
                # 顯示效應量結果
                st.dataframe(effect_size_results)
                
                # 解釋效應量
                st.write("##### 效應量說明")
                st.write("""
                - **Cohen's d**：測量兩組數據平均值差異的標準化大小。
                - **解釋標準**：
                  - d < 0.2：微小差異
                  - 0.2 ≤ d < 0.5：小差異
                  - 0.5 ≤ d < 0.8：中等差異
                  - d ≥ 0.8：大差異
                """)
                
                # 顯示合併的統計資訊表格
                st.write("#### 詳細統計資訊比較")
                st.dataframe(combined_stats.style.background_gradient(cmap='RdYlGn', subset=['平均分數差異', '中位數差異']))
                
               
            
            
            # 新增：顯示所有老師的評分比較
            st.write("### 所有老師評分比較")
            
            # 檢查是否有足夠的資料進行比較
            if len(teachers) > 1:
                # 設定中文字型
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
                plt.rcParams['axes.unicode_minus'] = False
                
                # 創建圖形 - 使用更大的尺寸以容納更多資料
                fig, ax = plt.subplots(figsize=(14, 8))
                
                
                
                # 顯示所有老師的評分統計資訊
                all_teachers_stats = df.groupby(['評核老師', 'EPA評核項目'])['等級數值'].agg([
                    ('平均分數', 'mean'),
                    ('中位數', 'median'),
                    ('標準差', 'std'),
                    ('評分次數', 'count')
                ]).round(2)
                
                # 使用 unstack 將老師作為列，EPA 項目作為欄
                avg_scores_by_teacher = df.groupby(['評核老師', 'EPA評核項目'])['等級數值'].mean().unstack()
                
                # 顯示平均分數表格
                st.write("##### 各老師對各 EPA 項目的平均評分")
                st.dataframe(avg_scores_by_teacher.style.background_gradient(cmap='YlGnBu', axis=None))
                
                # 顯示評分次數表格
                count_by_teacher = df.groupby(['評核老師', 'EPA評核項目'])['等級數值'].count().unstack()
                st.write("##### 各老師對各 EPA 項目的評分次數")
                st.dataframe(count_by_teacher)
                

            else:
                st.info("只有一位老師的評分資料，無法進行比較")
                
            
            # 檢查是否有足夠的資料進行分析
            if 'EPA評核項目' in df.columns and '等級數值' in df.columns:
                # 計算每個EPA項目的詳細統計資料
                epa_stats = df.groupby('EPA評核項目')['等級數值'].agg([
                    ('平均數', 'mean'),
                    ('中位數', 'median'),
                    ('標準差', 'std'),
                    ('第一四分位數', lambda x: x.quantile(0.25)),
                    ('第三四分位數', lambda x: x.quantile(0.75)),
                    ('最小值', 'min'),
                    ('最大值', 'max'),
                    ('評分次數', 'count')
                ]).round(2)
                
                # 顯示統計資料表格
                st.write("#### 各EPA項目的統計資料")
                st.dataframe(epa_stats.style.background_gradient(cmap='YlGnBu', subset=['平均數', '中位數']))
                
                # 繪製箱型圖，顯示所有EPA項目的分布情況
                st.write("#### 各EPA項目的分數分布箱型圖")
                
                # 設定中文字型
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
                plt.rcParams['axes.unicode_minus'] = False
                
                # 創建圖形
                fig, ax = plt.subplots(figsize=(14, 8))
                
                # 使用seaborn繪製箱型圖
                sns.boxplot(x='EPA評核項目', y='等級數值', data=df, ax=ax)
                
                # 添加數據點以顯示分布
                sns.stripplot(x='EPA評核項目', y='等級數值', data=df, 
                             size=4, color=".3", linewidth=0, alpha=0.3, ax=ax)
                
                # 設定圖表屬性
                ax.set_title('各EPA項目的評分分布', fontsize=16)
                ax.set_xlabel('EPA評核項目', fontsize=12)
                ax.set_ylabel('評分等級', fontsize=12)
                ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                
                # 旋轉 x 軸標籤以避免重疊
                plt.xticks(rotation=45, ha='right')
                
                # 添加網格線以便於閱讀
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                
                # 調整布局
                plt.tight_layout()
                
                # 顯示圖表
                st.pyplot(fig)
                
                # 繪製小提琴圖，更好地顯示分布形狀
                st.write("#### 各EPA項目的分數分布小提琴圖")
                
                # 創建圖形
                fig, ax = plt.subplots(figsize=(14, 8))
                
                # 使用seaborn繪製小提琴圖
                sns.violinplot(x='EPA評核項目', y='等級數值', data=df, inner='quartile', ax=ax)
                
                # 設定圖表屬性
                ax.set_title('各EPA項目的評分分布小提琴圖', fontsize=16)
                ax.set_xlabel('EPA評核項目', fontsize=12)
                ax.set_ylabel('評分等級', fontsize=12)
                ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                
                # 旋轉 x 軸標籤以避免重疊
                plt.xticks(rotation=45, ha='right')
                
                # 添加網格線以便於閱讀
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                
                # 調整布局
                plt.tight_layout()
                
                # 顯示圖表
                st.pyplot(fig)
                
                # 顯示每個EPA項目的分數分布直方圖
                st.write("#### 各EPA項目的分數分布直方圖")
                
                # 獲取所有EPA項目
                epa_items = sorted(df['EPA評核項目'].unique())
                
                # 計算需要的行數（每行最多3個圖表）
                n_items = len(epa_items)
                n_cols = 3
                n_rows = (n_items + n_cols - 1) // n_cols
                
                # 創建子圖
                fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
                axes = axes.flatten() if n_rows > 1 or n_cols > 1 else [axes]
                
                # 為每個EPA項目繪製直方圖
                for i, item in enumerate(epa_items):
                    if i < len(axes):
                        # 篩選該EPA項目的資料
                        item_data = df[df['EPA評核項目'] == item]['等級數值']
                        
                        # 繪製直方圖
                        sns.histplot(item_data, bins=10, kde=True, ax=axes[i])
                        
                        # 添加平均值和中位數線
                        mean_val = item_data.mean()
                        median_val = item_data.median()
                        axes[i].axvline(mean_val, color='red', linestyle='--', label=f'平均值: {mean_val:.2f}')
                        axes[i].axvline(median_val, color='green', linestyle='-.', label=f'中位數: {median_val:.2f}')
                        
                        # 設定圖表屬性
                        axes[i].set_title(f'{item}', fontsize=10)
                        axes[i].set_xlabel('評分等級')
                        axes[i].set_ylabel('頻率')
                        axes[i].set_xlim(0, 5)
                        axes[i].legend(fontsize='small')
                
                # 隱藏多餘的子圖
                for j in range(i + 1, len(axes)):
                    axes[j].set_visible(False)
                
                # 調整布局
                plt.tight_layout()
                
                # 顯示圖表
                st.pyplot(fig)
            else:
                st.warning("缺少必要欄位，無法進行EPA項目統計分析")
