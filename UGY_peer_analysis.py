import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import plotly.express as px

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """用於自然排序的鍵函數"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]

def show_UGY_peer_analysis_section(df):
    """顯示UGY同梯次分析的函數"""
    
    st.subheader("UGY同梯次分析")
    
    # 選擇訓練階段期間（多選）
    if '訓練階段期間' in df.columns:
        training_periods = sorted(df['訓練階段期間'].unique().tolist())
        selected_periods = st.multiselect(
            "選擇訓練階段期間",
            options=training_periods,
            key='UGY_peer_analysis_periods'
        )
        
        if selected_periods:
            # 篩選選定階段的資料
            period_data = df[df['訓練階段期間'].isin(selected_periods)]
            
            # 找出所有成績相關欄位
            score_cols = [col for col in period_data.columns if '成績' in col or '分數' in col]
            core_skill_cols = [col for col in period_data.columns if '教師評核' in col]
            all_score_cols = score_cols + core_skill_cols
            
            # 不呈現個別學生分數表格
            
            # 找出所有 EPA 編號，並按自然順序排序
            epa_columns = [col for col in all_score_cols if col.startswith('EPA')]
            epa_columns_sorted = sorted(epa_columns, key=natural_sort_key)
            
            st.subheader("EPA 評量比較")
            
            # 修改雷達圖標籤處理
            epa_labels = [col.split('(')[0].strip() for col in epa_columns_sorted]
            
            # 修改每行顯示的雷達圖數量
            CHARTS_PER_ROW = 1
            
            
            # 取得所有學員
            students = period_data['學員'].unique()
            
            # 建立雷達圖所需的資料
            radar_data = []
            for student in students:
                student_data = {'學員': student}
                # 獲取學員資料
                student_records = period_data[period_data['學員'] == student]
                
                # 獲取初評醫師簽名
                initial_reviewer = student_records.loc[
                    student_records['初評醫師簽名'].notna(), 
                    '初評醫師簽名'
                ].iloc[-1] if not student_records['初評醫師簽名'].isna().all() else "未指定"
                
                # 獲取組別資訊
                group = student_records['組別'].iloc[0] if '組別' in student_records.columns else "未指定"
                
                student_data['初評醫師'] = initial_reviewer
                student_data['組別'] = group
                
                for col in epa_columns_sorted:
                    student_data[col] = period_data[period_data['學員'] == student][col].mean()
                radar_data.append(student_data)
            
            # 計算整體平均值
            avg_data = {}
            for col in epa_columns_sorted:
                avg_data[col] = period_data[col].mean()
            
            # 建立雷達圖
            cols = st.columns(CHARTS_PER_ROW)
            for idx, student_data in enumerate(radar_data):
                col_idx = idx % CHARTS_PER_ROW
                
                with cols[col_idx]:
                    fig = go.Figure()
                    
                    # 確保數據點首尾相連，使用簡化後的標籤
                    epa_labels_closed = epa_labels + [epa_labels[0]]
                    avg_scores_closed = [avg_data[col] for col in epa_columns_sorted] + [avg_data[epa_columns_sorted[0]]]
                    student_scores_closed = [student_data[col] for col in epa_columns_sorted] + [student_data[epa_columns_sorted[0]]]
                    
                    # 先畫同儕平均（深褐色）
                    fig.add_trace(go.Scatterpolar(
                        r=avg_scores_closed,
                        theta=epa_labels_closed,
                        name='同儕平均',
                        mode='lines',
                        line=dict(color='rgba(101, 67, 33, 1)', width=2),
                    ))
                    
                    # 後畫學生本人（紅色）
                    fig.add_trace(go.Scatterpolar(
                        r=student_scores_closed,
                        theta=epa_labels_closed,
                        name=student_data['學員'],
                        fill='toself',
                        fillcolor='rgba(255, 0, 0, 0.2)',
                        line=dict(color='rgba(255, 0, 0, 1)', width=2),
                    ))
                    
                    # 更新雷達圖樣式，加入組別資訊
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 5]
                            )
                        ),
                        showlegend=True,
                        title=f"{student_data['學員']} ({student_data['組別']}) (初評醫師: {student_data['初評醫師']})",
                        height=400,
                        width=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # 當完成一行後，添加新的一行
                if col_idx == CHARTS_PER_ROW - 1:
                    cols = st.columns(CHARTS_PER_ROW)
            
 
            
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