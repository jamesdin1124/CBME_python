import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
import re
import traceback
from plotly.colors import convert_colors_to_same_type, make_colorscale



def plot_radar_chart(df=None, plot_types=None, student_id=None, categories=None, values=None, 
                    title="EPA 雷達圖", standard_categories=None, proceeded_EPA_df=None,
                    labels={
                        'layer': '階層 {}',  # {} 會被替換成實際的層級
                        'teacher_avg': '教師評核平均',
                        'student_avg': '學員自評平均',
                        'individual': '學員 {}'  # {} 會被替換成實際的學員ID
                    }):
    """繪製 EPA 雷達圖，支援多種模式包括學生個人雷達圖
    
    Args:
        df (DataFrame, optional): 包含EPA評核資料的DataFrame
        plot_types (list, optional): 要顯示的圖表類型列表 (在學生模式下通常不使用)
        student_id (str, optional): 學生學號，用於學生模式
        categories (list, optional): 雷達圖的類別列表 (簡單模式)
        values (list, optional): 對應類別的數值列表 (簡單模式)
        title (str): 圖表標題
        standard_categories (list, optional): 標準的EPA評核項目順序列表
        labels (dict): 圖例標籤的自定義文字
        
    Returns:
        plotly.graph_objects.Figure: 雷達圖物件
    """
    import hashlib # 用於生成顏色
    
    # 定義階層顏色 (移到函數開頭以便學生模式使用)
    layer_colors = {
        'C1': 'rgba(255, 100, 100, 0.7)',  # 淡紅色
        'C2': 'rgba(100, 100, 255, 0.7)',  # 淡藍色
        'PGY': 'rgba(100, 200, 100, 0.7)' # 淡綠色
        # 可以根據需要添加更多階層
    }
    def get_random_color(seed_str, alpha=0.7):
        """根據字符串生成確定性隨機顏色"""
        hash_value = int(hashlib.md5(str(seed_str).encode()).hexdigest(), 16)
        r = (hash_value & 0xFF) % 200 
        g = ((hash_value >> 8) & 0xFF) % 200
        b = ((hash_value >> 16) & 0xFF) % 200
        return f'rgba({r}, {g}, {b}, {alpha})'

    # 創建默認圖表物件，確保即使中途出錯，也能返回一個有效的圖表
    default_fig = go.Figure()
    default_fig.update_layout(
        title="無法繪製雷達圖：資料不足或格式錯誤",
        annotations=[dict(
            text="請檢查輸入資料是否符合要求",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5
        )]
    )

    try:
        # 檢測使用模式：
        # 1. 簡單模式：直接提供categories和values
        # 2. 學生模式：提供student_id和df
        # 3. 完整模式：提供df和plot_types
        
        # === 簡單模式 ===
        if categories is not None and values is not None:
            categories_closed = categories + [categories[0]]
            values_closed = values + [values[0]]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill='toself',
                name='數值'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 5]
                    )
                ),
                showlegend=True,
                title=title
            )
            return fig
        
        # === 學生模式 ===
        elif student_id is not None and df is not None:
            # 確保 df 是有效的 DataFrame
            if df is None or df.empty:
                return default_fig

            # 篩選該學生的資料 (使用學號)
            # 注意：傳入的 df 應該已經是篩選過梯次的學生資料了
            # 我們在這裡主要是為了計算該學生的平均值
            student_df = df # 直接使用傳入的 df

            if student_df.empty:
                # 建立一個空的雷達圖，並添加警告訊息
                fig = go.Figure()
                fig.update_layout(
                    title=f"找不到學生 {student_id} 的雷達圖資料",
                    annotations=[
                        dict(
                            text="資料不足，無法繪製雷達圖",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5
                        )
                    ]
                )
                return fig
            
            # --- 新增：獲取學生姓名 --- 
            student_name = ""
            if '學員姓名' in student_df.columns and not student_df.empty:
                # 嘗試獲取第一個非空的姓名
                valid_names = student_df['學員姓名'].dropna()
                if not valid_names.empty:
                    student_name = valid_names.iloc[0]
            # 創建組合標籤
            student_label = f"{student_id}" 
            if student_name: # 如果成功獲取姓名
                student_label += f" ({student_name})"
            # --- 結束新增 --- 

            # 決定使用的EPA評核項目標準順序
            if standard_categories is None:
                standard_categories = sorted(df['EPA評核項目'].unique().tolist())
            
            # 按標準順序建立學生的評分值
            student_values = []
            categories = []
            score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in student_df.columns else '教師評核EPA等級'
            
            for category in standard_categories:
                category_data = student_df[student_df['EPA評核項目'] == category]
                if not category_data.empty:
                    avg_score = category_data[score_column].mean()
                    categories.append(category)
                    student_values.append(avg_score)
                else:
                    # 若該項目沒有分數，自動補 1
                    categories.append(category)
                    student_values.append(1)
            
            # 如果沒有足夠的資料，建立空圖
            if len(categories) < 2:
                fig = go.Figure()
                fig.update_layout(
                    title=f"學生 {student_label} 的評核項目不足，無法繪製雷達圖",
                    annotations=[
                        dict(
                            text="至少需要2個評核項目才能繪製雷達圖",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5
                        )
                    ]
                )
                return fig
            
            # 確保資料是閉合的
            categories_closed = categories + [categories[0]]
            student_values_closed = student_values + [student_values[0]]
            
            # 創建plotly雷達圖
            fig = go.Figure()
            # 繪製學生個人平均 (實線填充) - 使用組合標籤
            fig.add_trace(go.Scatterpolar(
                r=student_values_closed,
                theta=categories_closed,
                fill='toself',
                name=labels['individual'].format(student_label) # 使用組合標籤
            ))
            
            # 只顯示該學生所屬階層的平均，不顯示全體平均與CI區間
            student_layer = None
            if '階層' in student_df.columns and not student_df.empty:
                student_layer = student_df['階層'].iloc[0]
            if student_layer and proceeded_EPA_df is not None and hasattr(proceeded_EPA_df, 'columns') and '階層' in proceeded_EPA_df.columns:
                full_score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in proceeded_EPA_df.columns else '教師評核EPA等級'
                layer_df = proceeded_EPA_df[proceeded_EPA_df['階層'] == student_layer]
                if layer_df.empty:
                    print(f'警告：找不到階層 {student_layer} 的資料')
                # 強制 categories 來源與階層平均一致
                categories_for_layer = categories
                layer_values = []
                for category in categories_for_layer:
                    layer_data = layer_df[layer_df['EPA評核項目'] == category]
                    if not layer_data.empty:
                        layer_avg = layer_data[full_score_column].mean()
                        layer_values.append(layer_avg)
                    else:
                        layer_values.append(1)  # 若無資料補1
                layer_values_closed = layer_values + [layer_values[0]]
                layer_color = layer_colors.get(student_layer, get_random_color(student_layer, 0.7))
                fig.add_trace(go.Scatterpolar(
                    r=layer_values_closed,
                    theta=categories_closed,
                    fill='none',
                    name=f'{student_layer} 階層平均',
                    line=dict(dash='dash', color=layer_color)
                ))

            # 繪製所有階層的平均值 (虛線)
            if proceeded_EPA_df is not None and hasattr(proceeded_EPA_df, 'columns') and '階層' in proceeded_EPA_df.columns:
                full_score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in proceeded_EPA_df.columns else '教師評核EPA等級'
                all_layers = sorted(proceeded_EPA_df['階層'].unique().tolist())
                
                for layer in all_layers:
                    layer_df = proceeded_EPA_df[proceeded_EPA_df['階層'] == layer]
                    layer_values = []
                    # 確保使用與學生相同的 categories 順序
                    for category in categories:
                        layer_data = layer_df[layer_df['EPA評核項目'] == category]
                        if not layer_data.empty:
                            layer_avg = layer_data[full_score_column].mean()
                            layer_values.append(layer_avg)
                        else:
                            layer_values.append(0) # 如果該階層無此項目資料，補0
                    
                    # 檢查是否有計算出值
                    if any(v > 0 for v in layer_values): # 至少有一項大於0才繪製
                        layer_values_closed = layer_values + [layer_values[0]]
                        layer_color = layer_colors.get(layer, get_random_color(layer)) # 獲取顏色
                        fig.add_trace(go.Scatterpolar(
                            r=layer_values_closed,
                            theta=categories_closed,
                            fill='none', # 不填充
                            name=labels['layer'].format(layer), # 階層平均標籤
                            line=dict(dash='dash', color=layer_color) # 虛線及顏色
                        ))
            # 如果 proceeded_EPA_df 無效，顯示提示
            elif proceeded_EPA_df is None:
                fig.add_annotation(
                    text="無法取得全體資料，無法比較階層平均",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5
                )

            # 設定圖表樣式 - 使用組合標籤
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                showlegend=True,
                height=450,
                margin=dict(t=50, b=50, l=50, r=50),
                title=f"學生 {student_label} 的EPA評核雷達圖" # 使用組合標籤
            )
            
            return fig
        
        # === 完整模式 ===
        elif df is not None and plot_types is not None:
            # 確保 df 是有效的 DataFrame
            if df is None or df.empty:
                return default_fig
                
            # 定義顏色方案
            colors = {
                'C1': 'rgba(255, 0, 0, 0.3)',  # 半透明紅色
                'C2': 'rgba(0, 0, 255, 0.3)',  # 半透明藍色
                'PGY': 'rgba(230, 200, 255, 0.6)',  # 淡紫
                'teacher_avg': 'rgba(255, 200, 200, 0.6)',  # 淡紅
                'student_avg': 'rgba(200, 200, 255, 0.6)',  # 淡藍
                'individual': 'rgba(0, 0, 0, 0.8)'  # 黑色
            }
            
            # 準備圖表
            fig = go.Figure()
            
            categories = df['EPA評核項目'].unique()
            # 檢查項目數量，如不足則補充空白項目
            if len(categories) < 3:
                original_count = len(categories)
                categories = list(categories)  # 先轉換為列表以便添加新項目
                for i in range(3 - original_count):
                    categories.append(f"空白項目{i+1}")
                
            categories_closed = list(categories) + [categories[0]]
            
            # 檢查是否有轉換後的數值欄位
            teacher_score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in df.columns else '教師評核EPA等級'
            student_score_column = '學員自評EPA等級_數值' if '學員自評EPA等級_數值' in df.columns else '學員自評EPA等級'
            
            if plot_types is None:
                plot_types = ['layers']  # 預設顯示各階層平均
            
            # 繪製各階層平均
            if 'layers' in plot_types:
                layers = df['階層'].unique()
                for layer in layers:
                    layer_data = df[df['階層'] == layer]
                    avg_scores = []
                    
                    for category in categories:
                        avg = layer_data[layer_data['EPA評核項目'] == category][teacher_score_column].mean()
                        avg_scores.append(avg)
                    
                    avg_scores.append(avg_scores[0])  # 封閉雷達圖
                    
                    # 將所有0值替換為1
                    avg_scores = [max(1, score) for score in avg_scores]
                    
                    fig.add_trace(go.Scatterpolar(
                        r=avg_scores,
                        theta=categories_closed,
                        name=labels['layer'].format(layer),  # 使用自定義標籤
                        fill='toself',
                        fillcolor=colors.get(layer, 'rgba(200, 200, 200, 0.6)'),  # 使用預定義的半透明紅/藍色
                        line=dict(
                            color=colors.get(layer, 'rgba(200, 200, 200, 0.8)'),  # 線條使用相同但較深的顏色
                            width=2
                        )
                    ))
            
            # 繪製教師評核整體平均
            if 'teacher_avg' in plot_types:
                teacher_avg_scores = []
                for category in categories:
                    # 使用轉換後的數值欄位
                    avg = df[df['EPA評核項目'] == category][teacher_score_column].mean()
                    teacher_avg_scores.append(avg)
                
                teacher_avg_scores.append(teacher_avg_scores[0])
                
                # 將所有0值替換為1
                teacher_avg_scores = [max(1, score) for score in teacher_avg_scores]
                
                fig.add_trace(go.Scatterpolar(
                    r=teacher_avg_scores,
                    theta=categories_closed,
                    name=labels['teacher_avg'],  # 使用自定義標籤
                    fill='toself',
                    fillcolor=colors['teacher_avg'],
                    line=dict(color='rgba(255, 0, 0, 0.8)')
                ))
            
            # 繪製學生自評整體平均
            if 'student_avg' in plot_types:
                student_avg_scores = []
                for category in categories:
                    # 使用轉換後的數值欄位
                    avg = df[df['EPA評核項目'] == category][student_score_column].mean()
                    student_avg_scores.append(avg)
                
                student_avg_scores.append(student_avg_scores[0])
                
                # 將所有0值替換為1
                student_avg_scores = [max(1, score) for score in student_avg_scores]
                
                fig.add_trace(go.Scatterpolar(
                    r=student_avg_scores,
                    theta=categories_closed,
                    name=labels['student_avg'],  # 使用自定義標籤
                    fill='toself',
                    fillcolor=colors['student_avg'],
                    line=dict(color='rgba(0, 0, 255, 0.8)')
                ))
            
            # 繪製個別學生資料
            if 'individual' in plot_types and student_id:
                student_data = df[df['學員ID'] == student_id]
                if not student_data.empty:
                    individual_scores = []
                    for category in categories:
                        # 使用轉換後的數值欄位
                        score = student_data[student_data['EPA評核項目'] == category][teacher_score_column].iloc[0]
                        individual_scores.append(score)
                    
                    individual_scores.append(individual_scores[0])
                    
                    # 將所有0值替換為1
                    individual_scores = [max(1, score) for score in individual_scores]
                    
                    fig.add_trace(go.Scatterpolar(
                        r=individual_scores,
                        theta=categories_closed,
                        name=labels['individual'].format(student_id),  # 使用自定義標籤
                        fill='toself',
                        fillcolor=colors['individual'],
                        line=dict(color='rgba(0, 0, 0, 1)')
                    ))
            
            # 更新版面配置
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 5],  # EPA等級範圍為0-5
                        ticktext=['0', '1', '2', '3', '4', '5'],
                        tickvals=[0, 1, 2, 3, 4, 5]
                    )
                ),
                showlegend=True,
                title=title  # 使用自定義標題
            )
            
            return fig
        
        else:
            # 如果參數組合無效，返回預設圖
            return default_fig
            
    except Exception as e:
        # 捕獲所有異常，添加錯誤信息到圖表中
        # --- 新增：印出詳細錯誤 --- 
        print(f"\n--- ERROR in plot_radar_chart ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("Traceback:")
        traceback.print_exc() # 印出完整的追溯信息
        print("--- END ERROR ---\n")
        # --- 結束新增 ---
        
        default_fig.update_layout(
            title=f"繪製雷達圖時發生錯誤: {str(e)}",
            annotations=[dict(
                text="請檢查輸入資料和參數",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
        return default_fig

# ==================== 新的趨勢圖函數 (使用 Plotly Express) ====================
def plot_epa_trend_px(df, x_col, y_col, group_col=None, title="EPA 趨勢圖", 
                      sort_by_date=True, student_id=None, student_mode=False, full_df=None):
    """使用 Plotly Express 繪製 EPA 趨勢圖 (簡化版)
    
    Args:
        df (DataFrame): 包含EPA評核資料的DataFrame
        x_col (str): X軸的欄位名稱，通常是時間或梯次相關欄位
        y_col (str): Y軸的欄位名稱，通常是EPA等級相關欄位
        group_col (str, optional): 用於分組的欄位，如'EPA評核項目'
        title (str): 圖表標題
        sort_by_date (bool): 是否按日期排序X軸，預設為True
        student_id (str, optional): 學生學號，用於繪製學生趨勢圖
        student_mode (bool): 是否啟用學生模式，預設為False
        full_df (DataFrame, optional): 包含所有資料的完整DataFrame（用於計算階層整體平均）
        
    Returns:
        plotly.graph_objects.Figure: 趨勢圖物件
    """
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    import re # 需要 re 來輔助排序

    # 創建默認圖表物件
    default_fig = go.Figure()
    default_fig.update_layout(
        title="無法繪製趨勢圖：資料不足或格式錯誤",
        annotations=[dict(text="請檢查輸入資料是否符合要求", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)]
    )

    try:
        # 檢查輸入資料
        if df is None or df.empty:
            st.warning(f"[plot_epa_trend_px] 輸入 df 為空")
            return default_fig
            
        required_cols = [x_col, y_col]
        if group_col:
            required_cols.append(group_col)
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.warning(f"[plot_epa_trend_px] 缺少必要欄位: {missing_cols}")
            default_fig.update_layout(title=f"缺少必要欄位: {', '.join(missing_cols)}")
            return default_fig
            
        # 確保 y_col 是數值類型
        if not pd.api.types.is_numeric_dtype(df[y_col]):
             try:
                 df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                 if df[y_col].isnull().all(): # 如果轉換後全是 NaN
                      st.warning(f"[plot_epa_trend_px] Y軸欄位 '{y_col}' 無法轉換為數值或轉換後全為NaN")
                      return default_fig
             except Exception as convert_e:
                 st.warning(f"[plot_epa_trend_px] 轉換Y軸欄位 '{y_col}' 為數值時出錯: {convert_e}")
                 return default_fig

        # --- 複製 preprocess_and_sort_batches 函數 --- 
        # (直接複製過來避免依賴外部修改)
        def _preprocess_and_sort_batches(data_df, column):
            df_copy = data_df.copy()
            df_copy['_temp_date'] = None
            unique_batches = df_copy[column].dropna().unique()
            batch_to_date = {}
            for batch in unique_batches:
                try:
                    date_obj = pd.to_datetime(batch)
                    batch_to_date[batch] = date_obj
                except:
                    if isinstance(batch, str):
                        match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', batch)
                        if match:
                            year, month, day = match.groups()
                            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            try:
                                date_obj = pd.to_datetime(date_str)
                                batch_to_date[batch] = date_obj
                                continue
                            except: pass
                    batch_to_date[batch] = pd.Timestamp.max # 無法解析的排最後
            
            # 應用日期映射並處理NaN批次 (給它們一個非常早的日期以排在前面或忽略它們)
            # df_copy['_temp_date'] = df_copy[column].map(batch_to_date)
            # 更安全的方式避免 map 產生 NaN:
            for batch_val, date_val in batch_to_date.items():
                df_copy.loc[df_copy[column] == batch_val, '_temp_date'] = date_val
            # 對於原始就是 NaN 的批次，給予最早日期或保持 NaT
            df_copy['_temp_date'] = df_copy['_temp_date'].fillna(pd.Timestamp.min)

            df_copy = df_copy.sort_values('_temp_date')
            sorted_unique_batches = df_copy[column].unique()
            # 從排序後的結果中移除 None 或 NaN (如果存在)
            sorted_unique_batches = [b for b in sorted_unique_batches if pd.notna(b)]
            return sorted_unique_batches
        # --- 結束複製 --- 

        # 獲取排序後的梯次
        sorted_batches = _preprocess_and_sort_batches(df, x_col) if sort_by_date else df[x_col].dropna().unique()
        if not sorted_batches: # 如果沒有有效的梯次
            st.warning(f"[plot_epa_trend_px] 找不到有效的梯次 ({x_col}) 進行排序")
            return default_fig

        # === 預先定義 EPA 項目顏色 ===
        # 定義 EPA 項目的標準顏色 (十六進制)
        epa_colors = {
            '病歷紀錄': '#EF553B',  # 紅色系
            '當班處置': '#00CC96',  # 綠色系
            '住院接診': '#636EFA',  # 深藍色系
            '新增項目1': '#FFA15A', # 橙色系
            '新增項目2': '#AB63FA'  # 紫色系
        }
        
        # --- 新增：階層顏色定義 ---
        layer_colors = {
            'C1': '#9C27B0',  # 紫色
            'C2': '#03A9F4',  # 藍色
            'PGY': '#4CAF50', # 綠色
            'R': '#FFC107'    # 黃色
        }
        # --- 結束新增 ---
        
        # 處理學生模式
        if student_mode and student_id is not None:
            # 檢查學生資料
            if 'ID' not in df.columns and '學號' not in df.columns:
                st.warning(f"[plot_epa_trend_px] 缺少學生識別欄位")
                return default_fig
                
            # 確定學生ID欄位
            id_column = 'ID' if 'ID' in df.columns else '學號'
            
            # 篩選該學生資料
            student_df = df[df[id_column].astype(str) == str(student_id)]
            if student_df.empty:
                st.warning(f"[plot_epa_trend_px] 找不到學生 {student_id} 的資料")
                return default_fig
                
            # 獲取學生階層
            student_layer = None
            if '階層' in student_df.columns:
                student_layer = student_df['階層'].iloc[0] if not student_df.empty else None
                
            # 處理學生資料
            plot_df = student_df.dropna(subset=[y_col])
            if plot_df.empty:
                st.warning(f"[plot_epa_trend_px] 學生 {student_id} 沒有有效的評分資料")
                return default_fig
                
            # 獲取學生姓名
            student_name = ""
            name_col = '學員姓名' if '學員姓名' in student_df.columns else '姓名' if '姓名' in student_df.columns else None
            if name_col and not student_df.empty:
                student_name = student_df[name_col].iloc[0]
                
            # 調整標題
            if student_name:
                title = f"學生 {student_id} ({student_name}) 的EPA評核趨勢"
            else:
                title = f"學生 {student_id} 的EPA評核趨勢"
                
            # 執行學生資料的分組聚合
            agg_cols = [x_col]
            if group_col:
                agg_cols.append(group_col)
                
            try:
                agg_df = plot_df.groupby(agg_cols, observed=True)[y_col].mean().reset_index()
            except Exception as agg_e:
                st.error(f"[plot_epa_trend_px] 學生資料聚合時發生錯誤: {agg_e}")
                return default_fig
                
            if agg_df.empty:
                st.warning(f"[plot_epa_trend_px] 聚合後無學生資料可繪製")
                return default_fig
                
            # 準備繪製學生圖表
            px_args = {
                'data_frame': agg_df,
                'x': x_col,
                'y': y_col,
                'markers': True,
                'title': title
            }
            
            if group_col:
                px_args['color'] = group_col
                px_args['color_discrete_map'] = epa_colors
                
            # 繪製學生資料線條
            fig = px.line(**px_args)
            
            # === 繪製階層背景 (該學生所屬階層的平均CI) ===
            if student_layer and full_df is not None and '階層' in full_df.columns:
                # 篩選該階層的所有數據
                layer_df = full_df[full_df['階層'] == student_layer].dropna(subset=[y_col])
                
                if not layer_df.empty:
                    # 計算該階層在各梯次的統計數據
                    layer_stats_cols = [x_col]
                    if group_col:
                        layer_stats_cols.append(group_col)
                        
                    layer_stats = layer_df.groupby(layer_stats_cols, observed=True)[y_col].agg(['mean', 'count', 'std']).reset_index()
                    
                    # 獲取所有組合
                    if group_col:
                        all_groups = layer_df[group_col].unique()
                        layer_full_index = pd.MultiIndex.from_product([sorted_batches, all_groups], names=[x_col, group_col])
                        layer_stats_full = pd.DataFrame(index=layer_full_index).reset_index()
                        layer_stats_full = layer_stats_full.merge(layer_stats, on=layer_stats_cols, how='left')
                        layer_stats_full[['count', 'std']] = layer_stats_full[['count', 'std']].fillna(0)
                        layer_stats_full['mean'] = layer_stats_full.groupby(group_col)['mean'].ffill().bfill()
                        layer_stats_full['mean'] = layer_stats_full['mean'].fillna(0)
                        
                        # 為每個評核項目繪製階層背景CI
                        for group_name, group_data in layer_stats_full.groupby(group_col):
                            # 篩選 count >= 2 的數據計算CI
                            ci_data = group_data[group_data['count'] >= 2].copy()
                            
                            if not ci_data.empty:
                                try:
                                    # 計算CI
                                    degrees_freedom = ci_data['count'] - 1
                                    t_critical = stats.t.ppf(0.975, degrees_freedom)
                                    ci_data['sem'] = ci_data['std'] / np.sqrt(ci_data['count'])
                                    ci_width = t_critical * ci_data['sem']
                                    ci_data['lower'] = (ci_data['mean'] - ci_width).clip(0, 5)
                                    ci_data['upper'] = (ci_data['mean'] + ci_width).clip(0, 5)
                                    
                                    # 準備繪圖資料
                                    ci_data = ci_data.set_index(x_col).reindex(sorted_batches).reset_index()
                                    ci_data = ci_data.dropna(subset=['lower', 'upper'])
                                    
                                    if not ci_data.empty:
                                        # 獲取該項目顏色
                                        hex_color = epa_colors.get(group_name, '#808080')
                                        # 將十六進制顏色轉換為更淺的半透明RGBA (透明度提高)
                                        r = int(hex_color[1:3], 16)
                                        g = int(hex_color[3:5], 16)
                                        b = int(hex_color[5:7], 16)
                                        fill_color = f"rgba({r},{g},{b},0.1)" # 更淺的透明度
                                        
                                        # 添加階層CI區域
                                        fig.add_trace(go.Scatter(
                                            x=np.concatenate([ci_data[x_col], ci_data[x_col][::-1]]),
                                            y=np.concatenate([ci_data['upper'], ci_data['lower'][::-1]]),
                                            fill='toself',
                                            fillcolor=fill_color,
                                            line=dict(color='rgba(0,0,0,0)'),
                                            showlegend=False,
                                            name=f'{student_layer} 階層 {group_name} 95% CI',
                                            hoverinfo='skip'
                                        ))
                                except Exception as layer_ci_e:
                                    print(f"[ERROR] 計算階層 '{student_layer}' 項目 '{group_name}' 的CI時出錯: {layer_ci_e}")
                    else:
                        # 不分組的情況
                        layer_stats = layer_df.groupby([x_col], observed=True)[y_col].agg(['mean', 'count', 'std']).reset_index()
                        # 接下來的處理邏輯與分組情況類似
                        # ...
                    
                    # 將階層CI移到最底層
                    layer_ci_traces = [trace for trace in fig.data if '階層' in trace.name]
                    student_traces = [trace for trace in fig.data if '階層' not in trace.name]
                    fig.data = layer_ci_traces + student_traces
                    
                    # 添加階層標籤
                    layer_color = layer_colors.get(student_layer, '#808080')
                    layer_label = f"階層: {student_layer}"
                    fig.add_annotation(
                        x=0.02, y=0.98,
                        xref="paper", yref="paper",
                        text=layer_label,
                        showarrow=False,
                        font=dict(color=layer_color, size=12),
                        bgcolor="rgba(255,255,255,0.7)",
                        bordercolor=layer_color,
                        borderwidth=1,
                        borderpad=4,
                        align="left"
                    )
            # === 結束繪製階層背景 ===
            
            # 更新圖表佈局
            fig.update_layout(
                xaxis=dict(
                    title=x_col,
                    type='category',
                    categoryorder='array',
                    categoryarray=sorted_batches
                ),
                yaxis=dict(
                    title=f"平均 {y_col}",
                    range=[0, 5.1]
                ),
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
                )
            )
            
            return fig
        
        # 如果不是學生模式，則執行標準的分組聚合
        plot_df = df.dropna(subset=[y_col]).copy()
        agg_cols = [x_col]
        if group_col:
            agg_cols.append(group_col)
        
        try:
            agg_df = plot_df.groupby(agg_cols, observed=True)[y_col].mean().reset_index()
        except Exception as agg_e:
            st.error(f"[plot_epa_trend_px] 資料聚合時發生錯誤: {agg_e}")
            traceback.print_exc()
            return default_fig
            
        if agg_df.empty:
            st.warning("[plot_epa_trend_px] 聚合後無資料可繪製")
            return default_fig
        
        # 若有未定義的項目，補充顏色
        if group_col:
            all_groups = plot_df[group_col].unique()
            
            # 標準 Plotly 顏色序列
            default_colors = px.colors.qualitative.Plotly
            
            # 為未預定義的項目添加顏色
            undefined_groups = [g for g in all_groups if g not in epa_colors]
            for i, group in enumerate(undefined_groups):
                color_idx = i % len(default_colors)
                epa_colors[group] = default_colors[color_idx]
            
            # 顯示顏色映射
            for group, color in epa_colors.items():
                if group in all_groups:  # 只顯示實際存在的項目
                    print(f"[INFO] EPA項目 '{group}' 使用顏色: {color}")
            
            # 將 agg_df 中的組別轉換為類別型，以確保顏色映射一致
            if group_col in agg_df.columns:
                agg_df[group_col] = pd.Categorical(
                    agg_df[group_col], 
                    categories=list(epa_colors.keys()), 
                    ordered=True
                )

        # 準備 Plotly Express 參數
        px_args = {
            'data_frame': agg_df,
            'x': x_col,
            'y': y_col, # y 軸現在是聚合後的平均值
            'markers': True, # 顯示點
            'title': title
        }
        
        if group_col:
            px_args['color'] = group_col # 按評核項目分色
            px_args['color_discrete_map'] = epa_colors # 使用自定義顏色
        
        # 繪圖
        fig = px.line(**px_args)

        # --- 新增：計算並繪製 95% CI ---
        if group_col: # 僅在分組時計算 CI
            # 計算統計數據 (mean, count, std)
            stats_df = plot_df.groupby([x_col, group_col], observed=True)[y_col].agg(['mean', 'count', 'std']).reset_index()
            
            # 合併回 agg_df 以確保所有組合都在，並填充缺失統計值
            all_groups = plot_df[group_col].unique()
            full_index = pd.MultiIndex.from_product([sorted_batches, all_groups], names=[x_col, group_col])
            stats_full_df = pd.DataFrame(index=full_index).reset_index()
            stats_full_df = stats_full_df.merge(stats_df, on=[x_col, group_col], how='left')
            stats_full_df[['count', 'std']] = stats_full_df[['count', 'std']].fillna(0)
            # 重新計算 mean 以處理原始缺失值
            stats_full_df['mean'] = stats_full_df.groupby(group_col)['mean'].ffill().bfill()
            stats_full_df['mean'] = stats_full_df['mean'].fillna(stats_full_df.groupby(x_col)['mean'].transform('mean'))
            stats_full_df['mean'] = stats_full_df['mean'].fillna(0)
            
            # 每個 EPA 項目分別繪製 CI
            for group_name, group_data in stats_full_df.groupby(group_col):
                # 篩選 count >= 2 的數據計算 CI
                ci_data = group_data[group_data['count'] >= 2].copy()
                
                if not ci_data.empty:
                    try:
                        degrees_freedom = ci_data['count'] - 1
                        t_critical = stats.t.ppf(0.975, degrees_freedom)
                        
                        # 計算標準誤差和CI寬度
                        ci_data['sem'] = ci_data['std'] / np.sqrt(ci_data['count']) 
                        ci_width = t_critical * ci_data['sem']
                        
                        # 計算上下界並限制在 [0, 5] 範圍
                        ci_data['lower'] = (ci_data['mean'] - ci_width).clip(0, 5)
                        ci_data['upper'] = (ci_data['mean'] + ci_width).clip(0, 5)
                        
                        # 準備繪圖數據
                        ci_data = ci_data.set_index(x_col).reindex(sorted_batches).reset_index()
                        ci_data = ci_data.dropna(subset=['lower', 'upper'])
                        
                        if not ci_data.empty:
                            # 從預定義顏色中獲取該項目的顏色
                            hex_color = epa_colors.get(group_name, '#808080')  # 默認灰色
                            
                            # 將十六進制顏色轉換為半透明 RGBA
                            r = int(hex_color[1:3], 16)
                            g = int(hex_color[3:5], 16)
                            b = int(hex_color[5:7], 16)
                            fill_color = f"rgba({r},{g},{b},0.2)"
                            
                            print(f"[INFO] 繪製 '{group_name}' 的 CI: {hex_color} -> {fill_color}")
                            
                            # 添加 CI 區域
                            fig.add_trace(go.Scatter(
                                x=np.concatenate([ci_data[x_col], ci_data[x_col][::-1]]),
                                y=np.concatenate([ci_data['upper'], ci_data['lower'][::-1]]),
                                fill='toself',
                                fillcolor=fill_color,
                                line=dict(color='rgba(0,0,0,0)'), # 隱藏邊界線
                                showlegend=False,
                                name=f'{group_name} 95% CI',
                                hoverinfo='skip'
                            ))
                    except Exception as ci_e:
                        print(f"[ERROR] 計算 '{group_name}' 的 CI 時出錯: {ci_e}")
            
            # 將 CI 區域移到線條下方
            ci_traces = [trace for trace in fig.data if 'CI' in trace.name]
            line_traces = [trace for trace in fig.data if 'CI' not in trace.name]
            fig.data = ci_traces + line_traces
        # --- 結束 CI 繪製 ---

        # 更新圖表佈局
        fig.update_layout(
            xaxis=dict(
                title=x_col,
                type='category',
                categoryorder='array',
                categoryarray=sorted_batches # 強制按排序後的梯次顯示
            ),
            yaxis=dict(
                title=f"平均 {y_col}",
                range=[0, 5.1]  # EPA等級範圍
            ),
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
            )
        )

        return fig

    except Exception as e:
        # 捕獲所有異常
        st.error(f"[plot_epa_trend_px] 繪製趨勢圖時發生未預期錯誤: {e}")
        print(f"\n--- ERROR in plot_epa_trend_px ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        print("--- END ERROR ---")
        return default_fig
# ==================== 結束新的趨勢圖函數 ====================

# 為了向後相容，設定別名
plot_epa_radar = plot_radar_chart
plot_radar_charts = plot_radar_chart 