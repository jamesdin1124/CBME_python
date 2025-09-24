import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date
import numpy as np
import re

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
    tab1, tab2, tab3, tab4 = st.tabs(["📊 資料概覽", "👥 個別評核分析", "🎯 EPA項目追蹤", "📈 學習進度分析"])
    
    with tab1:
        show_data_overview()
    
    with tab2:
        show_individual_analysis()
    
    with tab3:
        show_epa_tracking()
    
    with tab4:
        show_learning_progress()

def load_fam_data():
    """載入家醫部評核資料"""
    try:
        # 調試：顯示session state中的資料
        if st.session_state.get('debug_mode', False):
            st.write("🔍 調試資訊：")
            st.write("Session state keys:", [key for key in st.session_state.keys() if 'data' in key])
        
        # 從session state讀取家醫部資料
        df = None
        if 'fam_data' in st.session_state and st.session_state.fam_data is not None:
            df = st.session_state.fam_data.copy()
            if st.session_state.get('debug_mode', False):
                st.write("✅ 從 fam_data 載入資料")
        elif '家醫部_data' in st.session_state and st.session_state['家醫部_data'] is not None:
            df = st.session_state['家醫部_data'].copy()
            if st.session_state.get('debug_mode', False):
                st.write("✅ 從 家醫部_data 載入資料")
        else:
            return None, "請先上傳家醫部EPA評核資料檔案"
        
        if df is None or df.empty:
            return None, "資料為空，請檢查上傳的檔案"
        
        if st.session_state.get('debug_mode', False):
            st.write(f"📊 原始資料形狀: {df.shape}")
            st.write("📋 原始欄位:", list(df.columns))
        
        # 使用資料處理器清理資料
        processor = FAMDataProcessor()
        debug_mode = st.session_state.get('debug_mode', False)
        cleaned_df = processor.clean_data(df, debug=debug_mode)
        
        if st.session_state.get('debug_mode', False):
            st.write(f"🧹 清理後資料形狀: {cleaned_df.shape}")
            if not cleaned_df.empty:
                st.write("👥 學員清單:", cleaned_df['學員'].unique() if '學員' in cleaned_df.columns else "無學員欄位")
                st.write("🎯 EPA項目:", cleaned_df['EPA項目'].unique() if 'EPA項目' in cleaned_df.columns else "無EPA項目欄位")
        
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
            st.plotly_chart(fig, use_container_width=True, key="epa_distribution_chart")
        
        with col2:
            st.subheader("EPA項目清單")
            for epa, count in epa_distribution.items():
                st.write(f"**{epa}**: {count}次")
    
    # 住院醫師分布
    st.subheader("👥 住院醫師評核分布")
    st.info("💡 顯示每個住院醫師整體EPA分數的分布情況")
    
    # 創建每個住院醫師EPA分數的boxplot和折線圖
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Boxplot顯示分數分布
        fig = visualizer.create_student_epa_scores_boxplot(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="student_epa_scores_boxplot")
        else:
            st.warning("無法生成住院醫師EPA分數分布圖")
    
    with col2:
        # 折線圖顯示每個學生隨時間的EPA分數趨勢
        line_fig = visualizer.create_student_epa_scores_line_chart(df)
        if line_fig:
            st.plotly_chart(line_fig, use_container_width=True, key="student_epa_scores_line_chart")
        else:
            st.warning("無法生成住院醫師EPA分數趨勢圖")
    
    # 複雜程度分布
    complexity_distribution = processor.get_complexity_distribution(df)
    if complexity_distribution is not None:
        st.subheader("📊 複雜程度分布")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = visualizer.create_complexity_distribution_chart(complexity_distribution)
            st.plotly_chart(fig, use_container_width=True, key="complexity_distribution_chart")
        
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
        
        if selected_student:
            # 取得該住院醫師的資料（已經過濾過的資料）
            student_data = processor.get_student_data(df, selected_student)
            
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
                    available_columns = [col for col in display_columns if col in student_data.columns]
                        
                    if available_columns:
                        st.dataframe(
                            student_data[available_columns],
                            use_container_width=True,
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
                    st.plotly_chart(radar_fig, use_container_width=True, key="individual_reliability_radar")
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
                    st.plotly_chart(boxplot_fig, use_container_width=True, key="individual_reliability_boxplot")
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
            
            # 獲取所有EPA項目
            epa_items = processor.get_epa_items(df)
            
            if epa_items:
                # 為每個EPA項目創建左右布局
                for epa_item in epa_items:
                    epa_data = student_data[student_data['EPA項目'] == epa_item]
                    
                    if not epa_data.empty:
                        # 創建左右兩欄布局（1:1比例）
                        col_left, col_right = st.columns([1, 1])
                        
                        with col_left:
                            # 計算該EPA項目的月度趨勢
                            monthly_trend_data = processor.calculate_monthly_epa_trend(epa_data, epa_item)
                            
                            if monthly_trend_data is not None and not monthly_trend_data.empty:
                                # 創建boxplot趨勢圖
                                try:
                                    # 優先使用簡化版趨勢圖（箱線圖）
                                    simple_fig = visualizer.create_simple_monthly_trend_chart(
                                        monthly_trend_data,
                                        epa_item,
                                        selected_student,
                                        epa_data  # 傳入原始數據用於更好的boxplot
                                    )
                                    
                                    if simple_fig is not None:
                                        st.plotly_chart(simple_fig, use_container_width=True, key=f"epa_trend_{epa_item}")
                                    else:
                                        # 備用：嘗試完整版趨勢圖
                                        trend_fig = visualizer.create_epa_monthly_trend_chart(
                                            monthly_trend_data, 
                                            epa_item, 
                                            selected_student
                                        )
                                        
                                        if trend_fig is not None:
                                            st.plotly_chart(trend_fig, use_container_width=True, key=f"epa_trend_full_{epa_item}")
                            
                                except Exception as e:
                                    st.error(f"❌ {epa_item} 趨勢圖創建時發生異常: {str(e)}")
                                
                                # 顯示趨勢統計
                                st.write(f"**{epa_item} 統計：**")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("總評核次數", len(epa_data))
                                    st.metric("評核月數", len(monthly_trend_data))
                                with col2:
                                    # 計算整體平均信賴程度
                                    if '信賴程度(教師評量)_數值' in epa_data.columns:
                                        avg_score = epa_data['信賴程度(教師評量)_數值'].mean()
                                        st.metric("平均信賴程度", f"{avg_score:.2f}")
                                    else:
                                        st.metric("平均信賴程度", "N/A")
                                    
                                    # 計算趨勢變化
                                    if len(monthly_trend_data) >= 2:
                                        first_score = monthly_trend_data.iloc[0]['平均信賴程度']
                                        last_score = monthly_trend_data.iloc[-1]['平均信賴程度']
                                        trend_change = last_score - first_score
                                        st.metric("趨勢變化", f"{trend_change:+.2f}")
                                    else:
                                        st.metric("趨勢變化", "N/A")
                            else:
                                st.info(f"ℹ️ {epa_item} 尚未有足夠的月度評核記錄來呈現趨勢。")
                        
                        with col_right:
                            # 顯示該EPA項目的教師回饋
                            st.write(f"**{epa_item} 教師回饋**")
                            
                            # 獲取該EPA項目的教師回饋
                            feedback_data = epa_data[epa_data['教師給學員回饋'].notna() & (epa_data['教師給學員回饋'] != '')]
                            
                            if not feedback_data.empty:
                                # 準備表格數據
                                table_data = []
                                for idx, (_, row) in enumerate(feedback_data.iterrows(), 1):
                                    # 格式化日期
                                    date_str = "N/A"
                                    if '日期' in row and pd.notna(row['日期']):
                                        if hasattr(row['日期'], 'strftime'):
                                            date_str = row['日期'].strftime('%Y-%m-%d')
                                        else:
                                            date_str = str(row['日期'])
                                    
                                    table_data.append({
                                        '日期': date_str,
                                        '回饋內容': str(row['教師給學員回饋'])[:100] + ('...' if len(str(row['教師給學員回饋'])) > 100 else '')
                                    })
                                
                                # 創建DataFrame並顯示表格
                                feedback_df = pd.DataFrame(table_data)
                                
                                # 使用Streamlit表格顯示
                                st.dataframe(
                                    feedback_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "日期": st.column_config.TextColumn(
                                            "日期",
                                            help="評核日期",
                                            width="small"
                                        ),
                                        "回饋內容": st.column_config.TextColumn(
                                            "回饋內容",
                                            help="教師給學員的回饋內容",
                                            width="large"
                                        )
                                    },
                                    height=300  # 設置固定高度，使表格可滾動
                                )
                                
                                # 顯示回饋統計
                                total_feedback = len(feedback_data)
                                st.write(f"**回饋統計：**")
                                st.write(f"• 總回饋次數: {total_feedback}")
                                st.write(f"• 回饋率: {(total_feedback/len(epa_data)*100):.1f}%")
                            else:
                                st.info("暫無教師回饋")
                    
                    # 在每個EPA項目之間添加分隔線
                    st.divider()
            else:
                st.warning("❌ 沒有找到EPA項目")
            
    else:
        st.warning("沒有找到住院醫師資料")

def show_epa_tracking():
    """顯示EPA項目追蹤"""
    st.subheader("🎯 EPA項目完成追蹤")
    
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
        selected_student = st.selectbox("選擇住院醫師", students, key="epa_tracking_student")
        
        if selected_student:
            student_data = processor.get_student_data(df, selected_student)
            
            st.subheader(f"{selected_student} - EPA項目完成追蹤")
            
            # 計算EPA項目完成狀況
            progress_df = processor.calculate_epa_progress(student_data)
            
            # 顯示進度條
            st.subheader("完成進度")
            for _, row in progress_df.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.progress(row['完成率(%)'] / 100)
                    st.write(f"**{row['EPA項目']}**: {row['已完成次數']}/{row['要求次數']} 次")
                with col2:
                    st.write(row['狀態'])
            
            # 進度圖表
            fig = visualizer.create_epa_progress_chart(progress_df, selected_student)
            st.plotly_chart(fig, use_container_width=True, key="epa_progress_chart")
            
            # 詳細完成狀況表格
            st.subheader("詳細完成狀況")
            st.dataframe(
                progress_df,
                use_container_width=True,
                hide_index=True
            )
            
            # EPA項目詳細分析（保留原有功能）
            st.subheader("🔍 EPA項目詳細分析")
            epa_items = processor.get_epa_items(df)
            if epa_items:
                selected_epa = st.selectbox("選擇EPA項目進行詳細分析", epa_items, key="epa_detail_analysis")
                
                if selected_epa:
                    epa_data = student_data[student_data['EPA項目'] == selected_epa]
                    
                    if not epa_data.empty:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("完成次數", len(epa_data))
                            st.metric("要求次數", FAM_EPA_REQUIREMENTS.get(selected_epa, {}).get('minimum', 0))
                        
                        with col2:
                            if '複雜程度' in epa_data.columns:
                                complexity_counts = epa_data['複雜程度'].value_counts()
                                st.write("複雜度分布:")
                                for complexity, count in complexity_counts.items():
                                    st.write(f"- {complexity}: {count}次")
                        
                        # 時間進度分析
                        epa_temporal_data = processor.get_epa_temporal_progress(student_data, selected_epa)
                        if epa_temporal_data is not None:
                            st.subheader(f"{selected_epa} - 時間進度分析")
                            fig = visualizer.create_epa_temporal_chart(epa_temporal_data, selected_epa, selected_student)
                            st.plotly_chart(fig, use_container_width=True, key=f"epa_comparison_{selected_epa}")
                    else:
                        st.info(f"該住院醫師尚未完成任何 {selected_epa} 項目")
    else:
        st.warning("沒有找到住院醫師資料")

def show_learning_progress():
    """顯示學習進度分析"""
    st.subheader("📈 學習進度分析")
    
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
        selected_student = st.selectbox("選擇住院醫師", students, key="learning_progress_student")
        
        if selected_student:
            student_data = processor.get_student_data(df, selected_student)
            
            # 時間序列分析
            temporal_progress = processor.get_temporal_progress(student_data)
            if temporal_progress is not None:
                st.subheader(f"{selected_student} - 學習進度時間軸")
                
                # 轉換月份為字串格式
                temporal_progress['月份'] = temporal_progress['月份'].astype(str)
                
                fig = visualizer.create_temporal_progress_chart(temporal_progress)
                st.plotly_chart(fig, use_container_width=True, key="learning_progress_chart")
                
                # EPA項目學習進度
                epa_items = processor.get_epa_items(df)
                if epa_items:
                    st.subheader("EPA項目學習進度")
                    
                    # 選擇特定EPA項目
                    selected_epa = st.selectbox("選擇EPA項目", epa_items, key="epa_progress_item")
                    
                    if selected_epa:
                        epa_temporal_data = processor.get_epa_temporal_progress(student_data, selected_epa)
                        if epa_temporal_data is not None:
                            fig = visualizer.create_epa_temporal_chart(epa_temporal_data, selected_epa, selected_student)
                            st.plotly_chart(fig, use_container_width=True, key=f"learning_epa_temporal_{selected_epa}")
                        else:
                            st.info(f"該住院醫師尚未完成任何 {selected_epa} 項目")
            
            # 複雜度挑戰進度
            complexity_analysis = processor.get_complexity_analysis(student_data)
            if complexity_analysis:
                st.subheader("複雜度挑戰進度")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig = visualizer.create_complexity_challenge_chart(
                        complexity_analysis['counts'], 
                        selected_student
                    )
                    st.plotly_chart(fig, use_container_width=True, key="complexity_challenge_chart")
                
                with col2:
                    st.subheader("複雜度統計")
                    st.metric("平均複雜度", f"{complexity_analysis['average']:.1f}")
                    
                    total_cases = sum(complexity_analysis['distribution'].values())
                    for complexity, count in complexity_analysis['distribution'].items():
                        percentage = (count / total_cases) * 100
                        st.metric(complexity, f"{count}次 ({percentage:.1f}%)")
            
            # 同儕比較
            st.subheader("同儕比較分析")
            epa_items = processor.get_epa_items(df)
            if epa_items:
                # 選擇比較模式
                comparison_mode = st.radio(
                    "選擇比較模式",
                    ["完成次數比較", "信賴程度比較", "全部EPA項目比較"],
                    key="comparison_mode"
                )
                
                if comparison_mode == "全部EPA項目比較":
                    # 創建包含所有EPA項目的比較雷達圖
                    st.subheader("🏥 全部EPA項目同儕比較")
                    st.info("💡 此雷達圖顯示所有學員在各個EPA項目上的信賴程度表現")
                    
                    # 創建全部EPA項目比較雷達圖
                    all_epa_radar_fig = visualizer.create_all_epa_comparison_radar_chart(
                        df,
                        f"所有學員 - 全部EPA項目信賴程度比較"
                    )
                    
                    if all_epa_radar_fig:
                        st.plotly_chart(all_epa_radar_fig, use_container_width=True, key="peer_all_epa_radar")
                        
                        # 顯示該學員的整體表現摘要
                        st.subheader(f"{selected_student} - 整體EPA表現摘要")
                        overall_analysis = processor.calculate_reliability_progress(student_data)
                        if overall_analysis:
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("平均信賴程度", f"{overall_analysis['average']:.1f}")
                            with col2:
                                st.metric("總評核次數", overall_analysis['total_count'])
                            with col3:
                                st.metric("EPA項目種類", len(overall_analysis['distribution']))
                            with col4:
                                # 計算最高信賴程度
                                max_reliability = max(overall_analysis['distribution'].keys(), 
                                                    key=lambda x: {'不允許學員觀察': 0, '學員在旁觀察': 1, '教師在旁逐步共同操作': 2, 
                                                                 '教師在旁必要時協助': 3, '教師事後重點確認': 4, '必要時知會教師確認': 4, '獨立執行': 5}.get(x, 0))
                                st.metric("最高信賴程度", max_reliability)
                    else:
                        st.info("無法生成全部EPA項目比較雷達圖，可能缺少信賴程度資料")
                
                else:
                    selected_epa_comparison = st.selectbox("選擇EPA項目進行同儕比較", epa_items, key="epa_comparison")
                    
                    if selected_epa_comparison:
                        if comparison_mode == "完成次數比較":
                            # 計算所有住院醫師在該EPA項目的完成次數
                            all_students_epa = df[df['EPA項目'] == selected_epa_comparison]['學員'].value_counts()
                            
                            fig = visualizer.create_epa_comparison_chart(all_students_epa, selected_epa_comparison)
                            st.plotly_chart(fig, use_container_width=True, key=f"peer_epa_comparison_{selected_epa_comparison}")
                            
                            # 顯示排名
                            current_student_count = all_students_epa.get(selected_student, 0)
                            rank = (all_students_epa >= current_student_count).sum()
                            total_students = len(all_students_epa)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("完成次數", current_student_count)
                            with col2:
                                st.metric("排名", f"{rank}/{total_students}")
                            with col3:
                                percentile = ((total_students - rank + 1) / total_students) * 100
                                st.metric("百分位數", f"{percentile:.1f}%")
                        
                        else:  # 信賴程度比較
                            # 創建信賴程度比較雷達圖
                            radar_fig = visualizer.create_epa_comparison_radar_chart(
                                df, 
                                selected_epa_comparison,
                                f"各學員 - {selected_epa_comparison} 信賴程度比較"
                            )
                            
                            if radar_fig:
                                st.plotly_chart(radar_fig, use_container_width=True, key=f"peer_reliability_radar_{selected_epa_comparison}")
                            else:
                                st.info("無法生成信賴程度比較雷達圖，可能缺少信賴程度資料")
                            
                            # 顯示該學員在該EPA項目的表現
                            student_epa_data = student_data[student_data['EPA項目'] == selected_epa_comparison]
                            if not student_epa_data.empty:
                                reliability_analysis = processor.calculate_reliability_progress(student_epa_data)
                                if reliability_analysis:
                                    st.subheader(f"{selected_student} - {selected_epa_comparison} 表現")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("平均信賴程度", f"{reliability_analysis['average']:.1f}")
                                    with col2:
                                        st.metric("評核次數", len(student_epa_data))
    else:
        st.warning("沒有找到住院醫師資料")

# 主要功能函數
def main():
    """主要功能"""
    show_fam_resident_evaluation_section()

if __name__ == "__main__":
    main()
