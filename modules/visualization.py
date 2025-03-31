import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
import re



def plot_radar_chart(df=None, plot_types=None, student_id=None, categories=None, values=None, 
                    title="EPA 雷達圖", student_name=None, standard_categories=None, full_df=None,
                    labels={
                        'layer': '階層 {}',  # {} 會被替換成實際的層級
                        'teacher_avg': '教師評核平均',
                        'student_avg': '學員自評平均',
                        'individual': '學員 {}'  # {} 會被替換成實際的學員ID
                    }):
    """繪製 EPA 雷達圖，支援多種模式包括學生個人雷達圖
    
    Args:
        df (DataFrame, optional): 包含EPA評核資料的DataFrame
        plot_types (list, optional): 要顯示的圖表類型列表
        student_id (str, optional): 學生ID，用於舊版API
        student_name (str, optional): 學生姓名，用於新版學生雷達圖
        categories (list, optional): 雷達圖的類別列表
        values (list, optional): 對應類別的數值列表
        title (str): 圖表標題
        standard_categories (list, optional): 標準的EPA評核項目順序列表
        full_df (DataFrame, optional): 包含所有資料的完整DataFrame（用於計算階層整體平均）
        labels (dict): 圖例標籤的自定義文字
        
    Returns:
        plotly.graph_objects.Figure: 雷達圖物件
    """
    import plotly.graph_objects as go
    
    # 檢測使用模式：
    # 1. 簡單模式：直接提供categories和values
    # 2. 學生模式：提供student_name和df
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
    elif student_name is not None and df is not None:
        # 篩選該學生的資料
        student_df = df[df['學員姓名'] == student_name]
        
        if student_df.empty:
            # 建立一個空的雷達圖，並添加警告訊息
            fig = go.Figure()
            fig.update_layout(
                title=f"找不到學生 {student_name} 的雷達圖資料",
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
        
        # 檢查是否有轉換後的數值欄位
        score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in student_df.columns else '教師評核EPA等級'
        
        # 對每個標準評核項目，獲取該學生的評分（若存在）
        for category in standard_categories:
            category_data = student_df[student_df['EPA評核項目'] == category]
            if not category_data.empty:
                # 使用該項目的平均分數 - 使用轉換後的數值欄位
                avg_score = category_data[score_column].mean()
                categories.append(category)
                values.append(avg_score)
        
        # 如果沒有足夠的資料，建立空圖
        if len(categories) < 2:
            fig = go.Figure()
            fig.update_layout(
                title=f"學生 {student_name} 的評核項目不足，無法繪製雷達圖",
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
            
            # 檢查完整資料集中是否有轉換後的數值欄位
            full_score_column = '教師評核EPA等級_數值' if full_df is not None and '教師評核EPA等級_數值' in full_df.columns else '教師評核EPA等級'
            
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
                    # 使用轉換後的數值欄位
                    layer_avg = layer_data[full_score_column].mean()
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
            margin=dict(t=20, b=20, l=20, r=20),
            title=title if title != "EPA 雷達圖" else f"學生 {student_name} 的EPA評核雷達圖"
        )
        
        return fig
    
    # === 完整模式（原有的plot_radar_chart邏輯） ===
    else:
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
        
        if df is None:
            # 如果沒有提供數據，返回空圖
            fig.update_layout(
                title="無可用資料繪製雷達圖",
                annotations=[
                    dict(
                        text="請提供資料",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5
                    )
                ]
            )
            return fig
        
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

def plot_epa_trend(df, x_col, y_col, group_col=None, by_layer=False, confidence_interval=True, title="EPA 趨勢圖", 
                  sort_by_date=True, student_name=None, student_mode=False, full_df=None):
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
        student_name (str, optional): 學生姓名，用於繪製學生趨勢圖
        student_mode (bool): 是否啟用學生模式，預設為False
        full_df (DataFrame, optional): 包含所有資料的完整DataFrame（用於計算階層整體平均）
        
    Returns:
        dict or fig: 如果by_layer為True，返回包含各階層圖表的字典；否則返回單一圖表
    """
    
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
    if student_mode and student_name is not None:
        fig = go.Figure()
        
        # 檢查資料是否有梯次欄位
        if x_col not in df.columns:
            fig.update_layout(
                title=f"無法顯示學生 {student_name} 的趨勢圖：缺少 {x_col} 欄位",
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
            
        # 篩選出該學生的資料
        student_df = df[df['學員姓名'] == student_name]
        
        if student_df.empty:
            fig.update_layout(
                title=f"無法顯示學生 {student_name} 的趨勢圖：找不到資料",
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
                        # 生成隨機顏色
                        r, g, b = np.random.randint(0, 200, 3)
                        line_color = default_color.format(r, g, b, 1.0)
                        fill_color = default_color.format(r, g, b, 0.2)
                    
                    # 計算該項目的平均分數
                    batch_mean = group_df[y_col].mean()
                    
                    # 繪製點
                    fig.add_trace(go.Scatter(
                        x=x_values,
                        y=[batch_mean],
                        mode='markers',
                        name=f'{group} - {student_name}',
                        marker=dict(color=line_color, size=10)
                    ))
                    
                    # 如果有階層資訊，添加階層參考線和置信區間
                    if '階層' in student_df.columns and full_df is not None:
                        layer = student_df['階層'].iloc[0]  # 假設學生只屬於一個階層
                        layer_df = full_df[(full_df['階層'] == layer) & (full_df[group_col] == group)]
                        
                        if not layer_df.empty:
                            # 計算該階層在該梯次的平均分數
                            batch = x_values[0]
                            layer_batch_df = layer_df[layer_df[x_col] == batch]
                            
                            if not layer_batch_df.empty:
                                batch_layer_mean = layer_batch_df[y_col].mean()
                                batch_layer_std = layer_batch_df[y_col].std() if len(layer_batch_df) > 1 else 0
                                batch_layer_count = len(layer_batch_df)
                                
                                # 計算95%置信區間
                                if batch_layer_count > 1:
                                    t_critical = stats.t.ppf(0.975, batch_layer_count - 1)
                                    ci_width = t_critical * batch_layer_std / np.sqrt(batch_layer_count)
                                    lower_bound = max(0, batch_layer_mean - ci_width)
                                    upper_bound = min(5, batch_layer_mean + ci_width)
                                    
                                    # 繪製置信區間
                                    fig.add_trace(go.Scatter(
                                        x=[batch, batch],
                                        y=[lower_bound, upper_bound],
                                        mode='lines',
                                        line=dict(color=fill_color, width=10, dash='dot'),
                                        name=f'{group} - 階層 {layer} 95% CI'
                                    ))
                                
                                # 繪製參考點
                                fig.add_trace(go.Scatter(
                                    x=x_values,
                                    y=[batch_layer_mean],
                                    mode='markers',
                                    name=f'{group} - 階層 {layer} 平均',
                                    marker=dict(color=fill_color, size=10, symbol='diamond')
                                ))
            else:
                # 不分組，直接使用所有資料計算平均值
                batch_mean = student_df[y_col].mean()
                
                # 繪製點
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=[batch_mean],
                    mode='markers',
                    name=f'{student_name}',
                    marker=dict(color='rgba(0, 0, 255, 1.0)', size=10)
                ))
                
                # 如果有階層資訊，添加階層參考線和置信區間
                if '階層' in student_df.columns and full_df is not None:
                    layer = student_df['階層'].iloc[0]  # 假設學生只屬於一個階層
                    layer_df = full_df[full_df['階層'] == layer]
                    
                    if not layer_df.empty:
                        # 計算該階層在該梯次的平均分數
                        batch = x_values[0]
                        layer_batch_df = layer_df[layer_df[x_col] == batch]
                        
                        if not layer_batch_df.empty:
                            batch_layer_mean = layer_batch_df[y_col].mean()
                            batch_layer_std = layer_batch_df[y_col].std() if len(layer_batch_df) > 1 else 0
                            batch_layer_count = len(layer_batch_df)
                            
                            # 計算95%置信區間
                            if batch_layer_count > 1:
                                t_critical = stats.t.ppf(0.975, batch_layer_count - 1)
                                ci_width = t_critical * batch_layer_std / np.sqrt(batch_layer_count)
                                lower_bound = max(0, batch_layer_mean - ci_width)
                                upper_bound = min(5, batch_layer_mean + ci_width)
                                
                                # 繪製置信區間
                                fig.add_trace(go.Scatter(
                                    x=[batch, batch],
                                    y=[lower_bound, upper_bound],
                                    mode='lines',
                                    line=dict(color='rgba(100, 100, 100, 0.5)', width=10, dash='dot'),
                                    name=f'階層 {layer} 95% CI'
                                ))
                            
                            # 繪製參考點
                            fig.add_trace(go.Scatter(
                                x=x_values,
                                y=[batch_layer_mean],
                                mode='markers',
                                name=f'階層 {layer} 平均',
                                marker=dict(color='rgba(100, 100, 100, 0.8)', size=10, symbol='diamond')
                            ))
        else:
            # 多個梯次，繪製趨勢線
            if group_col and group_col in student_df.columns:
                # 按評核項目分組
                groups = student_df[group_col].unique()
                
                for group in groups:
                    group_df = student_df[student_df[group_col] == group]
                    
                    # 選擇顏色
                    if group in colors:
                        line_color = colors[group].format(1.0)
                        fill_color = colors[group].format(0.2)
                    else:
                        line_color = get_random_color(group, 1.0)
                        fill_color = get_random_color(group, 0.2)
                    
                    # 初始化聚合數據結果
                    means = []
                    
                    # 按排序後的梯次計算統計值
                    for batch in x_values:
                        batch_data = group_df[group_df[x_col] == batch][y_col]
                        means.append(batch_data.mean() if not batch_data.empty else None)
                    
                    # 處理可能的None值
                    valid_indices = [i for i, m in enumerate(means) if m is not None]
                    valid_x = [x_values[i] for i in valid_indices]
                    valid_means = [means[i] for i in valid_indices]
                    
                    # 如果有有效資料，繪製學生趨勢線
                    if valid_means:
                        fig.add_trace(go.Scatter(
                            x=valid_x,
                            y=valid_means,
                            mode='lines+markers',
                            name=f'{group} - {student_name}',
                            line=dict(color=line_color, width=3)  # 加粗學生的線
                        ))
                    
                    # 添加階層平均趨勢和置信區間
                    if '階層' in student_df.columns and full_df is not None:
                        layer = student_df['階層'].iloc[0]  # 假設學生只屬於一個階層
                        layer_df = full_df[(full_df['階層'] == layer) & (full_df[group_col] == group)]
                        
                        if not layer_df.empty:
                            # 初始化聚合數據結果
                            layer_means = []
                            layer_counts = []
                            layer_stds = []
                            
                            # 按排序後的梯次計算統計值
                            for batch in x_values:
                                layer_batch_data = layer_df[layer_df[x_col] == batch][y_col]
                                layer_means.append(layer_batch_data.mean() if not layer_batch_data.empty else None)
                                layer_counts.append(len(layer_batch_data) if not layer_batch_data.empty else 0)
                                layer_stds.append(layer_batch_data.std() if len(layer_batch_data) > 1 else 0)
                            
                            # 處理可能的None值
                            valid_indices = [i for i, m in enumerate(layer_means) if m is not None]
                            valid_x = [x_values[i] for i in valid_indices]
                            valid_layer_means = [layer_means[i] for i in valid_indices]
                            valid_layer_counts = [layer_counts[i] for i in valid_indices]
                            valid_layer_stds = [layer_stds[i] for i in valid_indices]
                            
                            # 繪製階層平均趨勢線
                            if valid_layer_means:
                                # 添加階層平均線 - 使用淡色虛線
                                fig.add_trace(go.Scatter(
                                    x=valid_x,
                                    y=valid_layer_means,
                                    mode='lines',
                                    line=dict(color=fill_color.replace('0.2', '0.7'), width=1, dash='dash'),
                                    name=f'{group} - 階層 {layer} 平均'
                                ))
                                
                                # 計算95%置信區間
                                if confidence_interval and len(valid_layer_means) > 1:
                                    # 創建數據框以便計算置信區間
                                    agg_data = pd.DataFrame({
                                        'mean': valid_layer_means,
                                        'count': valid_layer_counts,
                                        'std': valid_layer_stds
                                    })
                                    
                                    # 使用t分布計算95%置信區間
                                    t_critical = stats.t.ppf(0.975, agg_data['count'] - 1)  # 95% 置信度
                                    # 防止除以零錯誤
                                    sqrt_counts = np.sqrt(agg_data['count'])
                                    sqrt_counts = np.where(sqrt_counts == 0, 1, sqrt_counts)
                                    
                                    ci_width = t_critical * agg_data['std'] / sqrt_counts
                                    lower_bound = agg_data['mean'] - ci_width
                                    upper_bound = agg_data['mean'] + ci_width
                                    
                                    # 確保邊界在有效範圍內
                                    lower_bound = np.maximum(0, lower_bound)  # EPA等級下限為0
                                    upper_bound = np.minimum(5, upper_bound)  # EPA等級上限為5
                                    
                                    # 添加置信區間 - 使用與線條相同但較淡的顏色
                                    fig.add_trace(go.Scatter(
                                        x=np.concatenate([valid_x, valid_x[::-1]]),
                                        y=np.concatenate([upper_bound, lower_bound[::-1]]),
                                        fill='toself',
                                        fillcolor=fill_color,
                                        line=dict(color='rgba(0, 0, 0, 0)'),
                                        showlegend=True,  # 顯示在圖例中
                                        name=f'{group} - 階層 {layer} 95% CI'
                                    ))
            else:
                # 不分組，直接使用所有資料計算趨勢
                means = []
                
                # 按排序後的梯次計算統計值
                for batch in x_values:
                    batch_data = student_df[student_df[x_col] == batch][y_col]
                    means.append(batch_data.mean() if not batch_data.empty else None)
                
                # 處理可能的None值
                valid_indices = [i for i, m in enumerate(means) if m is not None]
                valid_x = [x_values[i] for i in valid_indices]
                valid_means = [means[i] for i in valid_indices]
                
                # 如果有有效資料，繪製學生趨勢線
                if valid_means:
                    fig.add_trace(go.Scatter(
                        x=valid_x,
                        y=valid_means,
                        mode='lines+markers',
                        name=f'{student_name}',
                        line=dict(color='rgba(0, 0, 255, 1.0)', width=3)  # 加粗學生的線
                    ))
                
                # 添加階層平均趨勢和置信區間
                if '階層' in student_df.columns and full_df is not None:
                    layer = student_df['階層'].iloc[0]  # 假設學生只屬於一個階層
                    layer_df = full_df[full_df['階層'] == layer]
                    
                    if not layer_df.empty:
                        # 初始化聚合數據結果
                        layer_means = []
                        layer_counts = []
                        layer_stds = []
                        
                        # 按排序後的梯次計算統計值
                        for batch in x_values:
                            layer_batch_data = layer_df[layer_df[x_col] == batch][y_col]
                            layer_means.append(layer_batch_data.mean() if not layer_batch_data.empty else None)
                            layer_counts.append(len(layer_batch_data) if not layer_batch_data.empty else 0)
                            layer_stds.append(layer_batch_data.std() if len(layer_batch_data) > 1 else 0)
                        
                        # 處理可能的None值
                        valid_indices = [i for i, m in enumerate(layer_means) if m is not None]
                        valid_x = [x_values[i] for i in valid_indices]
                        valid_layer_means = [layer_means[i] for i in valid_indices]
                        valid_layer_counts = [layer_counts[i] for i in valid_indices]
                        valid_layer_stds = [layer_stds[i] for i in valid_indices]
                        
                        # 繪製階層平均趨勢線
                        if valid_layer_means:
                            # 添加階層平均線 - 使用虛線
                            fig.add_trace(go.Scatter(
                                x=valid_x,
                                y=valid_layer_means,
                                mode='lines',
                                name=f'階層 {layer} 平均',
                                line=dict(color='rgba(100, 100, 100, 0.7)', width=1, dash='dash')
                            ))
                            
                            # 計算95%置信區間
                            if confidence_interval and len(valid_layer_means) > 1:
                                # 創建數據框以便計算置信區間
                                agg_data = pd.DataFrame({
                                    'mean': valid_layer_means,
                                    'count': valid_layer_counts,
                                    'std': valid_layer_stds
                                })
                                
                                # 使用t分布計算95%置信區間
                                t_critical = stats.t.ppf(0.975, agg_data['count'] - 1)  # 95% 置信度
                                # 防止除以零錯誤
                                sqrt_counts = np.sqrt(agg_data['count'])
                                sqrt_counts = np.where(sqrt_counts == 0, 1, sqrt_counts)
                                
                                ci_width = t_critical * agg_data['std'] / sqrt_counts
                                lower_bound = agg_data['mean'] - ci_width
                                upper_bound = agg_data['mean'] + ci_width
                                
                                # 確保邊界在有效範圍內
                                lower_bound = np.maximum(0, lower_bound)  # EPA等級下限為0
                                upper_bound = np.minimum(5, upper_bound)  # EPA等級上限為5
                                
                                # 添加置信區間 - 使用淡灰色
                                fig.add_trace(go.Scatter(
                                    x=np.concatenate([valid_x, valid_x[::-1]]),
                                    y=np.concatenate([upper_bound, lower_bound[::-1]]),
                                    fill='toself',
                                    fillcolor='rgba(100, 100, 100, 0.2)',
                                    line=dict(color='rgba(0, 0, 0, 0)'),
                                    showlegend=True,  # 顯示在圖例中
                                    name=f'階層 {layer} 95% CI'
                                ))
        
        # 設定圖表樣式
        student_title = f"學生 {student_name} 的EPA評核趨勢" if title == "EPA 趨勢圖" else title
        fig.update_layout(
            title=student_title,
            xaxis=dict(
                title=x_col,
                type='category',
                categoryorder='array',
                categoryarray=x_values
            ),
            yaxis=dict(
                title=y_col,
                range=[0, 5]  # EPA等級範圍為0-5
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
        
        return fig
    
    # 單一圖表繪製邏輯
    fig = go.Figure()
    
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
            
            # 使用之前定義的排序後的梯次
            x_values = sorted_batches
            
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
                # 創建聚合數據框
                agg_data = pd.DataFrame({
                    x_col: valid_x,
                    'mean': valid_means,
                    'count': valid_counts,
                    'std': valid_stds
                })
                
                # 計算95%置信區間
                if confidence_interval and len(agg_data) > 1:
                    # 處理可能的NaN值
                    agg_data = agg_data.fillna({'std': 0, 'count': 1})
                    
                    # 使用t分布計算95%置信區間
                    t_critical = stats.t.ppf(0.975, agg_data['count'] - 1)  # 95% 置信度
                    # 防止除以零錯誤
                    sqrt_counts = np.sqrt(agg_data['count'])
                    sqrt_counts = np.where(sqrt_counts == 0, 1, sqrt_counts)
                    
                    ci_width = t_critical * agg_data['std'] / sqrt_counts
                    lower_bound = agg_data['mean'] - ci_width
                    upper_bound = agg_data['mean'] + ci_width
                    
                    # 確保邊界在有效範圍內
                    lower_bound = np.maximum(0, lower_bound)  # EPA等級下限為0
                    upper_bound = np.minimum(5, upper_bound)  # EPA等級上限為5
                    
                    # 添加置信區間，使用與線條相同但半透明的顏色
                    fig.add_trace(go.Scatter(
                        x=np.concatenate([agg_data[x_col], agg_data[x_col][::-1]]),
                        y=np.concatenate([upper_bound, lower_bound[::-1]]),
                        fill='toself',
                        fillcolor=fill_color,
                        line=dict(color='rgba(0, 0, 0, 0)'),
                        showlegend=False,
                        name=f'{group} 95% CI'
                    ))
                
                # 添加平均值線
                fig.add_trace(go.Scatter(
                    x=agg_data[x_col],
                    y=agg_data['mean'],
                    mode='lines+markers',
                    name=f'{group}',
                    line=dict(color=line_color, width=2)
                ))
    else:
        # 沒有分組時，繪製單一趨勢線
        # 使用排序後的梯次
        x_values = sorted_batches
        
        # 初始化聚合數據結果
        means = []
        counts = []
        stds = []
        
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
                # 處理可能的NaN值
                agg_data = agg_data.fillna({'std': 0, 'count': 1})
                
                t_critical = stats.t.ppf(0.975, agg_data['count'] - 1)
                # 防止除以零錯誤
                sqrt_counts = np.sqrt(agg_data['count'])
                sqrt_counts = np.where(sqrt_counts == 0, 1, sqrt_counts)
                
                ci_width = t_critical * agg_data['std'] / sqrt_counts
                lower_bound = agg_data['mean'] - ci_width
                upper_bound = agg_data['mean'] + ci_width
                
                # 確保邊界在有效範圍內
                lower_bound = np.maximum(0, lower_bound)
                upper_bound = np.minimum(5, upper_bound)
                
                # 添加置信區間，使用半透明的藍色
                fig.add_trace(go.Scatter(
                    x=np.concatenate([agg_data[x_col], agg_data[x_col][::-1]]),
                    y=np.concatenate([upper_bound, lower_bound[::-1]]),
                    fill='toself',
                    fillcolor=fill_color,
                    line=dict(color='rgba(0, 0, 0, 0)'),
                    showlegend=False,
                    name='95% CI'
                ))
            
            # 添加平均值線
            fig.add_trace(go.Scatter(
                x=agg_data[x_col],
                y=agg_data['mean'],
                mode='lines+markers',
                name=y_col,
                line=dict(color=line_color, width=2)
            ))
    
    # 明確設定X軸的排序
    fig.update_layout(
        title=title,
        xaxis=dict(
            title=x_col,
            type='category',  # 使用category類型
            categoryorder='array',
            categoryarray=sorted_batches
        ),
        yaxis=dict(
            title=y_col,
            range=[0, 5]  # EPA等級範圍為0-5
        ),
        showlegend=True
    )
    
    return fig

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





# 為了向後相容，設定別名
plot_epa_radar = plot_radar_chart
plot_radar_charts = plot_radar_chart 