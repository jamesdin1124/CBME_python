import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
from modules.google_connection import fetch_google_form_data, setup_google_connection
import gspread
from google.oauth2.service_account import Credentials
import re

# 小兒部住院醫師評核表單欄位對應
PEDIATRIC_FORM_FIELDS = {
    '時間戳記': 'timestamp',
    '評核教師': 'evaluator_teacher', 
    '評核日期': 'evaluation_date',
    '受評核人員': 'evaluated_person',
    '評核時級職': 'evaluation_level',
    '評核項目': 'evaluation_item',
    '會議名稱': 'meeting_name',
    '內容是否充分': 'content_sufficient',
    '辯證資料的能力': 'data_analysis_ability',
    '口條、呈現方式是否清晰': 'presentation_clarity',
    '是否具開創、建設性的想法': 'innovative_ideas',
    '回答提問是否具邏輯、有條有理': 'logical_response',
    '會議報告教師回饋': 'teacher_feedback',
    '病歷號': 'patient_id',
    '評核技術項目': 'technical_evaluation_item',
    '鎮靜藥物': 'sedation_medication',
    '可信賴程度': 'reliability_level',
    '操作技術教師回饋': 'technical_teacher_feedback',
    '熟練程度': 'proficiency_level'
}

# 小兒科住院醫師技能基本要求次數
PEDIATRIC_SKILL_REQUIREMENTS = {
    '插氣管內管': {'minimum': 3, 'description': '訓練期間最少3次'},
    '插臍(動靜脈)導管': {'minimum': 1, 'description': '訓練期間最少1次'},
    '腰椎穿刺': {'minimum': 3, 'description': 'PGY2/R1 訓練期間最少3次'},
    '插中心靜脈導管(CVC)': {'minimum': 3, 'description': '訓練期間最少3次'},
    '肋膜液或是腹水抽取': {'minimum': 1, 'description': '訓練期間最少1次'},
    '插胸管': {'minimum': 2, 'description': '訓練期間最少2次'},
    '放置動脈導管': {'minimum': 2, 'description': '訓練期間最少2次'},
    '經皮式中央靜脈導管(PICC)': {'minimum': 3, 'description': '訓練期間最少3次'},
    '腦部超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '心臟超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '腹部超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '腎臟超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '病歷書寫': {'minimum': 10, 'description': '訓練期間最少10次'},
    'NRP': {'minimum': 10, 'description': '訓練期間最少10次'}
}

def show_pediatric_evaluation_section():
    """顯示小兒部住院醫師評核分頁"""
    st.title("🏥 小兒部住院醫師評核系統")
    st.markdown("---")
    
    # 顯示Google表單連結
    st.info("📋 **評核表單連結**: [小兒部住院醫師評核表單](https://docs.google.com/spreadsheets/d/1n4kc2d3Z-x9SvIDApPCCz2HSDO0wSrrk9Y5jReMhr-M/edit?usp=sharing)")
    
    # 創建分頁
    tab1, tab2, tab3 = st.tabs(["📊 資料概覽", "👥 個別評核分析", "⚙️ 資料管理"])
    
    with tab1:
        show_data_overview()
    
    with tab2:
        show_individual_analysis()
    
    with tab3:
        show_data_management()

def load_pediatric_data():
    """載入小兒部評核資料"""
    try:
        # 使用提供的Google表單URL
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1n4kc2d3Z-x9SvIDApPCCz2HSDO0wSrrk9Y5jReMhr-M/edit?usp=sharing"
        
        # 嘗試載入資料
        df, sheet_titles = fetch_google_form_data(spreadsheet_url=spreadsheet_url)
        
        if df is not None and not df.empty:
            # 處理資料
            processed_df = process_pediatric_data(df)
            return processed_df, sheet_titles
        else:
            st.warning("無法載入小兒部評核資料")
            return None, None
            
    except Exception as e:
        st.error(f"載入資料時發生錯誤：{str(e)}")
        return None, None

def process_pediatric_data(df):
    """處理小兒部評核資料"""
    try:
        # 複製資料框
        processed_df = df.copy()
        
        # 處理評核日期
        if '評核日期' in processed_df.columns:
            # 如果評核日期已經是日期格式，直接使用
            if processed_df['評核日期'].dtype == 'object':
                # 嘗試將字串轉換為日期
                try:
                    processed_df['評核日期'] = pd.to_datetime(processed_df['評核日期'], errors='coerce').dt.date
                except Exception as e:
                    st.warning(f"⚠️ 評核日期轉換錯誤: {str(e)}")
        
        # 如果沒有評核日期欄位，嘗試從時間戳記解析
        elif '時間戳記' in processed_df.columns:
            # 創建評核日期欄位
            processed_df['評核日期'] = None
            
            # 嘗試解析時間戳記中的日期部分
            for idx, timestamp in processed_df['時間戳記'].items():
                if pd.notna(timestamp):
                    timestamp_str = str(timestamp).strip()
                    
                    # 提取日期部分（在空格之前的部分）
                    date_part = timestamp_str.split(' ')[0] if ' ' in timestamp_str else timestamp_str
                    
                    # 嘗試解析日期
                    try:
                        parsed_date = pd.to_datetime(date_part, format='%Y/%m/%d').date()
                        processed_df.at[idx, '評核日期'] = parsed_date
                    except:
                        pass
        
        # 處理數值評分欄位
        score_columns = ['內容是否充分', '辯證資料的能力', '口條、呈現方式是否清晰', 
                        '是否具開創、建設性的想法', '回答提問是否具邏輯、有條有理']
        
        for col in score_columns:
            if col in processed_df.columns:
                # 將文字評分轉換為數值
                processed_df[f'{col}_數值'] = processed_df[col].apply(convert_score_to_numeric)
        
        # 處理可信賴程度
        if '可信賴程度' in processed_df.columns:
            processed_df['可信賴程度_數值'] = processed_df['可信賴程度'].apply(convert_reliability_to_numeric)
        
        # 處理熟練程度
        if '熟練程度' in processed_df.columns:
            processed_df['熟練程度_數值'] = processed_df['熟練程度'].apply(convert_proficiency_to_numeric)
        
        return processed_df
        
    except Exception as e:
        st.error(f"處理資料時發生錯誤：{str(e)}")
        return df

def convert_score_to_numeric(score_text):
    """將評分文字轉換為數值"""
    if pd.isna(score_text) or score_text == '':
        return None
    
    score_text = str(score_text).strip()
    
    # 定義評分對應
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
    numbers = re.findall(r'\d+', reliability_text)
    if numbers:
        return int(numbers[0])
    
    return None

def convert_proficiency_to_numeric(proficiency_text):
    """將熟練程度轉換為數值"""
    if pd.isna(proficiency_text) or proficiency_text == '':
        return None
    
    proficiency_text = str(proficiency_text).strip()
    
    # 定義熟練程度對應
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

def show_data_overview():
    """顯示資料概覽"""
    st.subheader("📊 小兒部住院醫師評核資料概覽")
    
    # 載入資料
    df, sheet_titles = load_pediatric_data()
    
    if df is not None and not df.empty:
        # 基本統計資訊
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("總評核數", len(df))
        
        with col2:
            unique_patients = len(df['病歷號'].unique()) if '病歷號' in df.columns else 0
            st.metric("評核病歷數", unique_patients)
        
        with col3:
            unique_evaluators = len(df['評核教師'].unique()) if '評核教師' in df.columns else 0
            st.metric("評核教師數", unique_evaluators)
        
        with col4:
            unique_residents = len(df['受評核人員'].unique()) if '受評核人員' in df.columns else 0
            st.metric("受評核人員數", unique_residents)
        
        # 顯示原始資料
        with st.expander("原始資料預覽", expanded=False):
            st.dataframe(df, use_container_width=True)
        
        # 評核項目分布
        if '評核項目' in df.columns:
            st.subheader("評核項目分布")
            evaluation_items = df['評核項目'].value_counts()
            
            fig = px.pie(
                values=evaluation_items.values,
                names=evaluation_items.index,
                title="評核項目分布"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 評核教師分布
        if '評核教師' in df.columns:
            st.subheader("評核教師分布")
            teachers = df['評核教師'].value_counts().head(10)
            
            fig = px.bar(
                x=teachers.values,
                y=teachers.index,
                orientation='h',
                title="評核教師評核次數 (前10名)"
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        # 時間趨勢
        if '評核日期' in df.columns and df['評核日期'].notna().any():
            st.subheader("評核時間趨勢")
            
            # 計算每日評核次數
            daily_counts = df.groupby('評核日期').size().reset_index(name='評核次數')
            
            if not daily_counts.empty:
                # 篩選一週內的資料
                from datetime import datetime, timedelta
                today = datetime.now().date()
                week_ago = today - timedelta(days=7)
                
                # 篩選最近一週的資料
                recent_counts = daily_counts[daily_counts['評核日期'] >= week_ago].copy()
                
                if not recent_counts.empty:
                    # 確保日期按順序排列
                    recent_counts = recent_counts.sort_values('評核日期')
                    
                    # 顯示一週內趨勢
                    fig = px.line(
                        recent_counts,
                        x='評核日期',
                        y='評核次數',
                        title="最近一週評核次數趨勢",
                        markers=True
                    )
                    
                    # 添加今日標記
                    if today in recent_counts['評核日期'].values:
                        today_count = recent_counts[recent_counts['評核日期'] == today]['評核次數'].iloc[0]
                        fig.add_annotation(
                            x=today,
                            y=today_count,
                            text=f"今日: {today_count}次",
                            showarrow=True,
                            arrowhead=2,
                            arrowcolor="red",
                            bgcolor="yellow"
                        )
                    
                    # 添加昨日標記
                    yesterday = today - timedelta(days=1)
                    if yesterday in recent_counts['評核日期'].values:
                        yesterday_count = recent_counts[recent_counts['評核日期'] == yesterday]['評核次數'].iloc[0]
                        fig.add_annotation(
                            x=yesterday,
                            y=yesterday_count,
                            text=f"昨日: {yesterday_count}次",
                            showarrow=True,
                            arrowhead=2,
                            arrowcolor="blue",
                            bgcolor="lightblue"
                        )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 顯示一週統計摘要
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("一週內評核次數", recent_counts['評核次數'].sum())
                    
                    with col2:
                        st.metric("一週內評核天數", len(recent_counts))
                    
                    with col3:
                        avg_daily = recent_counts['評核次數'].mean()
                        st.metric("平均每日評核次數", f"{avg_daily:.1f}")
                    
                    # 可展開的詳細資料
                    with st.expander("一週內詳細評核記錄", expanded=False):
                        st.dataframe(recent_counts, use_container_width=True)
                else:
                    st.info("最近一週內沒有評核記錄")
                    
                    # 顯示所有資料的趨勢
                    fig = px.line(
                        daily_counts,
                        x='評核日期',
                        y='評核次數',
                        title="所有評核次數趨勢",
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("沒有找到有效的評核日期資料")
        else:
            st.warning("資料中沒有找到有效的評核日期欄位")
    
    else:
        st.warning("無法載入資料，請檢查Google表單連接")

def show_individual_analysis():
    """顯示個別評核分析"""
    st.subheader("👥 個別評核分析")
    
    df, _ = load_pediatric_data()
    
    if df is not None and not df.empty:
        # 選擇受評核人員
        if '受評核人員' in df.columns:
            residents = sorted(df['受評核人員'].unique())
            selected_resident = st.selectbox("選擇受評核人員", residents)
            
            if selected_resident:
                # 篩選該人員的資料
                resident_data = df[df['受評核人員'] == selected_resident]
                
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
                
                # 詳細資料表格
                with st.expander("詳細評核資料", expanded=True):
                    st.dataframe(resident_data, use_container_width=True)
                
    
    else:
        st.warning("無法載入資料")

def show_statistical_analysis():
    """顯示統計分析"""
    st.subheader("📈 統計分析")
    
    df, _ = load_pediatric_data()
    
    if df is not None and not df.empty:
        # 評分統計分析
        score_columns = ['內容是否充分_數值', '辯證資料的能力_數值', '口條、呈現方式是否清晰_數值',
                        '是否具開創、建設性的想法_數值', '回答提問是否具邏輯、有條有理_數值']
        
        available_scores = [col for col in score_columns if col in df.columns]
        
        if available_scores:
            st.subheader("整體評分統計")
            
            # 計算統計資料
            stats_data = []
            for col in available_scores:
                scores = df[col].dropna()
                if not scores.empty:
                    stats_data.append({
                        '評分項目': col.replace('_數值', ''),
                        '平均分數': scores.mean(),
                        '標準差': scores.std(),
                        '最高分': scores.max(),
                        '最低分': scores.min(),
                        '評分次數': len(scores)
                    })
            
            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(stats_df, use_container_width=True)
                
                # 評分分布圖
                fig = go.Figure()
                
                for col in available_scores:
                    scores = df[col].dropna()
                    if not scores.empty:
                        fig.add_trace(go.Box(
                            y=scores,
                            name=col.replace('_數值', ''),
                            boxpoints='all',
                            jitter=0.3,
                            pointpos=-1.8
                        ))
                
                fig.update_layout(
                    title="各項評分分布箱線圖",
                    yaxis_title="評分",
                    xaxis_title="評分項目"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # 評核教師分析
        if '評核教師' in df.columns:
            st.subheader("評核教師分析")
            
            teacher_stats = []
            for teacher in df['評核教師'].unique():
                teacher_data = df[df['評核教師'] == teacher]
                
                teacher_stat = {
                    '評核教師': teacher,
                    '評核次數': len(teacher_data)
                }
                
                # 計算平均評分
                for col in available_scores:
                    if col in teacher_data.columns:
                        scores = teacher_data[col].dropna()
                        if not scores.empty:
                            teacher_stat[f'{col.replace("_數值", "")}_平均'] = scores.mean()
                
                teacher_stats.append(teacher_stat)
            
            if teacher_stats:
                teacher_df = pd.DataFrame(teacher_stats)
                st.dataframe(teacher_df, use_container_width=True)
        
        # 時間分析
        if '評核日期' in df.columns:
            st.subheader("時間分析")
            
            # 每月評核次數
            df['評核月份'] = pd.to_datetime(df['評核日期']).dt.to_period('M')
            monthly_counts = df.groupby('評核月份').size().reset_index(name='評核次數')
            monthly_counts['評核月份'] = monthly_counts['評核月份'].astype(str)
            
            fig = px.bar(
                monthly_counts,
                x='評核月份',
                y='評核次數',
                title="每月評核次數"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.warning("無法載入資料")

def show_data_management():
    """顯示資料管理"""
    st.subheader("⚙️ 資料管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 資料匯入")
        if st.button("重新載入Google表單資料", type="primary"):
            with st.spinner("正在載入資料..."):
                df, sheet_titles = load_pediatric_data()
                if df is not None:
                    st.success("資料載入成功！")
                    st.session_state['pediatric_data'] = df
                else:
                    st.error("資料載入失敗")
    
    with col2:
        st.markdown("### 📤 資料匯出")
        if 'pediatric_data' in st.session_state:
            df = st.session_state['pediatric_data']
            
            # 轉換為CSV
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="下載CSV檔案",
                data=csv,
                file_name=f"小兒部評核資料_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("請先載入資料")
    
    # 資料驗證
    st.markdown("### 🔍 資料驗證")
    if 'pediatric_data' in st.session_state:
        df = st.session_state['pediatric_data']
        
        # 檢查缺失值
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0]
        
        if not missing_data.empty:
            st.warning("發現缺失資料：")
            st.dataframe(missing_data.to_frame('缺失數量'))
        else:
            st.success("沒有發現缺失資料")
        
        # 檢查重複資料
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            st.warning(f"發現 {duplicates} 筆重複資料")
        else:
            st.success("沒有發現重複資料")
    
    # 資料統計摘要
    st.markdown("### 📊 資料統計摘要")
    if 'pediatric_data' in st.session_state:
        df = st.session_state['pediatric_data']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("總記錄數", len(df))
        
        with col2:
            st.metric("欄位數", len(df.columns))
        
        with col3:
            if '評核日期' in df.columns:
                date_range = (pd.to_datetime(df['評核日期']).max() - pd.to_datetime(df['評核日期']).min()).days
                st.metric("資料時間跨度", f"{date_range} 天")
            else:
                st.metric("資料時間跨度", "N/A")

def show_skill_tracking():
    """顯示技能追蹤功能"""
    st.subheader("🎯 小兒科住院醫師技能追蹤")
    
    # 載入資料
    df, _ = load_pediatric_data()
    
    if df is not None and not df.empty:
        # 選擇受評核人員
        if '受評核人員' in df.columns:
            residents = sorted(df['受評核人員'].unique())
            selected_resident = st.selectbox("選擇受評核人員", residents, key="skill_tracking_resident")
            
            if selected_resident:
                # 篩選該人員的資料
                resident_data = df[df['受評核人員'] == selected_resident]
                
                st.subheader(f"技能追蹤 - {selected_resident}")
                
                # 計算技能完成次數
                skill_counts = calculate_skill_counts(resident_data)
                
                # 顯示技能完成狀況
                show_skill_progress(skill_counts, selected_resident)
                
                # 顯示詳細技能記錄
                show_skill_details(resident_data, selected_resident)
                
                # 技能完成度統計
                show_skill_completion_stats(skill_counts)
    
    else:
        st.warning("無法載入資料")

def calculate_skill_counts(resident_data):
    """計算住院醫師各項技能完成次數"""
    skill_counts = {}
    
    # 從評核技術項目欄位中提取技能資訊
    if '評核技術項目' in resident_data.columns:
        technical_items = resident_data['評核技術項目'].dropna()
        
        for skill in PEDIATRIC_SKILL_REQUIREMENTS.keys():
            # 計算該技能出現的次數
            count = 0
            for item in technical_items:
                if skill in str(item):
                    count += 1
            
            skill_counts[skill] = {
                'completed': count,
                'required': PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum'],
                'description': PEDIATRIC_SKILL_REQUIREMENTS[skill]['description'],
                'progress': min(count / PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum'] * 100, 100)
            }
    
    return skill_counts

def show_skill_progress(skill_counts, resident_name):
    """顯示技能進度條"""
    st.subheader("技能完成進度")
    
    # 創建進度條
    for skill, data in skill_counts.items():
        # 技能標題區域
        st.markdown(f"### {skill}")
        st.caption(data['description'])
        
        # 完成度顯示區域
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # 進度條
            progress = data['progress'] / 100
            st.progress(progress)
            
            # 狀態指示
            if data['completed'] >= data['required']:
                st.success(f"✅ 已完成 ({data['completed']}/{data['required']})")
            else:
                remaining = data['required'] - data['completed']
                st.warning(f"⚠️ 還需 {remaining} 次 ({data['completed']}/{data['required']})")
        
        with col2:
            st.metric("已完成", data['completed'])
        
        with col3:
            st.metric("需完成", data['required'])
        
        # 添加分隔線
        st.markdown("---")

def show_skill_details(resident_data, resident_name):
    """顯示詳細技能記錄"""
    st.subheader("詳細技能記錄")
    
    # 篩選包含技能評核的記錄
    skill_records = resident_data[resident_data['評核技術項目'].notna()].copy()
    
    if not skill_records.empty:
        # 選擇要顯示的欄位
        display_columns = ['評核日期', '評核教師', '評核技術項目', '熟練程度', '操作技術教師回饋']
        
        # 確保所有欄位都存在
        available_columns = [col for col in display_columns if col in skill_records.columns]
        
        if available_columns:
            # 按日期排序
            if '評核日期' in available_columns:
                skill_records = skill_records.sort_values('評核日期', ascending=False)
            
            st.dataframe(skill_records[available_columns], use_container_width=True)
        else:
            st.warning("沒有可用的技能記錄欄位")
    else:
        st.info("該住院醫師目前沒有技能評核記錄")

def show_skill_completion_stats(skill_counts):
    """顯示技能完成度統計"""
    st.subheader("技能完成度統計")
    
    # 計算統計資料
    total_skills = len(skill_counts)
    completed_skills = sum(1 for data in skill_counts.values() if data['completed'] >= data['required'])
    in_progress_skills = total_skills - completed_skills
    
    # 顯示統計卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總技能數", total_skills)
    
    with col2:
        st.metric("已完成技能", completed_skills)
    
    with col3:
        st.metric("進行中技能", in_progress_skills)
    
    with col4:
        completion_rate = (completed_skills / total_skills * 100) if total_skills > 0 else 0
        st.metric("完成率", f"{completion_rate:.1f}%")
    
    # 技能完成度圖表
    if skill_counts:
        # 準備圖表資料
        skills = list(skill_counts.keys())
        completed = [data['completed'] for data in skill_counts.values()]
        required = [data['required'] for data in skill_counts.values()]
        
        # 創建長條圖
        fig = go.Figure()
        
        # 已完成次數
        fig.add_trace(go.Bar(
            name='已完成',
            x=skills,
            y=completed,
            marker_color='lightgreen'
        ))
        
        # 需要完成次數
        fig.add_trace(go.Bar(
            name='需要完成',
            x=skills,
            y=required,
            marker_color='lightcoral',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="技能完成次數對比",
            xaxis_title="技能項目",
            yaxis_title="次數",
            barmode='group',
            height=500,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 技能完成度圓餅圖
        fig_pie = go.Figure(data=[go.Pie(
            labels=['已完成', '進行中'],
            values=[completed_skills, in_progress_skills],
            marker_colors=['lightgreen', 'lightcoral']
        )])
        
        fig_pie.update_layout(
            title="技能完成狀況分布",
            height=400
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)

def show_skill_requirements():
    """顯示技能要求清單"""
    st.subheader("小兒科住院醫師技能基本要求")
    
    # 創建技能要求表格
    skill_data = []
    for skill, data in PEDIATRIC_SKILL_REQUIREMENTS.items():
        skill_data.append({
            '技能項目': skill,
            '最少次數': data['minimum'],
            '說明': data['description']
        })
    
    skill_df = pd.DataFrame(skill_data)
    st.dataframe(skill_df, use_container_width=True)
    
    # 技能分類統計
    st.subheader("技能分類統計")
    
    # 按最少次數分類
    category_stats = skill_df.groupby('最少次數').size().reset_index(name='技能數量')
    category_stats['分類'] = category_stats['最少次數'].apply(
        lambda x: f"需要{x}次" if x == 1 else f"需要{x}次"
    )
    
    fig = px.pie(
        category_stats,
        values='技能數量',
        names='分類',
        title="技能要求次數分布"
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    show_pediatric_evaluation_section()
