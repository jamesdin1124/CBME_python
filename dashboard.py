import streamlit as st
import pandas as pd
import os
from io import BytesIO
from student_analysis import show_analysis_section
import sys
from resident_analysis import show_resident_analysis_section

# 獲取當前檔案的目錄
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from UGY_peer_analysis import show_UGY_peer_analysis_section
except ImportError:
    st.error("無法載入 UGY_peer_analysis 模組，請確認檔案位置是否正確")

def merge_excel_files(folder_path):
    try:
        # 取得所有Excel檔案
        excel_files = [
            f for f in os.listdir(folder_path) 
            if f.endswith(('.xlsx', '.xls'))
        ]
        
        if not excel_files:
            st.warning("所選資料夾中沒有Excel檔案！")
            return None
            
        # 定義轉換對照表
        
        teacher_evaluation_texts = {
            ' Level I': 1,
            ' Level II': 2,
            ' Level III': 3,
            ' Level IV': 4,
            ' Level V': 5
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
        for file in excel_files:
            file_path = os.path.join(folder_path, file)
            df = pd.read_excel(file_path)
            
            # 處理檔案名稱，移除括號內的版本號
            clean_filename = re.sub(r'\s*\([0-9]+\)\.xls$', '.xls', file)
            
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
                    df[col] = df[col].apply(lambda x: teacher_evaluation_texts.get(str(x), x))
                elif 'EPA' in col:
                    df[col] = df[col].apply(lambda x: teacher_support_texts.get(str(x), x))
            
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
    
    # 側邊欄設置
    with st.sidebar:
        st.header("資料處理")
        uploaded_folder = st.text_input("請輸入Excel檔案所在的資料夾路徑")
        
        if st.button("合併Excel檔案") and uploaded_folder:
            result = merge_excel_files(uploaded_folder)
            if result is not None:
                st.success("檔案合併成功！")
                st.session_state.merged_data = result
            else:
                st.error("檔案合併失敗！")
    
    # 修改分頁設置，從三個分頁改為兩個，並更改名稱
    tab1, tab2 = st.tabs(["住院醫師分析", "UGY分析"])
    
    with tab1:
        if 'merged_data' in st.session_state:
            show_resident_analysis_section(st.session_state.merged_data)
        else:
            st.warning("請先在側邊欄合併Excel檔案")
    
    with tab2:
        if 'merged_data' in st.session_state:
            show_UGY_peer_analysis_section(st.session_state.merged_data)
        else:
            st.warning("請先在側邊欄合併Excel檔案")

if __name__ == "__main__":
    main()

#streamlit run dashboard.py