"""
教師評分分析模組
專門分析教師評分模式，找出評分特別高或特別低的老師
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from modules.data_processing import process_epa_level
from modules.google_connection import fetch_google_form_data

def analyze_teacher_scoring_patterns(df):
    """
    分析教師評分模式
    
    Args:
        df: 包含教師評核資料的DataFrame
        
    Returns:
        dict: 包含各種分析結果的字典
    """
    if df is None or df.empty:
        return None
    
    # 檢查並統一教師欄位名稱
    teacher_column = None
    if '教師' in df.columns:
        teacher_column = '教師'
    elif '評核老師' in df.columns:
        teacher_column = '評核老師'
    elif '電子郵件地址' in df.columns:
        teacher_column = '電子郵件地址'
        df = df.copy()
        df['教師'] = df['電子郵件地址']
        teacher_column = '教師'
    else:
        st.error("找不到教師欄位，請確認資料包含「教師」、「評核老師」或「電子郵件地址」欄位")
        return None
    
    # 確保必要的欄位存在
    required_columns = [teacher_column, '教師評核EPA等級', 'EPA評核項目']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"缺少必要欄位：{missing_columns}")
        return None
    
    # 處理EPA等級資料
    df_processed = df.copy()
    
    # 確保評分欄位是數值型
    if df_processed['教師評核EPA等級'].dtype == 'object':
        df_processed['教師評核EPA等級'] = df_processed['教師評核EPA等級'].apply(process_epa_level)
    else:
        df_processed['教師評核EPA等級'] = pd.to_numeric(df_processed['教師評核EPA等級'], errors='coerce')
    
    # 移除無效的評分資料
    df_processed = df_processed.dropna(subset=['教師評核EPA等級'])
    df_processed = df_processed[df_processed['教師評核EPA等級'] > 0]
    
    # 計算每位教師的評分統計
    teacher_stats = df_processed.groupby(teacher_column)['教師評核EPA等級'].agg([
        'count', 'mean', 'std', 'min', 'max', 'median'
    ]).round(2)
    
    teacher_stats.columns = ['評核次數', '平均分數', '標準差', '最低分', '最高分', '中位數']
    
    # 計算整體統計
    overall_mean = df_processed['教師評核EPA等級'].mean()
    overall_std = df_processed['教師評核EPA等級'].std()
    
    # 識別評分異常的教師
    # 高評分教師：平均分數 > 整體平均 + 1.5 * 標準差
    # 低評分教師：平均分數 < 整體平均 - 1.5 * 標準差
    high_threshold = overall_mean + 1.5 * overall_std
    low_threshold = overall_mean - 1.5 * overall_std
    
    high_scoring_teachers = teacher_stats[teacher_stats['平均分數'] > high_threshold]
    low_scoring_teachers = teacher_stats[teacher_stats['平均分數'] < low_threshold]
    
    # 計算評分一致性（標準差）
    consistent_teachers = teacher_stats[teacher_stats['標準差'] < 0.5]  # 標準差小於0.5
    variable_teachers = teacher_stats[teacher_stats['標準差'] > 1.0]   # 標準差大於1.0
    
    return {
        'teacher_stats': teacher_stats,
        'overall_stats': {
            'mean': overall_mean,
            'std': overall_std,
            'count': len(df_processed)
        },
        'high_scoring_teachers': high_scoring_teachers,
        'low_scoring_teachers': low_scoring_teachers,
        'consistent_teachers': consistent_teachers,
        'variable_teachers': variable_teachers,
        'processed_data': df_processed
    }

def create_teacher_scoring_charts(analysis_results):
    """創建教師評分分析圖表"""
    
    teacher_stats = analysis_results['teacher_stats']
    overall_stats = analysis_results['overall_stats']
    
    # 1. 教師平均分數分布圖
    fig1 = px.histogram(
        teacher_stats, 
        x='平均分數',
        nbins=20,
        title='教師平均評分分布',
        labels={'平均分數': '平均評分', 'count': '教師人數'}
    )
    fig1.add_vline(x=overall_stats['mean'], line_dash="dash", line_color="red", 
                   annotation_text=f"整體平均: {overall_stats['mean']:.2f}")
    
    # 2. 評分次數 vs 平均分數散點圖
    fig2 = px.scatter(
        teacher_stats,
        x='評核次數',
        y='平均分數',
        size='標準差',
        hover_data=['最低分', '最高分', '中位數'],
        title='教師評核次數 vs 平均評分',
        labels={'評核次數': '評核次數', '平均分數': '平均評分', '標準差': '評分變異性'}
    )
    fig2.add_hline(y=overall_stats['mean'], line_dash="dash", line_color="red",
                   annotation_text=f"整體平均: {overall_stats['mean']:.2f}")
    
    # 3. 評分一致性分析
    fig3 = px.scatter(
        teacher_stats,
        x='平均分數',
        y='標準差',
        size='評核次數',
        hover_data=['最低分', '最高分', '中位數'],
        title='教師評分一致性分析',
        labels={'平均分數': '平均評分', '標準差': '評分標準差', '評核次數': '評核次數'}
    )
    
    # 4. 前10名高評分教師
    top_teachers = teacher_stats.nlargest(min(10, len(teacher_stats)), '平均分數')
    teacher_name_col = top_teachers.index.name if top_teachers.index.name else '教師'
    fig4 = px.bar(
        top_teachers.reset_index(),
        x=teacher_name_col,
        y='平均分數',
        title='前10名高評分教師',
        labels={teacher_name_col: '教師姓名', '平均分數': '平均評分'}
    )
    fig4.update_xaxes(tickangle=45)
    
    # 5. 前10名低評分教師
    bottom_teachers = teacher_stats.nsmallest(min(10, len(teacher_stats)), '平均分數')
    fig5 = px.bar(
        bottom_teachers.reset_index(),
        x=teacher_name_col,
        y='平均分數',
        title='前10名低評分教師',
        labels={teacher_name_col: '教師姓名', '平均分數': '平均評分'}
    )
    fig5.update_xaxes(tickangle=45)
    
    return fig1, fig2, fig3, fig4, fig5

def create_epa_item_analysis(analysis_results):
    """分析各EPA項目的評分模式"""
    
    df = analysis_results['processed_data']
    
    # 按EPA項目分析評分分布
    epa_stats = df.groupby('EPA評核項目')['教師評核EPA等級'].agg([
        'count', 'mean', 'std', 'min', 'max'
    ]).round(2)
    
    epa_stats.columns = ['評核次數', '平均分數', '標準差', '最低分', '最高分']
    
    # EPA項目評分分布圖
    fig = px.box(
        df,
        x='EPA評核項目',
        y='教師評核EPA等級',
        title='各EPA項目評分分布',
        labels={'EPA評核項目': 'EPA項目', '教師評核EPA等級': '評分'}
    )
    fig.update_xaxes(tickangle=45)
    
    return fig, epa_stats

def show_teacher_scoring_analysis():
    """顯示教師評分分析主頁面 - 簡化版，專注於評分級距分析"""
    
    st.header("📊 教師評分級距分析")
    st.markdown("分析所有教師和各科的評分級距分布")
    
    # 資料載入
    if 'teacher_analysis_data' not in st.session_state:
        st.warning("請先在「老師評分分析」頁面載入資料")
        return
    
    df = st.session_state['teacher_analysis_data']
    
    # 處理資料
    with st.spinner("正在處理資料..."):
        df_processed = process_teacher_data(df)
    
    if df_processed is None:
        st.error("資料處理失敗，請檢查資料格式")
        return
    
    # 顯示基本統計
    st.subheader("📈 基本統計")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總評核次數", f"{len(df_processed):,}")
    with col2:
        st.metric("參與教師數", df_processed['教師'].nunique())
    with col3:
        st.metric("EPA項目數", df_processed['EPA評核項目'].nunique())
    with col4:
        st.metric("整體平均分數", f"{df_processed['教師評核EPA等級'].mean():.2f}")
    
    # 教師評分級距分析
    st.subheader("👨‍🏫 所有教師評分級距")
    
    # 創建教師評分箱線圖
    fig_teachers = px.box(
        df_processed,
        x='教師',
        y='教師評核EPA等級',
        title='各教師評分級距分布',
        labels={'教師': '教師姓名', '教師評核EPA等級': '評分'},
        color_discrete_sequence=['#1f77b4']
    )
    fig_teachers.update_xaxes(tickangle=45)
    fig_teachers.update_layout(height=600)
    
    st.plotly_chart(fig_teachers, width="stretch")
    
    # 各科評分級距分析
    st.subheader("🏥 各科評分級距")
    
    # 創建EPA項目評分箱線圖
    fig_epa = px.box(
        df_processed,
        x='EPA評核項目',
        y='教師評核EPA等級',
        title='各EPA項目評分級距分布',
        labels={'EPA評核項目': 'EPA項目', '教師評核EPA等級': '評分'},
        color_discrete_sequence=['#ff7f0e']
    )
    fig_epa.update_xaxes(tickangle=45)
    fig_epa.update_layout(height=600)
    
    st.plotly_chart(fig_epa, width="stretch")
    
    # 教師評分統計表
    st.subheader("📋 教師評分統計摘要")
    
    teacher_stats = df_processed.groupby('教師')['教師評核EPA等級'].agg([
        'count', 'mean', 'std', 'min', 'max', 'median'
    ]).round(2)
    teacher_stats.columns = ['評核次數', '平均分數', '標準差', '最低分', '最高分', '中位數']
    
    # 添加篩選選項
    col1, col2 = st.columns(2)
    with col1:
        min_evaluations = st.slider("最少評核次數", 1, int(teacher_stats['評核次數'].max()), 5)
    with col2:
        sort_by = st.selectbox("排序方式", ["平均分數", "評核次數", "標準差"], index=0)
    
    # 篩選和排序
    filtered_stats = teacher_stats[teacher_stats['評核次數'] >= min_evaluations].sort_values(sort_by, ascending=False)
    
    st.dataframe(filtered_stats)
    
    # EPA項目評分統計表
    st.subheader("📋 EPA項目評分統計摘要")
    
    epa_stats = df_processed.groupby('EPA評核項目')['教師評核EPA等級'].agg([
        'count', 'mean', 'std', 'min', 'max', 'median'
    ]).round(2)
    epa_stats.columns = ['評核次數', '平均分數', '標準差', '最低分', '最高分', '中位數']
    
    st.dataframe(epa_stats.sort_values('平均分數', ascending=False))

def process_teacher_data(df):
    """處理教師資料"""
    if df is None or df.empty:
        return None
    
    # 檢查並統一教師欄位名稱
    teacher_column = None
    if '教師' in df.columns:
        teacher_column = '教師'
    elif '評核老師' in df.columns:
        teacher_column = '評核老師'
    elif '電子郵件地址' in df.columns:
        teacher_column = '電子郵件地址'
        df = df.copy()
        df['教師'] = df['電子郵件地址']
        teacher_column = '教師'
    else:
        st.error("找不到教師欄位，請確認資料包含「教師」、「評核老師」或「電子郵件地址」欄位")
        return None
    
    # 確保必要的欄位存在
    required_columns = [teacher_column, '教師評核EPA等級', 'EPA評核項目']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"缺少必要欄位：{missing_columns}")
        return None
    
    # 處理EPA等級資料
    df_processed = df.copy()
    
    # 確保評分欄位是數值型
    if df_processed['教師評核EPA等級'].dtype == 'object':
        df_processed['教師評核EPA等級'] = df_processed['教師評核EPA等級'].apply(process_epa_level)
    else:
        df_processed['教師評核EPA等級'] = pd.to_numeric(df_processed['教師評核EPA等級'], errors='coerce')
    
    # 移除無效的評分資料
    df_processed = df_processed.dropna(subset=['教師評核EPA等級'])
    df_processed = df_processed[df_processed['教師評核EPA等級'] > 0]
    
    # 統一使用「教師」欄位名稱
    if teacher_column != '教師':
        df_processed['教師'] = df_processed[teacher_column]
    
    return df_processed

def show_teacher_comparison():
    """顯示教師比較分析"""
    
    st.header("🔄 教師評分比較分析")
    
    if 'teacher_analysis_data' not in st.session_state:
        st.warning("請先在「老師評分分析」頁面載入資料")
        return
    
    df = st.session_state['teacher_analysis_data']
    
    # 處理資料
    df_processed = df.copy()
    
    # 檢查並統一教師欄位名稱
    teacher_column = None
    if '教師' in df_processed.columns:
        teacher_column = '教師'
    elif '評核老師' in df_processed.columns:
        teacher_column = '評核老師'
    elif '電子郵件地址' in df_processed.columns:
        teacher_column = '電子郵件地址'
        df_processed['教師'] = df_processed['電子郵件地址']
        teacher_column = '教師'
    else:
        st.error("找不到教師欄位，請確認資料包含「教師」、「評核老師」或「電子郵件地址」欄位")
        return
    
    df_processed['教師評核EPA等級'] = df_processed['教師評核EPA等級'].apply(process_epa_level)
    df_processed = df_processed.dropna(subset=['教師評核EPA等級'])
    df_processed = df_processed[df_processed['教師評核EPA等級'] > 0]
    
    # 教師選擇
    teachers = df_processed[teacher_column].unique()
    selected_teachers = st.multiselect("選擇要比較的教師", teachers, default=teachers[:5])
    
    if len(selected_teachers) < 2:
        st.warning("請至少選擇2位教師進行比較")
        return
    
    # 篩選資料
    comparison_data = df_processed[df_processed[teacher_column].isin(selected_teachers)]
    
    # 創建比較圖表
    fig = px.box(
        comparison_data,
        x=teacher_column,
        y='教師評核EPA等級',
        title='教師評分比較',
        labels={teacher_column: '教師姓名', '教師評核EPA等級': '評分'}
    )
    fig.update_xaxes(tickangle=45)
    
    st.plotly_chart(fig, width="stretch")
    
    # 統計比較表
    comparison_stats = comparison_data.groupby(teacher_column)['教師評核EPA等級'].agg([
        'count', 'mean', 'std', 'min', 'max'
    ]).round(2)
    
    comparison_stats.columns = ['評核次數', '平均分數', '標準差', '最低分', '最高分']
    st.dataframe(comparison_stats.sort_values('平均分數', ascending=False))
