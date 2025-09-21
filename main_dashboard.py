import streamlit as st
import httpx
import sqlite3
from datetime import datetime

# 設定頁面配置為寬屏模式
st.set_page_config(
    layout="wide",  # 使用寬屏模式
    page_title="學生評核系統",
    initial_sidebar_state="expanded"  # 預設展開側邊欄
)

import pandas as pd
import os
import re
import sys  # 匯入 sys
from io import BytesIO
from analysis_pgy_students import show_analysis_section
from analysis_residents import show_resident_analysis_section
from analysis_anesthesia_residents import show_ANE_R_EPA_peer_analysis_section
from analysis_teachers import show_teacher_analysis_section, fetch_google_form_data
from analysis_ugy_peers import show_UGY_peer_analysis_section
from analysis_ugy_overview import show_ugy_student_overview
from analysis_ugy_individual import show_ugy_student_analysis
from modules.epa_constants import EPA_LEVEL_MAPPING
from modules.auth import show_login_page, show_user_management, check_permission, USER_ROLES, show_registration_page, filter_data_by_permission, get_user_department
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from openai import OpenAI
from dotenv import load_dotenv
import traceback # 匯入 traceback
from supabase import create_client

# 載入環境變數
load_dotenv()

def get_openai_client():
    """獲取 OpenAI 客戶端實例並提供更詳細的錯誤訊息，使用自訂 httpx 客戶端"""
    try:
        # 重新載入 .env 檔案以確保取得最新設定
        load_dotenv(override=True)
        
        # 讀取 API 金鑰
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            st.error("❌ 錯誤：未在 .env 檔案中找到 OPENAI_API_KEY。")
            st.error("""
            請在 .env 檔案中設定正確的 OpenAI API 金鑰：
            OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            
            OpenAI API 金鑰應該是以 sk-proj- 或 sk- 開頭的一串英文字母和數字。
            請確保：
            1. 金鑰完整複製（通常約 40-50 個字元）
            2. 沒有換行符號
            3. 沒有多餘的引號或空格
            4. 整個金鑰都在同一行
            """)
            return None
            
        # 清理和驗證 API 金鑰
        api_key = api_key.strip().strip('"').strip("'")
        
        # 檢查金鑰格式
        if not (api_key.startswith("sk-proj-") or api_key.startswith("sk-")):
            st.error("❌ API 金鑰格式不正確：金鑰必須以 'sk-proj-' 或 'sk-' 開頭")
            return None
            
        # 建立 HTTP 客戶端
        http_client = httpx.Client(
            trust_env=False,  # 不使用系統代理設定
            timeout=30.0      # 設定超時時間
        )
        
        # 初始化 OpenAI 客戶端
        client = OpenAI(
            api_key=api_key,
            http_client=http_client
        )
        st.success("✅ OpenAI 客戶端初始化成功")
        
        return client
        
    except Exception as e:
        st.error(f"❌ 初始化過程中發生錯誤：{str(e)}")
        st.error(f"詳細追蹤：\n{traceback.format_exc()}")
        return None

# 初始化 session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def merge_excel_files(uploaded_files):
    """
    合併上傳的多個 Excel 檔案。

    Args:
        uploaded_files (list): Streamlit file_uploader 上傳的檔案列表。

    Returns:
        pandas.DataFrame or None: 合併後的 DataFrame，如果失敗則返回 None。
    """
    try:
        if not uploaded_files:
            st.warning("請上傳Excel檔案！")
            return None

        all_data = []
        all_columns = set() # 記錄所有檔案中出現過的欄位
        epa_related_columns = set() # 記錄所有 EPA 相關欄位 (教師評核, 學員自評, EPA)

        # 第一遍：讀取檔案，預處理，並收集所有欄位名稱
        for uploaded_file in uploaded_files:
            # 讀取 Excel 檔案
            try:
                df = pd.read_excel(uploaded_file)
            except Exception as read_error:
                st.error(f"讀取檔案 {uploaded_file.name} 時發生錯誤: {read_error}")
                continue # 跳過這個檔案

            # 處理檔案名稱，移除括號內的版本號
            clean_filename = re.sub(r'\s*\([0-9]+\)\.xls$', '.xls', uploaded_file.name)
            df['檔案名稱'] = clean_filename # 先加入檔案名稱

            # 記錄原始欄位
            all_columns.update(df.columns)

            # 處理訓練階段期間
            if '訓練階段期間' in df.columns:
                try:
                    # 將期間字串分割成開始和結束日期
                    date_extracted = df['訓練階段期間'].str.extract(r'(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})')
                    df[['開始日期', '結束日期']] = date_extracted

                    # 轉換為日期格式
                    df['開始日期'] = pd.to_datetime(df['開始日期'], errors='coerce')
                    df['結束日期'] = pd.to_datetime(df['結束日期'], errors='coerce')

                    # 計算訓練天數 (僅在日期有效時計算)
                    valid_dates = df['開始日期'].notna() & df['結束日期'].notna()
                    df.loc[valid_dates, '訓練天數'] = (df.loc[valid_dates, '結束日期'] - df.loc[valid_dates, '開始日期']).dt.days + 1
                    # 記錄新增的欄位
                    all_columns.update(['開始日期', '結束日期', '訓練天數'])
                except Exception as date_error:
                    st.warning(f"處理檔案 {uploaded_file.name} 的 '訓練階段期間' 時發生錯誤: {date_error}")
                    # 即使出錯，也確保欄位存在，避免後續合併問題
                    if '開始日期' not in df.columns: df['開始日期'] = pd.NaT
                    if '結束日期' not in df.columns: df['結束日期'] = pd.NaT
                    if '訓練天數' not in df.columns: df['訓練天數'] = pd.NA
                    all_columns.update(['開始日期', '結束日期', '訓練天數'])

            # 預處理欄位值 和 識別 EPA 相關欄位
            cols_to_process = df.columns.tolist()
            for col in cols_to_process:
                # 移除特定文字 (先轉換成字串避免錯誤)
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace("本表單與畢業成績無關，請依學生表現落實評量;", "", regex=False)

                is_epa_col = False
                if '教師評核' in col or '學員自評' in col or 'EPA' in col:
                    is_epa_col = True
                    original_col_name = f"{col} [原始]"
                     # 檢查原始欄位是否已存在 (避免重複添加)
                    if original_col_name not in df.columns:
                         df[original_col_name] = df[col].copy()
                         all_columns.add(original_col_name) # 記錄原始欄位名稱
                    epa_related_columns.add(col) # 記錄 EPA 欄位名稱
                    epa_related_columns.add(original_col_name) # 也記錄原始欄位

                    # 應用 EPA 等級映射 (轉換前確保是字串)
                    df[col] = df[col].apply(lambda x: EPA_LEVEL_MAPPING.get(str(x).strip(), x))
                    # 轉換為數值，無法轉換的變為 NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            all_data.append(df)

        if not all_data:
            st.warning("沒有成功讀取的檔案可供合併。")
            return None

        # 第二遍：確保所有 DataFrame 都有所有欄位，特別是 EPA 相關欄位
        processed_data = []
        for df in all_data:
            # 找出當前 df 缺少的欄位
            missing_cols = all_columns - set(df.columns)
            for col in missing_cols:
                df[col] = pd.NA # 使用 pandas 的 NA 標記缺失值，更通用

             # 特別檢查 EPA 相關欄位，如果缺少則填 NaN (因為它們預期是數值)
            # 注意：上一步的 pd.NA 已經處理了，這裡再確認一次以防萬一
            # for epa_col in epa_related_columns:
            #     if epa_col not in df.columns:
            #         # 如果是轉換後的數值欄位，填 NaN
            #         if not epa_col.endswith(" [原始]"):
            #             df[epa_col] = pd.NA # pd.to_numeric 會處理 pd.NA
            #         else: # 如果是原始欄位，也填 NA
            #             df[epa_col] = pd.NA
            processed_data.append(df)


        # 合併所有DataFrame，sort=False 保持欄位順序，不存在的欄位會自動填充 NaN
        try:
            merged_df = pd.concat(processed_data, ignore_index=True, sort=False)
        except Exception as concat_error:
            st.error(f"合併 DataFrame 時發生錯誤: {concat_error}")
            # 嘗試找出哪個 DataFrame 導致問題
            for i, df_check in enumerate(processed_data):
                 st.write(f"DataFrame {i} (來源: {df_check['檔案名稱'].iloc[0] if not df_check.empty else '未知'}) 欄位: {df_check.columns.tolist()}")
            return None


        # 重新排序欄位，確保 '檔案名稱' 在最前面
        if '檔案名稱' in merged_df.columns:
            cols = merged_df.columns.tolist()
            cols.remove('檔案名稱')
            merged_df = merged_df[['檔案名稱'] + cols]
        else:
             st.warning("合併結果中缺少 '檔案名稱' 欄位。")


        # --- 下載按鈕和儲存到 session state ---
        # 將合併後的資料轉換為 CSV
        try:
            csv = merged_df.to_csv(index=False).encode('utf-8') # 指定 utf-8 編碼
        except Exception as csv_error:
            st.error(f"轉換為 CSV 時發生錯誤: {csv_error}")
            csv = None

        # 將合併後的資料轉換為 Excel
        excel_buffer = BytesIO()
        try:
            merged_df.to_excel(excel_buffer, index=False, engine='openpyxl') # 明確指定引擎
            excel_data = excel_buffer.getvalue()
        except Exception as excel_error:
            st.error(f"轉換為 Excel 時發生錯誤: {excel_error}")
            excel_data = None

        # 建立兩個並排的下載按鈕 (只有在成功轉換時才顯示)
        col1, col2 = st.columns(2)
        with col1:
            if csv:
                st.download_button(
                    label="下載 CSV 檔案",
                    data=csv,
                    file_name="merged_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("無法產生 CSV 檔案。")

        with col2:
            if excel_data:
                st.download_button(
                    label="下載 Excel 檔案",
                    data=excel_data,
                    file_name="merged_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("無法產生 Excel 檔案。")

        # 合併完成後存入 session state
        st.session_state.merged_data = merged_df
        return merged_df

    except Exception as e:
        st.error(f"合併檔案過程中發生未預期的錯誤：{str(e)}")
        import traceback
        st.error(traceback.format_exc()) # 顯示詳細的錯誤追蹤
        return None

def correct_text_with_gpt(text):
    """
    使用 GPT API 修正文字
    
    Args:
        text (str): 需要修正的文字
        
    Returns:
        str: 修正後的文字
    """
    client = get_openai_client()
    if not client:
        st.warning("無法獲取 OpenAI 客戶端，文字修正功能無法使用。")
        return text

    try:
        st.info("正在呼叫 OpenAI API 進行文字修正...")
        
        # 確保提示文本是有效的 UTF-8 字符串
        system_content = "你是一個專業的醫學教育文字編輯助手。你的任務是整理臨床教師對實習醫學生的口頭回饋，使其更有條理且易於閱讀。請保持原意，但可以：\n1. 修正錯別字和語法\n2. 改善句子結構\n3. 適當分段\n4. 使用更專業的醫學用語\n5. 保持評語的建設性和教育意義\n\n請直接返回修改後的文字，不需要其他說明。"
        
        # 顯示用於診斷的信息
        st.info(f"使用者文字字節長度：{len(text.encode('utf-8'))} bytes")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        st.success("✅ OpenAI API 呼叫成功！")
        return response.choices[0].message.content.strip()
    except Exception as e:
        # 安全地獲取錯誤訊息字串
        error_details = f"錯誤類型: {type(e).__name__}"
        try:
            error_message = str(e)
        except Exception:
            error_message = "無法顯示的錯誤訊息 (編碼問題)"

        st.error(f"❌ 呼叫 OpenAI API 時發生錯誤：{error_message} ({error_details})", icon="🚨")
        tb_str = f"詳細追蹤資訊:\n{traceback.format_exc()}"
        st.error(tb_str)
        return text

def init_test_form_db():
    """初始化測試表單資料庫"""
    try:
        conn = sqlite3.connect('test_form.db')
        cursor = conn.cursor()
        
        # 建立測試表單資料表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_form_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            batch TEXT NOT NULL,
            epa_1 INTEGER NOT NULL,
            epa_2 INTEGER NOT NULL,
            epa_3 INTEGER NOT NULL,
            epa_4 INTEGER NOT NULL,
            epa_5 INTEGER NOT NULL,
            comments TEXT,
            submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"初始化資料庫時發生錯誤：{str(e)}")
        return False

def save_to_sqlite(form_data):
    """將表單資料儲存到 SQLite 資料庫"""
    try:
        conn = sqlite3.connect('test_form.db')
        cursor = conn.cursor()
        
        # 插入資料
        cursor.execute('''
        INSERT INTO test_form_submissions 
        (name, batch, epa_1, epa_2, epa_3, epa_4, epa_5, comments, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            form_data['姓名'],
            form_data['梯次'],
            form_data['EPA_1'],
            form_data['EPA_2'],
            form_data['EPA_3'],
            form_data['EPA_4'],
            form_data['EPA_5'],
            form_data['評語'],
            form_data['提交時間']
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"儲存資料到資料庫時發生錯誤：{str(e)}")
        return False

def main():
    # 檢查是否已登入
    if not st.session_state.logged_in:
        # 建立選項卡讓用戶選擇登入或註冊
        login_tab, register_tab, test_form_tab, test_result_tab = st.tabs(["登入", "申請帳號", "測試表單", "測試結果"])
        
        with login_tab:
            if show_login_page():
                st.rerun()
        
        with register_tab:
            if show_registration_page():
                st.success("帳號申請成功！請等待管理員審核後即可登入。")
                # 不需要立即重新運行，讓用戶看到成功訊息
                
        with test_form_tab:
            st.header("測試表單填寫")
            
            # 其他評語（表單外）
            st.subheader("其他評語")
            comments = st.text_area("請輸入評語", height=100, key="input_comments")
            
            # 文字修正按鈕（表單外）
            if comments:
                if st.button("修正文字", key="correct_button"):
                    corrected_comments = correct_text_with_gpt(comments)
                    st.session_state.corrected_comments = corrected_comments
                    st.text_area("修正後的評語", corrected_comments, height=100, key="corrected_text")
                    comments = corrected_comments
            
            st.markdown("---")  # 分隔線
            
            # 使用表單容器
            with st.form("test_form", clear_on_submit=False):
                st.subheader("基本資訊")
                col1, col2 = st.columns(2)
                with col1:
                    name = st.selectbox(
                        "姓名",
                        ["丁OO"]
                    )
                with col2:
                    batch = st.selectbox(
                        "梯次",
                        ["2025/02", "2025/03", "2025/04"]
                    )
                
                # EPA 評分項目
                st.subheader("EPA 評分")
                epa_scores = {}
                for i in range(1, 6):  # 假設有 5 個 EPA 項目
                    epa_scores[f"EPA_{i}"] = st.slider(
                        f"EPA {i} 評分",
                        min_value=1,
                        max_value=5,
                        value=3,
                        help="1: 需要監督, 2: 需要指導, 3: 需要提示, 4: 獨立完成, 5: 可指導他人"
                    )
                
                # 顯示最終評語
                st.subheader("最終評語")
                final_comments = st.text_area("確認評語", comments, height=100, key="final_comments", disabled=True)
                
                # 提交按鈕
                submitted = st.form_submit_button("提交表單")
                
                if submitted:
                    # 建立資料字典
                    form_data = {
                        "姓名": name,
                        "梯次": batch,
                        "EPA_1": epa_scores["EPA_1"],
                        "EPA_2": epa_scores["EPA_2"],
                        "EPA_3": epa_scores["EPA_3"],
                        "EPA_4": epa_scores["EPA_4"],
                        "EPA_5": epa_scores["EPA_5"],
                        "評語": comments,
                        "提交時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 將資料轉換為 DataFrame
                    df = pd.DataFrame([form_data])
                    
                    # 檢查檔案是否存在
                    try:
                        # 如果檔案存在，讀取並附加新資料
                        existing_df = pd.read_csv("test_form_data.csv")
                        df = pd.concat([existing_df, df], ignore_index=True)
                    except FileNotFoundError:
                        # 如果檔案不存在，直接使用新資料
                        pass
                    
                    # 儲存到 CSV 檔案
                    df.to_csv("test_form_data.csv", index=False, encoding='utf-8-sig')
                    
                    # 儲存到 SQLite 資料庫
                    if init_test_form_db():
                        if save_to_sqlite(form_data):
                            st.success("資料已成功儲存到本機資料庫！")
                        else:
                            st.warning("資料已儲存到 CSV，但資料庫儲存失敗")
                    else:
                        st.warning("資料已儲存到 CSV，但資料庫初始化失敗")
                    
                    # 顯示成功訊息
                    st.success("表單提交成功！")
                    # 顯示提交的資料
                    st.write("提交的資料：")
                    st.write(f"姓名：{name}")
                    st.write(f"梯次：{batch}")
                    st.write("EPA 評分：", epa_scores)
                    st.write("評語：", comments)
        
        with test_result_tab:
            st.header("測試結果分析")
            
            try:
                # 讀取 CSV 檔案
                df = pd.read_csv("test_form_data.csv")
                
                # 顯示原始資料
                st.subheader("原始資料")
                st.dataframe(df)
                
                # EPA 評分統計
                st.subheader("EPA 評分統計")
                epa_columns = [f"EPA_{i}" for i in range(1, 6)]
                epa_stats = df[epa_columns].describe()
                st.dataframe(epa_stats)
                
                # EPA 平均分數雷達圖
                st.subheader("EPA 平均分數雷達圖")
                epa_means = df[epa_columns].mean()
                
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=epa_means.values,
                    theta=[f"EPA {i}" for i in range(1, 6)],
                    fill='toself',
                    name='平均分數',
                    hovertemplate='EPA: %{theta}<br>平均分數: %{r:.2f}<extra></extra>'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 5],
                            ticktext=['1', '2', '3', '4', '5'],
                            tickvals=[1, 2, 3, 4, 5]
                        )
                    ),
                    showlegend=False,
                    title="EPA 平均分數雷達圖",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # EPA 評分趨勢圖
                st.subheader("EPA 評分趨勢（按梯次）")
                
                # 按照梯次分組計算平均分數
                epa_trend = df.groupby('梯次')[epa_columns].mean().reset_index()
                
                fig = go.Figure()
                
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']  # 自定義顏色
                
                for i, epa in enumerate(epa_columns):
                    fig.add_trace(go.Scatter(
                        x=epa_trend['梯次'],
                        y=epa_trend[epa],
                        mode='lines+markers',
                        name=f'EPA {i+1}',
                        line=dict(width=3, color=colors[i]),
                        marker=dict(size=10, symbol='circle', color=colors[i]),
                        hovertemplate='梯次: %{x}<br>平均分數: %{y:.2f}<extra></extra>'
                    ))
                
                fig.update_layout(
                    title=dict(
                        text="EPA 評分趨勢（按梯次）",
                        font=dict(size=24)
                    ),
                    xaxis=dict(
                        title="梯次",
                        categoryorder='array',
                        categoryarray=['2025/02', '2025/03', '2025/04'],
                        tickfont=dict(size=14),
                        gridcolor='lightgrey'
                    ),
                    yaxis=dict(
                        title="平均分數",
                        range=[1, 5],
                        tickmode='linear',
                        tick0=1,
                        dtick=1,
                        tickfont=dict(size=14),
                        gridcolor='lightgrey'
                    ),
                    hovermode="x unified",
                    showlegend=True,
                    legend=dict(
                        font=dict(size=12),
                        yanchor="top",
                        y=0.99,
                        xanchor="right",
                        x=0.99
                    ),
                    height=600,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    margin=dict(t=100)
                )
                
                # 添加網格線
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
                
                st.plotly_chart(fig, use_container_width=True)
                
                # EPA 評分分布圖
                st.subheader("EPA 評分分布")
                fig = make_subplots(rows=2, cols=3, subplot_titles=[f"{epa} 分布" for epa in epa_columns])
                
                for i, epa in enumerate(epa_columns):
                    row = (i // 3) + 1
                    col = (i % 3) + 1
                    
                    fig.add_trace(
                        go.Histogram(
                            x=df[epa],
                            nbinsx=5,
                            name=epa,
                            hovertemplate='評分: %{x}<br>次數: %{y}<extra></extra>'
                        ),
                        row=row, col=col
                    )
                
                fig.update_layout(
                    height=800,
                    showlegend=False,
                    title_text="EPA 評分分布"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 評語分析
                st.subheader("評語分析")
                if not df['評語'].empty:
                    st.write("最近 5 筆評語：")
                    for comment in df['評語'].tail(5):
                        st.write(f"- {comment}")
                
            except FileNotFoundError:
                st.warning("尚未有測試資料，請先填寫表單。")
            except Exception as e:
                st.error(f"讀取或分析資料時發生錯誤：{str(e)}")
        return
    
    # 顯示登出按鈕
    with st.sidebar:
        if st.button("登出"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.user_name = None
            st.session_state.user_department = None
            st.session_state.student_id = None
            st.rerun()
    
    st.title("學生評核系統")
    
    # 定義科別列表
    departments = [
        "小兒部", 
        "內科", 
        "外科", 
        "婦產科", 
        "神經科", 
        "精神科", 
        "家醫科", 
        "急診醫學科", 
        "麻醉科", 
        "放射科", 
        "病理科", 
        "復健科", 
        "皮膚科", 
        "眼科", 
        "耳鼻喉科", 
        "泌尿科", 
        "骨科", 
        "其他科別"
    ]
    
    # 獲取使用者科別
    user_department = st.session_state.get('user_department', None)
    
    # 側邊欄設置
    with st.sidebar:
        st.header("資料來源選擇")
        
        st.header("科別選擇")
        
        # 科別選擇 - 根據權限限制可選擇的科別
        if check_permission(st.session_state.role, 'can_view_all'):
            # 管理員可以選擇所有科別
            available_departments = departments
        elif st.session_state.role == 'teacher' and user_department:
            # 主治醫師只能選擇自己的科別
            available_departments = [user_department]
        else:
            # 其他角色只能選擇自己的科別（如果有的話）
            available_departments = [user_department] if user_department else departments
        
        selected_dept = st.selectbox(
            "請選擇科別",
            available_departments
        )
        
        # 根據權限顯示上傳區域
        if check_permission(st.session_state.role, 'can_upload_files'):
            st.subheader(f"{selected_dept}評核資料")
            
            # 檔案上傳區域
            uploaded_files = st.file_uploader(
                f"請上傳{selected_dept} Excel檔案",
                type=['xlsx', 'xls'],
                accept_multiple_files=True,
                key=f"{selected_dept}_files"
            )
            
            if st.button(f"合併{selected_dept}檔案") and uploaded_files:
                result = merge_excel_files(uploaded_files)
                if result is not None:
                    st.success(f"{selected_dept}檔案合併成功！")
                    # 將資料存入 session state，使用科別作為 key
                    st.session_state[f"{selected_dept}_data"] = result
                    st.session_state.merged_data = result
                else:
                    st.error(f"{selected_dept}檔案合併失敗！")
        
        # 顯示已上傳的科別 - 根據權限過濾
        if check_permission(st.session_state.role, 'can_view_all'):
            st.subheader("已上傳的科別")
            uploaded_depts = [dept for dept in departments if f"{dept}_data" in st.session_state]
            if uploaded_depts:
                for dept in uploaded_depts:
                    st.write(f"✅ {dept}")
            else:
                st.write("尚未上傳任何科別資料")
        elif st.session_state.role == 'teacher' and user_department:
            # 主治醫師只能看到自己科的資料
            st.subheader("已上傳的科別")
            if f"{user_department}_data" in st.session_state:
                st.write(f"✅ {user_department}")
            else:
                st.write(f"尚未上傳 {user_department} 的資料")
        
        # 系統管理員可以管理使用者
        if check_permission(st.session_state.role, 'can_manage_users'):
            st.markdown("---")
            show_user_management()
        
        # 添加測試系統連結
        st.markdown("---")
        st.subheader("測試系統")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("填寫表單測試", key="sidebar_form_button"):
                st.markdown('<meta http-equiv="refresh" content="0;URL=test_form">', unsafe_allow_html=True)
        with col2:
            if st.button("查看測試結果", key="sidebar_result_button"):
                st.markdown('<meta http-equiv="refresh" content="0;URL=test_results">', unsafe_allow_html=True)

    # 分頁設置 - 根據權限顯示不同的分頁
    tab_names = []
    
    # 根據角色和權限顯示不同的分頁
    if check_permission(st.session_state.role, 'can_view_all'):
        # 管理員可以看到所有資料
        tab_names.append("UGY")
        tab_names.append("PGY")
        tab_names.append("住院醫師")
        tab_names.append("老師評分分析")
    elif check_permission(st.session_state.role, 'can_view_ugy_data'):
        # 主治醫師和住院醫師可以看到UGY資料
        tab_names.append("UGY")
        
        if check_permission(st.session_state.role, 'can_view_pgy_data'):
            tab_names.append("PGY")
        
        if check_permission(st.session_state.role, 'can_view_resident_data'):
            tab_names.append("住院醫師")
        
        if check_permission(st.session_state.role, 'can_view_analytics'):
            tab_names.append("老師評分分析")
    elif st.session_state.role == 'student':
        # UGY只能看到自己的資料
        tab_names.append("我的評核資料")
    
    if not tab_names:
        st.warning("您沒有權限查看任何資料")
        return
    
    # 根據角色動態創建分頁
    if st.session_state.role == 'student':
        # UGY現在也可能有多個分頁
        tabs = st.tabs(tab_names)
        
        # 根據分頁名稱動態處理內容
        for i, tab_name in enumerate(tab_names):
            with tabs[i]:
                if tab_name == "我的評核資料":
                    st.header("我的評核資料")
                    # 從 session state 中獲取所有科別的資料
                    all_data = []
                    for dept in departments:
                        if f"{dept}_data" in st.session_state:
                            all_data.append(st.session_state[f"{dept}_data"])
                    
                    if all_data:
                        # 合併所有科別的資料
                        current_data = pd.concat(all_data, ignore_index=True)
                        # 過濾出該學生的資料
                        student_data = current_data[current_data['學號'] == st.session_state.get('student_id')]
                        if not student_data.empty:
                            # 顯示基本資訊
                            st.subheader("基本資訊")
                            st.write(f"姓名：{student_data['姓名'].iloc[0]}")
                            st.write(f"學號：{student_data['學號'].iloc[0]}")
                            st.write(f"科別：{student_data['科別'].iloc[0]}")
                            
                            # 顯示 EPA 評分
                            st.subheader("EPA 評分")
                            epa_columns = [col for col in student_data.columns if 'EPA' in col]
                            for epa_col in epa_columns:
                                st.write(f"{epa_col}：{student_data[epa_col].iloc[0]}")
                            
                            # 顯示評語
                            if '評語' in student_data.columns:
                                st.subheader("評語")
                                st.write(student_data['評語'].iloc[0])
                            
                            # 顯示趨勢圖
                            st.subheader("評分趨勢")
                            if len(student_data) > 1:  # 確保有多筆資料才顯示趨勢圖
                                trend_data = student_data[epa_columns].T
                                trend_data.columns = ['評分']
                                st.line_chart(trend_data)
                            
                            # 顯示雷達圖
                            st.subheader("能力雷達圖")
                            if epa_columns:
                                radar_data = student_data[epa_columns].iloc[0]
                                fig = go.Figure()
                                fig.add_trace(go.Scatterpolar(
                                    r=radar_data.values,
                                    theta=radar_data.index,
                                    fill='toself',
                                    name='能力評分'
                                ))
                                fig.update_layout(
                                    polar=dict(
                                        radialaxis=dict(
                                            visible=True,
                                            range=[0, 5]
                                        )
                                    ),
                                    showlegend=False
                                )
                                st.plotly_chart(fig)
                        else:
                            st.warning("找不到您的評核資料")
                    else:
                        st.warning("尚未上傳任何評核資料")
                
                elif tab_name == "UGY":
                    if check_permission(st.session_state.role, 'can_view_ugy_data'):
                        # 根據角色決定顯示的分頁
                        if st.session_state.role == 'student':
                            # 學生帳號只顯示個別學生分析
                            st.header("我的評核資料分析")
                            show_ugy_student_analysis()
                        else:
                            # 其他角色顯示完整的分頁
                            ugy_subtabs = st.tabs(["學生總覽", "個別學生分析"])
                            
                            with ugy_subtabs[0]:
                                st.header("學生總覽")
                                show_ugy_student_overview()
                            
                            with ugy_subtabs[1]:
                                st.header("個別學生分析")
                                show_ugy_student_analysis()
    else:
        # 為非學生角色準備 current_data
        current_data = None
        all_data = []
        for dept in departments:
            if f"{dept}_data" in st.session_state:
                all_data.append(st.session_state[f"{dept}_data"])
        
        if all_data:
            current_data = pd.concat(all_data, ignore_index=True)
        
        # 動態創建分頁
        tabs = st.tabs(tab_names)
        
        # 根據分頁名稱動態處理內容
        for i, tab_name in enumerate(tab_names):
            with tabs[i]:
                if tab_name == "UGY":
                    if check_permission(st.session_state.role, 'can_view_all') or check_permission(st.session_state.role, 'can_view_ugy_data'):
                        # 根據角色決定顯示的分頁
                        if st.session_state.role == 'student':
                            # 學生帳號只顯示個別學生分析
                            st.header("我的評核資料分析")
                            show_ugy_student_analysis()
                        else:
                            # 其他角色顯示完整的分頁
                            ugy_subtabs = st.tabs(["學生總覽", "個別學生分析"])
                            
                            with ugy_subtabs[0]:
                                st.header("學生總覽")
                                show_ugy_student_overview()
                            
                            with ugy_subtabs[1]:
                                st.header("個別學生分析")
                                show_ugy_student_analysis()
                
                elif tab_name == "PGY":
                    if check_permission(st.session_state.role, 'can_view_pgy_data'):
                        st.header("PGY 分析")
                        if current_data is not None:
                            pgy_data = current_data[current_data['檔案名稱'].str.contains('PGY', case=False, na=False)]
                            if not pgy_data.empty:
                                # 根據權限過濾PGY資料
                                filtered_pgy_data = filter_data_by_permission(pgy_data, st.session_state.role, user_department, 'pgy')
                                if not filtered_pgy_data.empty:
                                    show_analysis_section(filtered_pgy_data)
                                else:
                                    st.warning("您沒有權限查看此資料")
                            else:
                                st.warning("沒有 PGY 資料")
                        else:
                            st.warning("請先載入資料")
                
                elif tab_name == "住院醫師":
                    if check_permission(st.session_state.role, 'can_view_resident_data') or check_permission(st.session_state.role, 'can_view_all'):
                        # 檢查是否選擇小兒部
                        if selected_dept == "小兒部":
                            # 直接顯示小兒部評核系統
                            from analysis_pediatric import show_pediatric_evaluation_section
                            show_pediatric_evaluation_section()
                        else:
                            # 顯示一般住院醫師分析
                            st.header("住院醫師分析")
                            if current_data is not None:
                                r_data = current_data[current_data['檔案名稱'].str.contains('R', case=False, na=False)]
                                if not r_data.empty:
                                    # 根據權限過濾住院醫師資料
                                    filtered_r_data = filter_data_by_permission(r_data, st.session_state.role, user_department, 'resident')
                                    if not filtered_r_data.empty:
                                        if selected_dept == "麻醉科":
                                            show_ANE_R_EPA_peer_analysis_section(filtered_r_data)
                                        else:
                                            show_resident_analysis_section(filtered_r_data)
                                    else:
                                        st.warning("您沒有權限查看此資料")
                                else:
                                    st.warning("沒有住院醫師資料")
                            else:
                                st.warning("請先載入資料")
                
                elif tab_name == "老師評分分析":
                    if check_permission(st.session_state.role, 'can_view_analytics'):
                        show_teacher_analysis_section()

if __name__ == "__main__":
    main()

# streamlit run main_dashboard.py

# GitHub 更新指令說明
# 1. 初次設定
# git init  # 初始化 git 倉庫
# git remote add origin <repository_url>  # 連接遠端倉庫

# 2. 更新流程
# git add .  # 加入所有修改的檔案
# git commit -m "更新說明"  # 提交修改並加入說明
# git push origin main  # 推送到 GitHub 主分支

# 3. 如果遇到衝突
# git pull origin main  # 先拉取最新版本
# 解決衝突後再執行步驟 2

# 4. 查看狀態
# git status  # 檢查檔案狀態
# git log  # 查看提交歷史 

