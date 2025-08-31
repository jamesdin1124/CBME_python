import re
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from modules.google_connection import fetch_google_form_data, SHOW_DIAGNOSTICS
from modules.data_processing import (
    process_epa_level, 
    convert_date_to_batch, 
    convert_tw_time,
    process_training_departments,
    get_student_departments,
    merge_epa_with_departments
)
from modules.visualization import plot_radar_chart, plot_epa_trend_px
# 暫時註解掉不需要的導入
# from modules.data_analysis import analyze_epa_data

# 在檔案開頭宣告全域變數
proceeded_EPA_df = None

# 定義階層顏色（供雷達圖與表格用）
layer_colors = {
    'C1': 'rgba(255, 100, 100, 0.7)',  # 淡紅色
    'C2': 'rgba(100, 100, 255, 0.7)',  # 淡藍色
    'PGY': 'rgba(100, 200, 100, 0.7)'  # 淡綠色
    # 可依需求擴充
}

# 產生隨機顏色（若階層未定義顏色時使用）
import hashlib
def get_random_color(seed_str, alpha=0.7):
    hash_value = int(hashlib.md5(str(seed_str).encode()).hexdigest(), 16)
    r = (hash_value & 0xFF) % 200 
    g = ((hash_value >> 8) & 0xFF) % 200
    b = ((hash_value >> 16) & 0xFF) % 200
    return f'rgba({r}, {g}, {b}, {alpha})'

# ==================== 資料載入與處理函數 ====================

def load_sheet_data(sheet_title=None, show_info=True):
    """載入Google表單資料
    
    Args:
        sheet_title (str, optional): 工作表名稱
        show_info (bool): 是否顯示載入資訊
        
    Returns:
        tuple: (DataFrame, sheet_titles list)
    """
    df, sheet_titles = fetch_google_form_data(sheet_title=sheet_title)
    return df, sheet_titles

def show_diagnostic(message: str, type: str = "info"):
    """顯示診斷訊息的輔助函數
    
    Args:
        message: 要顯示的訊息
        type: 訊息類型 ("info", "success", "warning", "error")
    """
    if SHOW_DIAGNOSTICS:
        if type == "info":
            st.info(message)
        elif type == "success":
            st.success(message)
        elif type == "warning":
            st.warning(message)
        elif type == "error":
            st.error(message)

def process_data(df):
    """處理EPA資料"""
    if df is not None:
        try:
            # 移除重複欄位
            df = df.loc[:, ~df.columns.duplicated()]
            
            # 檢查必要欄位
            required_columns = ['學員自評EPA等級', '教師評核EPA等級', '教師']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"缺少必要欄位：{missing_columns}")
                return None
        
            try:
                # 加入勾選框讓使用者選擇是否要限制只顯示有教師評核的資料
                filter_teacher_data = st.checkbox("只顯示有認證教師評核的資料", value=True)
                
                if filter_teacher_data:
                    # 只保留教師欄位有資料的列
                    df = df[df['教師'].notna() & (df['教師'] != '')]
                    show_diagnostic("已過濾只顯示有教師評核的資料", "info")
                else:
                    show_diagnostic("顯示所有資料（包含無教師評核的資料）", "info")
                
                # 創建新欄位儲存轉換後的數值
                df['學員自評EPA等級_數值'] = df['學員自評EPA等級'].apply(process_epa_level)
                df['教師評核EPA等級_數值'] = df['教師評核EPA等級'].apply(process_epa_level)
            except Exception as e:
                st.error(f"EPA等級轉換失敗：{str(e)}")
                return None
            
            # 日期轉換和梯次處理
            try:
                if '時間戳記' in df.columns:
                    df['評核日期'] = df['時間戳記'].apply(convert_tw_time)
                    df['評核日期'] = df['評核日期'].dt.date
                elif '評核時間' in df.columns:
                    df['評核日期'] = pd.to_datetime(df['評核時間']).dt.date
                
                if '評核日期' in df.columns:
                    df['梯次'] = df['評核日期'].astype(str).apply(convert_date_to_batch)
                    show_diagnostic("日期轉換成功", "info")
                else:
                    st.warning("找不到日期欄位，跳過梯次處理")
            except Exception as e:
                st.error(f"日期處理失敗：{str(e)}")
            
            show_diagnostic("資料處理完成", "info")
            return df
            
        except Exception as e:
            st.error(f"資料處理時發生錯誤：{str(e)}")
            st.exception(e)
            return None
    else:
        st.error("輸入的資料框為空")
        return None

# ==================== 資料顯示函數 ====================

def display_data_preview(df):
    """顯示資料預覽
    
    Args:
        df (DataFrame): 處理後的資料框
    """
    st.subheader("資料預覽")
    st.dataframe(df.head(10))

def display_dept_data(dept_df):
    """顯示訓練科部資料
    
    Args:
        dept_df (pd.DataFrame): 訓練科部資料DataFrame
    """
    if dept_df is not None and not dept_df.empty:
        st.subheader("訓練科部資料")
        
        # 找出日期欄位
        date_columns = [col for col in dept_df.columns 
                       if isinstance(col, str) and len(col.split('/')) == 3]
        
        # 選擇要顯示的欄位
        display_columns = ['學號', '姓名'] + date_columns
        
        # 顯示資料
        st.dataframe(dept_df[display_columns], use_container_width=True)
        
        # 顯示統計資訊
        st.caption("資料統計")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"總學生人數：{len(dept_df)}")
        with col2:
            st.info(f"訓練時段數：{len(date_columns)}")
    else:
        st.warning("沒有可用的訓練科部資料")

# ==================== 視覺化函數 ====================

def display_student_data(student_df, student_id, standard_categories=None):
    """顯示學生資料，包含雷達圖、趨勢圖和回饋表格"""
    # 檢查是否有學生資料
    if student_df.empty:
        st.warning(f"找不到學生 {student_id} 的資料")
        return
    
    # 檢查梯次數量
    batches = student_df['梯次'].unique() if '梯次' in student_df.columns else []
    multiple_batches = len(batches) > 1
    
    # 雷達圖和回饋表格的左右布局
    col1, col2 = st.columns([1, 1])  # 從1:1改為3:2比例，讓雷達圖有更寬的顯示空間
    
    # 左欄：顯示雷達圖
    with col1:
        st.caption("EPA評核雷達圖")
        # 使用整合後的plot_radar_chart函數替代draw_student_radar
        radar_fig = plot_radar_chart(
            df=student_df, 
            student_id=student_id,  # 改用student_id
            standard_categories=standard_categories
        )
        st.plotly_chart(radar_fig, use_container_width=True, key=f"student_radar_{student_id}")

        # ===== 新增：顯示該學生所屬階層的EPA平均及95%CI表格 =====
        # 取得該學生所屬階層
        student_layer = None
        if '階層' in student_df.columns and not student_df.empty:
            student_layer = student_df['階層'].iloc[0]

        # 只畫該階層平均
        if student_layer and proceeded_EPA_df is not None and hasattr(proceeded_EPA_df, 'columns') and '階層' in proceeded_EPA_df.columns:
            # 封閉的 EPA 項目順序（用於雷達圖）
            standard_categories_closed = standard_categories + [standard_categories[0]]
            full_score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in proceeded_EPA_df.columns else '教師評核EPA等級'
            layer_df = proceeded_EPA_df[proceeded_EPA_df['階層'] == student_layer]
            if layer_df.empty:
                print(f'警告：找不到階層 {student_layer} 的資料')
            layer_values = []
            for category in standard_categories:
                layer_data = layer_df[layer_df['EPA評核項目'] == category]
                if not layer_data.empty:
                    layer_avg = layer_data[full_score_column].mean()
                    layer_values.append(layer_avg)
                else:
                    layer_values.append(1)  # 若無資料補1
            layer_values_closed = layer_values + [layer_values[0]]
            layer_color = layer_colors.get(student_layer, get_random_color(student_layer, 0.7))
            radar_fig.add_trace(go.Scatterpolar(
                r=layer_values_closed,
                theta=standard_categories_closed,
                fill='none',
                name=f'{student_layer} 階層平均',
                line=dict(dash='dash', color=layer_color)
            ))
    
    # 右欄：顯示回饋表格和統計
    with col2:
        # 使用摺疊框顯示評核回饋詳情，預設為收起狀態，並調整高度
        with st.expander("評核回饋詳情", expanded=True):
            # 準備回饋表格資料
            feedback_data = student_df.copy()
            
            # 選擇需要顯示的欄位
            display_columns = ['臨床情境', '回饋', '教師評核EPA等級', '梯次', 'EPA評核項目', '教師']
            
            # 確保所有需要的欄位都存在，如果不存在就創建空欄位
            for col in display_columns:
                if col not in feedback_data.columns:
                    feedback_data[col] = "未提供"
            
            # 只選擇需要顯示的欄位
            feedback_display = feedback_data[display_columns].copy()
            
            # 按梯次和EPA評核項目排序
            feedback_display = feedback_display.sort_values(['梯次', 'EPA評核項目'])
            
            # 顯示回饋表格，設定較小的固定高度
            st.dataframe(feedback_display, use_container_width=True, height=150)
        
        # 使用摺疊框顯示評核統計，預設為展開狀態
        with st.expander("評核統計", expanded=False):
            # 獲取所有可能的EPA評核項目
            all_epa_items = sorted(student_df['EPA評核項目'].unique().tolist())
            
            # 獲取所有梯次
            all_batches = student_df['梯次'].unique().tolist()
            
            # 首先顯示按梯次分組的評核數量統計
            batch_count = student_df.groupby(['梯次', 'EPA評核項目']).size().reset_index()
            batch_count.columns = ['梯次', 'EPA評核項目', '評核數量']
            
            # 創建所有梯次和評核項目的完整組合
            complete_index = pd.MultiIndex.from_product([all_batches, all_epa_items], 
                                                        names=['梯次', 'EPA評核項目'])
            complete_data = pd.DataFrame(index=complete_index).reset_index()
            
            # 合併實際資料，填充缺失值為0
            complete_counts = complete_data.merge(batch_count, on=['梯次', 'EPA評核項目'], how='left')
            complete_counts['評核數量'] = complete_counts['評核數量'].fillna(0).astype(int)
            
            # 按梯次和EPA評核項目排序
            complete_counts = complete_counts.sort_values(['梯次', 'EPA評核項目'])
            
            # 使用樞紐分析表格式顯示數據
            st.write("各梯次各項目評核數量")
            
            # 將數據轉換為樞紐分析表格式
            pivot_counts = complete_counts.pivot(index='梯次', columns='EPA評核項目', values='評核數量')
            
            # 確保所有欄位都有值，缺失的填0
            pivot_counts = pivot_counts.fillna(0).astype(int)
            
            # 新增總計行和總計列
            pivot_counts['總計'] = pivot_counts.sum(axis=1)
            
            # 如果使用totals=True不能自動添加總計列，則手動添加總計行
            total_row = pd.DataFrame(pivot_counts.sum(axis=0)).T
            total_row.index = ['總計']
            
            # 合併總計行
            pivot_counts_with_totals = pd.concat([pivot_counts, total_row])
            
            # 定義樣式函數 - 小於2的數值標記為紅色背景
            def highlight_insufficient(val):
                color = 'background-color: rgba(255, 0, 0, 0.2)' if val < 2 else ''
                return color
            
            # 應用條件格式 - 對'總計'列以外的所有數據應用格式
            styled_pivot = pivot_counts_with_totals.style.applymap(
                highlight_insufficient, 
                subset=pd.IndexSlice[:, pivot_counts_with_totals.columns[:-1]]
            )
            
            # 顯示樞紐分析表，調整高度使整體佈局更加平衡
            st.dataframe(styled_pivot, use_container_width=True, height=180)
            
            # 然後顯示整體統計數據
            # 首先創建包含所有EPA評核項目的DataFrame
            all_items_df = pd.DataFrame({'EPA評核項目': all_epa_items})
            
            # 計算現有的統計
            raw_stats = student_df.groupby('EPA評核項目')['教師評核EPA等級_數值'].agg(
                平均分=('mean'),
                最高分=('max'),
                最低分=('min'),
                評核總數=('count')
            ).reset_index()
            
            # 合併，確保所有項目都包含在內
            stats = all_items_df.merge(raw_stats, on='EPA評核項目', how='left')
            
            # 填充缺失值
            stats['評核總數'] = stats['評核總數'].fillna(0).astype(int)
            stats['平均分'] = stats['平均分'].fillna(0)
            stats['最高分'] = stats['最高分'].fillna(0)
            stats['最低分'] = stats['最低分'].fillna(0)
            
            # 按評核總數由高到低排序
            stats = stats.sort_values('評核總數', ascending=False)
            
            # 顯示整體統計，同樣調整高度
            st.write("整體評核統計")
            st.dataframe(stats.round(2), use_container_width=True, height=180)
    
    # 如果有多個梯次，顯示趨勢圖
    if multiple_batches:
        st.caption("EPA評核趨勢圖")
        draw_student_trend(student_df, student_id, proceeded_EPA_df)
    elif '梯次' in student_df.columns:
        # 單一梯次，仍然顯示趨勢圖但添加說明
        st.caption("EPA評核趨勢圖 (僅單一梯次資料)")
        draw_student_trend(student_df, student_id, proceeded_EPA_df)

def draw_student_trend(student_df, student_id, full_df):
    """繪製學生EPA評核趨勢圖
    
    Args:
        student_df: 包含該學生資料的DataFrame
        student_id: 學生學號
        full_df: 包含所有資料的完整DataFrame（用於計算階層整體平均）
    """
    # 使用整合後的plot_epa_trend函數繪製學生趨勢圖
    trend_fig = plot_epa_trend_px(
        df=student_df,
        x_col='梯次',
        y_col='教師評核EPA等級_數值',
        group_col='EPA評核項目',
        student_id=student_id,  # 改用student_id
        student_mode=True,
        full_df=full_df,
        sort_by_date=True
    )
    
    # 顯示趨勢圖，為學生趨勢圖添加唯一key
    st.plotly_chart(trend_fig, use_container_width=True, key=f"student_trend_{student_id}")

def display_visualizations():
    """顯示資料視覺化"""
    global proceeded_EPA_df  # 使用全域變數

    # 檢查 proceeded_EPA_df 是否有效
    if proceeded_EPA_df is None or proceeded_EPA_df.empty:
        st.warning("沒有可用的已處理資料進行視覺化。")
        return

    st.markdown("<h1 style='color:#1E90FF; font-size:32px;'>學生總覽</h1>", unsafe_allow_html=True)
    
    # ========== 訓練科部多選篩選 ========== 
    # 使用 proceeded_EPA_df 進行篩選
    current_df_view = proceeded_EPA_df.copy() # 建立副本以進行篩選，不直接修改全域變數

    if '訓練科部' in current_df_view.columns:
        all_depts = sorted([d for d in current_df_view['訓練科部'].dropna().unique().tolist() if d not in [None, '', 'None']])
        if all_depts:
            selected_depts = st.multiselect(
                "選擇訓練科部 (可複選)",
                options=all_depts,
                default=all_depts,
                format_func=lambda x: f"科部: {x}"
            )
            if not selected_depts:
                st.warning("請選擇至少一個訓練科部")
                return
            current_df_view = current_df_view[current_df_view['訓練科部'].isin(selected_depts)]
    
    # ========== 1. 計算梯次排序（背景處理） ==========
    try:
        layer_batch_orders = {}
        
        if '階層' in current_df_view.columns:
            all_layers = sorted(current_df_view['階層'].unique().tolist())
            
            selected_layers = st.multiselect(
                "選擇階層 (可複選)",
                options=all_layers,
                default=all_layers,
                format_func=lambda x: f"階層: {x}"
            )
            
            if not selected_layers:
                st.warning("請選擇至少一個階層")
                return
            
            filtered_by_layer_df = current_df_view[current_df_view['階層'].isin(selected_layers)].copy() # 用於後續圖表的全階層篩選後資料
            
            for layer in selected_layers:
                layer_df_for_batch_order = current_df_view[current_df_view['階層'] == layer].copy() # 僅用於計算該階層梯次順序
                
                try:
                    layer_df_for_batch_order['梯次日期'] = pd.to_datetime(layer_df_for_batch_order['梯次'], errors='coerce')
                    if layer_df_for_batch_order['梯次日期'].isna().any():
                        import re
                        date_pattern = re.compile(r'(\\d{4})[-/](\\d{1,2})[-/](\\d{1,2})')
                        for idx, value in layer_df_for_batch_order[layer_df_for_batch_order['梯次日期'].isna()]['梯次'].items():
                            if isinstance(value, str):
                                match = date_pattern.search(value)
                                if match:
                                    year, month, day = match.groups()
                                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                    layer_df_for_batch_order.loc[idx, '梯次日期'] = pd.to_datetime(date_str, errors='coerce')
                except:
                    layer_batch_orders[layer] = layer_df_for_batch_order['梯次'].unique().tolist()
                    continue
                
                stats_df = layer_df_for_batch_order.groupby('梯次').agg({'梯次日期': 'first'}).reset_index()
                sorted_stats = stats_df.sort_values('梯次日期')
                
                if not sorted_stats.empty:
                    layer_batch_orders[layer] = sorted_stats['梯次'].tolist()
                else:
                    layer_batch_orders[layer] = []
            
            all_batches_df_for_global_order = pd.DataFrame({'梯次': filtered_by_layer_df['梯次'].unique()})
            try:
                all_batches_df_for_global_order['梯次日期'] = pd.to_datetime(all_batches_df_for_global_order['梯次'], errors='coerce')
                if all_batches_df_for_global_order['梯次日期'].isna().any():
                    for idx, value in all_batches_df_for_global_order[all_batches_df_for_global_order['梯次日期'].isna()]['梯次'].items():
                        if isinstance(value, str):
                            match = re.search(r'(\\d{4})[-/](\\d{1,2})[-/](\\d{1,2})', value)
                            if match:
                                year, month, day = match.groups()
                                date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                all_batches_df_for_global_order.loc[idx, '梯次日期'] = pd.to_datetime(date_str, errors='coerce')
                global_sorted_batches = all_batches_df_for_global_order.sort_values('梯次日期')['梯次'].tolist()
            except:
                global_sorted_batches = filtered_by_layer_df['梯次'].unique().tolist()
        else:
            layer_batch_orders = {}
            global_sorted_batches = current_df_view['梯次'].unique().tolist() if '梯次' in current_df_view.columns else []
            selected_layers = [] # 如果沒有階層，則 selected_layers 為空
            filtered_by_layer_df = current_df_view # 如果沒有階層，則使用科部篩選後的資料
            
    except Exception as e:
        st.error(f"計算梯次排序時發生錯誤: {e}")
        layer_batch_orders = {}
        global_sorted_batches = current_df_view['梯次'].unique().tolist() if '梯次' in current_df_view.columns else []
        selected_layers = current_df_view['階層'].unique().tolist() if '階層' in current_df_view.columns else []
        filtered_by_layer_df = current_df_view

    # ========== 2. 所有階層的雷達圖（合併在同一個圖中） ==========
    if '階層' not in filtered_by_layer_df.columns and not selected_layers : # 檢查階層欄位或是否有選定階層
         # 如果沒有階層欄位，並且 selected_layers 也為空 (例如，資料本身就沒有階層欄位)
         # 就不顯示階層相關的圖表，或者可以考慮顯示一個整體雷達圖（如果適用）
        st.info("資料中沒有 '階層' 欄位，或未選擇任何階層，跳過階層雷達圖和趨勢圖。")

    elif not filtered_by_layer_df.empty: # 確保有資料可以畫圖
        # ===== 雷達圖區域 (所有階層合併) =====
        st.subheader("EPA評核雷達圖")
        
        if not filtered_by_layer_df.empty:
            radar_fig = plot_radar_chart(
                df=filtered_by_layer_df, 
                plot_types=['layers'],
                title="各階層EPA評核雷達圖比較",
                labels={
                    'layer': '階層 {}',
                    'teacher_avg': '教師評核平均',
                    'student_avg': '學員自評平均',
                }
            )
            radar_fig.update_layout(
                height=500,
                margin=dict(t=50, b=50, l=50, r=50),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(radar_fig, use_container_width=True, key="all_layers_radar_chart")
        else:
            st.error("沒有足夠的資料繪製雷達圖 (經過篩選後)")
        
        # ===== 趨勢圖區域（上下排列） =====
        if selected_layers: # 只有在選擇了階層時才顯示
            st.subheader("EPA評核趨勢分析")
            for layer in selected_layers:
                layer_df_for_trend = filtered_by_layer_df[filtered_by_layer_df['階層'] == layer]
                
                if layer_df_for_trend.empty:
                    st.warning(f"階層 {layer} 沒有足夠的資料繪製趨勢圖 (經過篩選後)")
                    continue
                
                st.caption(f"階層 {layer} 的EPA評核趨勢")
                try:
                    batch_order = layer_batch_orders.get(layer, global_sorted_batches)
                    trend_fig = plot_epa_trend_px(
                        df=layer_df_for_trend,
                        x_col='梯次',
                        y_col='教師評核EPA等級_數值',
                        group_col='EPA評核項目',
                        title=''
                    )
                    trend_fig.update_layout(
                        xaxis=dict(categoryorder='array', categoryarray=batch_order),
                        height=450,
                        margin=dict(t=30, b=30, l=30, r=30)
                    )
                    st.plotly_chart(trend_fig, use_container_width=True, key=f"trend_chart_{layer}")
                    if layer != selected_layers[-1]:
                        st.markdown("---")
                except Exception as e:
                    st.error(f"繪製階層 {layer} 的趨勢圖時發生錯誤: {e}")
    else: # filtered_by_layer_df 為空
        st.warning("依目前篩選條件，沒有資料可供顯示總覽圖表。")

def analyze_student_data_completeness(student_df, all_epa_items=None):
    """分析學生資料的完整性，檢查每個梯次每個EPA評核項目是否有兩份以上資料
    
    Args:
        student_df: 包含學生資料的DataFrame
        all_epa_items: 所有可能的EPA評核項目列表，如果不提供則從數據中獲取
        
    Returns:
        DataFrame: 包含每個梯次每個EPA評核項目資料數量的分析結果
    """
    if student_df.empty:
        return pd.DataFrame()
    
    # 獲取所有可能的EPA評核項目
    if all_epa_items is None:
        all_epa_items = sorted(student_df['EPA評核項目'].unique().tolist())
    
    # 獲取所有梯次
    all_batches = student_df['梯次'].unique().tolist()
    
    # 依照梯次和EPA評核項目分組計算評核數量
    count_data = student_df.groupby(['梯次', 'EPA評核項目']).size().reset_index()
    count_data.columns = ['梯次', 'EPA評核項目', '評核數量']
    
    # 創建完整的梯次-項目組合的數據框架
    # 使用笛卡爾積確保每個梯次都有所有的評核項目
    complete_index = pd.MultiIndex.from_product([all_batches, all_epa_items], 
                                              names=['梯次', 'EPA評核項目'])
    
    # 重新索引，將缺失的組合填入0
    analysis = pd.DataFrame(index=complete_index).reset_index()
    analysis = analysis.merge(count_data, on=['梯次', 'EPA評核項目'], how='left')
    analysis['評核數量'] = analysis['評核數量'].fillna(0).astype(int)
    
    # 排序結果 - 先按梯次排序，再按評核項目排序
    analysis = analysis.sort_values(['梯次', 'EPA評核項目'])
    
    # 添加資料充足性標記
    analysis['資料充足性'] = analysis['評核數量'].apply(
        lambda x: "✅ 充足" if x >= 2 else "❌ 不足"
    )
    
    return analysis

def process_batch_data(df):
    """處理梯次資料，計算並排序梯次
    
    Args:
        df (pd.DataFrame): 包含梯次資料的DataFrame
        
    Returns:
        list: 排序後的梯次列表
        dict: 包含梯次相關統計資訊的字典
    """
    try:
        # 確保有梯次欄位
        if '梯次' not in df.columns:
            return [], {'error': '找不到梯次欄位'}
            
        # 獲取所有不重複的梯次
        all_batches = df['梯次'].unique().tolist()
        
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
        
        # 計算每個梯次的統計資訊
        batch_stats = {}
        for batch in sorted_batches:
            batch_data = df[df['梯次'] == batch]
            batch_stats[batch] = {
                '評核數量': len(batch_data),
                '學生人數': len(batch_data['學號'].unique()),
                'EPA項目數': len(batch_data['EPA評核項目'].unique()) if 'EPA評核項目' in batch_data.columns else 0
            }
        
        return sorted_batches, {
            'sorted_batches': sorted_batches,
            'total_batches': len(sorted_batches),
            'batch_stats': batch_stats
        }
        
    except Exception as e:
        return [], {'error': f'處理梯次資料時發生錯誤：{str(e)}'}

# ==================== 主應用程式流程 ====================

def show_UGY_EPA_section():
    """主要應用程式流程"""
    global proceeded_EPA_df  # 使用全域變數
    st.title("UGY EPA分析")

    # 檢查是否需要重新載入/處理資料
    if 'processed_df' not in st.session_state or st.button("重新載入 Google Sheet 資料"):
        # 執行資料載入與處理流程
        raw_df, sheet_titles = load_sheet_data(show_info=False)
        
        # 添加除錯訊息
        st.write("除錯訊息：")
        st.write(f"1. 工作表列表：{sheet_titles}")
        st.write(f"2. 原始資料是否為空：{raw_df is None or raw_df.empty}")
        
        dept_df, _ = load_sheet_data(sheet_title="訓練科部", show_info=False)
        processed_dept_df = None
        if dept_df is not None:
            processed_dept_df = process_training_departments(dept_df)
            if processed_dept_df is not None:
                show_diagnostic("成功載入並處理訓練科部資料", "success")
                with st.expander("訓練科部資料", expanded=False):
                    display_dept_data(processed_dept_df)
            else:
                show_diagnostic("訓練科部資料處理失敗", "warning")

        current_processed_df = None
        if sheet_titles:
            selected_sheet = sheet_titles[0] # 假設第一個是主要的EPA資料表
            epa_raw_df, _ = load_sheet_data(sheet_title=selected_sheet, show_info=False)

            # 添加除錯訊息
            st.write(f"3. EPA原始資料是否為空：{epa_raw_df is None or epa_raw_df.empty}")
            if epa_raw_df is not None:
                st.write(f"4. EPA原始資料欄位：{epa_raw_df.columns.tolist()}")

            if epa_raw_df is not None:
                with st.expander("載入的原始EPA資料", expanded=False):
                    st.dataframe(epa_raw_df)
                
                current_processed_df = process_data(epa_raw_df.copy()) # 傳入副本進行處理
                
                # 添加除錯訊息
                st.write(f"5. 處理後資料是否為空：{current_processed_df is None or current_processed_df.empty}")
                if current_processed_df is not None:
                    st.write(f"6. 處理後資料欄位：{current_processed_df.columns.tolist()}")
                
                if current_processed_df is not None and not current_processed_df.empty:
                    if processed_dept_df is not None:
                        try:
                            current_processed_df = merge_epa_with_departments(current_processed_df, processed_dept_df)
                            show_diagnostic("成功合併訓練科部資料到EPA資料", "success")
                        except Exception as e:
                            st.warning(f"合併訓練科部資料時發生錯誤：{str(e)}")
                    
                    _, batch_info = process_batch_data(current_processed_df)
                    if 'error' not in batch_info and 'sorted_batches' in batch_info :
                        show_diagnostic(f"成功處理梯次資料，共有 {batch_info.get('total_batches',0)} 個梯次", "success")
                        with st.expander("梯次統計資訊", expanded=False):
                            for batch in batch_info.get('sorted_batches', []):
                                stats = batch_info.get('batch_stats', {}).get(batch, {})
                                st.write(f"梯次 {batch}:")
                                st.write(f"- 評核數量: {stats.get('評核數量','N/A')}")
                                st.write(f"- 學生人數: {stats.get('學生人數','N/A')}")
                                st.write(f"- EPA項目數: {stats.get('EPA項目數','N/A')}")
                                st.write("---")
                    else:
                        st.warning(batch_info.get('error', "梯次資料處理時發生未知問題"))
                    
                    proceeded_EPA_df = current_processed_df # 更新全域變數
                    st.session_state['processed_df'] = current_processed_df # 更新 session_state
                    show_diagnostic(f"成功處理 {len(proceeded_EPA_df)} 筆EPA資料！", "success")
                else:
                    st.error("EPA 資料處理失敗或結果為空。")
                    proceeded_EPA_df = None
                    if 'processed_df' in st.session_state:
                        del st.session_state['processed_df']
            else:
                st.warning(f"無法載入工作表 '{selected_sheet}' 的EPA資料")
                proceeded_EPA_df = None
                if 'processed_df' in st.session_state:
                    del st.session_state['processed_df']
        else:
            st.error("無法獲取工作表列表")
            proceeded_EPA_df = None
            if 'processed_df' in st.session_state:
                del st.session_state['processed_df']
    else:
        # 從 session_state 恢復資料到全域變數
        retrieved_df = st.session_state.get('processed_df')
        if retrieved_df is not None and not retrieved_df.empty:
            proceeded_EPA_df = retrieved_df
            show_diagnostic("從快取載入處理後的資料", "info")
        else:
            proceeded_EPA_df = None
            if 'processed_df' in st.session_state: # 如果 key 存在但值無效
                 st.info("快取的資料無效或為空，請嘗試重新載入。")
                 del st.session_state['processed_df']

    # 後續顯示邏輯都基於 proceeded_EPA_df
    if proceeded_EPA_df is not None and not proceeded_EPA_df.empty:
        with st.expander("目前分析用資料 (已處理)", expanded=False):
            st.dataframe(proceeded_EPA_df)
        
        display_visualizations() # 調用修改後的函數，不傳參數
        
        # ========== 個別學生雷達圖分析 ==========
        st.markdown("<h1 style='color:#1E90FF; font-size:32px;'>個別學生雷達圖分析</h1>", unsafe_allow_html=True)

        # 先顯示每個階層、每個EPA項目的平均及95%CI
        if proceeded_EPA_df is not None and not proceeded_EPA_df.empty and '階層' in proceeded_EPA_df.columns:
            import numpy as np
            import scipy.stats as stats
            def mean_ci(series):
                n = series.count()
                mean = series.mean()
                std = series.std()
                if n > 1:
                    ci = stats.t.interval(0.95, n-1, loc=mean, scale=std/np.sqrt(n))
                    return pd.Series({'平均': mean, 'CI下界': ci[0], 'CI上界': ci[1], '樣本數': n})
                else:
                    return pd.Series({'平均': mean, 'CI下界': mean, 'CI上界': mean, '樣本數': n})
            # 只取有教師評核的資料
            score_col = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in proceeded_EPA_df.columns else '教師評核EPA等級'
            group_stats = proceeded_EPA_df.groupby(['階層', 'EPA評核項目'])[score_col].apply(mean_ci).unstack()
            # 展平成一層
            group_stats = group_stats.reset_index()
            # 四捨五入顯示
            group_stats['平均'] = group_stats['平均'].round(2)
            group_stats['CI下界'] = group_stats['CI下界'].round(2)
            group_stats['CI上界'] = group_stats['CI上界'].round(2)
            st.subheader("各階層EPA項目平均及95%信賴區間")
            st.dataframe(group_stats, use_container_width=True)

        required_columns_student = ['梯次', '學員姓名', 'EPA評核項目', '教師評核EPA等級', '學號']
        missing_columns_student = [col for col in required_columns_student if col not in proceeded_EPA_df.columns]
        
        if missing_columns_student:
            st.error(f"資料中缺少以下欄位，無法顯示學生雷達圖：{', '.join(missing_columns_student)}")
        else:
            standard_epa_categories = sorted(proceeded_EPA_df['EPA評核項目'].unique().tolist())
            total_students = len(proceeded_EPA_df['學號'].dropna().unique())
            # 確保梯次欄位存在才計算梯次數量
            num_batches_display = len(proceeded_EPA_df['梯次'].unique()) if '梯次' in proceeded_EPA_df.columns else "N/A"

            st.success(f"已選擇 {num_batches_display} 個梯次，共有 {total_students} 名不重複學生")
            
            student_numbers_in_batches = proceeded_EPA_df['學號'].dropna().unique()
            students_to_show = sorted([str(num) for num in student_numbers_in_batches])
            st.subheader(f"所有學生的EPA評核雷達圖 (所有梯次合併)")
            for student_id_str in students_to_show:
                student_df_all_batches = proceeded_EPA_df[proceeded_EPA_df['學號'].astype(str) == student_id_str].copy()
                if '教師' in student_df_all_batches.columns: # 篩選有教師評核的資料
                    student_df_all_batches = student_df_all_batches[student_df_all_batches['教師'].notna() & (student_df_all_batches['教師'] != '')]
                
                if student_df_all_batches.empty:
                    continue # 如果學生沒有資料或沒有教師評核資料，則不顯示
                
                st.markdown("---")
                student_name = student_df_all_batches['學員姓名'].iloc[0] if not student_df_all_batches.empty and '學員姓名' in student_df_all_batches.columns else student_id_str
                st.subheader(f"學生: {student_name} ({student_id_str}) (所有梯次合併)")
                
                # 先顯示該學生的資料
                with st.expander("學生評核資料", expanded=True):
                    st.dataframe(student_df_all_batches)
                
                display_student_data(
                    student_df_all_batches, 
                    student_id_str, 
                    standard_categories=standard_epa_categories
                )
    elif 'processed_df' in st.session_state : # proceeded_EPA_df 是 None 但 session_state 有key (可能值是None或empty)
        # 此情況已由 st.session_state.get('processed_df') 的 else 分支處理
        # 此處不需要額外訊息，避免重複
        pass
    else: # 初始狀態，或 proceeded_EPA_df 和 session_state 都沒有有效資料
        st.info("請點擊「重新載入 Google Sheet 資料」按鈕以開始分析。")
            
# ==================== 程式入口點 ====================

if __name__ == "__main__":
    # 取得原始資料
    show_UGY_EPA_section() 