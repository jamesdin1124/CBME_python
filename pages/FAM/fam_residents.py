import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date
import numpy as np
import re
import os

# 匯入自定義模組
from .fam_data_processor import FAMDataProcessor
from .fam_visualization import FAMVisualization

# 家醫部住院醫師EPA評核表單欄位對應
FAM_RESIDENT_FORM_FIELDS = {
    '臨床訓練計畫': 'training_plan',
    '組別': 'group',
    '階段/子階段': 'stage_substage',
    '訓練階段科部': 'training_department',
    '訓練階段期間': 'training_period',
    '學員': 'student_name',
    '學員帳號': 'student_account',
    '表單簽核流程': 'approval_process',
    '表單派送日期': 'form_send_date',
    '應完成日期': 'due_date',
    '日期': 'evaluation_date',
    'EPA項目': 'epa_item',
    '受評醫師': 'evaluated_doctor',
    '病歷號碼': 'patient_id',
    '個案姓名': 'patient_name',
    '診斷': 'diagnosis',
    '複雜程度': 'complexity',
    '觀察場域': 'observation_field',
    '信賴程度(學員自評)': 'self_assessment',
    '信賴程度(教師評量)': 'teacher_assessment',
    '教師給學員回饋': 'teacher_feedback',
    '教師簽名': 'teacher_signature',
    '教師給CCC回饋(僅CCC委員可讀，對學員隱藏)': 'ccc_feedback'
}

# 家醫部EPA項目基本要求
FAM_EPA_REQUIREMENTS = {
    '02門診/社區衛教': {'minimum': 10, 'description': '訓練期間最少10次'},
    '03預防注射': {'minimum': 15, 'description': '訓練期間最少15次'},
    '05健康檢查': {'minimum': 20, 'description': '訓練期間最少20次'},
    '07慢病照護': {'minimum': 25, 'description': '訓練期間最少25次'},
    '08急症照護': {'minimum': 15, 'description': '訓練期間最少15次'},
    '09居家整合醫療': {'minimum': 10, 'description': '訓練期間最少10次'},
    '11末病照護/安寧緩和': {'minimum': 5, 'description': '訓練期間最少5次'},
    '12家庭醫學科住院照護': {'minimum': 30, 'description': '訓練期間最少30次'},
    '13家庭醫學科門診照護': {'minimum': 40, 'description': '訓練期間最少40次'},
    '14社區醫學實習': {'minimum': 8, 'description': '訓練期間最少8次'},
    '15預防醫學與健康促進': {'minimum': 10, 'description': '訓練期間最少10次'},
    '16家庭醫學科急診照護': {'minimum': 20, 'description': '訓練期間最少20次'},
    '17長期照護': {'minimum': 5, 'description': '訓練期間最少5次'},
    '18家庭醫學科研習': {'minimum': 15, 'description': '訓練期間最少15次'}
}

def show_fam_resident_evaluation_section():
    """顯示家醫部住院醫師評核分頁"""
    st.title("🏥 家醫部住院醫師EPA評核系統")
    st.markdown("---")
    
    # 顯示說明資訊
    st.info("📋 **家醫部住院醫師EPA評核系統** - 追蹤家庭醫學專科醫師訓練期間的EPA項目完成狀況與學習進度")
    
    # 調試模式開關（僅在開發時使用）
    if st.checkbox("🔧 調試模式", help="顯示詳細的資料載入和處理資訊"):
        st.session_state.debug_mode = True
    else:
        st.session_state.debug_mode = False
    
    # 創建分頁
    tab1, tab2 = st.tabs(["📊 資料概覽", "👥 個別評核分析"])
    
    with tab1:
        show_data_overview()
    
    with tab2:
        show_individual_analysis()

def load_fam_data():
    """載入家醫部評核資料"""
    try:
        # 調試：顯示session state中的資料
        if st.session_state.get('debug_mode', False):
            st.write("🔍 調試資訊：")
            st.write("Session state keys:", [key for key in st.session_state.keys() if 'data' in key])
        
        # 優先嘗試載入整合後的資料檔案（使用相對路徑）
        integrated_file = "pages/FAM/integrated_epa_data.csv"
        df = None
        
        try:
            if os.path.exists(integrated_file):
                df = pd.read_csv(integrated_file, encoding='utf-8')
                if st.session_state.get('debug_mode', False):
                    st.write("✅ 從整合資料檔案載入資料")
            else:
                if st.session_state.get('debug_mode', False):
                    st.write("⚠️ 整合資料檔案不存在，嘗試從session state載入")
        except Exception as e:
            if st.session_state.get('debug_mode', False):
                st.write(f"⚠️ 載入整合資料檔案失敗: {str(e)}")
        
        # 如果整合資料檔案不存在或載入失敗，從session state讀取
        if df is None or df.empty:
            if 'fam_data' in st.session_state and st.session_state.fam_data is not None:
                df = st.session_state.fam_data.copy()
                if st.session_state.get('debug_mode', False):
                    st.write("✅ 從 fam_data 載入資料")
            elif '家醫部_data' in st.session_state and st.session_state['家醫部_data'] is not None:
                df = st.session_state['家醫部_data'].copy()
                if st.session_state.get('debug_mode', False):
                    st.write("✅ 從 家醫部_data 載入資料")
            else:
                return None, "請先上傳家醫部EPA評核資料檔案，或確認整合資料檔案存在"
        
        if df is None or df.empty:
            return None, "資料為空，請檢查上傳的檔案"
        
        if st.session_state.get('debug_mode', False):
            st.write(f"📊 原始資料形狀: {df.shape}")
            st.write("📋 原始欄位:", list(df.columns))
            if '資料來源' in df.columns:
                st.write("📊 資料來源分布:", df['資料來源'].value_counts().to_dict())
        
        # 使用資料處理器清理資料
        processor = FAMDataProcessor()
        debug_mode = st.session_state.get('debug_mode', False)
        cleaned_df = processor.clean_data(df, debug=debug_mode)
        
        if st.session_state.get('debug_mode', False):
            st.write(f"🧹 清理後資料形狀: {cleaned_df.shape}")
            if not cleaned_df.empty:
                st.write("👥 學員清單:", cleaned_df['學員'].unique() if '學員' in cleaned_df.columns else "無學員欄位")
                st.write("🎯 EPA項目:", cleaned_df['EPA項目'].unique() if 'EPA項目' in cleaned_df.columns else "無EPA項目欄位")
                if '資料來源' in cleaned_df.columns:
                    st.write("📊 清理後資料來源分布:", cleaned_df['資料來源'].value_counts().to_dict())
        
        return cleaned_df, None
    
    except Exception as e:
        return None, f"載入資料時發生錯誤：{str(e)}"

def show_data_overview():
    """顯示資料概覽"""
    st.subheader("📊 家醫部住院醫師EPA評核資料概覽")
    
    # 載入資料
    df, error = load_fam_data()
    
    if error:
        st.error(error)
        return
    
    if df is None or df.empty:
        st.warning("沒有可用的資料")
        return
    
    # 初始化處理器和視覺化模組
    processor = FAMDataProcessor()
    visualizer = FAMVisualization()
    
    # 取得整體統計資料
    stats = processor.get_overall_statistics(df)
    
    # 顯示統計指標
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總評核記錄數", stats['total_records'])
    
    with col2:
        st.metric("住院醫師人數", stats['unique_students'])
    
    with col3:
        st.metric("EPA項目種類", stats['unique_epa_items'])
    
    with col4:
        st.metric("評核教師人數", stats['unique_teachers'])
    
    # 顯示資料來源資訊
    if '資料來源' in df.columns:
        st.subheader("📊 資料來源分布")
        source_counts = df['資料來源'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**資料來源統計:**")
            for source, count in source_counts.items():
                percentage = (count / len(df)) * 100
                st.write(f"• {source}: {count} 筆 ({percentage:.1f}%)")
        
        with col2:
            # 資料來源圓餅圖
            fig = px.pie(
                values=source_counts.values,
                names=source_counts.index,
                title="資料來源分布",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=300)
            st.plotly_chart(fig, width="stretch")
    
    # 資料時間範圍
    if stats['date_range']:
        st.subheader("📅 資料時間範圍")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("最早記錄", stats['date_range']['start'].strftime('%Y-%m-%d'))
        with col2:
            st.metric("最新記錄", stats['date_range']['end'].strftime('%Y-%m-%d'))
    
    # EPA項目分布
    epa_distribution = processor.get_epa_distribution(df)
    if epa_distribution is not None:
        st.subheader("🎯 EPA項目分布")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = visualizer.create_epa_distribution_chart(epa_distribution)
            st.plotly_chart(fig, width="stretch", key="epa_distribution_chart")
        
        with col2:
            st.subheader("EPA項目清單")
            for epa, count in epa_distribution.items():
                st.write(f"**{epa}**: {count}次")
    
    # 住院醫師分布
    st.subheader("👥 住院醫師評核分布")
    st.info("💡 顯示每個住院醫師整體EPA分數的分布情況")
    
    # 創建每個住院醫師EPA分數的boxplot和折線圖（上下獨立呈現）
    
    # 小提琴圖顯示分數分布
    st.write("**📊 EPA分數分布小提琴圖**")
    fig = visualizer.create_student_epa_scores_boxplot(df)
    if fig:
        st.plotly_chart(fig, width="stretch", key="student_epa_scores_boxplot")
    else:
        st.warning("無法生成住院醫師EPA分數分布圖")
    
    # 折線圖顯示每個學生隨時間的EPA分數趨勢
    st.write("**📈 EPA分數時間趨勢圖**")
    line_fig = visualizer.create_student_epa_scores_line_chart(df)
    if line_fig:
        st.plotly_chart(line_fig, width="stretch", key="student_epa_scores_line_chart")
    else:
        st.warning("無法生成住院醫師EPA分數趨勢圖")
    
    # 複雜程度分布
    complexity_distribution = processor.get_complexity_distribution(df)
    if complexity_distribution is not None:
        st.subheader("📊 複雜程度分布")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = visualizer.create_complexity_distribution_chart(complexity_distribution)
            st.plotly_chart(fig, width="stretch", key="complexity_distribution_chart")
        
        with col2:
            for complexity, count in complexity_distribution.items():
                percentage = (count / len(df)) * 100
                st.metric(complexity, f"{count}次 ({percentage:.1f}%)")

def show_individual_analysis():
    """顯示個別住院醫師分析"""
    st.subheader("👥 個別住院醫師評核分析")
    
    # 載入資料
    df, error = load_fam_data()
    
    if error:
        st.error(error)
        return
    
    if df is None or df.empty:
        st.warning("沒有可用的資料")
        return
    
    # 初始化處理器和視覺化模組
    processor = FAMDataProcessor()
    visualizer = FAMVisualization()
    
    # 選擇住院醫師
    students = processor.get_student_list(df)
    if students:
        selected_student = st.selectbox("選擇住院醫師", students, key="individual_analysis_student")
        
        # 資料來源過濾選項
        if '資料來源' in df.columns:
            data_sources = ['全部'] + list(df['資料來源'].unique())
            selected_source = st.selectbox(
                "資料來源", 
                data_sources, 
                key="individual_analysis_source",
                help="選擇要顯示的資料來源"
            )
        else:
            selected_source = '全部'
        
        if selected_student:
            # 先過濾資料來源
            filtered_df = df.copy()
            if selected_source != '全部' and '資料來源' in df.columns:
                filtered_df = filtered_df[filtered_df['資料來源'] == selected_source]
            
            # 取得該住院醫師的資料（已經過濾過的資料）
            student_data = processor.get_student_data(filtered_df, selected_student)
            
            st.subheader(f"住院醫師：{selected_student}")
            
            # 檢查是否有有效的資料
            if student_data.empty:
                st.warning("該住院醫師沒有有效的評核記錄")
                return
            
            # 基本統計（使用過濾後的資料）
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_evaluations = len(student_data)
                st.metric("總評核次數", total_evaluations)
            
            with col2:
                unique_epa = student_data['EPA項目'].nunique() if 'EPA項目' in student_data.columns else 0
                st.metric("EPA項目種類", unique_epa)
            
            with col3:
                complexity_analysis = processor.get_complexity_analysis(student_data)
                if complexity_analysis and '高' in complexity_analysis['distribution']:
                    high_complexity = complexity_analysis['distribution']['高']
                    st.metric("高複雜度案例", high_complexity)
                else:
                    st.metric("高複雜度案例", 0)
            
            with col4:
                temporal_progress = processor.get_temporal_progress(student_data)
                if temporal_progress is not None and len(temporal_progress) > 1:
                    date_span = (temporal_progress['月份'].max() - temporal_progress['月份'].min()).n
                    st.metric("訓練期間(月)", date_span)
                else:
                    st.metric("訓練期間(月)", "N/A")
            
            # 1. 詳細評核記錄：表格呈現該學生資料
            with st.expander("📋 詳細評核記錄", expanded=False):
                # 使用已經過濾的資料
                if not student_data.empty:
                    display_columns = ['日期', 'EPA項目', '病歷號碼', '個案姓名', '診斷', '複雜程度', '觀察場域', '信賴程度(教師評量)', '信賴程度(教師評量)_數值', '教師給學員回饋']
                    
                    # 如果有資料來源欄位，將其加入顯示欄位中
                    if '資料來源' in student_data.columns:
                        display_columns.append('資料來源')
                    
                    available_columns = [col for col in display_columns if col in student_data.columns]
                        
                    if available_columns:
                        st.dataframe(
                            student_data[available_columns],
                            width="stretch",
                            hide_index=True
                        )
                        
                        # 顯示統計資訊
                        st.write(f"📊 顯示 {len(student_data)} 筆有效記錄")
                        
                        # 顯示EPA項目統計
                        if 'EPA項目' in available_columns:
                            epa_counts = student_data['EPA項目'].value_counts()
                            
                            st.write(f"📋 EPA項目統計:")
                            st.write(f"  • 有EPA項目的記錄: {len(epa_counts)} 種，共 {len(student_data)} 筆")
                            st.write(f"  • 空EPA項目的記錄: 0 筆")
                            
                            if len(epa_counts) > 0:
                                st.write(f"  • EPA項目分佈:")
                                for epa, count in epa_counts.items():
                                    st.write(f"    - {epa}: {count} 筆")
                        
                        # 顯示調試資訊
                        if st.session_state.get('debug_mode', False):
                            st.write(f"🔍 調試資訊:")
                            st.write(f"  • 有效記錄數: {len(student_data)}")
                            st.write(f"  • 過濾條件已應用於資料處理層")
                    else:
                        st.info("暫無可顯示的詳細記錄")
                else:
                    st.info("沒有找到有效的資料")
            
            # 2. 信賴程度分析：雷達圖呈現所有EPA項目
            reliability_analysis = processor.calculate_reliability_progress(student_data)
            if reliability_analysis:
                st.subheader("📈 信賴程度分析")
                
                # 創建雷達圖顯示各EPA項目的信賴程度
                radar_fig = visualizer.create_reliability_radar_chart(
                    student_data, 
                    selected_student,
                    f"{selected_student} - 各EPA項目信賴程度雷達圖"
                )
                
                if radar_fig:
                    st.plotly_chart(radar_fig, width="stretch", key="individual_reliability_radar")
                else:
                    st.info("無法生成雷達圖，可能缺少EPA項目或信賴程度資料")
                
                # 顯示統計資訊
                st.write("**信賴程度統計：**")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("平均信賴程度", f"{reliability_analysis['average']:.1f}")
                
                with col2:
                    total_evaluations = sum(reliability_analysis['distribution'].values())
                    st.metric("總評核次數", total_evaluations)
                
                with col3:
                    # 計算最高信賴程度的百分比
                    max_level = max(reliability_analysis['distribution'], key=reliability_analysis['distribution'].get)
                    max_percentage = (reliability_analysis['distribution'][max_level] / total_evaluations) * 100
                    st.metric("最高信賴程度", f"{max_percentage:.1f}%")
                
                with col4:
                    # 計算獨立執行的百分比
                    independent_count = reliability_analysis['distribution'].get('獨立執行', 0)
                    independent_percentage = (independent_count / total_evaluations) * 100
                    st.metric("獨立執行比例", f"{independent_percentage:.1f}%")
                
                # 創建信賴程度boxplot
                boxplot_fig = visualizer.create_reliability_boxplot(student_data, selected_student)
                if boxplot_fig:
                    st.plotly_chart(boxplot_fig, width="stretch", key="individual_reliability_boxplot")
                else:
                    # 備用：顯示分布統計
                    st.write("**信賴程度分布：**")
                    for level, count in reliability_analysis['distribution'].items():
                        percentage = (count / sum(reliability_analysis['distribution'].values())) * 100
                        st.write(f"• {level}: {count}次 ({percentage:.1f}%)")
            else:
                st.info("暫無信賴程度評量資料")
            
            # 3. EPA項目趨勢分析：左邊boxplot，右邊老師回饋
            st.subheader("📊 EPA項目趨勢分析")
            st.info("💡 左邊顯示EPA項目信賴程度變化趨勢，右邊顯示相關教師回饋")
            
            # 資料來源過濾選項（用於趨勢分析）
            if '資料來源' in filtered_df.columns:
                trend_data_sources = ['全部'] + list(filtered_df['資料來源'].unique())
                selected_trend_source = st.selectbox(
                    "趨勢分析資料來源", 
                    trend_data_sources, 
                    key="trend_analysis_source",
                    help="選擇要顯示在趨勢分析中的資料來源"
                )
                
                # 根據選擇過濾趨勢分析資料
                if selected_trend_source != '全部':
                    trend_df = filtered_df[filtered_df['資料來源'] == selected_trend_source]
                else:
                    trend_df = filtered_df
            else:
                trend_df = filtered_df
                selected_trend_source = '全部'
            
            # 獲取所有EPA項目
            epa_items = processor.get_epa_items(trend_df)
            
            if epa_items:
                # 為每個EPA項目創建左右布局
                for epa_item in epa_items:
                    # 使用過濾後的趨勢分析資料
                    epa_data = trend_df[trend_df['學員'] == selected_student]
                    epa_data = epa_data[epa_data['EPA項目'] == epa_item]
                    
                    # 創建左右兩欄布局（1:1比例）
                    col_left, col_right = st.columns([1, 1])
                    
                    with col_left:
                        if not epa_data.empty:
                            # 創建增強版趨勢圖（支援多資料來源）
                            try:
                                # 優先使用增強版趨勢圖
                                enhanced_fig = visualizer.create_enhanced_monthly_trend_chart(
                                    epa_data,
                                    epa_item,
                                    selected_student
                                )
                                
                                if enhanced_fig is not None:
                                    st.plotly_chart(enhanced_fig, width="stretch", key=f"epa_enhanced_trend_{epa_item}")
                                else:
                                    # 備用：計算月度趨勢並使用簡化版趨勢圖
                                    monthly_trend_data = processor.calculate_monthly_epa_trend(epa_data, epa_item)
                                    
                                    if monthly_trend_data is not None and not monthly_trend_data.empty:
                                        simple_fig = visualizer.create_simple_monthly_trend_chart(
                                            monthly_trend_data,
                                            epa_item,
                                            selected_student,
                                            epa_data
                                        )
                                        
                                        if simple_fig is not None:
                                            st.plotly_chart(simple_fig, width="stretch", key=f"epa_trend_{epa_item}")
                                        else:
                                            # 最後備用：完整版趨勢圖
                                            trend_fig = visualizer.create_epa_monthly_trend_chart(
                                                monthly_trend_data, 
                                                epa_item, 
                                                selected_student
                                            )
                                            
                                            if trend_fig is not None:
                                                st.plotly_chart(trend_fig, width="stretch", key=f"epa_trend_full_{epa_item}")
                            
                            except Exception as e:
                                st.error(f"❌ {epa_item} 趨勢圖創建時發生異常: {str(e)}")
                                
                            # 顯示趨勢統計
                            st.write(f"**{epa_item} 統計：**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("總評核次數", len(epa_data))
                                
                                # 顯示資料來源統計
                                if '資料來源' in epa_data.columns:
                                    source_counts = epa_data['資料來源'].value_counts()
                                    st.write("**資料來源分布：**")
                                    for source, count in source_counts.items():
                                        st.write(f"• {source}: {count} 次")
                                else:
                                    st.metric("評核月數", "N/A")
                            
                            with col2:
                                # 計算整體平均信賴程度
                                if '信賴程度(教師評量)_數值' in epa_data.columns:
                                    avg_score = epa_data['信賴程度(教師評量)_數值'].mean()
                                    st.metric("平均信賴程度", f"{avg_score:.2f}")
                                    
                                    # 顯示各資料來源的平均信賴程度
                                    if '資料來源' in epa_data.columns:
                                        st.write("**各來源平均信賴程度：**")
                                        source_avg = epa_data.groupby('資料來源')['信賴程度(教師評量)_數值'].mean()
                                        for source, avg in source_avg.items():
                                            st.write(f"• {source}: {avg:.2f}")
                                else:
                                    st.metric("平均信賴程度", "N/A")
                        else:
                            st.info(f"ℹ️ {epa_item} 尚未有足夠的月度評核記錄來呈現趨勢。")
                    
                    with col_right:
                        # 顯示該EPA項目的教師回饋
                        st.write(f"**{epa_item} 教師回饋**")
                        
                        # 獲取該EPA項目的教師回饋（使用完整的過濾資料，包含EMYWAY資料）
                        feedback_data = filtered_df[
                            (filtered_df['學員'] == selected_student) & 
                            (filtered_df['EPA項目'] == epa_item)
                        ]
                        feedback_data = feedback_data[feedback_data['教師給學員回饋'].notna() & (feedback_data['教師給學員回饋'] != '')]
                        
                        if not feedback_data.empty:
                            # 按時間排序教師回饋（最新在前）
                            feedback_data_copy = feedback_data.copy()
                            if '日期' in feedback_data_copy.columns:
                                feedback_data_copy['日期'] = pd.to_datetime(feedback_data_copy['日期'], errors='coerce')
                                # 按日期降序排列（最新在前），無效日期放在最後
                                feedback_data_copy = feedback_data_copy.sort_values('日期', ascending=False)
                            
                            # 準備表格數據
                            table_data = []
                            for idx, (_, row) in enumerate(feedback_data_copy.iterrows(), 1):
                                # 格式化日期
                                date_str = "N/A"
                                if '日期' in row and pd.notna(row['日期']):
                                    if hasattr(row['日期'], 'strftime'):
                                        date_str = row['日期'].strftime('%Y-%m-%d')
                                    else:
                                        date_str = str(row['日期'])
                                
                                # 處理回饋內容，保留換行符並移除字符限制
                                feedback_content = str(row['教師給學員回饋']).strip()
                                
                                # 獲取資料來源
                                data_source = row.get('資料來源', '未知來源')
                                
                                table_data.append({
                                    '日期': date_str,
                                    '回饋內容': feedback_content,
                                    '資料來源': data_source
                                })
                            
                            # 創建DataFrame並顯示表格
                            feedback_df = pd.DataFrame(table_data)
                            
                            # 使用自定義CSS實現垂直滾動的教師回饋區域
                            st.markdown("""
                            <style>
                            .feedback-scroll-container {
                                max-height: 300px;
                                overflow-y: auto;
                                border: 1px solid #e1e5e9;
                                border-radius: 0.5rem;
                                padding: 15px;
                                margin: 10px 0;
                                background-color: #fafafa;
                            }
                            .feedback-item {
                                margin-bottom: 15px;
                                padding-bottom: 10px;
                                border-bottom: 1px dashed #ddd;
                            }
                            .feedback-item:last-child {
                                border-bottom: none;
                                margin-bottom: 0;
                            }
                            .feedback-date {
                                font-weight: bold;
                                color: #2563eb;
                                margin-bottom: 5px;
                            }
                            .feedback-content {
                                margin-left: 10px;
                                line-height: 1.6;
                                color: #374151;
                            }
                            .feedback-content ul {
                                margin: 5px 0;
                                padding-left: 20px;
                            }
                            .feedback-content li {
                                margin-bottom: 3px;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            st.write("**教師回饋內容：**")
                            
                            # 創建滾動容器
                            html_content = '<div class="feedback-scroll-container">'
                            
                            for i, row in feedback_df.iterrows():
                                date_str = row['日期']
                                feedback_text = str(row['回饋內容']).strip()
                                data_source = row.get('資料來源', '未知來源')
                                
                                html_content += '<div class="feedback-item">'
                                html_content += f'<div class="feedback-date">📅 {date_str} | 📊 {data_source}</div>'
                                
                                if feedback_text and feedback_text != 'nan':
                                    # 處理回饋內容，保持原始格式
                                    feedback_lines = feedback_text.split('\n')
                                    html_content += '<div class="feedback-content"><ul>'
                                    for line in feedback_lines:
                                        if line.strip():  # 只顯示非空行
                                            # 轉義HTML特殊字符
                                            escaped_line = line.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                            html_content += f'<li>{escaped_line}</li>'
                                    html_content += '</ul></div>'
                                else:
                                    html_content += '<div class="feedback-content"><ul><li>無回饋內容</li></ul></div>'
                                
                                html_content += '</div>'
                            
                            html_content += '</div>'
                            
                            st.markdown(html_content, unsafe_allow_html=True)
                            
                            # 添加滾動提示
                            st.caption("💡 提示：可以上下滾動查看所有回饋內容")
                            
                            # 顯示回饋統計
                            total_feedback = len(feedback_data)
                            st.write(f"**回饋統計：**")
                            st.write(f"• 總回饋次數: {total_feedback}")
                            
                            # 計算各資料來源的回饋統計
                            if '資料來源' in feedback_data.columns:
                                source_feedback_counts = feedback_data['資料來源'].value_counts()
                                st.write("• 各來源回饋次數:")
                                for source, count in source_feedback_counts.items():
                                    st.write(f"  - {source}: {count} 次")
                            
                            # 計算回饋率（使用完整的過濾資料作為分母）
                            total_records = len(filtered_df[
                                (filtered_df['學員'] == selected_student) & 
                                (filtered_df['EPA項目'] == epa_item)
                            ])
                            if total_records > 0:
                                feedback_rate = (total_feedback/total_records)*100
                                st.write(f"• 回饋率: {feedback_rate:.1f}%")
                        else:
                            st.info("暫無教師回饋")
                    
                    # 在每個EPA項目之間添加分隔線
                    st.divider()
            else:
                st.warning("❌ 沒有找到EPA項目")
            
    else:
        st.warning("沒有找到住院醫師資料")



# 主要功能函數
def main():
    """主要功能"""
    show_fam_resident_evaluation_section()

if __name__ == "__main__":
    main()
