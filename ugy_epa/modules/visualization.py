import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
import re



def plot_radar_chart(df, plot_types=None, student_id=None, categories=None, values=None, 
                    title="EPA 雷達圖",
                    labels={
                        'layer': '階層 {}',  # {} 會被替換成實際的層級
                        'teacher_avg': '教師評核平均',
                        'student_avg': '學員自評平均',
                        'individual': '學員 {}'  # {} 會被替換成實際的學員ID
                    }):
    """繪製 EPA 雷達圖
    
    Args:
        df (DataFrame, optional): 包含EPA評核資料的DataFrame
        plot_types (list, optional): 要顯示的圖表類型列表
        student_id (str, optional): 學生ID
        categories (list, optional): 雷達圖的類別列表
        values (list, optional): 對應類別的數值列表
        title (str): 圖表標題
        labels (dict): 圖例標籤的自定義文字，包含：
            - layer: 階層標籤格式
            - teacher_avg: 教師平均標籤
            - student_avg: 學生平均標籤
            - individual: 個別學生標籤格式
    """
    """繪製 EPA 雷達圖"""
    # 確保資料是閉合的（首尾相連）
    categories = categories + [categories[0]]
    values = values + [values[0]]
    
    # 計算角度
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=True)
    
    # 創建圖形
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # 繪製雷達圖
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    
    # 設定刻度和標籤
    ax.set_thetagrids(np.degrees(angles[:-1]), categories[:-1])
    ax.set_ylim(0, 5)
    ax.set_title(title)
    
    return fig

    import plotly.graph_objects as go
    
    # 如果提供了categories和values，使用簡單模式
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
    
    # 否則使用完整模式（原有的plot_radar_chart邏輯）
    # 定義顏色方案
    colors = {
        'C1': 'rgba(255, 255, 0, 0.6)',  # 黃
        'C2': 'rgba(0, 255, 0, 0.6)',  # 綠
        'PGY': 'rgba(230, 200, 255, 0.6)',  # 淡紫
        'teacher_avg': 'rgba(255, 200, 200, 0.6)',  # 淡紅
        'student_avg': 'rgba(200, 200, 255, 0.6)',  # 淡藍
        'individual': 'rgba(0, 0, 0, 0.8)'  # 黑色
    }
    
    # 準備圖表
    fig = go.Figure()
    categories = df['EPA評核項目'].unique()
    categories_closed = list(categories) + [categories[0]]
    
    if plot_types is None:
        plot_types = ['layers']  # 預設顯示各階層平均
    
    # 繪製各階層平均
    if 'layers' in plot_types:
        layers = df['階層'].unique()
        for layer in layers:
            layer_data = df[df['階層'] == layer]
            avg_scores = []
            
            for category in categories:
                avg = layer_data[layer_data['EPA評核項目'] == category]['教師評核EPA等級'].mean()
                avg_scores.append(avg)
            
            avg_scores.append(avg_scores[0])  # 封閉雷達圖
            
            fig.add_trace(go.Scatterpolar(
                r=avg_scores,
                theta=categories_closed,
                name=labels['layer'].format(layer),  # 使用自定義標籤
                fill='toself',
                fillcolor=colors.get(layer, 'rgba(200, 200, 200, 0.6)'),
                line=dict(color=colors.get(layer, 'rgba(200, 200, 200, 0.8)'))
            ))
    
    # 繪製教師評核整體平均
    if 'teacher_avg' in plot_types:
        teacher_avg_scores = []
        for category in categories:
            avg = df[df['EPA評核項目'] == category]['教師評核EPA等級'].mean()
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
            avg = df[df['EPA評核項目'] == category]['學員自評EPA等級'].mean()
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
                score = student_data[student_data['EPA評核項目'] == category]['教師評核EPA等級'].iloc[0]
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

def plot_epa_trend(df, x_col, y_col, group_col=None, by_layer=False, confidence_interval=True, title="EPA 趨勢圖", sort_by_date=True):
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
    
    # 預處理並排序梯次
    def preprocess_and_sort_batches(df, x_col):
        """預處理梯次並按日期排序"""
        # 複製DataFrame以避免修改原始數據
        df_copy = df.copy()
        
        # 創建臨時日期列
        df_copy['_temp_date'] = None
        
        # 遍歷每個梯次值，嘗試轉換為日期
        unique_batches = df_copy[x_col].unique()
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
            df_copy.loc[df_copy[x_col] == batch, '_temp_date'] = date_obj
        
        # 按臨時日期列排序
        df_copy = df_copy.sort_values('_temp_date')
        
        # 獲取排序後的唯一梯次
        sorted_batches = df_copy[x_col].unique()
        
        # 刪除臨時列
        df_copy.drop('_temp_date', axis=1, inplace=True)
        
        return sorted_batches
    
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
            
            # 獲取並排序梯次 - 使用新方法
            if sort_by_date:
                x_values = preprocess_and_sort_batches(group_df, x_col)
            else:
                x_values = group_df[x_col].unique()
            
            # 初始化聚合數據結果
            means = []
            counts = []
            stds = []
            
            # 按排序後的梯次計算統計值
            for batch in x_values:
                batch_data = group_df[group_df[x_col] == batch][y_col]
                means.append(batch_data.mean())
                counts.append(len(batch_data))
                stds.append(batch_data.std())
            
            # 創建聚合數據框
            agg_data = pd.DataFrame({
                x_col: x_values,
                'mean': means,
                'count': counts,
                'std': stds
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
        # 獲取並排序梯次 - 使用新方法
        if sort_by_date:
            x_values = preprocess_and_sort_batches(df, x_col)
        else:
            x_values = df[x_col].unique()
        
        # 初始化聚合數據結果
        means = []
        counts = []
        stds = []
        
        # 按排序後的梯次計算統計值
        for batch in x_values:
            batch_data = df[df[x_col] == batch][y_col]
            means.append(batch_data.mean())
            counts.append(len(batch_data))
            stds.append(batch_data.std())
        
        # 創建聚合數據框
        agg_data = pd.DataFrame({
            x_col: x_values,
            'mean': means,
            'count': counts,
            'std': stds
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
    
    # 明確設定X軸的順序
    fig.update_layout(
        title=title,
        xaxis=dict(
            title=x_col,
            type='category',  # 使用category類型
            categoryorder='array',
            categoryarray=x_values  # 指定正確排序的類別陣列
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



def plot_trend_chart(df):
    """繪製 EPA 評核趨勢圖
    
    Args:
        df (DataFrame): 包含EPA評核資料的DataFrame
        
    Returns:
        go.Figure: Plotly趨勢圖物件
    """
    # 依梯次計算平均值
    trend_data = df.groupby('梯次').agg({
        '學員自評EPA等級': 'mean',
        '教師評核EPA等級': 'mean'
    }).reset_index()
    
    # 創建趨勢圖
    fig = go.Figure()
    
    # 添加學員自評趨勢線
    fig.add_trace(go.Scatter(
        x=trend_data['梯次'],
        y=trend_data['學員自評EPA等級'],
        mode='lines+markers',
        name='學員自評平均',
        line=dict(color='blue')
    ))
    
    # 添加教師評核趨勢線
    fig.add_trace(go.Scatter(
        x=trend_data['梯次'],
        y=trend_data['教師評核EPA等級'],
        mode='lines+markers',
        name='教師評核平均',
        line=dict(color='red')
    ))
    
    # 設定圖表樣式
    fig.update_layout(
        title='EPA評核趨勢變化',
        xaxis_title='梯次',
        yaxis_title='EPA等級平均值',
        yaxis=dict(range=[0, 5]),  # EPA等級範圍為1-5
        showlegend=True
    )
    
    return fig 

# 為了向後相容，設定別名
plot_epa_radar = plot_radar_chart
plot_radar_charts = plot_radar_chart 