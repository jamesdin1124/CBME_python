#!/usr/bin/env python3
"""
測試個別評核分析分項目功能
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta

def create_sample_individual_data():
    """創建模擬的個別評核資料，包含操作技術和會議報告"""
    
    sample_data = {
        '時間戳記': [
            '2025/9/12 上午 11:11:3',
            '2025/9/12 下午 1:26:13',
            '2025/9/11 上午 9:30:00',
            '2025/9/11 下午 2:15:00',
            '2025/9/10 上午 10:45:00',
            '2025/9/10 下午 3:20:00'
        ],
        '評核教師': [
            '丁肇壯', '林盈秀', '丁肇壯', '王小明', '林盈秀', '丁肇壯'
        ],
        '受評核人員': [
            '林盈秀', '林盈秀', '林盈秀', '林盈秀', '林盈秀', '林盈秀'
        ],
        '評核項目': [
            '操作技術', '會議報告', '操作技術', '會議報告', '操作技術', '會議報告'
        ],
        '評核日期': [
            '2025/9/12', '2025/9/12', '2025/9/11', '2025/9/11', '2025/9/10', '2025/9/10'
        ],
        '評核技術項目': [
            '插氣管內管（訓練期間最少3次）',
            None,
            '腎臟超音波（訓練期間最少5次）',
            None,
            '腰椎穿刺（PGY2/R1 訓練期間最少3次）',
            None
        ],
        '會議名稱': [
            None,
            '晨會報告',
            None,
            '病例討論會',
            None,
            '學術研討會'
        ],
        '可信賴程度': [
            '3', None, '4', None, '5', None
        ],
        '熟練程度': [
            '熟練', None, '基本熟練', None, '熟練', None
        ],
        '內容是否充分': [
            None, '同意', None, '非常同意', None, '同意'
        ],
        '辯證資料的能力': [
            None, '同意', None, '非常同意', None, '同意'
        ],
        '口條、呈現方式是否清晰': [
            None, '非常同意', None, '同意', None, '同意'
        ],
        '是否具開創、建設性的想法': [
            None, '同意', None, '非常同意', None, '普通'
        ],
        '回答提問是否具邏輯、有條有理': [
            None, '同意', None, '非常同意', None, '同意'
        ],
        '操作技術教師回饋': [
            '操作技術熟練，表現優秀',
            None,
            '超音波技術需要加強',
            None,
            '腰椎穿刺技術已達標準',
            None
        ],
        '會議報告教師回饋': [
            None,
            '報告內容充實，表達清楚',
            None,
            '分析深入，建議有建設性',
            None,
            '報告結構完整，但可更深入'
        ]
    }
    
    return pd.DataFrame(sample_data)

def process_individual_data(df):
    """處理個別評核資料"""
    processed_df = df.copy()
    
    # 處理評核日期
    if '評核日期' in processed_df.columns:
        processed_df['評核日期'] = pd.to_datetime(processed_df['評核日期'], errors='coerce').dt.date
    
    # 處理數值評分欄位
    score_columns = ['內容是否充分', '辯證資料的能力', '口條、呈現方式是否清晰', 
                    '是否具開創、建設性的想法', '回答提問是否具邏輯、有條有理']
    
    for col in score_columns:
        if col in processed_df.columns:
            processed_df[f'{col}_數值'] = processed_df[col].apply(convert_score_to_numeric)
    
    # 處理可信賴程度
    if '可信賴程度' in processed_df.columns:
        processed_df['可信賴程度_數值'] = processed_df['可信賴程度'].apply(convert_reliability_to_numeric)
    
    # 處理熟練程度
    if '熟練程度' in processed_df.columns:
        processed_df['熟練程度_數值'] = processed_df['熟練程度'].apply(convert_proficiency_to_numeric)
    
    return processed_df

def convert_score_to_numeric(score_text):
    """將評分文字轉換為數值"""
    if pd.isna(score_text) or score_text == '':
        return None
    
    score_text = str(score_text).strip()
    
    score_mapping = {
        '非常同意': 5,
        '同意': 4,
        '普通': 3,
        '不同意': 2,
        '非常不同意': 1,
        '優秀': 5,
        '良好': 4,
        '普通': 3,
        '待改進': 2,
        '需加強': 1
    }
    
    return score_mapping.get(score_text, None)

def convert_reliability_to_numeric(reliability_text):
    """將可信賴程度轉換為數值"""
    if pd.isna(reliability_text) or reliability_text == '':
        return None
    
    reliability_text = str(reliability_text).strip()
    
    # 提取數字
    import re
    numbers = re.findall(r'\d+', reliability_text)
    if numbers:
        return int(numbers[0])
    
    return None

def convert_proficiency_to_numeric(proficiency_text):
    """將熟練程度轉換為數值"""
    if pd.isna(proficiency_text) or proficiency_text == '':
        return None
    
    proficiency_text = str(proficiency_text).strip()
    
    proficiency_mapping = {
        '熟練': 5,
        '基本熟練': 4,
        '部分熟練': 3,
        '初學': 2,
        '不熟練': 1,
        '一兩次內完成': 5,
        '協助下完成': 3,
        '需指導完成': 2
    }
    
    return proficiency_mapping.get(proficiency_text, None)

def test_individual_analysis():
    """測試個別評核分析功能"""
    st.title("🧪 個別評核分析分項目測試")
    
    st.subheader("測試說明")
    st.write("""
    此測試展示個別評核分析的分項目功能：
    - 操作技術評核分析
    - 會議報告評核分析
    - 分別顯示統計、圖表和詳細記錄
    """)
    
    # 創建模擬資料
    df = create_sample_individual_data()
    processed_df = process_individual_data(df)
    
    st.subheader("原始資料")
    st.dataframe(processed_df, use_container_width=True)
    
    # 選擇受評核人員
    selected_resident = "林盈秀"
    resident_data = processed_df[processed_df['受評核人員'] == selected_resident]
    
    st.subheader(f"受評核人員：{selected_resident}")
    
    # 基本統計
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總評核次數", len(resident_data))
    with col2:
        unique_items = len(resident_data['評核項目'].unique()) if '評核項目' in resident_data.columns else 0
        st.metric("評核項目數", unique_items)
    with col3:
        if '評核日期' in resident_data.columns:
            date_range = f"{resident_data['評核日期'].min()} 至 {resident_data['評核日期'].max()}"
            st.metric("評核期間", date_range)
    
    # 分項目分析
    if '評核項目' in resident_data.columns:
        # 分離操作技術和會議報告
        technical_data = resident_data[resident_data['評核項目'] == '操作技術']
        meeting_data = resident_data[resident_data['評核項目'] == '會議報告']
        
        # 第一部分：操作技術分析
        st.subheader("🔧 操作技術評核分析")
        
        if not technical_data.empty:
            # 操作技術統計
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("操作技術評核次數", len(technical_data))
            with col2:
                if '評核技術項目' in technical_data.columns:
                    unique_skills = len(technical_data['評核技術項目'].unique())
                    st.metric("技能項目數", unique_skills)
            with col3:
                if '評核日期' in technical_data.columns:
                    date_range = f"{technical_data['評核日期'].min()} 至 {technical_data['評核日期'].max()}"
                    st.metric("評核期間", date_range)
            
            # 技能項目分析與完成狀況
            if '評核技術項目' in technical_data.columns:
                st.write("**技能項目分布與完成狀況**")
                
                # 計算技能完成次數
                skill_counts = calculate_skill_counts(technical_data)
                
                if skill_counts:
                    # 準備圖表資料
                    skills = list(skill_counts.keys())
                    completed = [data['completed'] for data in skill_counts.values()]
                    required = [data['required'] for data in skill_counts.values()]
                    
                    # 創建對比長條圖
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    
                    # 已完成次數
                    fig.add_trace(go.Bar(
                        name='已完成',
                        x=skills,
                        y=completed,
                        marker_color='lightgreen',
                        text=completed,
                        textposition='auto'
                    ))
                    
                    # 需要完成次數
                    fig.add_trace(go.Bar(
                        name='需要完成',
                        x=skills,
                        y=required,
                        marker_color='lightcoral',
                        opacity=0.7,
                        text=required,
                        textposition='auto'
                    ))
                    
                    fig.update_layout(
                        title=f"{selected_resident} 操作技術技能完成狀況",
                        xaxis_title="技能項目",
                        yaxis_title="次數",
                        barmode='group',
                        height=500,
                        xaxis_tickangle=-45
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 技能完成度統計
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_skills = len(skill_counts)
                    completed_skills = sum(1 for data in skill_counts.values() if data['completed'] >= data['required'])
                    in_progress_skills = total_skills - completed_skills
                    completion_rate = (completed_skills / total_skills * 100) if total_skills > 0 else 0
                    
                    with col1:
                        st.metric("總技能數", total_skills)
                    
                    with col2:
                        st.metric("已完成技能", completed_skills)
                    
                    with col3:
                        st.metric("進行中技能", in_progress_skills)
                    
                    with col4:
                        st.metric("完成率", f"{completion_rate:.1f}%")
                    
                else:
                    st.info("該住院醫師目前沒有技能評核記錄")
            
            # 操作技術評分趨勢分析
            technical_score_columns = ['可信賴程度_數值', '熟練程度_數值']
            available_technical_scores = [col for col in technical_score_columns if col in technical_data.columns]
            
            if available_technical_scores and '評核日期' in technical_data.columns:
                st.write("**操作技術評分進步趨勢**")
                
                # 準備趨勢資料
                trend_data = []
                
                for col in available_technical_scores:
                    # 按日期排序並計算累積平均分數
                    skill_data = technical_data[['評核日期', col]].dropna()
                    if not skill_data.empty:
                        skill_data = skill_data.sort_values('評核日期')
                        
                        # 計算累積平均分數
                        skill_data['累積平均'] = skill_data[col].expanding().mean()
                        
                        for idx, row in skill_data.iterrows():
                            trend_data.append({
                                '評核日期': row['評核日期'],
                                '評分項目': col.replace('_數值', ''),
                                '當次分數': row[col],
                                '累積平均分數': row['累積平均']
                            })
                
                if trend_data:
                    trend_df = pd.DataFrame(trend_data)
                    
                    # 創建折線圖
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    
                    # 定義不同技能的顏色
                    colors = {
                        '可信賴程度': ['#1f77b4', '#aec7e8'],  # 藍色系
                        '熟練程度': ['#ff7f0e', '#ffbb78']    # 橙色系
                    }
                    
                    # 為每個評分項目創建趨勢線
                    for score_item in trend_df['評分項目'].unique():
                        item_data = trend_df[trend_df['評分項目'] == score_item]
                        color_set = colors.get(score_item, ['#2ca02c', '#98df8a'])  # 預設綠色系
                        
                        # 累積平均趨勢線
                        fig.add_trace(go.Scatter(
                            x=item_data['評核日期'],
                            y=item_data['累積平均分數'],
                            mode='lines+markers',
                            name=f'{score_item} (累積平均)',
                            line=dict(width=3, color=color_set[0]),
                            marker=dict(size=8, color=color_set[0])
                        ))
                        
                        # 當次分數點
                        fig.add_trace(go.Scatter(
                            x=item_data['評核日期'],
                            y=item_data['當次分數'],
                            mode='markers',
                            name=f'{score_item} (當次分數)',
                            marker=dict(size=6, color=color_set[1], opacity=0.8),
                            showlegend=True
                        ))
                    
                    # 添加滿分線
                    fig.add_hline(y=5, line_dash="dash", line_color="red", 
                                annotation_text="滿分線 (5分)", annotation_position="top right")
                    
                    fig.update_layout(
                        title=f"{selected_resident} 操作技術評分進步趨勢",
                        xaxis_title="評核日期",
                        yaxis_title="分數",
                        yaxis=dict(range=[0, 5.5]),
                        height=500,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 顯示最新評分摘要
                    st.write("**最新評分摘要**")
                    latest_scores = trend_df.groupby('評分項目').tail(1)
                    
                    col1, col2 = st.columns(2)
                    for idx, row in latest_scores.iterrows():
                        with col1 if row['評分項目'] == '可信賴程度' else col2:
                            st.metric(
                                f"{row['評分項目']} (最新)",
                                f"{row['當次分數']:.1f}/5.0",
                                f"累積平均: {row['累積平均分數']:.1f}"
                            )
                else:
                    st.info("沒有足夠的評分資料來顯示趨勢")
            elif available_technical_scores:
                # 如果沒有日期資料，顯示簡單的平均分數
                st.write("**操作技術評分分析**")
                technical_score_data = []
                for col in available_technical_scores:
                    scores = technical_data[col].dropna()
                    if not scores.empty:
                        technical_score_data.append({
                            '評分項目': col.replace('_數值', ''),
                            '平均分數': scores.mean(),
                            '評分次數': len(scores)
                        })
                
                if technical_score_data:
                    technical_score_df = pd.DataFrame(technical_score_data)
                    
                    fig = px.bar(
                        technical_score_df,
                        x='評分項目',
                        y='平均分數',
                        title=f"{selected_resident} 操作技術評分平均",
                        range_y=[0, 5]
                    )
                    fig.add_hline(y=5, line_dash="dash", line_color="red", 
                                annotation_text="滿分線 (5分)", annotation_position="top right")
                    st.plotly_chart(fig, use_container_width=True)
            
            # 操作技術詳細記錄
            with st.expander("操作技術詳細記錄", expanded=False):
                display_columns = ['評核日期', '評核教師', '評核技術項目', '可信賴程度', '熟練程度', '操作技術教師回饋']
                available_columns = [col for col in display_columns if col in technical_data.columns]
                if available_columns:
                    st.dataframe(technical_data[available_columns], use_container_width=True)
        else:
            st.info("該住院醫師目前沒有操作技術評核記錄")
        
        # 分隔線
        st.markdown("---")
        
        # 第二部分：會議報告分析
        st.subheader("📋 會議報告評核分析")
        
        if not meeting_data.empty:
            # 會議報告統計
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("會議報告評核次數", len(meeting_data))
            with col2:
                if '會議名稱' in meeting_data.columns:
                    unique_meetings = len(meeting_data['會議名稱'].unique())
                    st.metric("會議類型數", unique_meetings)
            with col3:
                if '評核日期' in meeting_data.columns:
                    date_range = f"{meeting_data['評核日期'].min()} 至 {meeting_data['評核日期'].max()}"
                    st.metric("評核期間", date_range)
            
            # 會議類型分析
            if '會議名稱' in meeting_data.columns:
                st.write("**會議類型分布**")
                meeting_counts = meeting_data['會議名稱'].value_counts()
                fig = px.bar(
                    x=meeting_counts.index,
                    y=meeting_counts.values,
                    title=f"{selected_resident} 會議報告類型分布"
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # 會議報告評分分析
            meeting_score_columns = ['內容是否充分_數值', '辯證資料的能力_數值', '口條、呈現方式是否清晰_數值',
                                   '是否具開創、建設性的想法_數值', '回答提問是否具邏輯、有條有理_數值']
            available_meeting_scores = [col for col in meeting_score_columns if col in meeting_data.columns]
            
            if available_meeting_scores:
                st.write("**會議報告評分分析**")
                meeting_score_data = []
                for col in available_meeting_scores:
                    scores = meeting_data[col].dropna()
                    if not scores.empty:
                        meeting_score_data.append({
                            '評分項目': col.replace('_數值', ''),
                            '平均分數': scores.mean(),
                            '評分次數': len(scores)
                        })
                
                if meeting_score_data:
                    meeting_score_df = pd.DataFrame(meeting_score_data)
                    
                    fig = px.bar(
                        meeting_score_df,
                        x='評分項目',
                        y='平均分數',
                        title=f"{selected_resident} 會議報告評分平均"
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
            
            # 會議報告詳細記錄
            with st.expander("會議報告詳細記錄", expanded=False):
                display_columns = ['評核日期', '評核教師', '會議名稱', '內容是否充分', '辯證資料的能力', 
                                 '口條、呈現方式是否清晰', '是否具開創、建設性的想法', '回答提問是否具邏輯、有條有理', '會議報告教師回饋']
                available_columns = [col for col in display_columns if col in meeting_data.columns]
                if available_columns:
                    st.dataframe(meeting_data[available_columns], use_container_width=True)
        else:
            st.info("該住院醫師目前沒有會議報告評核記錄")

def main():
    """主函數"""
    st.set_page_config(
        page_title="個別評核分析測試",
        layout="wide"
    )
    
    test_individual_analysis()

if __name__ == "__main__":
    main()
