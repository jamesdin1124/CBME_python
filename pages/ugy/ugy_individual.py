"""
UGY 個別學生分析模組
提供個別學生分析功能（雷達圖功能已移除）
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import plotly.express as px
import numpy as np
from pages.ugy.ugy_data.ugy_epa_google_sheets import display_student_data

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """用於自然排序的鍵函數"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]

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
        '5': 5
    }
    
    return level_map.get(value, 0)

# create_individual_radar_chart 函數已移除

def create_student_trend_chart(student_data, student_name):
    """創建學生梯次分數趨勢圖"""
    try:
        if student_data.empty:
            return None
        
        # 檢查是否有梯次和分數資料
        if '梯次' not in student_data.columns:
            st.warning("沒有找到梯次資料，無法創建趨勢圖")
            return None
        
        # 找出 EPA 相關欄位
        epa_columns = [col for col in student_data.columns if 'EPA' in col and '等級' in col]
        if not epa_columns:
            st.warning("沒有找到 EPA 評核資料，無法創建趨勢圖")
            return None
        
        # 準備趨勢圖資料
        trend_data = []
        
        for _, row in student_data.iterrows():
            batch = row.get('梯次', '')
            for col in epa_columns:
                score = convert_level_to_score(row[col])
                if score > 0:
                    epa_name = col.replace('教師評核', '').replace('EPA等級', '').replace('_數值', '')
                    trend_data.append({
                        '梯次': batch,
                        'EPA項目': epa_name,
                        '分數': score
                    })
        
        if not trend_data:
            st.warning("沒有找到有效的分數資料")
            return None
        
        trend_df = pd.DataFrame(trend_data)
        
        # 創建折線圖
        fig = px.line(
            trend_df,
            x='梯次',
            y='分數',
            color='EPA項目',
            title=f"{student_name} - EPA評核分數趨勢圖",
            markers=True,
            line_shape='linear'
        )
        
        # 更新布局
        fig.update_layout(
            height=500,
            xaxis_title="梯次",
            yaxis_title="評核分數",
            yaxis=dict(range=[0, 5.5]),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        
        return fig
        
    except Exception as e:
        st.error(f"創建趨勢圖時發生錯誤：{str(e)}")
        return None

def display_teacher_comments(student_data, student_name):
    """顯示老師評語"""
    try:
        if student_data.empty:
            st.warning("沒有找到學生資料")
            return
        
        # 尋找評語相關欄位
        comment_columns = [col for col in student_data.columns if any(keyword in col for keyword in ['評語', '回饋', '建議', 'comment', 'feedback'])]
        
        if not comment_columns:
            st.info("沒有找到老師評語欄位")
            return
        
        # 顯示評語
        for col in comment_columns:
            comments = student_data[col].dropna().unique()
            if len(comments) > 0:
                st.write(f"**{col}：**")
                for comment in comments:
                    if str(comment).strip() and str(comment) != 'nan':
                        st.write(f"- {comment}")
                st.write("---")
        
        # 如果沒有找到任何評語
        if not any(student_data[col].dropna().unique().size > 0 for col in comment_columns):
            st.info("目前沒有老師評語")
            
    except Exception as e:
        st.error(f"顯示老師評語時發生錯誤：{str(e)}")

# create_comparison_radar_chart 函數已移除

def calculate_average_scores_by_level_and_epa(df):
    """計算所有學生按階層和EPA項目的平均分數"""
    try:
        if df.empty:
            return None
        
        # 檢查必要的欄位
        required_columns = ['階層', '教師評核EPA等級_數值']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.warning(f"缺少必要欄位：{missing_columns}")
            return None
        
        # 找出所有EPA相關欄位
        epa_columns = [col for col in df.columns if 'EPA' in col and '等級' in col and '_數值' in col]
        
        if not epa_columns:
            st.warning("沒有找到EPA評核數值欄位")
            return None
        
        # 準備資料
        results = []
        
        for _, row in df.iterrows():
            level = row.get('階層', '')
            if pd.isna(level) or level == '':
                continue
                
            for epa_col in epa_columns:
                score = row[epa_col]
                if pd.isna(score) or score == 0:
                    continue
                
                # 提取EPA項目名稱
                epa_name = epa_col.replace('教師評核', '').replace('EPA等級_數值', '').replace('_數值', '')
                
                results.append({
                    '階層': level,
                    'EPA項目': epa_name,
                    '分數': score
                })
        
        if not results:
            st.warning("沒有找到有效的分數資料")
            return None
        
        # 轉換為DataFrame並計算平均分數
        results_df = pd.DataFrame(results)
        average_df = results_df.groupby(['階層', 'EPA項目'])['分數'].agg(['mean', 'count']).reset_index()
        average_df.columns = ['階層', 'EPA項目', '平均分數', '評核次數']
        average_df['平均分數'] = average_df['平均分數'].round(2)
        
        return average_df
        
    except Exception as e:
        st.error(f"計算平均分數時發生錯誤：{str(e)}")
        return None

def display_average_scores_table(df):
    """顯示所有學生各階層各EPA項目的平均分數表格"""
    try:
        st.subheader("📊 所有學生各階層EPA平均分數")
        
        # 計算平均分數
        average_df = calculate_average_scores_by_level_and_epa(df)
        
        if average_df is None or average_df.empty:
            st.warning("無法計算平均分數")
            return
        
        # 顯示統計資訊
        total_records = len(average_df)
        unique_levels = average_df['階層'].nunique()
        unique_epas = average_df['EPA項目'].nunique()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("總記錄數", total_records)
        with col2:
            st.metric("階層數", unique_levels)
        with col3:
            st.metric("EPA項目數", unique_epas)
        
        # 創建樞紐表格格式
        pivot_df = average_df.pivot(index='EPA項目', columns='階層', values='平均分數')
        
        # 填補NaN值
        pivot_df = pivot_df.fillna('-')
        
        # 顯示表格
        st.dataframe(
            pivot_df,
            width="stretch",
            height=400
        )
        
        # 顯示詳細資料
        with st.expander("📋 詳細資料", expanded=False):
            st.dataframe(average_df, width="stretch")
        
        # 顯示階層統計
        st.subheader("📈 階層統計")
        level_stats = average_df.groupby('階層').agg({
            '平均分數': ['mean', 'min', 'max', 'count'],
            '評核次數': 'sum'
        }).round(2)
        
        level_stats.columns = ['平均分數_平均', '平均分數_最低', '平均分數_最高', 'EPA項目數', '總評核次數']
        st.dataframe(level_stats, width="stretch")
        
    except Exception as e:
        st.error(f"顯示平均分數表格時發生錯誤：{str(e)}")

def show_individual_student_analysis(df):
    """顯示個別學生分析的主要函數"""
    
    st.markdown("<h1 style='color:#1E90FF; font-size:32px;'>個別學生分析</h1>", unsafe_allow_html=True)

    # 直接使用原始資料，不進行篩選
    student_filter_df = df.copy()
    
    # 檢查資料
    if student_filter_df.empty:
        st.warning("沒有可用的資料")
        return
    
    # 顯示資料統計
    st.info(f"共找到 {len(student_filter_df)} 筆資料")
    
    # 直接顯示個別學生分析，移除分析模式選擇
    
    # 檢查可用的學生識別欄位
    if '學員姓名' in student_filter_df.columns:
        student_name_column = '學員姓名'
    elif '姓名' in student_filter_df.columns:
        student_name_column = '姓名'
    else:
        st.error("資料中沒有找到學生姓名欄位")
        return
    
    all_students = sorted(student_filter_df[student_name_column].unique().tolist())
    
    if not all_students:
        st.warning("沒有找到學生資料")
        return
    
    # 根據使用者角色決定學生選擇方式
    user_role = st.session_state.get('role', None)
    logged_in_user_name = st.session_state.get('user_name', None)
    
    # 學生選擇邏輯
    if user_role == 'student':
        # 學生帳號只能看到自己的資料
        if logged_in_user_name and logged_in_user_name in all_students:
            selected_student = logged_in_user_name
            st.info(f"學生帳號：已自動選擇您的資料 - {selected_student}")
        else:
            st.warning(f"找不到您的資料，登入姓名：{logged_in_user_name}")
            return
    else:
        # 住院醫師、主治醫師、管理員可以自由選擇學生
        st.subheader("請選擇要分析的學生")
        
        # 添加搜尋功能
        search_term = st.text_input("搜尋學生姓名", placeholder="輸入學生姓名進行搜尋...")
        
        # 根據搜尋條件過濾學生名單
        if search_term:
            filtered_students = [student for student in all_students 
                               if search_term.lower() in student.lower()]
        else:
            filtered_students = all_students
        
        if not filtered_students:
            st.warning("沒有找到符合搜尋條件的學生")
            return
        
        # 學生選擇下拉選單
        selected_student = st.selectbox(
            "選擇學生",
            options=filtered_students,
            index=0,
            help=f"共 {len(filtered_students)} 位學生可選擇"
        )
        
        # 顯示選擇的學生資訊
        st.info(f"已選擇學生：{selected_student}")
    
    # 取得該學生的資料
    student_data = student_filter_df[student_filter_df[student_name_column] == selected_student]
    
    if not student_data.empty:
        # 顯示學生姓名（與原始版本一致）
        student_name = student_data['學員姓名'].iloc[0] if '學員姓名' in student_data.columns else selected_student
        st.subheader(f"學生: {student_name} ({selected_student})")
        
        # 顯示學生基本統計資訊（與原始版本一致）
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("總評核數", len(student_data))
        with col2:
            unique_epa_items = len(student_data['EPA評核項目'].unique()) if 'EPA評核項目' in student_data.columns else 0
            st.metric("EPA項目數", unique_epa_items)
        with col3:
            unique_batches = len(student_data['梯次'].unique()) if '梯次' in student_data.columns else 0
            st.metric("梯次數", unique_batches)
        with col4:
            if '教師評核EPA等級_數值' in student_data.columns:
                avg_score = student_data['教師評核EPA等級_數值'].mean()
                st.metric("平均分數", f"{avg_score:.2f}")
            else:
                st.metric("平均分數", "N/A")
        
        # 顯示該學生的資料（與原始版本一致）
        with st.expander("學生評核資料", expanded=True):
            st.dataframe(student_data)
        
        # 雷達圖功能已移除
        
        # 顯示學生分析資料（使用原始的 display_student_data 函數）
        standard_epa_categories = sorted(student_data['EPA評核項目'].unique().tolist()) if 'EPA評核項目' in student_data.columns else []
        display_student_data(student_data, selected_student, standard_categories=standard_epa_categories)
        
    else:
        st.warning("沒有找到該學生的資料")

def show_ugy_student_analysis():
    """顯示 UGY 個別學生分析的主要函數"""
    # 檢查是否有處理後的資料
    if 'processed_df' not in st.session_state:
        st.warning("請先在「學生總覽」頁面按「重新載入 Google Sheet 資料」按鈕載入資料")
        return
    
    # 從 session_state 取得資料
    df = st.session_state.get('processed_df')
    
    if df is None or df.empty:
        st.warning("沒有可用的資料進行分析，請先在「學生總覽」頁面按「重新載入 Google Sheet 資料」按鈕載入資料")
        return
    
    # 顯示個別學生分析
    show_individual_student_analysis(df)
