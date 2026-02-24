import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def wes_pt_page():
    st.header("病患資料整理")
    
    # 定義要作為篩選器的欄位
    filter_columns = [
        "MH_No", "Name", "Chart_number", 
        "來源", "其他", "資訊", "確診"
    ]
    
    # 設定 Google Sheets API 認證
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    # 從 Streamlit Secrets 獲取憑證資訊
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
    
    try:
        # 建立認證
        creds = Credentials.from_service_account_info(credentials, scopes=scope)
        client = gspread.authorize(creds)
        
        # 指定要讀取的 Google Sheets
        sheet_urls = {
            "病患基本資料": "https://docs.google.com/spreadsheets/d/1Gh3B6GKIPulN6gw1LksFlTdthxciqOvuGrl-7Vlxn00/edit?gid=0#gid=0",
            "基因檢測結果": "https://docs.google.com/spreadsheets/d/16yxglLjSkd8IOdiGvvaYxMDbA70eaGaKTv2YM9H4_HY/edit?gid=57216002#gid=57216002"
       }
        
        # 使用 @st.cache_data 來快取資料，修改參數名稱
        @st.cache_data(ttl=600)  # 快取10分鐘
        def load_sheet_data(_client, url):
            sheet = _client.open_by_url(url)
            worksheet = sheet.get_worksheet(0)  # 只讀取第一個工作表
            return worksheet.get_all_values()
        
        @st.cache_data(ttl=600)  # 快取10分鐘
        def load_genetic_data(_client, url):
            sheet = _client.open_by_url(url)
            all_data = []
            for worksheet in sheet.worksheets():
                values = worksheet.get_all_values()
                if len(values) > 0:
                    all_data.append(values)
            return all_data
        
        # 讀取第一個表格（病患基本資料）
        base_values = load_sheet_data(client, sheet_urls["病患基本資料"])
        base_df = None
        
        if len(base_values) > 0:
            headers = base_values[0]
            base_df = pd.DataFrame(base_values[1:], columns=headers)
            
            # 創建篩選器
            st.subheader("資料篩選")
            
            # 處理 Tentative_diagnosis 的複選篩選器
            if 'Tentative_diagnosis' in base_df.columns:
                st.write("診斷篩選")
                # 處理包含逗號的診斷，並轉換為小寫
                all_diagnoses = []
                for diagnoses in base_df['Tentative_diagnosis'].dropna():
                    # 分割逗號分隔的診斷，並去除空白，轉換為小寫
                    split_diagnoses = [d.strip().lower() for d in diagnoses.split(',')]
                    all_diagnoses.extend(split_diagnoses)
                
                # 去除重複並排序
                unique_diagnoses = sorted(set(all_diagnoses))
                
                selected_diagnoses = st.multiselect(
                    "選擇 Tentative_diagnosis",
                    options=unique_diagnoses,
                    default=None
                )
            
            # 創建其他篩選器
            st.write("其他篩選")
            cols = st.columns(4)
            filters = {}
            
            for i, col in enumerate(filter_columns):
                if col in base_df.columns:
                    with cols[i % 4]:
                        unique_values = ["全部"] + sorted(base_df[col].dropna().unique().tolist())
                        filters[col] = st.selectbox(
                            f"選擇{col}",
                            options=unique_values
                        )
        
        # 讀取第二個表格（基因檢測結果）
        genetic_values = load_genetic_data(client, sheet_urls["基因檢測結果"])
        genetic_data = []
        
        for values in genetic_values:
            if len(values) > 0:
                headers = values[0]
                df = pd.DataFrame(values[1:], columns=headers)
                
                if 'Name' in df.columns:
                    selected_cols = ['Name']
                    if 'Genetic_analysis' in df.columns:
                        selected_cols.append('Genetic_analysis')
                    
                    temp_df = df[selected_cols].copy()
                    genetic_data.append(temp_df)
        
        # 合併基因檢測資料
        if genetic_data and base_df is not None:
            combined_genetic_df = pd.concat(genetic_data, ignore_index=True)
            
            # 將基因資料合併到基本資料中，使用 Name 作為合併依據
            base_df = base_df.merge(
                combined_genetic_df,
                on='Name',
                how='left'
            )
            
            # 修改 Tentative_diagnosis 的篩選邏輯
            filtered_df = base_df.copy()
            
            if 'Tentative_diagnosis' in base_df.columns and selected_diagnoses:
                # 創建篩選條件，不分大小寫
                mask = filtered_df['Tentative_diagnosis'].apply(
                    lambda x: any(diagnosis.lower() in str(x).lower() for diagnosis in selected_diagnoses)
                    if pd.notna(x) else False
                )
                filtered_df = filtered_df[mask]
            
            # 應用其他篩選條件
            for col, value in filters.items():
                if value != "全部" and col in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[col] == value]
            
            # 顯示合併後的資料
            st.subheader("合併後的病患資料")
            st.write(f"資料筆數：{len(filtered_df)} 筆")
            st.write(f"欄位數量：{len(filtered_df.columns)} 個")
            st.dataframe(filtered_df, use_container_width=True)
            
            # 在側邊欄添加數值欄位篩選
            st.sidebar.markdown("### 數值欄位篩選")
            
            # 找出所有數值型欄位
            numeric_columns = base_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
            if numeric_columns:
                # 選擇要篩選的數值欄位
                selected_numeric_column = st.sidebar.selectbox(
                    "選擇要篩選的數值欄位",
                    options=['不篩選'] + numeric_columns
                )
                
                if selected_numeric_column != '不篩選':
                    # 選擇篩選條件
                    filter_condition = st.sidebar.selectbox(
                        "選擇篩選條件",
                        options=['大於', '小於', '等於', '大於等於', '小於等於']
                    )
                    
                    # 輸入篩選值
                    filter_value = st.sidebar.number_input(
                        "輸入篩選值",
                        value=float(base_df[selected_numeric_column].mean()),
                        step=0.1
                    )
                    
                    # 根據選擇的條件進行篩選
                    if filter_condition == '大於':
                        filtered_df = filtered_df[filtered_df[selected_numeric_column] > filter_value]
                    elif filter_condition == '小於':
                        filtered_df = filtered_df[filtered_df[selected_numeric_column] < filter_value]
                    elif filter_condition == '等於':
                        filtered_df = filtered_df[filtered_df[selected_numeric_column] == filter_value]
                    elif filter_condition == '大於等於':
                        filtered_df = filtered_df[filtered_df[selected_numeric_column] >= filter_value]
                    elif filter_condition == '小於等於':
                        filtered_df = filtered_df[filtered_df[selected_numeric_column] <= filter_value]
                    
                    st.sidebar.write(f"篩選後剩餘資料筆數: {len(filtered_df)}")
            else:
                st.sidebar.write("沒有可用的數值欄位進行篩選")
            
    except Exception as e:
        st.error(f"發生錯誤：{str(e)}")

if __name__ == "__main__":
    wes_pt_page() 