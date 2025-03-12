import streamlit as st
import pandas as pd
import os
from io import BytesIO
from student_analysis import show_analysis_section
import sys
from resident_analysis import show_resident_analysis_section
from ANE_R_EPA_analysis import show_ANE_R_EPA_peer_analysis_section
import re
from UGY_EPA import show_google_form_import_section, analyze_epa_data
from teacher_analysis import show_teacher_analysis_section
from UGY_peer_analysis import show_UGY_peer_analysis_section

# 設定頁面配置為寬屏模式
st.set_page_config(
    layout="wide",  # 使用寬屏模式
    page_title="臨床教師評核系統",
    initial_sidebar_state="expanded"  # 預設展開側邊欄
)

# 獲取當前檔案的目錄
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from UGY_peer_analysis import show_UGY_peer_analysis_section
except ImportError:
    st.error("無法載入 UGY_peer_analysis 模組，請確認檔案位置是否正確")

def merge_excel_files(uploaded_files):
    # ... 現有代碼 ...
    try:
        if not uploaded_files:
            st.warning("請上傳Excel檔案！")
            return None
            
        # 定義轉換對照表
        teacher_evaluation_texts = {
        'LEVEL I': 1,
        'LEVEL II': 2,
        'LEVEL III': 3,
        'LEVEL IV': 4,
        'LEVEL V': 5,
        'Level I': 1,
        'Level II': 2, 
        'Level III': 3,
        'Level IV': 4,
        'Level V': 5,
        'level i': 1,
        'level ii': 2,
        'level iii': 3,
        'level iv': 4,
        'level v': 5,
        'I': 1,
        'II': 2,
        'III': 3,
        'IV': 4,
        'V': 5,
        'i': 1,
        'ii': 2,
        'iii': 3,
        'iv': 4,
        'v': 5,
        'LEVEL 1': 1,
        'LEVEL 2': 2,
        'LEVEL 3': 3,
        'LEVEL 4': 4,
        'LEVEL 5': 5,
        'Level 1': 1,
        'Level 2': 2,
        'Level 3': 3,
        'Level 4': 4,
        'Level 5': 5,
        'level 1': 1,
        'level 2': 2,
        'level 3': 3,
        'level 4': 4,
        'level 5': 5,
        '1': 1,
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
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
        
        teacher_support_texts = {
            '教師在旁逐步共同操作': 1,
            '教師在旁必要時協助 ': 2,
            '教師可立即到場協助，事後須再確認': 3,
            '教師可稍後到場協助，重點須再確認': 4,
            '我可獨立執行': 5
        }
        
        # 合併所有Excel檔案
        all_data = []
        for uploaded_file in uploaded_files:
            # ... 處理檔案的代碼 ...
            df = pd.read_excel(uploaded_file)
            
            # 處理檔案名稱，移除括號內的版本號
            clean_filename = re.sub(r'\s*\([0-9]+\)\.xls$', '.xls', uploaded_file.name)
            
            # 處理訓練階段期間
            if '訓練階段期間' in df.columns:
                # 將期間字串分割成開始和結束日期
                df[['開始日期', '結束日期']] = df['訓練階段期間'].str.extract(r'(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})')
                
                # 轉換為日期格式
                df['開始日期'] = pd.to_datetime(df['開始日期'])
                df['結束日期'] = pd.to_datetime(df['結束日期'])
                
                # 計算訓練天數
                df['訓練天數'] = (df['結束日期'] - df['開始日期']).dt.days + 1
            
            # 轉換欄位（如果存在）
            for col in df.columns:
                # 移除特定文字
                df[col] = df[col].replace("本表單與畢業成績無關，請依學生表現落實評量;", "")
                
                if '教師評核' in col:
                    # 確保轉換後的值是數值型態
                    df[col] = df[col].apply(lambda x: teacher_evaluation_texts.get(str(x).strip(), x))
                    # 強制轉換為數值型態
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                elif '學員自評' in col:
                    df[col] = df[col].apply(lambda x: teacher_evaluation_texts.get(str(x), x))
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                elif 'EPA' in col:
                    df[col] = df[col].apply(lambda x: teacher_support_texts.get(str(x), x))
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            
            # 加入處理過的檔案名稱欄位
            df['檔案名稱'] = clean_filename
            all_data.append(df)
        
        # 直接合併所有DataFrame，保留所有欄位
        merged_df = pd.concat(all_data, ignore_index=True, sort=False)
        
        # 確保檔案名稱欄位在最前面
        cols = merged_df.columns.tolist()
        cols.remove('檔案名稱')
        merged_df = merged_df[['檔案名稱'] + cols]
        
        # 將合併後的資料轉換為 CSV
        csv = merged_df.to_csv(index=False)
        
        # 將合併後的資料轉換為 Excel
        excel_buffer = BytesIO()
        merged_df.to_excel(excel_buffer, index=False)
        excel_data = excel_buffer.getvalue()
        
        # 建立兩個並排的下載按鈕
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="下載 CSV 檔案",
                data=csv,
                file_name="merged_data.csv",
                mime="text/csv"
            )
        
        with col2:
            st.download_button(
                label="下載 Excel 檔案",
                data=excel_data,
                file_name="merged_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # 合併完成後存入 session state
        st.session_state.merged_data = merged_df
        
        return merged_df
        
    except Exception as e:
        st.error(f"合併檔案時發生錯誤：{str(e)}")
        return None

def show_overall_analysis(df):
    """顯示整體分析的函數"""
    # ... 現有代碼 ...
    st.subheader("整體成績分析")
    
    # 1. 基本統計資訊
    score_cols = [col for col in df.columns if '成績' in col or '分數' in col]
    if score_cols:
        st.write("各項成績統計")
        for col in score_cols:
            with st.expander(f"{col} 統計資訊"):
                # 只處理數值型資料
                numeric_data = pd.to_numeric(df[col], errors='coerce')
                if not numeric_data.empty:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("平均分數", f"{numeric_data.mean():.2f}")
                    with col2:
                        st.metric("最高分", f"{numeric_data.max():.2f}")
                    with col3:
                        st.metric("最低分", f"{numeric_data.min():.2f}")
    
    # 2. 各階段完成度分析
    if '訓練階段' in df.columns:
        st.write("各訓練階段作業完成情況")
        completion_by_stage = df.groupby('訓練階段').size()
        st.bar_chart(completion_by_stage)
    
    # 3. 教師評核分布
    evaluation_cols = [col for col in df.columns if '教師評核' in col]
    if evaluation_cols:
        st.write("教師評核分布")
        for col in evaluation_cols:
            with st.expander(f"{col} 分布"):
                # 確保資料是數值型
                numeric_eval = pd.to_numeric(df[col], errors='coerce')
                if not numeric_eval.empty:
                    eval_dist = numeric_eval.value_counts().sort_index()
                    st.bar_chart(eval_dist)
    
    # 4. 時間趨勢分析
    if '日期' in df.columns and score_cols:
        st.write("成績時間趨勢")
        for score_col in score_cols:
            with st.expander(f"{score_col} 時間趨勢"):
                # 確保只使用數值型資料
                df_clean = df.copy()
                df_clean[score_col] = pd.to_numeric(df_clean[score_col], errors='coerce')
                df_clean = df_clean.dropna(subset=[score_col])
                
                if not df_clean.empty:
                    # 使用 DataFrame 的方式呈現
                    st.write("成績趨勢表")
                    trend_data = df_clean.groupby('日期')[score_col].mean().reset_index()
                    st.dataframe(trend_data)
                    
                    # 使用基本折線圖
                    st.write("成績趨勢圖")
                    chart_data = pd.DataFrame({
                        '日期': trend_data['日期'],
                        '平均分數': trend_data[score_col]
                    })
                    st.line_chart(chart_data.set_index('日期'))

def main():
    st.title("臨床教師評核系統")
    
    # 定義科別列表
    departments = [
        "小兒科", 
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
    
    # 側邊欄設置 - 改為科別選擇
    with st.sidebar:
        st.header("科別選擇")
        
        # 科別選擇
        selected_dept = st.selectbox(
            "請選擇科別",
            departments
        )
        
        # 根據選擇的科別顯示上傳區域
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
            else:
                st.error(f"{selected_dept}檔案合併失敗！")
        
        # 顯示已上傳的科別
        st.subheader("已上傳的科別")
        uploaded_depts = [dept for dept in departments if f"{dept}_data" in st.session_state]
        if uploaded_depts:
            for dept in uploaded_depts:
                st.write(f"✅ {dept}")
        else:
            st.write("尚未上傳任何科別資料")

    # 分頁設置 - 改為 UGY, PGY, R, 老師評分分析
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["UGY EPA", "UGY整合", "PGY", "R", "老師評分分析"])
    
    # 獲取當前選擇的科別資料
    current_data = st.session_state.get(f"{selected_dept}_data", None)
    
    with tab1:
        st.header("UGY EPA 分析")
        show_google_form_import_section()
        
        # 新增：從 Google API 獲取的資料分析
        if 'epa_data' in st.session_state and st.session_state.epa_data is not None:
            st.subheader("EPA 資料分析結果")
            analyze_epa_data(st.session_state.epa_data)
            
            # 顯示資料下載按鈕
            csv = st.session_state.epa_data.to_csv(index=False)
            excel_buffer = BytesIO()
            st.session_state.epa_data.to_excel(excel_buffer, index=False)
            excel_data = excel_buffer.getvalue()
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="下載 EPA 資料 (CSV)",
                    data=csv,
                    file_name="epa_data.csv",
                    mime="text/csv"
                )
            with col2:
                st.download_button(
                    label="下載 EPA 資料 (Excel)",
                    data=excel_data,
                    file_name="epa_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    with tab2:
        st.header("UGY整合分析")
        if current_data is not None:
            # 將當前資料存入 session state 的 ugy_data
            st.session_state.ugy_data = current_data
            show_UGY_peer_analysis_section(current_data)
        else:
            st.warning("請先在側邊欄合併 CEPO Excel檔案")
    
    with tab3:
        st.header(f"{selected_dept} - PGY 分析")
        if current_data is not None:
            # 篩選 PGY 相關資料
            pgy_data = current_data[current_data['檔案名稱'].str.contains('PGY', case=False, na=False)]
            if not pgy_data.empty:
                show_analysis_section(pgy_data)
            else:
                st.warning(f"沒有 {selected_dept} 的 PGY 資料")
        else:
            st.warning(f"請先上傳並合併 {selected_dept} 的資料")
    
    with tab4:
        st.header(f"{selected_dept} - R 分析")
        if current_data is not None:
            # 篩選住院醫師相關資料
            r_data = current_data[current_data['檔案名稱'].str.contains('R', case=False, na=False)]
            if not r_data.empty:
                # 根據科別選擇不同的分析函數
                if selected_dept == "麻醉科":
                    # 使用麻醉科專用的分析函數
                    show_ANE_R_EPA_peer_analysis_section(r_data)
                else:
                    # 使用一般住院醫師分析函數
                    show_resident_analysis_section(r_data)
            else:
                st.warning(f"沒有 {selected_dept} 的住院醫師資料")
        else:
            st.warning(f"請先上傳並合併 {selected_dept} 的資料")
    
    with tab5:
        # 直接呼叫函數，不傳遞任何參數
        show_teacher_analysis_section()


if __name__ == "__main__":
    main()

# streamlit run new_dashboard.py

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
