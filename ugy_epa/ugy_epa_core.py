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
from modules.supabase_connection import SupabaseConnection
# 暫時註解掉不需要的導入
# from modules.data_analysis import analyze_epa_data

# ==================== 資料載入與處理函數 ====================

def load_sheet_data(sheet_title=None, show_info=True):
    """載入資料（從 Supabase）
    
    Args:
        sheet_title (str, optional): 已不再使用
        show_info (bool): 是否顯示載入資訊
        
    Returns:
        tuple: (DataFrame, None)
    """
    try:
        # 建立 Supabase 連線
        supabase_conn = SupabaseConnection()
        
        # 根據 sheet_title 決定要載入哪種資料
        if sheet_title == "訓練科部":
            df = supabase_conn.fetch_department_data()
        else:
            df = supabase_conn.fetch_epa_data()
        
        if show_info:
            st.success(f"成功從 Supabase 載入 {len(df)} 筆資料")
        
        return df, None  # 第二個返回值保持為 None 以維持相容性
        
    except Exception as e:
        st.error(f"從 Supabase 載入資料失敗：{str(e)}")
        return None, None

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
                # 只保留教師欄位有資料的列
                df = df[df['教師'].notna() & (df['教師'] != '')]
                
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

def display_student_data(student_df, student_id, full_df=None, standard_categories=None):
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
            full_df=full_df, 
            standard_categories=standard_categories
        )
        st.plotly_chart(radar_fig, use_container_width=True, key=f"student_radar_{student_id}")
    
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
        draw_student_trend(student_df, student_id, full_df)
    elif '梯次' in student_df.columns:
        # 單一梯次，仍然顯示趨勢圖但添加說明
        st.caption("EPA評核趨勢圖 (僅單一梯次資料)")
        draw_student_trend(student_df, student_id, full_df)

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

def display_visualizations(df):
    """顯示資料視覺化"""
    st.markdown("<h1 style='color:#1E90FF; font-size:32px;'>學生總覽</h1>", unsafe_allow_html=True)
    
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
    
    # ========== 2. 所有階層的雷達圖（合併在同一個圖中） ==========
    if '階層' not in df.columns:
        st.error("資料框中沒有 '階層' 欄位，無法繪製視覺化圖表")
    else:
        layers = df['階層'].unique()
        
        # ===== 雷達圖區域 (所有階層合併) =====
        st.subheader("EPA評核雷達圖")
        
        # 檢查是否有足夠的資料繪製圖表
        if not df.empty:
            # 使用plot_radar_chart的完整模式繪製所有階層合併的雷達圖
            radar_fig = plot_radar_chart(
                df=df,  # 使用完整資料框
                plot_types=['layers'],  # 指定繪製所有階層
                title="各階層EPA評核雷達圖比較",
                labels={
                    'layer': '階層 {}',  # {} 會被替換成實際的階層
                    'teacher_avg': '教師評核平均',
                    'student_avg': '學員自評平均',
                }
            )
            
            # 調整圖表外觀
            radar_fig.update_layout(
                height=500,  # 增加高度，因為有多個階層
                margin=dict(t=50, b=50, l=50, r=50),
                showlegend=True,
                legend=dict(
                    orientation="h",  # 水平圖例
                    yanchor="bottom",
                    y=1.02,  # 放在圖表上方
                    xanchor="center",
                    x=0.5
                )
            )
            
            # 顯示雷達圖
            st.plotly_chart(radar_fig, use_container_width=True, key="all_layers_radar_chart")
        else:
            st.error("沒有足夠的資料繪製雷達圖")
        
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
                trend_fig = plot_epa_trend_px(
                    df=layer_df,
                    x_col='梯次',
                    y_col='教師評核EPA等級_數值',
                    group_col='EPA評核項目',
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
                
                # 顯示趨勢圖，為每個趨勢圖添加唯一key
                st.plotly_chart(trend_fig, use_container_width=True, key=f"trend_chart_{layer}")
                
                # 添加分隔線，除了最後一個階層
                if layer != layers[-1]:
                    st.markdown("---")
                    
            except Exception as e:
                st.error(f"繪製階層 {layer} 的趨勢圖時發生錯誤: {e}")

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
    st.title("UGY EPA分析")
    
    try:
        # 載入EPA資料
        df, sheet_titles = load_sheet_data(show_info=False)
        
        # 載入訓練科部資料
        dept_sheet_title = "訓練科部"
        dept_df, _ = load_sheet_data(sheet_title=dept_sheet_title, show_info=False)
        
        if dept_df is not None:
            # 處理訓練科部資料
            processed_dept_df = process_training_departments(dept_df)
            show_diagnostic("成功載入訓練科部資料", "success")
            
            # 顯示訓練科部資料
            with st.expander("訓練科部資料", expanded=False):
                display_dept_data(processed_dept_df)
        
        if sheet_titles:
            # 直接抓第一個工作表（EPA資料）
            selected_sheet = sheet_titles[0]
            
            # 重新載入選擇的工作表資料
            df, _ = load_sheet_data(sheet_title=selected_sheet, show_info=False)
            
            if df is not None:
                # 使用下拉式選單顯示原始資料
                with st.expander("載入的原始資料", expanded=False):
                    st.dataframe(df)
                
                # 處理EPA資料
                processed_df = process_data(df)
                
                if processed_df is not None and not processed_df.empty:
                    # 合併訓練科部資料
                    if dept_df is not None:
                        try:
                            processed_df = merge_epa_with_departments(processed_df, processed_dept_df)
                            show_diagnostic("成功合併訓練科部資料", "success")
                        except Exception as e:
                            st.warning(f"合併訓練科部資料時發生錯誤：{str(e)}")
                    
                    # 處理梯次資料
                    sorted_batches, batch_info = process_batch_data(processed_df)
                    if 'error' not in batch_info:
                        show_diagnostic(f"成功處理梯次資料，共有 {batch_info['total_batches']} 個梯次", "success")
                        
                        # 顯示梯次統計資訊
                        with st.expander("梯次統計資訊", expanded=False):
                            for batch in sorted_batches:
                                stats = batch_info['batch_stats'][batch]
                                st.write(f"梯次 {batch}:")
                                st.write(f"- 評核數量: {stats['評核數量']}")
                                st.write(f"- 學生人數: {stats['學生人數']}")
                                st.write(f"- EPA項目數: {stats['EPA項目數']}")
                                st.write("---")
                    else:
                        st.warning(batch_info['error'])
                    
                    show_diagnostic(f"成功處理 {len(processed_df)} 筆EPA資料！", "success")
                    
                    # 使用下拉式選單顯示處理後的資料
                    with st.expander("處理後資料", expanded=False):
                        st.dataframe(processed_df)
                    
                    # 顯示視覺化圖表
                    display_visualizations(processed_df)
                    
                    # ========== 5. 個別學生雷達圖分析 ==========
                    st.markdown("<h1 style='color:#1E90FF; font-size:32px;'>個別學生雷達圖分析</h1>", unsafe_allow_html=True)
                    
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
                            default=sorted_batches,  # 修改為預設全選所有梯次
                            format_func=lambda x: f"梯次: {x}"
                        )
                        
                        if not selected_batches:
                            st.warning("請選擇至少一個梯次")
                        else:
                            # 篩選所選梯次的資料
                            batch_df = processed_df[processed_df['梯次'].isin(selected_batches)]
                            
                            # 獲取選定梯次的所有學生
                            student_data = batch_df.groupby(['學號', '梯次']).size().reset_index()
                            student_data.columns = ['學號', '梯次', '評核數量']
                            
                            # 只使用學號來識別學生
                            student_numbers = batch_df['學號'].dropna().unique()
                            
                            # 顯示學生數量統計
                            total_students = len(student_numbers)
                            st.success(f"已選擇 {len(selected_batches)} 個梯次，共有 {total_students} 名不重複學生")
                            
                            # 決定顯示方式
                            display_mode = st.radio(
                                "顯示模式",
                                options=["選擇單一學生", "顯示所有學生", "按梯次分組顯示"],
                                horizontal=True
                            )
                            
                            if display_mode == "選擇單一學生":
                                # 獲取不重複的學生學號列表
                                students = sorted([str(num) for num in student_numbers])
                                
                                # 根據使用者角色過濾學生選項
                                user_role = st.session_state.get('role', 'admin')
                                user_student_id = st.session_state.get('student_id', None)
                                
                                # 如果是UGY（student角色），只能看到自己的資料
                                if user_role == 'student' and user_student_id:
                                    students = [str(user_student_id)] if str(user_student_id) in students else []
                                    if not students:
                                        st.warning("找不到您的評核資料，請確認資料已正確上傳。")
                                        return
                                
                                # 學生選擇器
                                selected_student = st.selectbox(
                                    "選擇學生學號",
                                    options=students
                                )
                                
                                if selected_student:
                                    # 篩選一次學生資料並創建副本
                                    student_df_filtered = batch_df[batch_df['學號'].astype(str) == str(selected_student)].copy()

                                    # 新增：顯示該學生的原始資料
                                    st.subheader(f"學生 {selected_student} 的原始資料")
                                    display_columns = [
                                        '時間戳記', 
                                        '學號', 
                                        '學員姓名', 
                                        '梯次', 
                                        'EPA評核項目', 
                                        '教師評核EPA等級',
                                        '教師評核EPA等級_數值',
                                        '回饋'
                                    ]
                                    # 確保欄位存在才選取
                                    display_columns_exist = [col for col in display_columns if col in student_df_filtered.columns]
                                    if not student_df_filtered.empty:
                                        display_df_raw = student_df_filtered[display_columns_exist].copy()
                                        # 排序資料 - 先依梯次，再依EPA評核項目
                                        if '梯次' in display_df_raw.columns and 'EPA評核項目' in display_df_raw.columns:
                                            display_df_raw = display_df_raw.sort_values(['梯次', 'EPA評核項目'])
                                    else:
                                        display_df_raw = pd.DataFrame(columns=display_columns_exist) # 創建空 df 以防萬一

                                    # 顯示資料框
                                    st.dataframe(
                                        display_df_raw,
                                        use_container_width=True,
                                        hide_index=True
                                    )
                                    st.info(f"共有 {len(display_df_raw)} 筆資料")
                                    st.markdown("---")

                                    # 檢查篩選後的資料是否為空
                                    if student_df_filtered.empty:
                                        st.warning(f"在選定的梯次中找不到學生 {selected_student} 的有效資料，無法進行後續分析。")
                                        # 可以選擇在此 return 或 st.stop()
                                        return None # 或者 pass

                                    # 獲取該學生參與的所有梯次 (從已篩選的 df)
                                    student_batches = student_df_filtered['梯次'].unique().tolist()

                                    # 如果學生參與了多個梯次，提供梯次選擇
                                    if len(student_batches) > 1:
                                        batch_for_student = st.radio(
                                            "選擇要顯示的梯次",
                                            options=["所有梯次合併"] + sorted(student_batches), # 排序梯次選項
                                            horizontal=True,
                                            key=f"batch_select_{selected_student}" # 添加 key 避免狀態問題
                                        )

                                        if batch_for_student == "所有梯次合併":
                                            st.subheader(f"學生 {selected_student} 的EPA評核 (所有梯次合併)")
                                            # 直接使用已篩選的 df
                                            df_to_display = student_df_filtered
                                        else:
                                            st.subheader(f"學生 {selected_student} 的EPA評核 (梯次: {batch_for_student})")
                                            # 從已篩選的 df 中進一步篩選梯次
                                            df_to_display = student_df_filtered[student_df_filtered['梯次'] == batch_for_student].copy()

                                    elif len(student_batches) == 1:
                                         # 只有一個梯次，直接顯示
                                        st.subheader(f"學生 {selected_student} 的EPA評核 (梯次: {student_batches[0]})")
                                        # 直接使用已篩選的 df
                                        df_to_display = student_df_filtered
                                    else: # student_batches 為空 (理論上 student_df_filtered.empty 檢查會攔截)
                                         st.error(f"內部錯誤：找不到學生 {selected_student} 的梯次資訊。")
                                         return None # 或者 pass

                                    # --- 統一呼叫 display_student_data ---
                                    # 檢查最終要顯示的 df 是否為空
                                    if df_to_display.empty:
                                         st.warning(f"找不到學生 {selected_student} 在梯次 '{batch_for_student if len(student_batches)>1 else (student_batches[0] if student_batches else 'N/A')}' 的資料。")
                                    else:
                                         # 新增：顯示資料充足性分析 (移到這裡)
                                         all_epa_items = sorted(processed_df['EPA評核項目'].unique().tolist()) # 從全局獲取標準項目
                                         completeness_analysis = analyze_student_data_completeness(df_to_display, all_epa_items)
                                         if not completeness_analysis.empty:
                                             st.subheader("資料充足性分析")
                                             st.caption("評核數量>=2為充足，<2為不足")
                                             # 根據資料充足性設定樣式
                                             def highlight_completeness(val):
                                                 if val == "✅ 充足":
                                                     return 'background-color: rgba(0, 255, 0, 0.2)'
                                                 elif val == "❌ 不足":
                                                     return 'background-color: rgba(255, 0, 0, 0.2)'
                                                 return ''
                                             styled_analysis = completeness_analysis.style.applymap(
                                                 highlight_completeness, subset=['資料充足性']
                                             )
                                             st.dataframe(styled_analysis, use_container_width=True)
                                             # 統計代碼
                                             insufficient_count = (completeness_analysis['評核數量'] < 2).sum()
                                             total_count = len(completeness_analysis)
                                             if insufficient_count > 0:
                                                 st.warning(f"共有 {insufficient_count}/{total_count} 個項目評核數量不足 (少於2份)")
                                             else:
                                                 st.success(f"所有 {total_count} 個項目都有充足的評核資料 (2份或以上)")

                                         # 呼叫圖表顯示函數
                                         display_student_data(df_to_display, selected_student, full_df=processed_df, standard_categories=standard_epa_categories)

                                    # 新增：顯示學生訓練科部資訊
                                    if 'dept_data' in st.session_state and display_mode == "選擇單一學生" and selected_student:
                                        st.subheader("訓練科部資訊")
                                        dept_info = get_student_departments(st.session_state['dept_data'], selected_student)
                                        
                                        if "error" not in dept_info:
                                            # 創建訓練科部資訊的DataFrame
                                            dept_data = pd.DataFrame(list(dept_info["訓練科部"].items()), 
                                                                   columns=['日期', '訓練科部'])
                                            dept_data = dept_data.sort_values('日期')
                                            
                                            # 顯示訓練科部資訊
                                            st.dataframe(dept_data, use_container_width=True)
                                        else:
                                            st.warning(f"無法獲取學生 {selected_student} 的訓練科部資訊：{dept_info['error']}")
                            
                            elif display_mode == "顯示所有學生":
                                # 獲取不重複的學生列表 (從已篩選梯次的 batch_df 中)
                                student_numbers_in_batches = batch_df['學號'].dropna().unique()
                                students_to_show = sorted([str(num) for num in student_numbers_in_batches])
                                
                                # 是否合併梯次資料
                                merge_batches = st.checkbox("合併所有梯次資料", value=True, key="merge_batches_all_students")
                                
                                st.subheader(f"所有學生的EPA評核雷達圖" + 
                                           (" (所有梯次合併)" if merge_batches else " (按梯次或合併顯示)"))
                                
                                # 循環顯示每個學生
                                for student_id_str in students_to_show:
                                    # --- 獲取學生資料 (統一使用 astype(str)) ---
                                    student_df_all_batches = batch_df[batch_df['學號'].astype(str) == student_id_str].copy()
                                    
                                    # 檢查是否有資料
                                    if student_df_all_batches.empty:
                                        st.warning(f"找不到學生 {student_id_str} 在所選梯次中的資料，跳過顯示。")
                                        continue # 處理下一個學生

                                    # 使用水平線分隔不同學生
                                    st.markdown("---")
                                    
                                    # 顯示學生子標題
                                    student_batches = student_df_all_batches['梯次'].unique().tolist()
                                    if merge_batches or len(student_batches) > 1:
                                        st.subheader(f"學生: {student_id_str} ({'所有梯次合併' if merge_batches else f'參與 {len(student_batches)} 個梯次'}) ")
                                        df_to_display_all = student_df_all_batches
                                    elif len(student_batches) == 1:
                                        st.subheader(f"學生: {student_id_str} (梯次: {student_batches[0]})")
                                        df_to_display_all = student_df_all_batches # 因為只有一個梯次，等同合併
                                    else: # student_batches is empty (理論上已被上面 empty 檢查攔截)
                                        st.error(f"內部錯誤：找不到學生 {student_id_str} 的梯次資訊。")
                                        continue

                                    # 顯示學生資料（雷達圖和回饋）
                                    display_student_data(df_to_display_all, student_id_str, full_df=processed_df, 
                                                        standard_categories=standard_epa_categories)
                    
                    return processed_df
                else:
                    st.error("資料處理失敗")
                    return df
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

# ==================== 程式入口點 ====================

if __name__ == "__main__":
    # 取得原始資料
    show_UGY_EPA_section() 