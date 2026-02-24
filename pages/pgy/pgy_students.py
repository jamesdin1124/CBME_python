import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re

def analyze_student_performance(df, student_id_col, score_cols):
    try:
        # 取得所有成績欄位的平均值
        avg_scores = df[score_cols].mean()
        
        # 建立成績趨勢圖
        fig_trend = go.Figure()
        for col in score_cols:
            fig_trend.add_trace(
                go.Scatter(
                    x=df['檔案名稱'],
                    y=df[col],
                    name=col,
                    mode='lines+markers'
                )
            )
        fig_trend.update_layout(
            title="成績趨勢圖",
            xaxis_title="考試檔案",
            yaxis_title="分數",
            height=500
        )
        
        # 建立雷達圖
        fig_radar = go.Figure()
        fig_radar.add_trace(
            go.Scatterpolar(
                r=avg_scores,
                theta=score_cols,
                fill='toself',
                name='平均成績'
            )
        )
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="成績分布雷達圖",
            height=500
        )
        
        return fig_trend, fig_radar, avg_scores
        
    except Exception as e:
        st.error(f"分析資料時發生錯誤：{str(e)}")
        return None, None, None

def show_analysis_section(df):
    """顯示分析區段的函數"""
    
    st.header("學員個別分析")
    
    if df is None:
        st.warning("請先載入資料")
        return
        
    # 從 session state 獲取合併後的資料
    if 'merged_data' not in st.session_state:
        st.warning('請先在側邊欄合併 Excel 檔案')
        return
        
    df = st.session_state.merged_data
    
    st.subheader("學員成績分析")
    
    # 1. 三層篩選
    filtered_df = df.copy()  # 創建一個資料副本用於篩選
    
    # 臨床訓練計劃多選
    if '臨床訓練計畫' in df.columns:
        training_programs = st.multiselect(
            "選擇臨床訓練計畫",
            options=df['臨床訓練計畫'].unique().tolist(),
            key='training_programs'
        )
        if training_programs:
            filtered_df = filtered_df[filtered_df['臨床訓練計畫'].isin(training_programs)]
    
    # 修改訓練階段期間的篩選邏輯
    if '開始日期' in filtered_df.columns and '結束日期' in filtered_df.columns:
        # 使用日期選擇器來篩選期間
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "開始日期",
                min_value=filtered_df['開始日期'].min(),
                max_value=filtered_df['結束日期'].max(),
                value=filtered_df['開始日期'].min()
            )
        with col2:
            end_date = st.date_input(
                "結束日期",
                min_value=filtered_df['開始日期'].min(),
                max_value=filtered_df['結束日期'].max(),
                value=filtered_df['結束日期'].max()
            )
        
        # 篩選日期範圍內的資料
        filtered_df = filtered_df[
            (filtered_df['開始日期'].dt.date <= end_date) & 
            (filtered_df['結束日期'].dt.date >= start_date)
        ]
    
    # 選擇學員（單選）
    if '學員' in filtered_df.columns:
        student_list = sorted(filtered_df['學員'].unique().tolist())
        if student_list:
            selected_student = st.selectbox(
                "選擇學員",
                options=student_list,
                key='selected_student'
            )
            
            if selected_student:
                student_data = filtered_df[filtered_df['學員'] == selected_student]
                
                # 作業完成狀況
                st.subheader("作業完成狀況")
                
                # 取得該學員所有的檔案名稱並排序
                assignments = sorted(student_data['檔案名稱'].unique())
                
                # 使用 expander 顯示所有作業
                with st.expander("查看所有作業", expanded=True):
                    for assignment in assignments:
                        # 取得該作業的資料
                        # 根據檔案名稱篩選出該學員的作業資料
                        assignment_data = student_data[student_data['檔案名稱'] == assignment]
                        
                        # 判斷是否完成
                        is_completed = False
                        if '表單簽核流程' in assignment_data.columns:
                            # 取得最後一個非空值的簽核流程
                            sign_flow = assignment_data['表單簽核流程'].dropna().iloc[-1] if not assignment_data['表單簽核流程'].dropna().empty else ""
                            
                            # 檢查作業名稱中是否包含特定關鍵字，以判斷作業類型
                            if any(keyword in assignment for keyword in ["教學住診", "教學門診", "夜間學習"]):
                                # 教學住診和教學門診需要三個右括號
                                is_completed = sign_flow.count(")") >= 3
                            elif "CEX" in assignment:
                                is_completed = sign_flow.count(")") >= 2
                            elif "核心技能" in assignment:
                                # 核心技能需要一個右括號
                                is_completed = sign_flow.endswith(")")
                            elif "coreEPA" in assignment:
                                # coreEPA 不能出現兩次"未指定"
                                is_completed = sign_flow.count("未指定") < 2
                        
                        # 顯示作業狀態
                        status_emoji = "✅" if is_completed else "❌"
                        st.write(f"{status_emoji} {assignment}")
                
                # 核心技能分析
                if any('五年級' in str(plan) for plan in student_data['臨床訓練計畫'].values):
                    st.subheader("核心技能分析")
                    
                    # 篩選核心技能相關資料
                    core_skill_data = student_data[
                        student_data['檔案名稱'].str.contains('核心技能', na=False)
                    ]
                    
                    if not core_skill_data.empty:
                        # 建立左右欄位
                        left_col, right_col = st.columns([3, 2])
                        
                        with left_col:
                            # 準備雷達圖資料
                            skill_scores = {}
                            for _, row in core_skill_data.iterrows():
                                filename = row['檔案名稱']
                                match = re.search(r'^臨床核心技能\s*(.*?)\.xls', filename)
                                if match:
                                    skill_name = match.group(1)
                                    skill_key = skill_name
                                    
                                    if pd.notna(row['教師評核']):
                                        try:
                                            score = float(row['教師評核'])
                                            skill_scores[skill_key] = score
                                        except (ValueError, TypeError):
                                            st.warning(f"無法轉換評核分數：{row['教師評核']}")
                            
                            if skill_scores:
                                # 取得當前學生的訓練計畫
                                current_training_program = student_data['臨床訓練計畫'].iloc[0]
                                
                                # 篩選同訓練計畫的同儕資料
                                peer_df = filtered_df[filtered_df['臨床訓練計畫'] == current_training_program]
                                peer_df = peer_df[peer_df['學員'] != selected_student]  # 排除當前學生
                                
                                # 計算同儕平均
                                peer_averages = {}
                                for filename in core_skill_data['檔案名稱'].unique():
                                    match = re.search(r'^臨床核心技能\s*(.*?)\.xls', filename)
                                    if match:
                                        skill_name = match.group(1)
                                        skill_key = skill_name
                                        
                                        # 計算該技能的平均分數
                                        peer_skill_data = peer_df[
                                            peer_df['檔案名稱'] == filename
                                        ]
                                        if not peer_skill_data.empty:
                                            peer_scores = pd.to_numeric(peer_skill_data['教師評核'], errors='coerce')
                                            peer_averages[skill_key] = peer_scores.mean()
                                
                                # 確保數據點首尾相連
                                skills = list(skill_scores.keys())
                                scores = [skill_scores[skill] for skill in skills]
                                peer_scores = [peer_averages.get(skill, 0) for skill in skills]
                                
                                skills_closed = skills + [skills[0]]
                                scores_closed = scores + [scores[0]]
                                peer_scores_closed = peer_scores + [peer_scores[0]]
                                
                                # 建立雷達圖
                                fig = go.Figure()
                                
                                # 先畫同儕平均（深褐色）
                                fig.add_trace(go.Scatterpolar(
                                    r=peer_scores_closed,
                                    theta=skills_closed,
                                    name='同儕平均',
                                    line=dict(color='rgba(101, 67, 33, 1)', width=2),
                                    fill='none'
                                ))
                                
                                # 後畫學生本人（紅色）
                                fig.add_trace(go.Scatterpolar(
                                    r=scores_closed,
                                    theta=skills_closed,
                                    name=selected_student,
                                    fill='toself',
                                    fillcolor='rgba(255, 0, 0, 0.2)',
                                    line=dict(color='rgba(255, 0, 0, 1)', width=2)
                                ))
                                
                                fig.update_layout(
                                    polar=dict(
                                        radialaxis=dict(
                                            visible=True,
                                            range=[0, 5]
                                        )
                                    ),
                                    showlegend=True,
                                    title=f"{selected_student} - 核心技能評核",
                                    height=500
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning(f"沒有找到 {selected_student} 的有效評核分數")
                        
                        with right_col:
                            st.markdown("### 教師評語")
                            for _, row in core_skill_data.iterrows():
                                filename = row['檔案名稱']
                                match = re.search(r'^臨床核心技能\s*(.*?)\.xls', filename)
                                if match:
                                    skill_name = match.group(1)
                                    if '教師評語與總結' in row and pd.notna(row['教師評語與總結']):
                                        st.markdown(f"**{skill_name}**：{row['教師評語與總結']}")
                    else:
                        st.warning("未找到核心技能相關資料")
                
                # EPA教師評核成績
                st.subheader("EPA教師評核成績")
                
                # 只篩選包含 'EPA' 的欄位，但排除包含 '教師評量' 的欄位
                score_cols = [col for col in student_data.columns if 'EPA' in col and '教師評量' not in col]
                
                if score_cols:
                    # 準備學生和同儕的數據
                    student_scores = []
                    peer_scores = []
                    display_labels = []
                    evaluators = []
                    comments_data = {}
                    
                    # 取得當前學生的訓練計畫
                    current_training_program = student_data['臨床訓練計畫'].iloc[0]
                    
                    # 篩選同訓練計畫的同儕資料
                    peer_df = filtered_df[filtered_df['臨床訓練計畫'] == current_training_program]
                    peer_df = peer_df[peer_df['學員'] != selected_student]
                    
                    for score_col in score_cols:
                        # 計算同訓練計畫的同儕平均分數
                        peer_mean = peer_df[score_col].mean()
                        # 計算學生平均分數
                        student_mean = student_data[score_col].mean()
                        
                        if not pd.isna(student_mean) and not pd.isna(peer_mean):
                            student_scores.append(student_mean)
                            peer_scores.append(peer_mean)
                            display_labels.append(score_col.split('(')[0].strip())
                            
                            # 收集評語和建議
                            comment_cols = [col for col in student_data.columns if '評語' in col or '建議' in col]
                            comments = []
                            for comment_col in comment_cols:
                                comment = student_data[comment_col].iloc[0] if not student_data[comment_col].empty else None
                                if pd.notna(comment):
                                    comments.append(f"{comment_col}: {comment}")
                            if comments:
                                comments_data[score_col] = '\n'.join(comments)
                    
                    # 取得初評醫師簽名及複評醫師簽名
                    evaluators = []
                    if '初評醫師簽名' in student_data.columns:
                        evaluators.extend(student_data['初評醫師簽名'].dropna().unique())
                    if '主治醫師簽名' in student_data.columns:
                        evaluators.extend(student_data['主治醫師簽名'].dropna().unique())
                    evaluators_text = '<br>'.join(evaluators) if evaluators else '無資料'
                    
                    # 1. 繪製雷達圖
                    if student_scores and peer_scores:
                        fig = go.Figure()
                        
                        # 確保數據點首尾相連
                        display_labels_closed = display_labels + [display_labels[0]]
                        peer_scores_closed = peer_scores + [peer_scores[0]]
                        student_scores_closed = student_scores + [student_scores[0]]
                        
                        # 先畫同儕平均（深褐色）
                        fig.add_trace(go.Scatterpolar(
                            r=peer_scores_closed,
                            theta=display_labels_closed,
                            name='同儕平均',
                            line=dict(color='rgba(101, 67, 33, 1)', width=2),
                            fill='none'
                        ))
                        
                        # 後畫學生本人（紅色）
                        fig.add_trace(go.Scatterpolar(
                            r=student_scores_closed,
                            theta=display_labels_closed,
                            name=f'{selected_student}',
                            fill='toself',
                            fillcolor='rgba(255, 0, 0, 0.2)',
                            line=dict(color='rgba(255, 0, 0, 1)', width=2)
                        ))
                        
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 5]
                                )
                            ),
                            title={
                                'text': f"EPA評核成績雷達圖比較<br><br><sub>評核醫師：{evaluators_text}</sub>",
                                'xanchor': 'center',
                                'x': 0.5,
                                'y': 0.95,
                                'yanchor': 'top'
                            },
                            margin=dict(t=150),
                            showlegend=True
                        )
                        
                        st.plotly_chart(fig)
                        
                        # 2. 顯示個別分數比較
                        st.subheader("EPA評核分數比較")
                        for i, label in enumerate(display_labels):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(
                                    label,
                                    f"{student_scores[i]:.1f}",
                                    f"{student_scores[i] - peer_scores[i]:+.1f} vs 同儕平均"
                                )
                            with col2:
                                st.metric("同儕平均", f"{peer_scores[i]:.1f}")
                        
                        # 3. 顯示評語與建議
                        if comments_data:
                            with st.expander("查看評語與建議", expanded=False):
                                # 找到對應的 EPA 檔案資料
                                epa_data = student_data[student_data['檔案名稱'].str.contains('EPA', na=False)].iloc[0:1]
                                
                                if not epa_data.empty:
                                    # 取得評核相關資訊
                                    if '初評回饋' in epa_data.columns:
                                        initial_feedback = epa_data['初評回饋'].iloc[0]
                                        if pd.notna(initial_feedback):
                                            st.markdown("**初評回饋：**")
                                            st.text(initial_feedback)
                                        
                                    if '初評醫師簽名' in epa_data.columns:
                                        initial_doctor = epa_data['初評醫師簽名'].iloc[0]
                                        if pd.notna(initial_doctor):
                                            st.markdown("**初評醫師：**")
                                            st.text(initial_doctor)
                                        
                                    if '複評回饋' in epa_data.columns:
                                        review_feedback = epa_data['複評回饋'].iloc[0]
                                        if pd.notna(review_feedback):
                                            st.markdown("**複評回饋：**")
                                            st.text(review_feedback)
                                        
                                    if '主治醫師簽名' in epa_data.columns:
                                        attending_doctor = epa_data['主治醫師簽名'].iloc[0]
                                        if pd.notna(attending_doctor):
                                            st.markdown("**主治醫師：**")
                                            st.text(attending_doctor)
                    else:
                        st.warning("沒有足夠的評核數據來產生雷達圖")
                
                # 4. 教師評語
                comment_cols = [col for col in student_data.columns if '評語' in col or '建議' in col]
                if comment_cols:
                    st.subheader("教師評語")
                    
                    # 將相同檔案名稱的評語整合在一起
                    comments_by_file = {}
                    for _, row in student_data[['檔案名稱'] + comment_cols].dropna(how='all', subset=comment_cols).iterrows():
                        filename = row['檔案名稱']
                        if filename not in comments_by_file:
                            comments_by_file[filename] = set()  # 使用集合來避免重複
                        
                        for col in comment_cols:
                            if pd.notna(row[col]):
                                # 將評語內容加入集合中
                                comments_by_file[filename].add((col, row[col]))
                    
                    # 顯示整合後的評語
                    for filename, comments in comments_by_file.items():
                        with st.expander(f"{filename}"):
                            # 將集合轉換為列表並排序，確保顯示順序一致
                            sorted_comments = sorted(list(comments), key=lambda x: x[0])
                            for col, comment in sorted_comments:
                                st.markdown(f"**{col}：**")
                                st.write(comment)

def show_peer_analysis_section():
    """顯示同梯次分析的函數"""
    # 這個函數的實現需要根據你的具體需求來實現
    # 這裡可以添加同梯次分析的相關程式碼
    pass

def main():
    st.title("臨床教師評核系統")
    
    # 移除 tab3，只保留 tab1 和 tab2
    tab1, tab2 = st.tabs(["學員分析", "同梯次分析"])
    
    with tab1:
        show_analysis_section()
    
    with tab2:
        show_peer_analysis_section() 