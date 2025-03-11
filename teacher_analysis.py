import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import re
from google.oauth2.service_account import Credentials
import gspread
import json
from scipy import stats

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
    """處理 EPA 表單資料的函數"""
    # 這個函數在您的代碼中似乎缺少，但被引用了
    # 這裡添加一個簡單的實現
    return df

def show_teacher_analysis_section(data=None, spreadsheet_url=None, key_prefix=""):
    """顯示老師評分分析的函數"""
    # 如果沒有提供 key_prefix，則生成一個唯一的前綴
    if not key_prefix:
        key_prefix = f"teacher_analysis_{id(data)}_{id(spreadsheet_url)}_"
    
    st.header("老師評分分析")
    
    # 檢查資料是否為空
    if data is None or data.empty:
        # 如果沒有提供資料，允許用戶輸入 Google 試算表連結
        st.warning("沒有提供資料，請輸入 Google 試算表連結")
        
        input_spreadsheet_url = st.text_input("輸入 Google 試算表連結", value=spreadsheet_url or DEFAULT_SPREADSHEET_URL, key=f"{key_prefix}spreadsheet_url")
        
        if input_spreadsheet_url:
            # 連接到 Google 試算表
            df, sheet_titles = fetch_google_form_data(input_spreadsheet_url)
            
            if sheet_titles:
                selected_sheet = st.selectbox("選擇工作表", options=sheet_titles, key=f"{key_prefix}sheet_select")
                
                # 直接載入選定的工作表資料
                with st.spinner("正在載入資料..."):
                    data, _ = fetch_google_form_data(input_spreadsheet_url, selected_sheet)
                    
                if data is None:
                    st.error("無法載入資料，請檢查試算表連結和權限設定")
                    return
                else:
                    st.success(f"成功載入 {len(data)} 筆資料")
                    # 更新 spreadsheet_url 為實際使用的 URL
                    spreadsheet_url = input_spreadsheet_url
            else:
                st.error("無法獲取工作表列表，請檢查試算表連結和權限設定")
                return
    
    # 再次檢查資料是否為空（可能是從試算表載入的）
    if data is None or data.empty:
        st.warning("沒有可用的資料進行分析")
        return
    
    # 顯示資料來源連結
    if spreadsheet_url:
        st.markdown(f"**資料來源**: [Google 試算表]({spreadsheet_url})")
    
    # 顯示資料基本資訊
    with st.expander("資料概覽"):
        st.write(f"資料列數: {len(data)}")
        st.write(f"資料欄位: {', '.join(data.columns)}")
        st.dataframe(data.head())
    
    # 處理欄位對應和資料轉換
    # 1. 檢查是否有需要的原始欄位
    required_original_cols = ['電子郵件地址', '評核等級', 'EPA評核項目']
    if not all(col in data.columns for col in required_original_cols):
        missing_cols = [col for col in required_original_cols if col not in data.columns]
        st.error(f"缺少以下必要原始欄位，無法進行分析：{', '.join(missing_cols)}")
        return
    
    # 2. 創建一個資料副本進行轉換
    processed_data = data.copy()
    
    # 3. 將 "電子郵件地址" 欄位重命名為 "評核老師"
    processed_data['評核老師'] = processed_data['電子郵件地址']
    
    # 4. 將 "評核等級" 欄位中的 Level I~V 轉換為數值
    def convert_level_to_numeric(level_str):
        if pd.isna(level_str):
            return np.nan
        
        # 移除可能的空格並轉換為大寫以統一格式
        level_str = str(level_str).strip().upper()
        
        # 定義等級對應的數值
        level_mapping = {
            'LEVEL I': 1,
            'LEVEL II': 2,
            'LEVEL III': 3,
            'LEVEL IV': 4,
            'LEVEL V': 5,
            'I': 1,
            'II': 2,
            'III': 3,
            'IV': 4,
            'V': 5,
            '1': 1,
            '2': 2,
            '3': 3,
            '4': 4,
            '5': 5
        }
        
        # 嘗試直接匹配
        if level_str in level_mapping:
            return level_mapping[level_str]
        
        # 嘗試匹配包含 "LEVEL" 的字串
        for key, value in level_mapping.items():
            if key in level_str:
                return value
        
        # 如果無法匹配，返回 NaN
        return np.nan
    
    # 應用轉換函數
    processed_data['等級數值'] = processed_data['評核等級'].apply(convert_level_to_numeric)
    
    # 檢查轉換後的資料
    with st.expander("轉換後的資料預覽"):
        st.write("原始評核等級與轉換後的等級數值對照")
        preview_df = processed_data[['評核等級', '等級數值']].drop_duplicates().sort_values('等級數值')
        st.dataframe(preview_df)
        
        st.write("轉換後的資料前幾行")
        st.dataframe(processed_data[['評核老師', '等級數值', 'EPA評核項目']].head())
    
    # 5. 老師與同儕評分差異分析
    st.write("# 老師評分差異分析")

    # 檢查必要欄位是否存在
    required_cols = ['評核老師', '等級數值', 'EPA評核項目']
    if all(col in processed_data.columns for col in required_cols):
        # 選擇要顯示的欄位並建立表格
        display_df = processed_data[required_cols].copy()
        
        # 檢查轉換後的數值是否有效
        invalid_count = display_df['等級數值'].isna().sum()
        if invalid_count > 0:
            st.warning(f"有 {invalid_count} 筆資料的評核等級無法轉換為數值，這些資料將被排除在分析之外。")
            # 移除無效資料
            display_df = display_df.dropna(subset=['等級數值'])
            
        # 確保等級數值是數值型別
        display_df['等級數值'] = pd.to_numeric(display_df['等級數值'])
        
        # 使用處理後的資料進行後續分析
        data = display_df
    else:
        # 如果缺少必要欄位則顯示警告
        missing_cols = [col for col in required_cols if col not in processed_data.columns]
        st.warning(f"轉換後仍缺少以下必要欄位，無法顯示評分明細：{', '.join(missing_cols)}")
        return
    
    # 老師個別評分分析
    st.write("### 個別老師評分分析")
    
    # 檢查是否有評核老師欄位
    if '評核老師' in data.columns:
        # 取得所有老師列表
        teachers = data['評核老師'].unique().tolist()
        
        # 讓使用者選擇要分析的老師
        selected_teacher = st.selectbox(
            "選擇要分析的老師",
            teachers,
            key=f"{key_prefix}teacher_select"
        )
        
        # 篩選選定老師的資料
        teacher_data = data[data['評核老師'] == selected_teacher]
        
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
            
            all_plot_data = data.copy()
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
            all_stats = data.groupby('EPA評核項目')['等級數值'].agg([
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
                    all_scores = data[data['EPA評核項目'] == epa_item]['等級數值']
                    
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
                    all_scores = data[data['EPA評核項目'] == epa_item]['等級數值']
                    
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
                all_teachers_stats = data.groupby(['評核老師', 'EPA評核項目'])['等級數值'].agg([
                    ('平均分數', 'mean'),
                    ('中位數', 'median'),
                    ('標準差', 'std'),
                    ('評分次數', 'count')
                ]).round(2)
                
                # 使用 unstack 將老師作為列，EPA 項目作為欄
                avg_scores_by_teacher = data.groupby(['評核老師', 'EPA評核項目'])['等級數值'].mean().unstack()
                
                # 顯示平均分數表格
                st.write("##### 各老師對各 EPA 項目的平均評分")
                st.dataframe(avg_scores_by_teacher.style.background_gradient(cmap='YlGnBu', axis=None))
                
                # 顯示評分次數表格
                count_by_teacher = data.groupby(['評核老師', 'EPA評核項目'])['等級數值'].count().unstack()
                st.write("##### 各老師對各 EPA 項目的評分次數")
                st.dataframe(count_by_teacher)
                

            else:
                st.info("只有一位老師的評分資料，無法進行比較")
                
            
            # 檢查是否有足夠的資料進行分析
            if 'EPA評核項目' in data.columns and '等級數值' in data.columns:
                # 計算每個EPA項目的詳細統計資料
                epa_stats = data.groupby('EPA評核項目')['等級數值'].agg([
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
                sns.boxplot(x='EPA評核項目', y='等級數值', data=data, ax=ax)
                
                # 添加數據點以顯示分布
                sns.stripplot(x='EPA評核項目', y='等級數值', data=data, 
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
                sns.violinplot(x='EPA評核項目', y='等級數值', data=data, inner='quartile', ax=ax)
                
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
                epa_items = sorted(data['EPA評核項目'].unique())
                
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
                        item_data = data[data['EPA評核項目'] == item]['等級數值']
                        
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
                
