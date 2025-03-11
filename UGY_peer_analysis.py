import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import plotly.express as px
import numpy as np

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """用於自然排序的鍵函數"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]

def convert_level_to_score(value):
    """將 LEVEL 轉換為數值分數"""
    if pd.isna(value):
        return 0
    
    # 轉換為大寫並移除空白
    value = str(value).upper().strip()
    
    # 定義轉換對照表
    level_map = {
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
        'LEVEL 1': 1,
        'LEVEL 2': 2,
        'LEVEL 3': 3,
        'LEVEL 4': 4,
        'LEVEL 5': 5,
        '1': 1,
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5
    }
    
    return level_map.get(value, 0)

def show_UGY_peer_analysis_section(df):
    """顯示UGY同梯次分析的函數"""
    
    st.subheader("UGY同梯次分析")

    # 取得所有可用的臨床訓練計畫
    training_plans = sorted(df['臨床訓練計畫'].unique())
    # 讓使用者選擇要分析的臨床訓練計畫
    selected_training_plan = st.selectbox(
        '請選擇要分析的臨床訓練計畫：',
        training_plans
    )

    # 篩選選定臨床訓練計畫的資料
    df = df[df['臨床訓練計畫'] == selected_training_plan]

    # 取得所有可用的訓練階段期間
    periods = df['訓練階段期間'].unique()
    # 讓使用者選擇要分析的訓練階段期間
    selected_period = st.selectbox(
        '請選擇要分析的訓練階段期間：',
        periods
    )

    # 篩選選定訓練階段期間的資料
    period_data = df[df['訓練階段期間'] == selected_period]
    
    # 在分析開始前先顯示完整的資料表
    st.markdown("### 完整資料表")
    st.dataframe(
        period_data,
        use_container_width=True,
        height=300
    )
    
    # 修改核心技能分析部分
    st.subheader("核心技能分析")

    # 直接使用合併後的資料
    core_skill_data = df[
        (df['訓練階段期間'] == selected_period) &
        (df['檔案名稱'].str.contains('核心技能', na=False))
    ]

    # 加入除錯資訊
    st.write(f"找到的核心技能資料筆數：{len(core_skill_data)}")

    if not core_skill_data.empty:
        # 顯示核心技能資料表
        st.markdown("### 核心技能評核資料")
        
        # 顯示資料表
        st.dataframe(
            core_skill_data,
            use_container_width=True,
            height=200
        )
    else:
        st.warning("未找到核心技能相關資料")

    # 取得所有學員
    students = core_skill_data['學員'].unique()
    
    # 為每個學員建立雷達圖
    for student in students:
        # 建立兩欄佈局
        col1, col2 = st.columns([1, 1])
        
        # 取得該學員的資料
        student_data = core_skill_data[core_skill_data['學員'] == student]
        
        # 取得臨床訓練計畫
        training_plan = student_data['臨床訓練計畫'].iloc[0] if '臨床訓練計畫' in student_data.columns else '未知'
        
        with col1:
            # 準備雷達圖資料
            skill_scores = {}
            for _, row in student_data.iterrows():
                filename = row['檔案名稱']
                match = re.search(r'^臨床核心技能\s*(.*?)\.xls', filename)
                if match:
                    skill_name = match.group(1)
                    skill_key = skill_name
                    
                    if pd.notna(row['教師評核']):
                        try:
                            score = float(row['教師評核'])
                            skill_scores[skill_key] = score # 將評核分數存入字典，只留最後一筆
                        except (ValueError, TypeError):
                            st.warning(f"無法轉換評核分數：{row['教師評核']}")
            
            if skill_scores:
                # 建立雷達圖
                fig = go.Figure()
                
                # 計算同儕平均
                peer_averages = {}
                for filename in core_skill_data['檔案名稱'].unique():
                    match = re.search(r'^臨床核心技能\s*(.*?)\.xls', filename)
                    if match:
                        skill_name = match.group(1)
                        skill_key = skill_name
                        
                        # 計算該技能的平均分數
                        skill_scores_all = core_skill_data[
                            core_skill_data['檔案名稱'] == filename
                        ]['教師評核'].astype(float).mean()
                        
                        peer_averages[skill_key] = skill_scores_all
                
                # 確保數據點首尾相連
                skills = list(skill_scores.keys())
                scores = [skill_scores[skill] for skill in skills]
                peer_scores = [peer_averages[skill] for skill in skills]
                
                skills_closed = skills + [skills[0]]
                scores_closed = scores + [scores[0]]
                peer_scores_closed = peer_scores + [peer_scores[0]]
                
                # 先畫同儕平均（黑色）
                fig.add_trace(go.Scatterpolar(
                    r=peer_scores_closed,
                    theta=skills_closed,
                    name='同儕平均',
                    line=dict(color='rgba(0, 0, 0, 1)', width=2),
                ))
                
                # 後畫學生本人（紅色）
                fig.add_trace(go.Scatterpolar(
                    r=scores_closed,
                    theta=skills_closed,
                    name=student,
                    fill='toself',
                    fillcolor='rgba(255, 0, 0, 0.2)',
                    line=dict(color='rgba(255, 0, 0, 1)', width=2),
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 5]
                        )
                    ),
                    showlegend=True,
                    title=f"{student} ({training_plan}) - 核心技能評核",
                    height=400,
                    width=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"沒有找到 {student} 的有效評核分數")
        
        with col2:
            st.markdown("### 教師評語")
            for _, row in student_data.iterrows():
                filename = row['檔案名稱']
                match = re.search(r'^臨床核心技能\s*(.*?)\.xls', filename)
                if match:
                    skill_name = match.group(1)
                    if '教師評語與總結' in row and pd.notna(row['教師評語與總結']):
                        st.markdown(f"**{skill_name}**：{row['教師評語與總結']}")

    # EPA 分析部分
    st.subheader("EPA 評量比較")
    
    # 從選定訓練階段期間的資料中找出 EPA 相關的資料
    epa_data = period_data[
        period_data['檔案名稱'].str.contains('coreEPA', na=False)
    ]

    if not epa_data.empty:
        # 找出包含 "EPA" 和 "教師評量" 的評分欄位
        score_columns = [col for col in epa_data.columns if 'EPA' in col and '教師評量' in col]
        
        # 顯示 EPA 資料表
        st.markdown("### EPA 評核資料")
        display_columns = [
            '學員', 
            '臨床訓練計畫', 
            '檔案名稱'
        ] + score_columns + [
            '初評回饋：',
            '複評回饋：',
            '教師評語與總結'
        ]
        
        st.dataframe(
            epa_data[display_columns],
            use_container_width=True,
            height=200
        )

        # 取得所有學員
        students = epa_data['學員'].unique()
        
        # 為每個學員建立雷達圖
        for student in students:
            # 建立兩欄佈局
            col1, col2 = st.columns([1, 1])
            
            # 取得該學員的資料
            student_data = epa_data[epa_data['學員'] == student]
            
            # 取得臨床訓練計畫
            training_plan = student_data['臨床訓練計畫'].iloc[0] if '臨床訓練計畫' in student_data.columns else '未知'
            
            with col1:
                # 準備雷達圖資料
                student_scores = []
                peer_scores = []
                display_labels = []
                
                # 取得當前學生的訓練計畫
                current_training_program = student_data['臨床訓練計畫'].iloc[0]
                
                # 篩選同訓練計畫的同儕資料
                peer_df = epa_data[epa_data['臨床訓練計畫'] == current_training_program]
                peer_df = peer_df[peer_df['學員'] != student]  # 排除當前學生
                
                # 使用 score_columns 取得評核分數
                for col in score_columns:
                    try:
                        # 學生分數
                        score = float(student_data[col].iloc[0])
                        student_scores.append(score)
                        
                        # 同儕平均
                        peer_score = peer_df[col].astype(float).mean()
                        peer_scores.append(peer_score)
                        
                        # 從欄位名稱提取 EPA 編號
                        epa_match = re.search(r'EPA(\d+)', col)
                        if epa_match:
                            epa_number = epa_match.group(1)
                            display_labels.append(f"EPA{epa_number}")
                    except (ValueError, TypeError):
                        st.warning(f"無法轉換評核分數：{col}")
                
                if student_scores and peer_scores and display_labels:
                    # 確保數據點首尾相連
                    display_labels_closed = display_labels + [display_labels[0]]
                    student_scores_closed = student_scores + [student_scores[0]]
                    peer_scores_closed = peer_scores + [peer_scores[0]]
                    
                    # 建立雷達圖
                    fig = go.Figure()
                    
                    # 先畫同儕平均（黑色）
                    fig.add_trace(go.Scatterpolar(
                        r=peer_scores_closed,
                        theta=display_labels_closed,
                        name='同儕平均',
                        line=dict(color='rgba(0, 0, 0, 1)', width=2),
                    ))
                    
                    # 後畫學生本人（紅色）
                    fig.add_trace(go.Scatterpolar(
                        r=student_scores_closed,
                        theta=display_labels_closed,
                        name=student,
                        fill='toself',
                        fillcolor='rgba(255, 0, 0, 0.2)',
                        line=dict(color='rgba(255, 0, 0, 1)', width=2),
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 5]
                            )
                        ),
                        showlegend=True,
                        title=f"{student} ({training_plan}) - EPA評量",
                        height=400,
                        width=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"沒有找到 {student} 的有效評核分數")
            
            with col2:
                st.markdown("### EPA 教師評語")
                for _, row in student_data.iterrows():
                    filename = row['檔案名稱']
                    match = re.search(r'coreEPA\s+(\d+)', filename)
                    if match:
                        epa_number = match.group(1)
                        
                        st.markdown(f"**EPA{epa_number}**")
                        
                        # 顯示初評回饋
                        initial_feedback = row.get('初評回饋：', '')
                        if pd.notna(initial_feedback) and str(initial_feedback).strip() != '':
                            st.markdown(f"{initial_feedback}")
                        
                        # 顯示複評回饋
                        review_feedback = row.get('複評回饋：', '')
                        if pd.notna(review_feedback) and str(review_feedback).strip() != '':
                            st.markdown(f"{review_feedback}")
                        
                        # 加入分隔線
                        st.markdown("---")

                # 除錯用：顯示一筆資料的內容
                if not student_data.empty:
                    st.write("第一筆資料內容：")
                    sample_row = student_data.iloc[0]
                    st.write("初評回饋：", repr(sample_row.get('初評回饋：', 'Not found')))
                    st.write("複評回饋：", repr(sample_row.get('複評回饋：', 'Not found')))

    # 作業繳交狀況
    st.subheader("作業繳交狀況")
    
    # 取得所有學員和作業
    students = period_data['學員'].unique()
    assignments = period_data['檔案名稱'].unique()
    
    # 建立作業繳交狀況表格
    submission_data = []
    
    for student in students:
        student_data = period_data[period_data['學員'] == student]
        row_data = {'學員': student}
        
        # 獲取學生的臨床訓練計畫
        training_plan = student_data['臨床訓練計畫'].iloc[0] if '臨床訓練計畫' in student_data.columns else "未知"
        row_data['臨床訓練計畫'] = training_plan
        
        for assignment in assignments:
            # 取得該作業的資料
            assignment_data = student_data[student_data['檔案名稱'] == assignment]
            
            # 判斷是否完成
            is_completed = False
            if not assignment_data.empty and '表單簽核流程' in assignment_data.columns:
                # 取得最後一個非空值的簽核流程
                sign_flow = assignment_data['表單簽核流程'].dropna().iloc[-1] if not assignment_data['表單簽核流程'].dropna().empty else ""
                
                if any(keyword in assignment for keyword in ["教學住診", "教學門診", "夜間學習"]):
                    is_completed = sign_flow.count(")") >= 3
                elif "CEX" in assignment:
                    is_completed = sign_flow.count(")") >= 2    
                elif "核心技能" in assignment:
                    is_completed = sign_flow.endswith(")")
                elif "coreEPA" in assignment:
                    is_completed = sign_flow.count("未指定") < 2
            
            row_data[assignment] = "✓" if is_completed else "✗"
        
        submission_data.append(row_data)
    
    # 轉換為 DataFrame 並顯示
    submission_df = pd.DataFrame(submission_data)
    
    # 重新排列欄位，確保學員和臨床訓練計畫在最前面
    cols = submission_df.columns.tolist()
    cols.remove('學員')
    cols.remove('臨床訓練計畫')
    submission_df = submission_df[['學員', '臨床訓練計畫'] + cols]
    
    # 設定表格樣式
    def color_status(val):
        if val in ["✓", "✗"]:
            color = 'green' if val == "✓" else 'red'
            return f'color: {color}'
        return ''
    
    # 應用樣式並顯示表格
    styled_df = submission_df.style.applymap(
        color_status, 
        subset=submission_df.columns.difference(['學員', '臨床訓練計畫'])
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=400
    ) 