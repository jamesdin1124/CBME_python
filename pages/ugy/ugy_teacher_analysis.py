"""
UGY 老師分析模組
提供老師評核次數排行榜和老師評核分數outlier分析功能
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from scipy import stats
from collections import Counter
import re

def get_teacher_evaluation_data(df):
    """從資料中提取老師評核相關資訊"""
    try:
        if df.empty:
            return None
        
        # 檢查是否有[教師]欄位
        teacher_column = None
        for col in df.columns:
            if col.strip() == '教師' or col.strip() == '[教師]':
                teacher_column = col
                break
        
        if teacher_column is None:
            st.warning("沒有找到[教師]欄位")
            return None
        
        # 尋找評核分數欄位
        score_columns = []
        for col in df.columns:
            if 'EPA' in col and ('等級' in col or '分數' in col or '評核' in col):
                score_columns.append(col)
        
        if not score_columns:
            st.warning("沒有找到EPA評核分數欄位")
            return None
        
        # 提取老師評核資料
        teacher_data = []
        
        for _, row in df.iterrows():
            teacher_name = row.get(teacher_column, '')
            if pd.notna(teacher_name) and str(teacher_name).strip():
                # 檢查這位老師的所有評核分數
                for score_col in score_columns:
                    score = row.get(score_col, None)
                    if pd.notna(score):
                        # 轉換分數為數值
                        numeric_score = convert_level_to_score(score)
                        if numeric_score > 0:
                            teacher_data.append({
                                '老師姓名': str(teacher_name).strip(),
                                '評核項目': score_col,
                                '原始分數': score,
                                '數值分數': numeric_score,
                                '學生姓名': row.get('學員姓名', row.get('姓名', '')),
                                '梯次': row.get('梯次', ''),
                                '科部': row.get('科部', row.get('臨床訓練計畫', '')),
                                '評核日期': row.get('評核日期', row.get('日期', ''))
                            })
        
        if not teacher_data:
            st.warning("沒有找到有效的老師評核資料")
            return None
        
        return pd.DataFrame(teacher_data)
        
    except Exception as e:
        st.error(f"提取老師評核資料時發生錯誤：{str(e)}")
        return None

def convert_level_to_score(value):
    """將 LEVEL 轉換為數值分數"""
    if pd.isna(value):
        return 0
    
    # 如果已經是數字，直接返回
    if isinstance(value, (int, float)) and 1 <= value <= 5:
        return value
    
    # 嘗試直接轉換為數字
    try:
        num_value = float(value)
        if 1 <= num_value <= 5:
            return num_value
    except (ValueError, TypeError):
        pass
    
    # 轉換為大寫並移除空白
    value = str(value).upper().strip()
    
    # 定義轉換對照表
    level_map = {
        'LEVEL I': 1, 'LEVEL II': 2, 'LEVEL III': 3, 'LEVEL IV': 4, 'LEVEL V': 5,
        'Level I': 1, 'Level II': 2, 'Level III': 3, 'Level IV': 4, 'Level V': 5,
        'level i': 1, 'level ii': 2, 'level iii': 3, 'level iv': 4, 'level v': 5,
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
        'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
        'LEVEL 1': 1, 'LEVEL 2': 2, 'LEVEL 3': 3, 'LEVEL 4': 4, 'LEVEL 5': 5,
        'Level 1': 1, 'Level 2': 2, 'Level 3': 3, 'Level 4': 4, 'Level 5': 5,
        'level 1': 1, 'level 2': 2, 'level 3': 3, 'level 4': 4, 'level 5': 5,
        '1': 1, '2': 2, '3': 3, '4': 4, '5': 5
    }
    
    return level_map.get(value, 0)

def show_teacher_evaluation_ranking(teacher_df):
    """顯示老師評核次數排行榜"""
    try:
        st.subheader("📊 老師評核次數排行榜")
        
        if teacher_df is None or teacher_df.empty:
            st.warning("沒有老師評核資料可供分析")
            return
        
        # 計算每位老師的評核次數
        teacher_stats = teacher_df.groupby('老師姓名').agg({
            '數值分數': ['count', 'mean', 'std', 'min', 'max'],
            '學生姓名': 'nunique'
        }).round(2)
        
        # 扁平化欄位名稱
        teacher_stats.columns = ['評核次數', '平均分數', '分數標準差', '最低分數', '最高分數', '評核學生數']
        teacher_stats = teacher_stats.reset_index()
        
        # 按評核次數排序
        teacher_stats = teacher_stats.sort_values('評核次數', ascending=False)
        
        # 顯示統計摘要
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("總老師數", len(teacher_stats))
        with col2:
            st.metric("總評核次數", teacher_stats['評核次數'].sum())
        with col3:
            st.metric("平均評核次數", f"{teacher_stats['評核次數'].mean():.1f}")
        with col4:
            st.metric("最高評核次數", teacher_stats['評核次數'].max())
        
        # 顯示排行榜表格
        st.markdown("### 🏆 評核次數排行榜")
        
        # 添加排名
        teacher_stats['排名'] = range(1, len(teacher_stats) + 1)
        
        # 重新排列欄位順序
        display_columns = ['排名', '老師姓名', '評核次數', '評核學生數', '平均分數', '分數標準差', '最低分數', '最高分數']
        display_df = teacher_stats[display_columns]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
        
        # 創建評核次數分佈圖
        fig_count = px.bar(
            teacher_stats.head(20),  # 只顯示前20名
            x='老師姓名',
            y='評核次數',
            title="前20名老師評核次數分佈",
            color='評核次數',
            color_continuous_scale='viridis'
        )
        
        fig_count.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig_count, use_container_width=True)
        
        # 創建平均分數分佈圖
        fig_score = px.scatter(
            teacher_stats,
            x='評核次數',
            y='平均分數',
            size='評核學生數',
            hover_name='老師姓名',
            title="老師評核次數 vs 平均分數關係圖",
            color='平均分數',
            color_continuous_scale='plasma'
        )
        
        fig_score.update_layout(height=500)
        st.plotly_chart(fig_score, use_container_width=True)
        
        # 顯示詳細資料
        with st.expander("📋 完整排行榜資料", expanded=False):
            st.dataframe(teacher_stats, use_container_width=True)
        
    except Exception as e:
        st.error(f"顯示老師評核排行榜時發生錯誤：{str(e)}")

def detect_outliers_iqr(data):
    """使用IQR方法檢測outlier"""
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return data[(data < lower_bound) | (data > upper_bound)]

def detect_outliers_zscore(data, threshold=2.5):
    """使用Z-score方法檢測outlier"""
    z_scores = np.abs(stats.zscore(data))
    return data[z_scores > threshold]

def show_teacher_score_outlier_analysis(teacher_df):
    """顯示老師評核分數outlier分析"""
    try:
        st.subheader("🔍 老師評核分數Outlier分析")
        
        if teacher_df is None or teacher_df.empty:
            st.warning("沒有老師評核資料可供分析")
            return
        
        # 選擇分析方法
        analysis_method = st.selectbox(
            "選擇Outlier檢測方法",
            ["IQR方法 (四分位距)", "Z-Score方法 (標準分數)", "兩種方法比較"],
            help="IQR方法：基於四分位距檢測異常值\nZ-Score方法：基於標準分數檢測異常值"
        )
        
        # 按老師分組分析
        teachers = teacher_df['老師姓名'].unique()
        outlier_results = []
        
        for teacher in teachers:
            teacher_data = teacher_df[teacher_df['老師姓名'] == teacher]['數值分數']
            
            if len(teacher_data) < 5:  # 評核次數太少，跳過outlier檢測
                continue
            
            # IQR方法
            if "IQR" in analysis_method or analysis_method == "兩種方法比較":
                iqr_outliers = detect_outliers_iqr(teacher_data)
                iqr_count = len(iqr_outliers)
            else:
                iqr_count = 0
            
            # Z-Score方法
            if "Z-Score" in analysis_method or analysis_method == "兩種方法比較":
                try:
                    zscore_outliers = detect_outliers_zscore(teacher_data)
                    zscore_count = len(zscore_outliers)
                except:
                    zscore_count = 0
            else:
                zscore_count = 0
            
            # 計算統計資訊
            stats_info = {
                '老師姓名': teacher,
                '總評核次數': len(teacher_data),
                '平均分數': teacher_data.mean(),
                '分數標準差': teacher_data.std(),
                '最低分數': teacher_data.min(),
                '最高分數': teacher_data.max(),
                'IQR_Outlier數': iqr_count,
                'ZScore_Outlier數': zscore_count,
                'IQR_Outlier比例': f"{(iqr_count/len(teacher_data)*100):.1f}%" if len(teacher_data) > 0 else "0%",
                'ZScore_Outlier比例': f"{(zscore_count/len(teacher_data)*100):.1f}%" if len(teacher_data) > 0 else "0%"
            }
            
            outlier_results.append(stats_info)
        
        if not outlier_results:
            st.warning("沒有足夠的資料進行outlier分析")
            return
        
        outlier_df = pd.DataFrame(outlier_results)
        
        # 顯示統計摘要
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("分析老師數", len(outlier_df))
        with col2:
            total_outliers_iqr = outlier_df['IQR_Outlier數'].sum()
            st.metric("IQR Outlier總數", total_outliers_iqr)
        with col3:
            total_outliers_zscore = outlier_df['ZScore_Outlier數'].sum()
            st.metric("Z-Score Outlier總數", total_outliers_zscore)
        with col4:
            avg_outlier_rate = (outlier_df['IQR_Outlier數'].sum() / outlier_df['總評核次數'].sum() * 100)
            st.metric("平均Outlier比例", f"{avg_outlier_rate:.1f}%")
        
        # 顯示Outlier分析結果
        st.markdown("### 📊 Outlier分析結果")
        
        # 按Outlier數量排序
        if analysis_method == "兩種方法比較":
            display_columns = ['老師姓名', '總評核次數', '平均分數', '分數標準差', 'IQR_Outlier數', 'IQR_Outlier比例', 'ZScore_Outlier數', 'ZScore_Outlier比例']
        elif "IQR" in analysis_method:
            display_columns = ['老師姓名', '總評核次數', '平均分數', '分數標準差', 'IQR_Outlier數', 'IQR_Outlier比例']
            outlier_df = outlier_df.sort_values('IQR_Outlier數', ascending=False)
        else:
            display_columns = ['老師姓名', '總評核次數', '平均分數', '分數標準差', 'ZScore_Outlier數', 'ZScore_Outlier比例']
            outlier_df = outlier_df.sort_values('ZScore_Outlier數', ascending=False)
        
        display_df = outlier_df[display_columns]
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # 創建Outlier分佈圖
        if analysis_method == "兩種方法比較":
            fig = go.Figure()
            
            # 添加IQR Outlier
            fig.add_trace(go.Bar(
                name='IQR Outlier數',
                x=outlier_df['老師姓名'],
                y=outlier_df['IQR_Outlier數'],
                marker_color='lightblue'
            ))
            
            # 添加Z-Score Outlier
            fig.add_trace(go.Bar(
                name='Z-Score Outlier數',
                x=outlier_df['老師姓名'],
                y=outlier_df['ZScore_Outlier數'],
                marker_color='lightcoral'
            ))
            
            fig.update_layout(
                title="老師Outlier檢測結果比較",
                xaxis_tickangle=-45,
                barmode='group',
                height=500
            )
        else:
            outlier_column = 'IQR_Outlier數' if "IQR" in analysis_method else 'ZScore_Outlier數'
            fig = px.bar(
                outlier_df.head(20),  # 只顯示前20名
                x='老師姓名',
                y=outlier_column,
                title=f"老師{outlier_column}分佈",
                color=outlier_column,
                color_continuous_scale='reds'
            )
            
            fig.update_layout(
                xaxis_tickangle=-45,
                height=500
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示高Outlier比例的老師
        st.markdown("### ⚠️ 需要關注的老師")
        
        if "IQR" in analysis_method or analysis_method == "兩種方法比較":
            high_outlier_teachers = outlier_df[
                (outlier_df['IQR_Outlier數'] >= 3) & 
                (outlier_df['IQR_Outlier比例'].str.replace('%', '').astype(float) >= 20)
            ]
        else:
            high_outlier_teachers = outlier_df[
                (outlier_df['ZScore_Outlier數'] >= 3) & 
                (outlier_df['ZScore_Outlier比例'].str.replace('%', '').astype(float) >= 20)
            ]
        
        if not high_outlier_teachers.empty:
            st.warning(f"發現 {len(high_outlier_teachers)} 位老師的評核分數有較多異常值，建議進一步了解評核標準的一致性")
            st.dataframe(high_outlier_teachers[['老師姓名', '總評核次數', '平均分數', 'IQR_Outlier數', 'IQR_Outlier比例'] if "IQR" in analysis_method else ['老師姓名', '總評核次數', '平均分數', 'ZScore_Outlier數', 'ZScore_Outlier比例']], use_container_width=True)
        else:
            st.success("所有老師的評核分數都在正常範圍內")
        
        # 顯示詳細資料
        with st.expander("📋 完整Outlier分析資料", expanded=False):
            st.dataframe(outlier_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"顯示Outlier分析時發生錯誤：{str(e)}")

def show_ugy_teacher_analysis():
    """顯示UGY老師分析的主要函數"""
    st.markdown("<h1 style='color:#1E90FF; font-size:32px;'>老師分析</h1>", unsafe_allow_html=True)
    
    # 檢查是否有處理後的資料
    if 'processed_df' not in st.session_state:
        st.warning("請先在「學生總覽」頁面載入資料")
        return
    
    # 從 session_state 取得資料
    df = st.session_state.get('processed_df')
    
    if df is None or df.empty:
        st.warning("沒有可用的資料進行分析，請先在「學生總覽」頁面載入資料")
        return
    
    # 顯示資料統計
    st.info(f"共找到 {len(df)} 筆資料")
    
    # 檢查資料欄位
    st.info(f"資料欄位：{list(df.columns)}")
    
    # 提取老師評核資料
    with st.spinner("正在提取老師評核資料..."):
        teacher_df = get_teacher_evaluation_data(df)
    
    if teacher_df is None:
        st.error("無法提取老師評核資料，請檢查資料格式")
        return
    
    st.success(f"成功提取 {len(teacher_df)} 筆老師評核資料，包含 {teacher_df['老師姓名'].nunique()} 位老師")
    
    # 顯示老師名單
    if not teacher_df.empty:
        unique_teachers = teacher_df['老師姓名'].unique()
        st.info(f"找到的老師：{list(unique_teachers)[:10]}{'...' if len(unique_teachers) > 10 else ''}")
    
    # 顯示原始資料
    with st.expander("📋 老師評核原始資料", expanded=False):
        st.dataframe(teacher_df, use_container_width=True)
    
    # 創建分析分頁
    analysis_tab1, analysis_tab2 = st.tabs(["📊 老師評核次數排行榜", "🔍 老師評核分數Outlier分析"])
    
    with analysis_tab1:
        show_teacher_evaluation_ranking(teacher_df)
    
    with analysis_tab2:
        show_teacher_score_outlier_analysis(teacher_df)
