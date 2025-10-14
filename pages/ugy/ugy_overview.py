"""
UGY 學生總覽模組
提供學生總覽的資料載入、處理和視覺化功能
"""

import re
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from modules.google_connection import fetch_google_form_data, SHOW_DIAGNOSTICS
from modules.data_processing import (
    process_epa_level, 
    convert_date_to_batch, 
    convert_tw_time,
    process_training_departments,
    get_student_departments,
    merge_epa_with_departments
)
from modules.visualization.visualization import plot_radar_chart, plot_epa_trend_px
from modules.visualization.dept_charts import create_dept_grade_percentage_chart
from modules.visualization.radar_trend import create_layer_radar_chart, create_epa_trend_charts

# 在檔案開頭宣告全域變數
proceeded_EPA_df = None

def show_diagnostic(message, level="info"):
    """顯示診斷訊息"""
    if SHOW_DIAGNOSTICS:
        if level == "success":
            st.success(f"✅ {message}")
        elif level == "warning":
            st.warning(f"⚠️ {message}")
        elif level == "error":
            st.error(f"❌ {message}")
        else:
            st.info(f"ℹ️ {message}")

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
                # 檢查並處理時間戳記欄位
                if '時間戳記' in df.columns:
                    # 先檢查時間戳記欄位是否包含有效的日期資料
                    sample_values = df['時間戳記'].dropna().head(5).tolist()
                    show_diagnostic(f"時間戳記欄位樣本值：{sample_values}", "info")
                    
                    # 嘗試轉換時間戳記
                    df['評核日期'] = df['時間戳記'].apply(convert_tw_time)
                    
                    # 檢查轉換結果
                    valid_dates = df['評核日期'].dropna()
                    if len(valid_dates) > 0:
                        df['評核日期'] = df['評核日期'].dt.date
                        show_diagnostic(f"成功轉換 {len(valid_dates)} 筆日期資料", "info")
                    else:
                        show_diagnostic("時間戳記欄位中沒有有效的日期資料", "warning")
                
                # 如果有有效的評核日期，進行梯次處理
                if '評核日期' in df.columns and not df['評核日期'].isna().all():
                    df['梯次'] = df['評核日期'].astype(str).apply(convert_date_to_batch)
                    show_diagnostic("日期轉換和梯次處理成功", "info")
                else:
                    st.warning("找不到有效的日期欄位，跳過梯次處理")
                
            except Exception as e:
                st.warning(f"日期處理時發生錯誤：{str(e)}")
            
            # 處理階層資料
            try:
                if '階層' in df.columns:
                    # 清理階層資料
                    df['階層'] = df['階層'].fillna('未知')
                    df['階層'] = df['階層'].astype(str).str.strip()
                    show_diagnostic(f"階層資料處理完成，共有 {df['階層'].nunique()} 個階層", "info")
            except Exception as e:
                st.warning(f"階層處理時發生錯誤：{str(e)}")
            
            return df
            
        except Exception as e:
            st.error(f"處理EPA資料時發生錯誤：{str(e)}")
            return None
    else:
        st.warning("沒有可處理的資料")
        return None

def safe_process_departments(df):
    """安全地處理訓練科部資料，包含錯誤處理和資料驗證"""
    try:
        if df is None or df.empty:
            st.warning("訓練科部資料為空或無效")
            return None
            
        # 檢查必要欄位（只需要姓名）
        required_columns = ['姓名']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"訓練科部資料缺少必要欄位：{', '.join(missing_columns)}")
            return None
            
        # 複製DataFrame避免修改原始資料
        processed_df = df.copy()
        
        # 清理資料：移除姓名欄位完全空白的行
        processed_df = processed_df.dropna(subset=['姓名'], how='all')
        
        # 處理姓名欄位
        processed_df['姓名'] = processed_df['姓名'].fillna('')
        
        # 移除姓名為空的資料
        processed_df = processed_df[processed_df['姓名'].str.strip() != '']
        
        if processed_df.empty:
            st.warning("清理後沒有有效的學生資料")
            return None
            
        # 找出可能的科部欄位（日期格式或其他）
        potential_dept_columns = []
        for col in processed_df.columns:
            if col not in required_columns:
                # 檢查是否為日期格式
                if isinstance(col, str):
                    if (len(col.split('/')) == 3 or 
                        len(col.split('-')) == 3 or 
                        len(col.split('.')) == 3):
                        potential_dept_columns.append(col)
                    else:
                        # 如果不是日期格式，也可能是科部欄位
                        potential_dept_columns.append(col)
        
        if not potential_dept_columns:
            st.warning("未找到科部相關欄位")
            return None
            
        # 添加處理資訊
        processed_df.attrs['dept_columns'] = potential_dept_columns
        processed_df.attrs['date_columns'] = [col for col in potential_dept_columns 
                                            if any(sep in col for sep in ['/', '-', '.'])]
        
        show_diagnostic(f"成功處理 {len(processed_df)} 筆學生資料，找到 {len(potential_dept_columns)} 個科部欄位", "success")
        return processed_df
        
    except Exception as e:
        st.error(f"處理訓練科部資料時發生錯誤：{str(e)}")
        return None

def safe_merge_epa_with_departments(epa_df, dept_df):
    """安全地合併EPA和訓練科部資料，不依賴學號欄位
    
    Args:
        epa_df (pd.DataFrame): EPA資料
        dept_df (pd.DataFrame): 訓練科部資料
        
    Returns:
        pd.DataFrame: 合併後的資料
    """
    try:
        if epa_df is None or dept_df is None:
            st.warning("EPA資料或訓練科部資料為空，跳過合併")
            return epa_df
            
        # 複製DataFrame避免修改原始資料
        epa_data = epa_df.copy()
        dept_data = dept_df.copy()
        
        # 檢查是否有評核日期欄位
        if '評核日期' not in epa_data.columns:
            st.warning("EPA資料中沒有評核日期欄位，無法進行時間相關的合併")
            # 如果沒有評核日期，仍然可以進行基本的科部資訊合併
            # 將訓練科部資料的欄位資訊添加到EPA資料中
            for col in dept_data.columns:
                if col not in ['姓名']:  # 排除姓名欄位
                    epa_data[f'科部_{col}'] = None
                    st.info(f"已添加科部欄位：科部_{col}")
            return epa_data
        
        # 如果有評核日期，嘗試進行時間相關的合併
        try:
            # 檢查是否有學生識別欄位
            student_id_col = None
            if '學號' in epa_data.columns:
                student_id_col = '學號'
            elif '學員姓名' in epa_data.columns:
                student_id_col = '學員姓名'
                # 創建虛擬學號欄位
                epa_data['學號'] = epa_data['學員姓名']
                student_id_col = '學號'
            
            if student_id_col is None:
                st.warning("EPA資料中沒有學號或學員姓名欄位，無法進行學生相關的合併")
                return epa_data
            
            # 確保學號為字串型態
            epa_data[student_id_col] = epa_data[student_id_col].astype(str)
            dept_data['姓名'] = dept_data['姓名'].astype(str)
            
            # 初始化訓練科部欄位
            epa_data['訓練科部'] = None
            
            # 獲取科部相關欄位
            dept_columns = dept_data.attrs.get('dept_columns', [])
            if not dept_columns:
                # 如果沒有dept_columns屬性，使用所有非姓名欄位
                dept_columns = [col for col in dept_data.columns if col != '姓名']
            
            # 對每一筆EPA資料尋找對應的訓練科部
            for idx, row in epa_data.iterrows():
                student_name = row.get('學員姓名', '')
                if pd.isna(student_name) or student_name == '':
                    continue
                    
                # 在訓練科部資料中尋找對應的學生
                student_dept_data = dept_data[dept_data['姓名'] == student_name]
                
                if not student_dept_data.empty:
                    # 找到學生，添加科部資訊
                    for dept_col in dept_columns:
                        if dept_col in student_dept_data.columns:
                            dept_value = student_dept_data[dept_col].iloc[0]
                            if pd.notna(dept_value) and dept_value != '':
                                epa_data.loc[idx, f'科部_{dept_col}'] = dept_value
                    
                    # 設置主要訓練科部欄位（使用第一個非空的科部值）
                    for dept_col in dept_columns:
                        if dept_col in student_dept_data.columns:
                            dept_value = student_dept_data[dept_col].iloc[0]
                            if pd.notna(dept_value) and dept_value != '':
                                epa_data.loc[idx, '訓練科部'] = dept_value
                                break
            
            show_diagnostic(f"成功合併訓練科部資料，共處理 {len(epa_data)} 筆EPA資料", "success")
            return epa_data
            
        except Exception as e:
            st.warning(f"合併過程中發生錯誤：{str(e)}，將返回原始EPA資料")
            return epa_data
            
    except Exception as e:
        st.error(f"合併EPA和訓練科部資料時發生錯誤：{str(e)}")
        return epa_df

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
            # 確定學生識別欄位
            student_id_col = '學號' if '學號' in batch_data.columns else '學員姓名'
            if student_id_col not in batch_data.columns:
                student_id_col = None
                
            batch_stats[batch] = {
                '評核數量': len(batch_data),
                '學生人數': len(batch_data[student_id_col].unique()) if student_id_col else 0,
                'EPA項目數': len(batch_data['EPA評核項目'].unique()) if 'EPA評核項目' in batch_data.columns else 0
            }
        
        return sorted_batches, {
            'sorted_batches': sorted_batches,
            'total_batches': len(sorted_batches),
            'batch_stats': batch_stats
        }
        
    except Exception as e:
        return [], {'error': f'處理梯次資料時發生錯誤：{str(e)}'}

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
        display_columns = ['姓名'] + date_columns
        
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


def display_visualizations():
    """顯示資料視覺化"""
    global proceeded_EPA_df  # 使用全域變數

    # 檢查 proceeded_EPA_df 是否有效
    if proceeded_EPA_df is None or proceeded_EPA_df.empty:
        st.warning("沒有可用的已處理資料進行視覺化。")
        return

    st.markdown("<h1 style='color:#1E90FF; font-size:32px;'>學生總覽</h1>", unsafe_allow_html=True)
    
    # ========== 實習科部多選篩選 ========== 
    # 使用 proceeded_EPA_df 進行篩選
    current_df_view = proceeded_EPA_df.copy() # 建立副本以進行篩選，不直接修改全域變數

    if '實習科部' in current_df_view.columns:
        all_depts = sorted([d for d in current_df_view['實習科部'].dropna().unique().tolist() if d not in [None, '', 'None']])
        if all_depts:
            selected_depts = st.multiselect(
                "選擇實習科部 (可複選)",
                options=all_depts,
                default=all_depts,
                format_func=lambda x: f"科部: {x}",
                key="overview_dept_selector"
            )
            if not selected_depts:
                st.warning("請選擇至少一個實習科部")
                return
            
            # 按科部篩選
            current_df_view = current_df_view[current_df_view['實習科部'].isin(selected_depts)].copy()
    
    # ========== 梯次時間區段篩選 ==========
    if '梯次' in current_df_view.columns:
        all_batches = sorted(current_df_view['梯次'].dropna().unique().tolist())
        if all_batches:
            selected_batches = st.multiselect(
                "選擇梯次時間區段 (可複選)",
                options=all_batches,
                default=all_batches,
                format_func=lambda x: f"梯次: {x}",
                key="overview_batch_selector"
            )
            if not selected_batches:
                st.warning("請選擇至少一個梯次時間區段")
                return
            
            # 按梯次篩選
            current_df_view = current_df_view[current_df_view['梯次'].isin(selected_batches)].copy()
    
    # ========== 1. 計算梯次排序（背景處理） ==========
    try:
        layer_batch_orders = {}
        
        if '階層' in current_df_view.columns:
            all_layers = sorted(current_df_view['階層'].unique().tolist())
            
            selected_layers = st.multiselect(
                "選擇階層 (可複選)",
                options=all_layers,
                default=all_layers,
                format_func=lambda x: f"階層: {x}",
                key="overview_layer_selector"
            )
            
            if not selected_layers:
                st.warning("請選擇至少一個階層")
                return
            
            # ========== EPA評核項目篩選 ==========
            if 'EPA評核項目' in current_df_view.columns:
                all_epa_items = sorted(current_df_view['EPA評核項目'].unique().tolist())
                
                # 預設只選擇「當班處置」項目
                default_epa_items = ['當班處置'] if '當班處置' in all_epa_items else all_epa_items[:1] if all_epa_items else []
                
                selected_epa_items = st.multiselect(
                    "選擇EPA評核項目 (可複選)",
                    options=all_epa_items,
                    default=default_epa_items,
                    format_func=lambda x: f"項目: {x}",
                    key="overview_epa_selector_with_layers"
                )
                
                if not selected_epa_items:
                    st.warning("請選擇至少一個EPA評核項目")
                    return
                
                # 先按階層篩選，再按EPA評核項目篩選
                filtered_by_layer_df = current_df_view[
                    (current_df_view['階層'].isin(selected_layers)) & 
                    (current_df_view['EPA評核項目'].isin(selected_epa_items))
                ].copy()
            else:
                # 如果沒有EPA評核項目欄位，只按階層篩選
                filtered_by_layer_df = current_df_view[current_df_view['階層'].isin(selected_layers)].copy()
            
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
            
            # ========== EPA評核項目篩選（無階層情況） ==========
            if 'EPA評核項目' in current_df_view.columns:
                all_epa_items = sorted(current_df_view['EPA評核項目'].unique().tolist())
                
                # 預設只選擇「當班處置」項目
                default_epa_items = ['當班處置'] if '當班處置' in all_epa_items else all_epa_items[:1] if all_epa_items else []
                
                selected_epa_items = st.multiselect(
                    "選擇EPA評核項目 (可複選)",
                    options=all_epa_items,
                    default=default_epa_items,
                    format_func=lambda x: f"項目: {x}",
                    key="overview_epa_selector_no_layers"
                )
                
                if not selected_epa_items:
                    st.warning("請選擇至少一個EPA評核項目")
                    return
                
                # 按EPA評核項目篩選
                filtered_by_layer_df = current_df_view[current_df_view['EPA評核項目'].isin(selected_epa_items)].copy()
            else:
                # 如果沒有EPA評核項目欄位，使用原始資料
                filtered_by_layer_df = current_df_view
            
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
        # ===== 1. 各實習科部教師評核等級數量分布 =====
        if '實習科部' in filtered_by_layer_df.columns or '訓練科部' in filtered_by_layer_df.columns:
            if '教師評核EPA等級_數值' in filtered_by_layer_df.columns:
                st.subheader("各實習科部教師評核等級數量分布")
                
                # 確定科部欄位名稱
                dept_column = '實習科部' if '實習科部' in filtered_by_layer_df.columns else '訓練科部'
                
                # 創建百分比和數量長條圖
                dept_grade_percentage_fig, dept_grade_quantity_fig = create_dept_grade_percentage_chart(filtered_by_layer_df, dept_column)
                
                # 顯示數量圖表（第一個）
                st.plotly_chart(dept_grade_quantity_fig, use_container_width=True, key="dept_grade_quantity_chart")
            else:
                st.warning(f"沒有教師評核EPA等級數值資料，無法進行數量分析")
        
        # ===== 2. 實習科部教師評核等級百分比分析 =====
        if '實習科部' in filtered_by_layer_df.columns or '訓練科部' in filtered_by_layer_df.columns:
            if '教師評核EPA等級_數值' in filtered_by_layer_df.columns:
                st.subheader("各實習科部教師評核等級百分比分布")
                
                # 確定科部欄位名稱
                dept_column = '實習科部' if '實習科部' in filtered_by_layer_df.columns else '訓練科部'
                
                # 創建百分比和數量長條圖
                dept_grade_percentage_fig, dept_grade_quantity_fig = create_dept_grade_percentage_chart(filtered_by_layer_df, dept_column)
                
                # 顯示百分比圖表（第二個）
                st.plotly_chart(dept_grade_percentage_fig, use_container_width=True, key="dept_grade_percentage_chart")
            else:
                st.warning(f"沒有教師評核EPA等級數值資料，無法進行百分比分析")

        # ===== 3. EPA評核雷達圖 =====
        st.subheader("EPA評核雷達圖")
        
        if not filtered_by_layer_df.empty:
            radar_fig = create_layer_radar_chart(filtered_by_layer_df, selected_layers)
            st.plotly_chart(radar_fig, use_container_width=True, key="all_layers_radar_chart")
        else:
            st.error("沒有足夠的資料繪製雷達圖 (經過篩選後)")

        # ===== 4. EPA評核趨勢分析 =====
        if selected_layers: # 只有在選擇了階層時才顯示
            st.subheader("EPA評核趨勢分析")
            trend_figures = create_epa_trend_charts(
                filtered_by_layer_df, 
                selected_layers, 
                layer_batch_orders, 
                global_sorted_batches
            )
            
            for i, layer in enumerate(selected_layers):
                if i < len(trend_figures):
                    st.caption(f"階層 {layer} 的EPA評核趨勢")
                    st.plotly_chart(trend_figures[i], use_container_width=True, key=f"trend_chart_{layer}")
                    if i != len(selected_layers) - 1:
                        st.markdown("---")

def show_ugy_student_overview():
    """顯示 UGY 學生總覽的主要函數"""
    global proceeded_EPA_df  # 使用全域變數
    st.title("UGY EPA分析")

    # 檢查是否需要重新載入/處理資料
    if st.button("重新載入 Google Sheet 資料"):
        # 執行資料載入與處理流程
        raw_df, sheet_titles = load_sheet_data(show_info=False)
        
        # 嘗試載入實習科部資料，如果失敗則嘗試載入訓練科部資料
        dept_df = None
        processed_dept_df = None
        
        # 優先嘗試載入「訓練科部」工作表
        try:
            dept_df, _ = load_sheet_data(sheet_title="訓練科部", show_info=False)
            if dept_df is not None and not dept_df.empty:
                # 使用新的安全處理函數
                processed_dept_df = safe_process_departments(dept_df)
                if processed_dept_df is not None:
                    show_diagnostic("成功載入並處理訓練科部資料", "success")
                    with st.expander("訓練科部資料", expanded=False):
                        display_dept_data(processed_dept_df)
                else:
                    show_diagnostic("訓練科部資料處理失敗", "warning")
            else:
                st.warning("訓練科部工作表為空")
        except Exception as e:
            st.warning(f"載入實習科部資料失敗：{str(e)}")
            # 如果實習科部載入失敗，嘗試載入訓練科部資料
            try:
                st.info("嘗試載入訓練科部資料作為備用...")
                dept_df, _ = load_sheet_data(sheet_title="訓練科部", show_info=False)
                if dept_df is not None and not dept_df.empty:
                    # 使用新的安全處理函數
                    processed_dept_df = safe_process_departments(dept_df)
                    if processed_dept_df is not None:
                        show_diagnostic("成功載入並處理訓練科部資料（備用）", "success")
                        with st.expander("訓練科部資料（備用）", expanded=False):
                            display_dept_data(processed_dept_df)
                    else:
                        show_diagnostic("訓練科部資料處理失敗", "warning")
                else:
                    st.warning("訓練科部資料也無法載入")
            except Exception as e2:
                st.error(f"載入訓練科部資料也失敗：{str(e2)}")
                st.info("將繼續處理EPA資料，但無法合併科部資訊")

        current_processed_df = None
        if sheet_titles:
            selected_sheet = sheet_titles[0] # 假設第一個是主要的EPA資料表
            epa_raw_df, _ = load_sheet_data(sheet_title=selected_sheet, show_info=False)

            if epa_raw_df is not None:
                with st.expander("載入的原始EPA資料", expanded=False):
                    st.dataframe(epa_raw_df)
                
                current_processed_df = process_data(epa_raw_df.copy()) # 傳入副本進行處理
                
                if current_processed_df is not None and not current_processed_df.empty:
                    if processed_dept_df is not None:
                        try:
                            # 使用改進的合併函數，不依賴學號欄位
                            current_processed_df = safe_merge_epa_with_departments(current_processed_df, processed_dept_df)
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
    
    # 檢查是否有已處理的資料可以顯示
    if 'processed_df' in st.session_state:
        # 從 session_state 恢復資料到全域變數
        retrieved_df = st.session_state.get('processed_df')
        if retrieved_df is not None and not retrieved_df.empty:
            proceeded_EPA_df = retrieved_df
            show_diagnostic("顯示已載入的資料", "info")
        else:
            proceeded_EPA_df = None
            if 'processed_df' in st.session_state: # 如果 key 存在但值無效
                 st.info("快取的資料無效或為空，請按上方按鈕重新載入。")
                 del st.session_state['processed_df']
    else:
        proceeded_EPA_df = None
        st.info("請按上方「重新載入 Google Sheet 資料」按鈕開始載入資料")

    # 後續顯示邏輯都基於 proceeded_EPA_df
    if proceeded_EPA_df is not None and not proceeded_EPA_df.empty:
        with st.expander("目前分析用資料 (已處理)", expanded=False):
            st.dataframe(proceeded_EPA_df)
        
        display_visualizations() # 調用修改後的函數，不傳參數
    else:
        st.warning("沒有可用的資料進行分析，請先載入資料。")
