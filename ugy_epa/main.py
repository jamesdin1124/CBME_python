import streamlit as st
import re
import pandas as pd
import plotly.graph_objects as go
from ugy_epa.modules.google_connection import fetch_google_form_data
from ugy_epa.modules.data_processing import (
    process_epa_level, 
    convert_date_to_batch, 
    convert_tw_time
)
from ugy_epa.modules.visualization import plot_radar_chart, plot_trend_chart, plot_epa_trend
# 暫時註解掉不需要的導入
# from ugy_epa.modules.data_analysis import analyze_epa_data

def load_sheet_data(sheet_title=None):
    """載入Google表單資料
    
    Args:
        sheet_title (str, optional): 工作表名稱
        
    Returns:
        tuple: (DataFrame, sheet_titles list)
    """
    df, sheet_titles = fetch_google_form_data(sheet_title=sheet_title)
    
    # 加入除錯資訊
    if sheet_title:
        st.write(f"正在載入工作表：{sheet_title}")
    if df is not None:
        st.write(f"載入資料大小：{df.shape}")
    
    return df, sheet_titles

def process_data(df):
    """處理EPA資料"""
    if df is not None:
        try:
            st.write("開始處理資料...")
            
            # 移除重複欄位
            df = df.loc[:, ~df.columns.duplicated()]
            st.write("已移除重複欄位")
            
            # 檢查必要欄位
            required_columns = ['學員自評EPA等級', '教師評核EPA等級']  # 移除時間戳記檢查
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"缺少必要欄位：{missing_columns}")
                st.write("目前可用欄位：", df.columns.tolist())
                return None
        
            
            try:
                df['學員自評EPA等級'] = df['學員自評EPA等級'].apply(process_epa_level)
                df['教師評核EPA等級'] = df['教師評核EPA等級'].apply(process_epa_level)
            except Exception as e:
                st.error(f"EPA等級轉換失敗：{str(e)}")
                return None
            

            
            # 日期轉換和梯次處理
            try:
                if '時間戳記' in df.columns:
                    df['評核日期'] = df['時間戳記'].apply(convert_tw_time)
                    df['評核日期'] = df['評核日期'].dt.date
                elif '評核時間' in df.columns:  # 檢查其他可能的日期欄位名稱
                    df['評核日期'] = pd.to_datetime(df['評核時間']).dt.date
                
                if '評核日期' in df.columns:
                    df['梯次'] = df['評核日期'].astype(str).apply(convert_date_to_batch)
                    st.write("日期轉換成功")
                else:
                    st.warning("找不到日期欄位，跳過梯次處理")
            except Exception as e:
                st.error(f"日期處理失敗：{str(e)}")
                # 即使日期處理失敗，仍然繼續處理
            
            st.write("資料處理完成")
            return df
            
        except Exception as e:
            st.error(f"資料處理時發生錯誤：{str(e)}")
            st.exception(e)
            return None
    else:
        st.error("輸入的資料框為空")
        return None

def display_data_preview(df):
    """顯示資料預覽
    
    Args:
        df (DataFrame): 處理後的資料框
    """
    st.subheader("資料預覽")
    st.dataframe(df.head(10))

def display_visualizations(df):
    """顯示資料視覺化"""
    st.header("資料視覺化")
    
    # ========== 1. 計算梯次排序（背景處理） ==========
    try:
        # 創建一個字典來保存每個階層的梯次排序
        layer_batch_orders = {}
        
        # 獲取所有階層
        if '階層' in df.columns:
            layers = df['階層'].unique()
            
            # 對每個階層進行處理
            for layer in layers:
                # 篩選該階層的資料
                layer_df = df[df['階層'] == layer].copy()
                
                # 處理梯次日期
                try:
                    # 嘗試轉換為日期
                    layer_df['梯次日期'] = pd.to_datetime(layer_df['梯次'], errors='coerce')
                    
                    # 處理無法直接轉換的日期
                    if layer_df['梯次日期'].isna().any():
                        import re
                        date_pattern = re.compile(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})')
                        
                        for idx, value in layer_df[layer_df['梯次日期'].isna()]['梯次'].items():
                            if isinstance(value, str):
                                match = date_pattern.search(value)
                                if match:
                                    year, month, day = match.groups()
                                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                    layer_df.loc[idx, '梯次日期'] = pd.to_datetime(date_str, errors='coerce')
                except:
                    # 如果轉換失敗，使用原始梯次順序
                    layer_batch_orders[layer] = layer_df['梯次'].unique().tolist()
                    continue
                
                # 計算每個梯次的統計資料並排序
                stats_df = layer_df.groupby('梯次').agg({'梯次日期': 'first'}).reset_index()
                sorted_stats = stats_df.sort_values('梯次日期')
                
                # 保存排序後的梯次列表
                if not sorted_stats.empty:
                    layer_batch_orders[layer] = sorted_stats['梯次'].tolist()
                else:
                    layer_batch_orders[layer] = []
            
            # 計算全局梯次順序
            all_batches_df = pd.DataFrame({'梯次': df['梯次'].unique()})
            
            try:
                # 嘗試將所有梯次轉換為日期
                all_batches_df['梯次日期'] = pd.to_datetime(all_batches_df['梯次'], errors='coerce')
                
                # 處理未轉換成功的日期
                if all_batches_df['梯次日期'].isna().any():
                    for idx, value in all_batches_df[all_batches_df['梯次日期'].isna()]['梯次'].items():
                        if isinstance(value, str):
                            match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', value)
                            if match:
                                year, month, day = match.groups()
                                date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                all_batches_df.loc[idx, '梯次日期'] = pd.to_datetime(date_str, errors='coerce')
                
                # 排序
                global_sorted_batches = all_batches_df.sort_values('梯次日期')['梯次'].tolist()
            except:
                global_sorted_batches = df['梯次'].unique().tolist()
        else:
            # 如果沒有階層欄位，使用默認值
            layer_batch_orders = {}
            global_sorted_batches = df['梯次'].unique().tolist() if '梯次' in df.columns else []
            
    except Exception as e:
        # 如果排序過程出錯，使用默認值
        layer_batch_orders = {layer: df[df['階層'] == layer]['梯次'].unique().tolist() 
                            for layer in df['階層'].unique()} if '階層' in df.columns else {}
        global_sorted_batches = df['梯次'].unique().tolist() if '梯次' in df.columns else []
    
    # ========== 2. 所有階層的雷達圖（左右並排） ==========
    if '階層' not in df.columns:
        st.error("資料框中沒有 '階層' 欄位，無法繪製視覺化圖表")
    else:
        layers = df['階層'].unique()
        
        # 引入所需套件
        import plotly.graph_objects as go
        
        # ===== 雷達圖區域（左右並排） =====
        st.subheader("EPA評核雷達圖")
        
        # 計算每行顯示的列數（根據階層數量調整）
        if len(layers) == 1:
            cols_per_row = 1
        elif len(layers) == 2:
            cols_per_row = 2
        else:
            cols_per_row = 3  # 一行最多3個圖表
        
        # 創建雷達圖行
        radar_cols = st.columns(cols_per_row)
        col_index = 0
        
        for layer in layers:
            layer_df = df[df['階層'] == layer]
            
            # 檢查是否有足夠的資料繪製圖表
            if layer_df.empty:
                with radar_cols[col_index]:
                    st.warning(f"階層 {layer} 沒有足夠的資料繪製雷達圖")
                col_index = (col_index + 1) % cols_per_row
                continue
            
            with radar_cols[col_index]:
                # === 繪製雷達圖 ===
                st.caption(f"階層 {layer}")
                
                # 獲取該階層的EPA評核項目和對應的教師評核EPA等級
                categories = layer_df['EPA評核項目'].unique().tolist()
                values = [layer_df[layer_df['EPA評核項目'] == category]['教師評核EPA等級'].mean() for category in categories]
                
                # 確保資料是閉合的
                categories_closed = categories + [categories[0]]
                values_closed = values + [values[0]]
                
                # 創建plotly雷達圖
                radar_fig = go.Figure()
                radar_fig.add_trace(go.Scatterpolar(
                    r=values_closed,
                    theta=categories_closed,
                    fill='toself',
                    name=f'階層 {layer}'
                ))
                
                radar_fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 5]
                        )
                    ),
                    showlegend=True,
                    height=400,  # 設置固定高度
                    margin=dict(t=30, b=30, l=30, r=30)  # 縮小邊距
                )
                
                # 顯示雷達圖
                st.plotly_chart(radar_fig, use_container_width=True)
            
            # 更新列索引，如果達到每行最大列數則換行
            col_index = (col_index + 1) % cols_per_row
        
        # ===== 趨勢圖區域（上下排列） =====
        st.subheader("EPA評核趨勢分析")
        
        for layer in layers:
            layer_df = df[df['階層'] == layer]
            
            # 檢查是否有足夠的資料繪製圖表
            if layer_df.empty:
                st.warning(f"階層 {layer} 沒有足夠的資料繪製趨勢圖")
                continue
            
            # === 繪製趨勢圖 ===
            st.caption(f"階層 {layer} 的EPA評核趨勢")
            
            try:
                # 獲取該階層的梯次順序
                batch_order = layer_batch_orders.get(layer, global_sorted_batches)
                
                # 繪製趨勢圖
                trend_fig = plot_epa_trend(
                    df=layer_df,
                    x_col='梯次',
                    y_col='教師評核EPA等級',
                    group_col='EPA評核項目',
                    by_layer=False,
                    confidence_interval=True,
                    title=''  # 移除標題，因為上方已有標題
                )
                
                # 手動設定X軸順序
                trend_fig.update_layout(
                    xaxis=dict(
                        categoryorder='array',
                        categoryarray=batch_order
                    ),
                    height=450,  # 設置固定高度，稍大於雷達圖
                    margin=dict(t=30, b=30, l=30, r=30)  # 縮小邊距
                )
                
                # 顯示趨勢圖
                st.plotly_chart(trend_fig, use_container_width=True)
                
                # 添加分隔線，除了最後一個階層
                if layer != layers[-1]:
                    st.markdown("---")
                    
            except Exception as e:
                st.error(f"繪製階層 {layer} 的趨勢圖時發生錯誤: {e}")

def show_UGY_EPA_section():
    """主要應用程式流程
    
    Returns:
        DataFrame: 處理後的資料框，如果發生錯誤則返回 None
    """
    st.title("UGY EPA分析")
    
    try:
        # 載入資料
        df, sheet_titles = load_sheet_data()
        
        if sheet_titles:
            # 直接抓第一個工作表
            selected_sheet = sheet_titles[0]
            
            # 重新載入選擇的工作表資料
            df, _ = load_sheet_data(sheet_title=selected_sheet)
            
            if df is not None:
                # 使用下拉式選單顯示原始資料
                with st.expander("載入的原始資料", expanded=False):
                    st.write("原始資料大小：", df.shape)
                    st.dataframe(df)
                
                # 處理資料
                st.write("開始進行資料處理...")
                processed_df = process_data(df)
                
                if processed_df is not None and not processed_df.empty:
                    st.success(f"成功處理 {len(processed_df)} 筆資料！")
                    
                    # 使用下拉式選單顯示處理後的資料
                    with st.expander("處理後資料", expanded=False):
                        st.write("處理後資料大小：", processed_df.shape)
                        st.dataframe(processed_df)
                    
                    # 顯示視覺化圖表
                    display_visualizations(processed_df)
                    
                    # ========== 5. 梯次學生雷達圖分析 ==========
                    st.header("梯次學生雷達圖分析")
                    
                    # 確認資料中有必要的欄位
                    required_columns = ['梯次', '學員姓名', 'EPA評核項目', '教師評核EPA等級']
                    missing_columns = [col for col in required_columns if col not in processed_df.columns]
                    
                    if missing_columns:
                        st.error(f"資料中缺少以下欄位，無法顯示學生雷達圖：{', '.join(missing_columns)}")
                    else:
                        # 獲取標準的EPA評核項目順序（從全局資料集）
                        standard_epa_categories = sorted(processed_df['EPA評核項目'].unique().tolist())
                        
                        # 獲取所有梯次並排序
                        all_batches = processed_df['梯次'].unique().tolist()
                        
                        # 嘗試將梯次轉換為日期並排序
                        try:
                            # 創建臨時數據框
                            temp_df = pd.DataFrame({'梯次': all_batches})
                            
                            # 嘗試將梯次轉換為日期
                            temp_df['梯次日期'] = pd.to_datetime(temp_df['梯次'], errors='coerce')
                            
                            # 處理無法直接轉換的日期
                            if temp_df['梯次日期'].isna().any():
                                import re
                                date_pattern = re.compile(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})')
                                
                                for idx, value in temp_df[temp_df['梯次日期'].isna()]['梯次'].items():
                                    if isinstance(value, str):
                                        match = date_pattern.search(value)
                                        if match:
                                            year, month, day = match.groups()
                                            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                            temp_df.loc[idx, '梯次日期'] = pd.to_datetime(date_str, errors='coerce')
                            
                            # 按日期排序
                            sorted_batches = temp_df.sort_values('梯次日期')['梯次'].tolist()
                        except:
                            # 如果排序失敗，使用原始順序
                            sorted_batches = all_batches
                        
                        # 梯次複選器
                        selected_batches = st.multiselect(
                            "選擇梯次 (可複選)",
                            options=sorted_batches,
                            default=[sorted_batches[0]] if sorted_batches else [],
                            format_func=lambda x: f"梯次: {x}"
                        )
                        
                        if not selected_batches:
                            st.warning("請選擇至少一個梯次")
                        else:
                            # 篩選所選梯次的資料
                            batch_df = processed_df[processed_df['梯次'].isin(selected_batches)]
                            
                            # 獲取選定梯次的所有學生
                            student_data = batch_df.groupby(['學員姓名', '梯次']).size().reset_index()
                            student_data.columns = ['學員姓名', '梯次', '評核數量']
                            
                            # 顯示學生數量統計
                            total_students = student_data['學員姓名'].nunique()
                            st.success(f"已選擇 {len(selected_batches)} 個梯次，共有 {total_students} 名不重複學生")
                            
                            # 決定顯示方式
                            display_mode = st.radio(
                                "顯示模式",
                                options=["選擇單一學生", "顯示所有學生", "按梯次分組顯示"],
                                horizontal=True
                            )
                            
                            if display_mode == "選擇單一學生":
                                # 獲取不重複的學生列表
                                students = student_data['學員姓名'].unique().tolist()
                                students.sort()  # 按姓名排序
                                
                                # 學生選擇器
                                selected_student = st.selectbox(
                                    "選擇學生",
                                    options=students
                                )
                                
                                if selected_student:
                                    # 獲取該學生參與的所有梯次
                                    student_batches = student_data[student_data['學員姓名'] == selected_student]['梯次'].tolist()
                                    
                                    # 如果學生參與了多個梯次，提供梯次選擇
                                    if len(student_batches) > 1:
                                        batch_for_student = st.radio(
                                            "選擇要顯示的梯次",
                                            options=["所有梯次合併"] + student_batches,
                                            horizontal=True
                                        )
                                        
                                        if batch_for_student == "所有梯次合併":
                                            # 顯示所有梯次合併的資料
                                            st.subheader(f"學生 {selected_student} 的EPA評核 (所有梯次合併)")
                                            student_df = batch_df[batch_df['學員姓名'] == selected_student]
                                            display_student_data(student_df, selected_student, full_df=processed_df, standard_categories=standard_epa_categories)
                                        else:
                                            # 顯示特定梯次的資料
                                            st.subheader(f"學生 {selected_student} 的EPA評核 (梯次: {batch_for_student})")
                                            student_df = batch_df[(batch_df['學員姓名'] == selected_student) & 
                                                                 (batch_df['梯次'] == batch_for_student)]
                                            display_student_data(student_df, selected_student, full_df=processed_df, standard_categories=standard_epa_categories)
                                    else:
                                        # 只有一個梯次，直接顯示
                                        st.subheader(f"學生 {selected_student} 的EPA評核 (梯次: {student_batches[0]})")
                                        student_df = batch_df[batch_df['學員姓名'] == selected_student]
                                        display_student_data(student_df, selected_student, full_df=processed_df, standard_categories=standard_epa_categories)
                                
                            elif display_mode == "顯示所有學生":
                                # 獲取不重複的學生列表
                                students = student_data['學員姓名'].unique().tolist()
                                students.sort()  # 按姓名排序
                                
                                # 是否合併梯次資料
                                merge_batches = st.checkbox("合併所有梯次資料", value=True)
                                
                                # 繪製所有學生的雷達圖，每層一個學生
                                st.subheader(f"所有學生的EPA評核雷達圖" + 
                                           (" (所有梯次合併)" if merge_batches else ""))
                                
                                # 循環顯示每個學生
                                for student in students:
                                    # 使用水平線分隔不同學生
                                    st.markdown("---")
                                    
                                    # 顯示學生姓名作為子標題
                                    if merge_batches:
                                        st.subheader(f"學生: {student} (所有梯次)")
                                    else:
                                        # 獲取該學生參與的所有梯次
                                        student_batches = student_data[student_data['學員姓名'] == student]['梯次'].tolist()
                                        if len(student_batches) == 1:
                                            st.subheader(f"學生: {student} (梯次: {student_batches[0]})")
                                        else:
                                            st.subheader(f"學生: {student} (參與 {len(student_batches)} 個梯次)")
                                    
                                    # 獲取學生資料
                                    if merge_batches:
                                        # 合併所有梯次的資料
                                        student_df = batch_df[batch_df['學員姓名'] == student]
                                    else:
                                        # 如果只有一個梯次，直接顯示
                                        if len(student_batches) == 1:
                                            student_df = batch_df[(batch_df['學員姓名'] == student) & 
                                                                 (batch_df['梯次'] == student_batches[0])]
                                        else:
                                            # 有多個梯次，顯示合併資料
                                            student_df = batch_df[batch_df['學員姓名'] == student]
                                    
                                    # 顯示學生資料（雷達圖和回饋）
                                    display_student_data(student_df, student, full_df=processed_df, 
                                                        standard_categories=standard_epa_categories)
                    
                    return processed_df  # 返回處理後的資料
                else:
                    st.error("資料處理失敗")
                    return df  # 資料處理失敗時返回原始資料
            else:
                st.warning(f"無法載入工作表 '{selected_sheet}' 的資料")
                return None
        else:
            st.error("無法獲取工作表列表")
            return None
            
    except Exception as e:
        st.error(f"載入資料時發生錯誤：{str(e)}")
        st.exception(e)
        return None

def display_student_data(student_df, student_name, full_df=None, standard_categories=None):
    """顯示學生資料，左側雷達圖，右側回饋表格
    
    Args:
        student_df: 包含該學生資料的DataFrame
        student_name: 學生姓名
        full_df: 包含所有資料的完整DataFrame（用於計算階層整體平均）
        standard_categories: 標準的EPA評核項目順序列表
    """
    # 檢查是否有學生資料
    if student_df.empty:
        st.warning(f"找不到學生 {student_name} 的資料")
        return
    
    # 創建左右兩欄布局 - 調整雷達圖佔比更大
    col1, col2 = st.columns([1, 1])  # 1:1比例
    
    # 左欄：顯示雷達圖
    with col1:
        # 傳遞標準EPA評核項目順序
        draw_student_radar(student_df, student_name, full_df, standard_categories)
    
    # 右欄顯示回饋詳情
    with col2:
        st.subheader("評核回饋詳情")
        
        # 準備回饋表格資料
        feedback_data = student_df.copy()
        
        # 選擇需要顯示的欄位
        display_columns = ['梯次', 'EPA評核項目', '教師', '教師評核EPA等級', '回饋']
        
        # 確保所有需要的欄位都存在，如果不存在就創建空欄位
        for col in display_columns:
            if col not in feedback_data.columns:
                feedback_data[col] = "未提供"
        
        # 只選擇需要顯示的欄位
        feedback_display = feedback_data[display_columns].copy()
        
        # 按梯次和EPA評核項目排序
        feedback_display = feedback_display.sort_values(['梯次', 'EPA評核項目'])
        
        # 顯示回饋表格
        st.dataframe(feedback_display, use_container_width=True)
        
        # 顯示評核統計
        st.caption("評核統計")
        stats = feedback_data.groupby('EPA評核項目')['教師評核EPA等級'].agg(
            平均分=('mean'),
            最高分=('max'),
            最低分=('min'),
            評核次數=('count')
        ).reset_index()
        st.dataframe(stats.round(2), use_container_width=True)

def draw_student_radar(df, student_name, full_df=None, standard_categories=None):
    """為指定學生繪製EPA評核雷達圖
    
    Args:
        df: 包含該學生資料的DataFrame
        student_name: 學生姓名
        full_df: 包含所有資料的完整DataFrame（用於計算階層整體平均）
        standard_categories: 標準的EPA評核項目順序列表
    """
    import plotly.graph_objects as go
    
    # 篩選該學生的資料
    student_df = df[df['學員姓名'] == student_name]
    
    if student_df.empty:
        st.warning(f"找不到學生 {student_name} 的雷達圖資料")
        return
    
    # 決定使用的EPA評核項目標準順序
    if standard_categories is None:
        if full_df is not None:
            # 從完整資料集獲取所有EPA評核項目並排序
            standard_categories = sorted(full_df['EPA評核項目'].unique().tolist())
        else:
            # 從當前資料集獲取並排序
            standard_categories = sorted(df['EPA評核項目'].unique().tolist())
    
    # 按標準順序建立學生的評分值
    values = []
    categories = []
    
    # 對每個標準評核項目，獲取該學生的評分（若存在）
    for category in standard_categories:
        category_data = student_df[student_df['EPA評核項目'] == category]
        if not category_data.empty:
            # 使用該項目的平均分數
            avg_score = category_data['教師評核EPA等級'].mean()
            categories.append(category)
            values.append(avg_score)
    
    # 如果沒有足夠的資料，顯示警告
    if len(categories) < 2:
        st.warning(f"學生 {student_name} 的評核項目不足，無法繪製雷達圖")
        return
    
    # 確保資料是閉合的
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]
    
    # 創建plotly雷達圖
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        name=student_name
    ))
    
    # 獲取階層平均值作為比較 - 使用所有梯次匯總的階層平均
    if '階層' in student_df.columns and len(student_df['階層']) > 0:
        layer = student_df['階層'].iloc[0]  # 假設學生只屬於一個階層
        
        # 使用完整資料集計算階層平均（如果有提供）
        if full_df is not None:
            layer_df = full_df[full_df['階層'] == layer]
        else:
            # 如果沒有提供完整資料集，則使用當前資料集
            layer_df = df[df['階層'] == layer]
        
        layer_values = []
        for category in categories:
            layer_data = layer_df[layer_df['EPA評核項目'] == category]
            if not layer_data.empty:
                layer_avg = layer_data['教師評核EPA等級'].mean()
                layer_values.append(layer_avg)
            else:
                # 如果該階層沒有此項目的資料，使用0填充
                layer_values.append(0)
        
        # 添加階層平均線
        fig.add_trace(go.Scatterpolar(
            r=layer_values + [layer_values[0]],
            theta=categories_closed,
            fill='none',
            name=f'階層 {layer} 整體平均',
            line=dict(dash='dash', color='rgba(100, 100, 100, 0.8)')
        ))
    
    # 設定圖表樣式
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )
        ),
        showlegend=True,
        height=450,  # 增加高度
        margin=dict(t=20, b=20, l=20, r=20)
    )
    
    # 顯示雷達圖
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    # 取得原始資料
    show_UGY_EPA_section()
    
