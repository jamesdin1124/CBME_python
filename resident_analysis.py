import streamlit as st
import pandas as pd
import plotly.express as px

def show_resident_analysis_section(df=None):
    st.header("住院醫師學習分析")
    
    if df is None:
        st.warning("請先載入資料")
        return
        
    # 基本資訊統計
    with st.expander("基本統計資訊"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("住院醫師總人數", len(df['學員姓名'].unique()))
        with col2:
            st.metric("評核紀錄總數", len(df))
    
    # EPA 程度分析
    epa_cols = [col for col in df.columns if 'EPA' in col]
    if epa_cols:
        st.subheader("EPA 程度分析")
        for col in epa_cols:
            with st.expander(f"{col} 分布"):
                fig = px.histogram(df, x=col, title=f"{col} 分布圖")
                st.plotly_chart(fig)
    
    # 訓練時間分析
    if '訓練天數' in df.columns:
        st.subheader("訓練時間分析")
        fig = px.box(df, y='訓練天數', title="訓練天數分布")
        st.plotly_chart(fig)
    
    # 教師評核分析
    eval_cols = [col for col in df.columns if '教師評核' in col]
    if eval_cols:
        st.subheader("教師評核分析")
        for col in eval_cols:
            with st.expander(f"{col} 趨勢"):
                fig = px.line(df.sort_values('日期'), 
                            x='日期', 
                            y=col,
                            title=f"{col} 時間趨勢")
                st.plotly_chart(fig) 