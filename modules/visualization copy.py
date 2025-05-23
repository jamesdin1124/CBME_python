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
                    title="EPA 雷達圖", standard_categories=None, full_df=None,
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
        full_df (DataFrame, optional): 包含所有資料的完整DataFrame（用於計算階層整體平均）
        labels (dict): 圖例標籤的自定義文字
        
    Returns:
        plotly.graph_objects.Figure: 雷達圖物件
    """
    import plotly.graph_objects as go
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
                if full_df is not None:
                    standard_categories = sorted(full_df['EPA評核項目'].unique().tolist())
                else:
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
                # else: # 如果學生沒有某項目的分數，可以選擇跳過或補0
                #     categories.append(category)
                #     student_values.append(0) 
            
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
            
            # 繪製所有階層的平均值 (虛線)
            if full_df is not None and '階層' in full_df.columns:
                full_score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in full_df.columns else '教師評核EPA等級'
                all_layers = sorted(full_df['階層'].unique().tolist())
                
                for layer in all_layers:
                    layer_df = full_df[full_df['階層'] == layer]
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
'''
def plot_epa_trend(df, x_col, y_col, group_col=None, by_layer=False, confidence_interval=True, title="EPA 趨勢圖", 
                  sort_by_date=True, student_id=None, student_mode=False, full_df=None):
    """繪製 EPA 趨勢圖
    
    Args:
        df (DataFrame): 包含EPA評核資料的DataFrame
        x_col (str): X軸的欄位名稱，通常是時間或梯次相關欄位
        y_col (str): Y軸的欄位名稱，通常是EPA等級相關欄位
        group_col (str, optional): 用於分組的欄位，如'EPA評核項目'
        by_layer (bool): 是否依據階層分別繪製趨勢圖，預設為False
        confidence_interval (bool): 是否顯示95%置信區間，預設為True
        title (str): 圖表標題
        sort_by_date (bool): 是否按日期排序X軸，預設為True
        student_id (str, optional): 學生學號，用於繪製學生趨勢圖
        student_mode (bool): 是否啟用學生模式，預設為False
        full_df (DataFrame, optional): 包含所有資料的完整DataFrame（用於計算階層整體平均）
        
    Returns:
        dict or fig: 如果by_layer為True，返回包含各階層圖表的字典；否則返回單一圖表
    """
    import plotly.graph_objects as go
    
    # 創建默認圖表物件，確保即使中途出錯，也能返回一個有效的圖表
    default_fig = go.Figure()
    default_fig.update_layout(
        title="無法繪製趨勢圖：資料不足或格式錯誤",
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
        # 檢查輸入資料
        if df is None or df.empty:
            return default_fig
            
        if x_col not in df.columns or y_col not in df.columns:
            default_fig.update_layout(
                title=f"缺少必要欄位: {x_col} 或 {y_col}",
                annotations=[dict(
                    text="請確認資料中包含所需欄位",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5
                )]
            )
            return default_fig
        
        # 定義顏色方案
        colors = {
            '當班處置': 'rgba(255, 0, 0, {})',  # 紅色
            '住院接診': 'rgba(0, 128, 0, {})',  # 綠色
            '病歷紀錄': 'rgba(0, 0, 255, {})',  # 藍色
        }
        
        # 預設顏色格式
        default_color = 'rgba({}, {}, {}, {})'
        
        # 生成隨機顏色的函數
        def get_random_color(seed_str, alpha=1.0):
            """根據字符串生成確定性隨機顏色"""
            import hashlib
            # 使用字符串的hash值作為隨機數種子
            hash_value = int(hashlib.md5(str(seed_str).encode()).hexdigest(), 16)
            r = (hash_value & 0xFF) % 200  # 限制亮度，避免太亮的顏色
            g = ((hash_value >> 8) & 0xFF) % 200
            b = ((hash_value >> 16) & 0xFF) % 200
            return f'rgba({r}, {g}, {b}, {alpha})'
        
        # 預處理並排序梯次
        def preprocess_and_sort_batches(data_df, column):
            """預處理梯次並按日期排序"""
            # 複製DataFrame以避免修改原始數據
            df_copy = data_df.copy()
            
            # 創建臨時日期列
            df_copy['_temp_date'] = None
            
            # 遍歷每個梯次值，嘗試轉換為日期
            unique_batches = df_copy[column].unique()
            batch_to_date = {}
            
            for batch in unique_batches:
                try:
                    # 嘗試直接解析為日期
                    date_obj = pd.to_datetime(batch)
                    batch_to_date[batch] = date_obj
                except:
                    # 嘗試提取日期部分
                    if isinstance(batch, str):
                        match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', batch)
                        if match:
                            year, month, day = match.groups()
                            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            try:
                                date_obj = pd.to_datetime(date_str)
                                batch_to_date[batch] = date_obj
                                continue
                            except:
                                pass
                    
                    # 如果無法解析，使用最大日期
                    batch_to_date[batch] = pd.Timestamp.max
            
            # 將日期對應填入臨時列
            for batch, date_obj in batch_to_date.items():
                df_copy.loc[df_copy[column] == batch, '_temp_date'] = date_obj
            
            # 按臨時日期列排序
            df_copy = df_copy.sort_values('_temp_date')
            
            # 獲取排序後的唯一梯次
            sorted_batches = df_copy[column].unique()
            
            # 刪除臨時列
            df_copy.drop('_temp_date', axis=1, inplace=True)
            
            return sorted_batches
        
        # 首先，獲取排序後的梯次 - 不論是否為學生模式
        sorted_batches = preprocess_and_sort_batches(df, x_col) if sort_by_date else df[x_col].unique()
        
        # === 學生趨勢圖模式 ===
        if student_mode and student_id is not None:
            fig = go.Figure()
            
            # 檢查資料是否有梯次欄位
            if x_col not in df.columns:
                fig.update_layout(
                    title=f"無法顯示學生 {student_id} 的趨勢圖：缺少 {x_col} 欄位",
                    annotations=[dict(
                        text="資料不足，無法繪製趨勢圖",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5
                    )]
                )
                return fig
            
            # 篩選出該學生的資料 (使用學號)
            student_df = df[df['學號'].astype(str) == str(student_id)]
            
            if student_df.empty:
                fig.update_layout(
                    title=f"無法顯示學生 {student_id} 的趨勢圖：找不到資料",
                    annotations=[dict(
                        text="找不到學生資料",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5
                    )]
                )
                return fig
            
            # 獲取學生數據的梯次（可能只是整體梯次的子集）
            student_batches = student_df[x_col].unique()
            # 按照完整排序重新排序學生的梯次
            student_sorted_batches = [batch for batch in sorted_batches if batch in student_batches]
            
            # 使用經過排序的學生梯次
            x_values = student_sorted_batches
            
            if len(x_values) <= 1:
                # 如果只有一個梯次，繪製簡單的點圖
                if group_col and group_col in student_df.columns:
                    # 按評核項目分組
                    groups = student_df[group_col].unique()
                    
                    for group in groups:
                        group_df = student_df[student_df[group_col] == group]
                        if group in colors:
                            line_color = colors[group].format(1.0)  # 完全不透明的線
                            fill_color = colors[group].format(0.2)  # 半透明的填充
                        else:
                            line_color = get_random_color(group, 1.0)
                            fill_color = get_random_color(group, 0.2)
                        
                        # --- 新增：在迴圈內部計算 means ---
                        group_df = student_df[student_df[group_col] == group] # 確保 group_df 在此處定義
                        means = [] # 為當前 group 初始化 means 列表
                        # 按排序後的學生梯次計算該 group 的平均分數
                        for batch in x_values: # x_values 是排序後的學生梯次
                            batch_data = group_df[group_df[x_col] == batch][y_col]
                            means.append(batch_data.mean() if not batch_data.empty else None)
                        # --- 結束新增 ---
                        
                        # --- 修改：將繪製學生線的程式碼移到迴圈內部（保持上次修改） ---
                        # 處理可能的None值 (學生線) - 確保在迴圈內定義
                        valid_indices = [i for i, m in enumerate(means) if m is not None]
                        valid_x_student = [x_values[i] for i in valid_indices]
                        valid_means_student = [means[i] for i in valid_indices]

                        # 繪製學生平均值線 (在 CI 之後，使其在最上方)
                        if valid_means_student:
                            fig.add_trace(go.Scatter(
                                x=valid_x_student,
                                y=valid_means_student,
                                mode='lines+markers',
                                name=f'{group}', # 圖例只顯示 EPA 項目名稱
                                line=dict(color=line_color, width=2),
                                uid=f"student_{student_id}_line_{group}"
                            ))
                    # --- 迴圈結束：for group in groups --- 

                else:
                    # 不分組，直接使用所有資料計算學生趨勢
                    means = []
                    
                    # 按排序後的梯次計算學生平均分數
                    for batch in x_values:
                        batch_data = student_df[student_df[x_col] == batch][y_col]
                        means.append(batch_data.mean() if not batch_data.empty else None)
                    
                    # 處理可能的None值 (學生線)
                    valid_indices = [i for i, m in enumerate(means) if m is not None]
                    valid_x_student = [x_values[i] for i in valid_indices]
                    valid_means_student = [means[i] for i in valid_indices]

                    # --- 新增：獲取學生最新階層 (無分組) --- 
                    latest_layer = None
                    if '階層' in student_df.columns and full_df is not None and '階層' in full_df.columns:
                        if not student_df.empty:
                            latest_layer = student_df['階層'].iloc[0]
                    # --- 結束新增 ---

                    # --- 新增：計算並繪製階層 CI (無分組) --- 
                    if latest_layer and confidence_interval:
                        layer_df = full_df[full_df['階層'] == latest_layer]
                        
                        layer_means = []
                        layer_counts = []
                        layer_stds = []
                        
                        for batch in sorted_batches:
                            batch_layer_data = layer_df[layer_df[x_col] == batch][y_col]
                            if not batch_layer_data.empty:
                                layer_means.append(batch_layer_data.mean())
                                layer_counts.append(len(batch_layer_data))
                                layer_stds.append(batch_layer_data.std())
                            else:
                                layer_means.append(None)
                                layer_counts.append(0)
                                layer_stds.append(0)
                                
                        valid_layer_indices = [i for i, m in enumerate(layer_means) if m is not None]
                        valid_x_layer = [sorted_batches[i] for i in valid_layer_indices]
                        valid_means_layer = [layer_means[i] for i in valid_layer_indices]
                        valid_counts_layer = [layer_counts[i] for i in valid_layer_indices]
                        valid_stds_layer = [layer_stds[i] for i in valid_layer_indices]
                        
                        if valid_means_layer:
                            agg_layer_data = pd.DataFrame({
                                x_col: valid_x_layer,
                                'mean': valid_means_layer,
                                'count': valid_counts_layer,
                                'std': valid_stds_layer
                            })
                            
                            ci_layer_data = agg_layer_data[agg_layer_data['count'] >= 2].copy()
                            
                            if not ci_layer_data.empty:
                                ci_layer_data['std'] = ci_layer_data['std'].fillna(0)
                                try:
                                    degrees_freedom = ci_layer_data['count'] - 1
                                    valid_ci_indices_layer = degrees_freedom > 0
                                    if valid_ci_indices_layer.any():
                                        degrees_freedom = degrees_freedom[valid_ci_indices_layer]
                                        ci_data_valid_df_layer = ci_layer_data[valid_ci_indices_layer]
                                        
                                        t_critical = stats.t.ppf(0.975, degrees_freedom)
                                        sqrt_counts = np.sqrt(ci_data_valid_df_layer['count'])
                                        ci_width = np.where(ci_data_valid_df_layer['std'] == 0, 0, 
                                                            t_critical * ci_data_valid_df_layer['std'] / sqrt_counts)
                                        lower_bound = ci_data_valid_df_layer['mean'] - ci_width
                                        upper_bound = ci_data_valid_df_layer['mean'] + ci_width
                                        lower_bound = np.maximum(0, lower_bound)
                                        upper_bound = np.minimum(5, upper_bound)
                                        
                                        # --- 修改：使用分組顏色繪製階層 CI ---
                                        # line_color 在循環開頭已定義
                                        ci_fill_color = 'rgba(200, 200, 200, 0.2)' # 預設灰色
                                        try:
                                            # 處理十六進制顏色代碼 (#RRGGBB 或 #RRGGBBAA)
                                            if line_color.startswith('#'):
                                                # 提取RGB值
                                                if len(line_color) >= 7:  # #RRGGBB 或 #RRGGBBAA
                                                    r = int(line_color[1:3], 16)
                                                    g = int(line_color[3:5], 16)
                                                    b = int(line_color[5:7], 16)
                                                    ci_fill_color = f"rgba({r}, {g}, {b}, 0.2)"
                                                    print(f"[DEBUG plot_epa_trend_px] 已從十六進位轉換: '{line_color}' -> {ci_fill_color}")
                                            else:
                                                # 使用 plotly 的顏色轉換工具處理非十六進位格式
                                                from plotly.colors import convert_colors_to_same_type
                                                
                                                # 先嘗試轉換為 rgb
                                                rgb_color = convert_colors_to_same_type([line_color], colortype='rgb')[0][0]
                                                if rgb_color.startswith('rgb'):
                                                    base_color = rgb_color.split(',')
                                                    r = base_color[0].split('(')[1].strip()
                                                    g = base_color[1].strip()
                                                    b = base_color[2].split(')')[0].strip()
                                                    ci_fill_color = f"rgba({r}, {g}, {b}, 0.2)"
                                                    print(f"[DEBUG plot_epa_trend_px] 已從RGB轉換: '{line_color}' -> {ci_fill_color}")
                                            
                                            print(f"[DEBUG plot_epa_trend_px] Group: '{line_color}', Line Color: {line_color}, Fill Color: {ci_fill_color}") # 偵錯輸出
                                            
                                        except Exception as color_e:
                                            print(f"[WARN plot_epa_trend_px] 無法轉換顏色 '{line_color}' 為 RGBA: {color_e}. 使用預設灰色 CI。")
                                            # 解析失敗則維持預設灰色
                                            
                                        # 創建一個包含單一梯次的DataFrame用於繪製CI
                                        ci_data_valid_df_layer = pd.DataFrame({
                                            x_col: [batch],
                                            'mean': [batch_layer_mean],
                                            'lower': [lower_bound],
                                            'upper': [upper_bound]
                                        })
                                        
                                        fig.add_trace(go.Scatter(
                                            x=np.concatenate([ci_data_valid_df_layer[x_col], ci_data_valid_df_layer[x_col][::-1]]),
                                            y=np.concatenate([ci_data_valid_df_layer['upper'], ci_data_valid_df_layer['lower'][::-1]]),
                                            fill='toself',
                                            fillcolor=ci_fill_color, # 使用解析出的帶 alpha 的顏色
                                            line=dict(color='rgba(0,0,0,0)'),
                                            showlegend=False,
                                            name=f'階層 {layer} {group} 95% CI',
                                            uid=f"student_{student_id}_line_{group}"
                                        ))
                                        # --- 結束修改 ---
                                except ValueError as e: 
                                    print(f"無法計算階層 {layer} 組 {group} 的 CI：{e}")
                        # --- 結束計算並繪製階層 CI (無分組) ---
                        
                        # 繪製學生平均值線 (在 CI 之後，使其在最上方)
                        if valid_means_student:
                            fig.add_trace(go.Scatter(
                                x=valid_x_student,
                                y=valid_means_student,
                                mode='lines+markers',
                                name=f'{group if "group" in locals() else ""}', # 圖例只顯示 EPA 項目名稱
                                line=dict(color=line_color if "line_color" in locals() else "rgba(0, 0, 255, 1.0)", width=2),
                                uid=f"student_{student_id}_trend"
                            ))

            else:
                # === 開始 非學生模式 / 階層趨勢圖模式 ===
                # 單一圖表繪製邏輯 (保持不變)
                fig = go.Figure()
                
                # 使用排序後的全局梯次
                x_values = sorted_batches
                
                if group_col:
                    # 獲取所有分組值
                    groups = df[group_col].unique()
                    
                    for group in groups:
                        # 選擇顏色 - 如果在預定義色表中則使用，否則生成隨機顏色
                        if group in colors:
                            line_color = colors[group].format(1.0)  # 完全不透明的線
                            fill_color = colors[group].format(0.2)  # 半透明的填充
                        else:
                            line_color = get_random_color(group, 1.0)
                            fill_color = get_random_color(group, 0.2)
                        
                        group_df = df[df[group_col] == group]
                        
                        # 初始化聚合數據結果
                        means = []
                        counts = []
                        stds = []
                        
                        # 按排序後的梯次計算統計值
                        for batch in x_values:
                            batch_data = group_df[group_df[x_col] == batch][y_col]
                            if not batch_data.empty:
                                means.append(batch_data.mean())
                                counts.append(len(batch_data))
                                stds.append(batch_data.std())
                            else:
                                # 如果沒有數據，使用 None
                                means.append(None)
                                counts.append(0)
                                stds.append(0)
                        
                        # 過濾掉沒有數據的梯次
                        valid_indices = [i for i, m in enumerate(means) if m is not None]
                        valid_x = [x_values[i] for i in valid_indices]
                        valid_means = [means[i] for i in valid_indices]
                        valid_counts = [counts[i] for i in valid_indices]
                        valid_stds = [stds[i] for i in valid_indices]
                        
                        # 只有在有效數據存在時才繪製
                        if valid_means:
                            # --- DEBUGGING --- 
                            print("--- DEBUG: Non-Student, Grouped --- ")
                            print(f"Group: {group}")
                            print(f"Length of valid_x: {len(valid_x)}")
                            print(f"Length of valid_means: {len(valid_means)}")
                            print(f"Length of valid_counts: {len(valid_counts)}")
                            print(f"Length of valid_stds: {len(valid_stds)}")
                            # --- END DEBUGGING ---
                            
                            # 創建聚合數據框
                            agg_data = pd.DataFrame({
                                x_col: valid_x,
                                'mean': valid_means,
                                'count': valid_counts,
                                'std': valid_stds
                            })
                            
                            # 計算95%置信區間
                            if confidence_interval and len(agg_data) > 1:
                                # 只對 count >= 2 的數據計算 CI
                                ci_data = agg_data[agg_data['count'] >= 2].copy()
                                
                                # --- DEBUGGING --- 
                                print(f"--- DEBUG CI for Group: '{group}' ---")
                                print(f"Shape of agg_data: {agg_data.shape}")
                                print(f"Shape of ci_data (count>=2): {ci_data.shape}")
                                print(f"Is ci_data empty? {ci_data.empty}")
                                # --- END DEBUGGING ---

                                if not ci_data.empty:
                                    # 處理可能的NaN std (雖然 count>=2 時不太可能)
                                    ci_data['std'] = ci_data['std'].fillna(0)
                                    
                                    # 使用t分布計算95%置信區間 (df = count - 1 >= 1)
                                    try:
                                        # 確保自由度 > 0
                                        degrees_freedom = ci_data['count'] - 1
                                        valid_ci_indices = degrees_freedom > 0
                                        if valid_ci_indices.any():
                                            degrees_freedom = degrees_freedom[valid_ci_indices]
                                            ci_data_valid_df = ci_data[valid_ci_indices]

                                            t_critical = stats.t.ppf(0.975, degrees_freedom)
                                            
                                            # 防止除以零錯誤
                                            sqrt_counts = np.sqrt(ci_data_valid_df['count'])
                                            
                                            # 計算 CI 寬度, 處理 std=0 的情況
                                            ci_width = np.where(ci_data_valid_df['std'] == 0, 0, 
                                                                t_critical * ci_data_valid_df['std'] / sqrt_counts)
                                            
                                            lower_bound = ci_data_valid_df['mean'] - ci_width
                                            upper_bound = ci_data_valid_df['mean'] + ci_width
                                            
                                            # 確保邊界在有效範圍內
                                            lower_bound = np.maximum(0, lower_bound)
                                            upper_bound = np.minimum(5, upper_bound)
                                            
                                    except ValueError as e:
                                        print(f"無法計算階層 {latest_layer} 組 {group} 的 CI：{e}")
                            
                            # 添加平均值線 (使用原始 agg_data)
                            fig.add_trace(go.Scatter(
                                x=agg_data[x_col],
                                y=agg_data['mean'],
                                mode='lines+markers',
                                name=f'{group}',
                                line=dict(color=line_color, width=2),
                                uid=f"group_{group}_line"
                            ))
                else:
                    # 沒有分組時，繪製單一趨勢線
                    # 初始化聚合數據結果
                    means = []
                
                # 按排序後的梯次計算統計值
                for batch in x_values:
                    batch_data = df[df[x_col] == batch][y_col]
                    if not batch_data.empty:
                        means.append(batch_data.mean())
                        counts.append(len(batch_data))
                        stds.append(batch_data.std())
                    else:
                        # 如果沒有數據，使用 None
                        means.append(None)
                        counts.append(0)
                        stds.append(0)
                
                # 過濾掉沒有數據的梯次
                valid_indices = [i for i, m in enumerate(means) if m is not None]
                valid_x = [x_values[i] for i in valid_indices]
                valid_means = [means[i] for i in valid_indices]
                valid_counts = [counts[i] for i in valid_indices]
                valid_stds = [stds[i] for i in valid_indices]
                
                # 只有在有效數據存在時才繪製
                if valid_means:
                    # --- DEBUGGING --- 
                    print("--- DEBUG: Non-Student, No Group --- ")
                    print(f"Length of valid_x: {len(valid_x)}")
                    print(f"Length of valid_means: {len(valid_means)}")
                    print(f"Length of valid_counts: {len(valid_counts)}")
                    print(f"Length of valid_stds: {len(valid_stds)}")
                    # --- END DEBUGGING ---
                    
                    # 創建聚合數據框
                    agg_data = pd.DataFrame({
                        x_col: valid_x,
                        'mean': valid_means,
                        'count': valid_counts,
                        'std': valid_stds
                    })
                    
                    line_color = "rgba(31, 119, 180, 1)"  # 標準藍色
                    fill_color = "rgba(31, 119, 180, 0.2)"  # 半透明藍色
                    
                    # 計算95%置信區間
                    if confidence_interval and len(agg_data) > 1:
                        # 只對 count >= 2 的數據計算 CI
                        ci_data = agg_data[agg_data['count'] >= 2].copy()
                        
                        # --- DEBUGGING --- 
                        print(f"--- DEBUG CI (No Group) ---")
                        print(f"Shape of agg_data: {agg_data.shape}")
                        print(f"Shape of ci_data (count>=2): {ci_data.shape}")
                        print(f"Is ci_data empty? {ci_data.empty}")
                        # --- END DEBUGGING ---

                        if not ci_data.empty:
                            ci_data['std'] = ci_data['std'].fillna(0)
                            try:
                                # 確保自由度 > 0
                                degrees_freedom = ci_data['count'] - 1
                                valid_ci_indices = degrees_freedom > 0
                                if valid_ci_indices.any():
                                    degrees_freedom = degrees_freedom[valid_ci_indices]
                                    ci_data_valid_df = ci_data[valid_ci_indices]

                                    t_critical = stats.t.ppf(0.975, degrees_freedom)
                                    sqrt_counts = np.sqrt(ci_data_valid_df['count'])
                                    ci_width = np.where(ci_data_valid_df['std'] == 0, 0, 
                                                        t_critical * ci_data_valid_df['std'] / sqrt_counts)
                                    lower_bound = ci_data_valid_df['mean'] - ci_width
                                    upper_bound = ci_data_valid_df['mean'] + ci_width
                                    lower_bound = np.maximum(0, lower_bound)
                                    upper_bound = np.minimum(5, upper_bound)
                                    
                                    # --- 修改：使用分組顏色繪製階層 CI ---
                                    # line_color 在循環開頭已定義
                                    ci_fill_color = 'rgba(200, 200, 200, 0.2)' # 預設灰色
                                    try:
                                        # 處理十六進制顏色代碼 (#RRGGBB 或 #RRGGBBAA)
                                        if line_color.startswith('#'):
                                            # 提取RGB值
                                            if len(line_color) >= 7:  # #RRGGBB 或 #RRGGBBAA
                                                r = int(line_color[1:3], 16)
                                                g = int(line_color[3:5], 16)
                                                b = int(line_color[5:7], 16)
                                                ci_fill_color = f"rgba({r}, {g}, {b}, 0.2)"
                                                print(f"[DEBUG plot_epa_trend_px] 已從十六進位轉換: '{line_color}' -> {ci_fill_color}")
                                        else:
                                            # 使用 plotly 的顏色轉換工具處理非十六進位格式
                                            from plotly.colors import convert_colors_to_same_type
                                            
                                            # 先嘗試轉換為 rgb
                                            rgb_color = convert_colors_to_same_type([line_color], colortype='rgb')[0][0]
                                            if rgb_color.startswith('rgb'):
                                                base_color = rgb_color.split(',')
                                                r = base_color[0].split('(')[1].strip()
                                                g = base_color[1].strip()
                                                b = base_color[2].split(')')[0].strip()
                                                ci_fill_color = f"rgba({r}, {g}, {b}, 0.2)"
                                                print(f"[DEBUG plot_epa_trend_px] 已從RGB轉換: '{line_color}' -> {ci_fill_color}")
                                        
                                        print(f"[DEBUG plot_epa_trend_px] Group: '{line_color}', Line Color: {line_color}, Fill Color: {ci_fill_color}") # 偵錯輸出
                                        
                                    except Exception as color_e:
                                        print(f"[WARN plot_epa_trend_px] 無法轉換顏色 '{line_color}' 為 RGBA: {color_e}. 使用預設灰色 CI。")
                                        # 解析失敗則維持預設灰色
                                        
                                    fig.add_trace(go.Scatter(
                                        x=np.concatenate([ci_data_valid_df[x_col], ci_data_valid_df[x_col][::-1]]),
                                        y=np.concatenate([upper_bound, lower_bound[::-1]]),
                                        fill='toself',
                                        fillcolor=ci_fill_color,
                                        line=dict(color='rgba(0,0,0,0)'), # 不顯示邊界線
                                        showlegend=False,
                                        name=f'階層 {latest_layer if "latest_layer" in locals() else ""} {group if "group" in locals() else ""} 95% CI',
                                        uid=f"group_{group}_line"
                                    ))
                                    # --- 結束修改 ---
                            except ValueError as e:
                                print(f"無法計算整體的 CI：{e}")
                                # 可以選擇添加日誌或錯誤處理
                            
                            # 添加平均值線 (使用原始 agg_data)
                            fig.add_trace(go.Scatter(
                                x=agg_data[x_col],
                                y=agg_data['mean'],
                                mode='lines+markers',
                                name=f'{group}',
                                line=dict(color=line_color, width=2),
                                uid=f"group_{group}_line"
                            ))
                            fig.add_trace(go.Scatter(
                                x=agg_data[x_col],
                                y=agg_data['mean'],
                                mode='lines+markers',
                                name=y_col, # 圖例顯示 Y 軸名稱
                                line=dict(color=line_color, width=2),
                                uid=f"overall_trend_line"
                            ))
            
            # 設定圖表樣式 (非學生模式標題)
            fig.update_layout(
                title=title, # 使用傳入的標題
                xaxis=dict(
                    title=x_col,
                    type='category',
                    categoryorder='array',
                    categoryarray=x_values # 使用全局排序的 x_values
                ),
                yaxis=dict(
                    title=y_col,
                    range=[0, 5.1]  # EPA等級範圍為0-5
                ),
                showlegend=True,
                legend=dict(
                    orientation="h",  # 水平圖例
                    yanchor="bottom",
                    y=1.02,  # 放在圖表上方
                    xanchor="center",
                    x=0.5
                )
            )
            
            return fig # 返回非學生模式的圖表
            # === 結束 非學生模式 / 階層趨勢圖模式 ===

        # 返回之前先檢查fig是否已定義
        if 'fig' not in locals() or fig is None:
            if by_layer:
                # 如果應該按層顯示但沒有成功創建圖表，返回默認圖
                return default_fig
            else:
                return default_fig
                
        return fig
            
    except Exception as e:
        # 捕獲所有異常，添加錯誤信息到圖表中
        # --- 新增：印出詳細錯誤 --- 
        print(f"\n--- ERROR in plot_epa_trend ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("Traceback:")
        traceback.print_exc() # 印出完整的追溯信息
        print("--- END ERROR ---")
        return default_fig

def plot_epa_distribution(df, column, title="EPA 分布圖"):
    """繪製 EPA 分布圖"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 繪製分布圖
    sns.histplot(data=df, x=column, bins=20, ax=ax)
    
    # 設定圖表屬性
    ax.set_title(title)
    ax.set_xlabel(column)
    ax.set_ylabel("頻率")
    
    return fig


def plot_epa_boxplot(df, x_col, y_col, title="EPA 箱型圖"):
    """繪製 EPA 箱型圖"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 繪製箱型圖
    sns.boxplot(data=df, x=x_col, y=y_col, ax=ax)
    
    # 設定圖表屬性
    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    
    # 旋轉 x 軸標籤
    plt.xticks(rotation=45)
    
    return fig

def display_epa_stats(df, group_col, value_col):
    """顯示 EPA 統計資訊"""
    stats = df.groupby(group_col)[value_col].agg([
        ('平均值', 'mean'),
        ('中位數', 'median'),
        ('標準差', 'std'),
        ('最小值', 'min'),
        ('最大值', 'max'),
        ('評核次數', 'count')
    ]).round(2)
    
    return stats
'''
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
        student_id (str, optional): 學生學號，用於繪製學生趨勢圖 (目前主要用於標題)
        student_mode (bool): 是否啟用學生模式，預設為False (目前主要用於標題)
        full_df (DataFrame, optional): (暫未使用) 包含所有資料的完整DataFrame
        
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

        # 資料聚合
        agg_cols = [x_col]
        if group_col:
            agg_cols.append(group_col)
        
        # 分組計算前過濾掉 y_col 的 NaN 值
        plot_df = df.dropna(subset=[y_col]).copy()
        if plot_df.empty:
            st.warning(f"[plot_epa_trend_px] 過濾 Y 軸 NaN 後無資料可繪製")
            return default_fig
            
        # 執行分組聚合
        try:
            agg_df = plot_df.groupby(agg_cols, observed=True)[y_col].mean().reset_index()
        except Exception as agg_e:
            st.error(f"[plot_epa_trend_px] 資料聚合時發生錯誤: {agg_e}")
            traceback.print_exc()
            return default_fig
            
        if agg_df.empty:
            st.warning("[plot_epa_trend_px] 聚合後無資料可繪製")
            return default_fig

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

        # 繪圖
        fig = px.line(**px_args)

        # --- 新增：計算並繪製 95% CI ---
        if group_col: # 僅在分組時計算 CI
            # 計算統計數據 (mean, count, std)
            stats_df = plot_df.groupby([x_col, group_col], observed=True)[y_col].agg(['mean', 'count', 'std']).reset_index()
            
            # 合併回 agg_df 以確保所有組合都在，並填充缺失統計值
            # 需要確保 agg_df 包含所有 x_col 和 group_col 的組合
            # 創建包含所有梯次和分組的完整索引
            all_groups = plot_df[group_col].unique()
            full_index = pd.MultiIndex.from_product([sorted_batches, all_groups], names=[x_col, group_col])
            stats_full_df = pd.DataFrame(index=full_index).reset_index()
            stats_full_df = stats_full_df.merge(stats_df, on=[x_col, group_col], how='left')
            stats_full_df[['count', 'std']] = stats_full_df[['count', 'std']].fillna(0)
            # 重新計算 mean 以處理原始缺失值（fillna(0)會影響）
            stats_full_df['mean'] = stats_full_df.groupby(group_col)['mean'].ffill().bfill()
            stats_full_df['mean'] = stats_full_df['mean'].fillna(stats_full_df.groupby(x_col)['mean'].transform('mean')) # 若還是有NaN，用梯次平均填充
            stats_full_df['mean'] = stats_full_df['mean'].fillna(0) # 最後手段填0

            # 從 Plotly Express 圖中獲取顏色映射
            color_map = {trace.name: trace.line.color for trace in fig.data}
            
            for group_name, group_data in stats_full_df.groupby(group_col):
                # 篩選 count >= 2 的數據計算 CI
                ci_data = group_data[group_data['count'] >= 2].copy()
                
                if not ci_data.empty:
                    try:
                        degrees_freedom = ci_data['count'] - 1
                        t_critical = stats.t.ppf(0.975, degrees_freedom)
                        
                        # 計算標準誤差 SEM
                        ci_data['sem'] = ci_data['std'] / np.sqrt(ci_data['count'])
                        
                        # 計算 CI 寬度
                        ci_width = t_critical * ci_data['sem']
                        
                        # 計算上下界
                        ci_data['lower'] = ci_data['mean'] - ci_width
                        ci_data['upper'] = ci_data['mean'] + ci_width
                        
                        # 限制在 [0, 5] 範圍
                        ci_data['lower'] = ci_data['lower'].clip(0, 5)
                        ci_data['upper'] = ci_data['upper'].clip(0, 5)
                        
                        # 準備繪圖數據 (確保按梯次排序)
                        ci_data = ci_data.set_index(x_col).reindex(sorted_batches).reset_index()
                        ci_data = ci_data.dropna(subset=['lower', 'upper']) # 移除計算 CI 失敗的行
                        
                        if not ci_data.empty:
                            # --- 更新：更可靠地處理顏色轉換 ---
                            line_color_str = color_map.get(group_name, 'rgb(128, 128, 128)') # 默認灰色
                            fill_color = 'rgba(128, 128, 128, 0.2)' # 預設半透明灰色
                            try:
                                # 處理十六進制顏色代碼 (#RRGGBB 或 #RRGGBBAA)
                                if line_color_str.startswith('#'):
                                    # 提取RGB值
                                    if len(line_color_str) >= 7:  # #RRGGBB 或 #RRGGBBAA
                                        r = int(line_color_str[1:3], 16)
                                        g = int(line_color_str[3:5], 16)
                                        b = int(line_color_str[5:7], 16)
                                        fill_color = f"rgba({r}, {g}, {b}, 0.2)"
                                        print(f"[DEBUG plot_epa_trend_px] 已從十六進位轉換: '{line_color_str}' -> {fill_color}")
                                else:
                                    # 使用 plotly 的顏色轉換工具處理非十六進位格式
                                    from plotly.colors import convert_colors_to_same_type
                                    
                                    # 先嘗試轉換為 rgb
                                    rgb_color = convert_colors_to_same_type([line_color_str], colortype='rgb')[0][0]
                                    if rgb_color.startswith('rgb'):
                                        base_color = rgb_color.split(',')
                                        r = base_color[0].split('(')[1].strip()
                                        g = base_color[1].strip()
                                        b = base_color[2].split(')')[0].strip()
                                        fill_color = f"rgba({r}, {g}, {b}, 0.2)"
                                        print(f"[DEBUG plot_epa_trend_px] 已從RGB轉換: '{line_color_str}' -> {fill_color}")
                                
                                print(f"[DEBUG plot_epa_trend_px] Group: '{line_color_str}', Line Color: {line_color_str}, Fill Color: {fill_color}") # 偵錯輸出
                                    
                            except Exception as color_e:
                                print(f"[WARN plot_epa_trend_px] 無法轉換顏色 '{line_color_str}' 為 RGBA: {color_e}. 使用預設灰色 CI。")
                                # 解析失敗則維持預設灰色
                                
                            fig.add_trace(go.Scatter(
                                x=np.concatenate([ci_data[x_col], ci_data[x_col][::-1]]),
                                y=np.concatenate([ci_data['upper'], ci_data['lower'][::-1]]),
                                fill='toself',
                                fillcolor=fill_color,
                                line=dict(color='rgba(0,0,0,0)'), # 不顯示邊界線
                                showlegend=False,
                                name=f'{group_name} 95% CI',
                                hoverinfo='skip' # 不顯示 hover 信息
                            ))
                    except Exception as ci_e:
                        print(f"[plot_epa_trend_px] 計算組 '{group_name}' 的 CI 時出錯: {ci_e}")
                        # traceback.print_exc() # 可選：印出詳細追溯
                        
            # 將 CI 圖層移到線圖層下方
            fig.data = fig.data[::-1]
        # --- 結束新增 CI --- 

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

        # 如果是學生模式，可以考慮添加階層平均線 (使用 go.Scatter)
        # (暫時省略以求簡潔)

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