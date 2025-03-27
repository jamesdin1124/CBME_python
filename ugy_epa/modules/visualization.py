import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def plot_epa_radar(df, categories, values, title="EPA 雷達圖"):
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

def plot_epa_trend(df, x_col, y_col, title="EPA 趨勢圖"):
    """繪製 EPA 趨勢圖"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 繪製趨勢線
    sns.lineplot(data=df, x=x_col, y=y_col, ax=ax)
    
    # 設定圖表屬性
    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.grid(True)
    
    # 旋轉 x 軸標籤
    plt.xticks(rotation=45)
    
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

# 為了向後相容，可以添加別名
plot_radar_charts = plot_epa_radar 

def plot_radar_chart(df):
    """繪製 EPA 評核雷達圖
    
    Args:
        df (DataFrame): 包含EPA評核資料的DataFrame
        
    Returns:
        go.Figure: Plotly雷達圖物件
    """
    # 計算每個EPA等級的平均值
    avg_student = df['學員自評EPA等級'].mean()
    avg_teacher = df['教師評核EPA等級'].mean()
    
    # 設定雷達圖的類別和數值
    categories = ['EPA Level']
    
    fig = go.Figure()
    
    # 添加學員自評數據
    fig.add_trace(go.Scatterpolar(
        r=[avg_student],
        theta=categories,
        name='學員自評平均',
        fill='toself'
    ))
    
    # 添加教師評核數據
    fig.add_trace(go.Scatterpolar(
        r=[avg_teacher],
        theta=categories,
        name='教師評核平均',
        fill='toself'
    ))
    
    # 設定雷達圖樣式
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]  # EPA等級範圍為1-5
            )
        ),
        showlegend=True,
        title='EPA評核平均值比較'
    )
    
    return fig

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