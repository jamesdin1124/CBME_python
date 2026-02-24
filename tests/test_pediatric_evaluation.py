#!/usr/bin/env python3
"""
小兒部住院醫師評核系統測試腳本
"""

import streamlit as st
import pandas as pd
from analysis_pediatric import (
    show_pediatric_evaluation_section,
    load_pediatric_data,
    process_pediatric_data,
    convert_score_to_numeric,
    convert_reliability_to_numeric,
    convert_proficiency_to_numeric
)

def test_data_processing():
    """測試資料處理功能"""
    st.title("🧪 小兒部評核系統測試")
    
    # 創建測試資料
    test_data = {
        '時間戳記': ['2025/9/12 上午 11:11:32', '2025/9/13 下午 2:30:15'],
        '評核教師': ['丁肇壯', '王小明'],
        '評核日期': ['2025/9/12', '2025/9/13'],
        '受評核人員': ['林盈秀', '張三'],
        '評核時級職': ['R3', 'R2'],
        '評核項目': ['操作技術', '病例討論'],
        '會議名稱': ['晨會', '病例討論會'],
        '內容是否充分': ['同意', '非常同意'],
        '辯證資料的能力': ['普通', '良好'],
        '口條、呈現方式是否清晰': ['同意', '非常同意'],
        '是否具開創、建設性的想法': ['普通', '良好'],
        '回答提問是否具邏輯、有條有理': ['同意', '非常同意'],
        '會議報告教師回饋': ['表現良好', '需要加強'],
        '病歷號': ['9113665', '9113666'],
        '評核技術項目': ['腎臟超音波', '心臟超音波'],
        '鎮靜藥物': ['不需使用', '需要'],
        '可信賴程度': ['3 協助下完成', '4 獨立完成'],
        '操作技術教師回饋': ['基本操作已經熟練', '需要更多練習'],
        '熟練程度': ['熟練', '基本熟練']
    }
    
    test_df = pd.DataFrame(test_data)
    
    st.subheader("原始測試資料")
    st.dataframe(test_df)
    
    # 測試資料處理
    st.subheader("處理後的資料")
    processed_df = process_pediatric_data(test_df)
    st.dataframe(processed_df)
    
    # 測試評分轉換
    st.subheader("評分轉換測試")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**評分轉換測試**")
        test_scores = ['非常同意', '同意', '普通', '不同意', '非常不同意']
        for score in test_scores:
            numeric = convert_score_to_numeric(score)
            st.write(f"{score} → {numeric}")
    
    with col2:
        st.write("**可信賴程度轉換測試**")
        test_reliability = ['1 需要指導', '2 部分獨立', '3 協助下完成', '4 獨立完成', '5 完全獨立']
        for rel in test_reliability:
            numeric = convert_reliability_to_numeric(rel)
            st.write(f"{rel} → {numeric}")
    
    with col3:
        st.write("**熟練程度轉換測試**")
        test_proficiency = ['不熟練', '初學', '部分熟練', '基本熟練', '熟練']
        for prof in test_proficiency:
            numeric = convert_proficiency_to_numeric(prof)
            st.write(f"{prof} → {numeric}")
    
    # 測試統計分析
    st.subheader("統計分析測試")
    
    if '內容是否充分_數值' in processed_df.columns:
        scores = processed_df['內容是否充分_數值'].dropna()
        if not scores.empty:
            st.write(f"平均分數: {scores.mean():.2f}")
            st.write(f"最高分數: {scores.max()}")
            st.write(f"最低分數: {scores.min()}")
            st.write(f"標準差: {scores.std():.2f}")

def test_google_sheets_connection():
    """測試Google Sheets連接"""
    st.subheader("Google Sheets連接測試")
    
    if st.button("測試連接"):
        with st.spinner("正在測試連接..."):
            try:
                df, sheet_titles = load_pediatric_data()
                if df is not None:
                    st.success("✅ 連接成功！")
                    st.write(f"載入資料筆數: {len(df)}")
                    st.write(f"工作表列表: {sheet_titles}")
                    
                    if not df.empty:
                        st.write("資料預覽:")
                        st.dataframe(df.head())
                else:
                    st.error("❌ 連接失敗")
            except Exception as e:
                st.error(f"❌ 連接錯誤: {str(e)}")

def main():
    """主測試函數"""
    st.set_page_config(
        page_title="小兒部評核系統測試",
        layout="wide"
    )
    
    # 創建分頁
    tab1, tab2 = st.tabs(["資料處理測試", "Google Sheets連接測試"])
    
    with tab1:
        test_data_processing()
    
    with tab2:
        test_google_sheets_connection()

if __name__ == "__main__":
    main()
