import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

def create_radar_chart(categories, values, title="雷達圖", scale=5, fill=True):
    """
    建立通用雷達圖函數
    
    參數:
    - categories: 雷達圖的各個維度名稱
    - values: 對應每個維度的數值
    - title: 圖表標題
    - scale: 雷達圖的最大刻度
    - fill: 是否填充雷達圖區域
    
    返回:
    - fig: plotly 圖表物件
    """
    # 確保資料是閉合的雷達圖（首尾相連）
    categories = list(categories)
    values = list(values)
    
    # 添加第一個點到最後，形成閉合
    categories.append(categories[0])
    values.append(values[0])
    
    # 建立 plotly 雷達圖
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself' if fill else None,
        name=title
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, scale]
            )
        ),
        title=title
    )
    
    return fig

def display_radar_chart(df, value_columns, name_column=None, title="能力評估雷達圖", scale=5):
    """
    顯示雷達圖的高階函數
    
    參數:
    - df: 包含資料的 DataFrame
    - value_columns: 要在雷達圖中顯示的數值欄位列表
    - name_column: 用於分組的欄位名稱（如學生姓名、教師姓名等）
    - title: 圖表標題
    - scale: 雷達圖的最大刻度
    """
    # 如果有分組欄位
    if name_column and name_column in df.columns:
        # 讓使用者選擇要顯示的特定對象
        unique_names = df[name_column].unique()
        selected_name = st.selectbox(f"選擇{name_column}", ["全部"] + list(unique_names))
        
        if selected_name != "全部":
            # 篩選特定對象的資料
            filtered_df = df[df[name_column] == selected_name]
            
            # 計算平均值
            values = [filtered_df[col].mean() for col in value_columns]
            
            # 建立並顯示雷達圖
            fig = create_radar_chart(value_columns, values, f"{selected_name} - {title}", scale)
            st.plotly_chart(fig, use_container_width=True)
        else:
            # 顯示全部資料的平均值
            values = [df[col].mean() for col in value_columns]
            
            # 建立並顯示雷達圖
            fig = create_radar_chart(value_columns, values, f"全部 - {title}", scale)
            st.plotly_chart(fig, use_container_width=True)
    else:
        # 沒有分組欄位，直接顯示整體平均
        values = [df[col].mean() for col in value_columns]
        
        # 建立並顯示雷達圖
        fig = create_radar_chart(value_columns, values, title, scale)
        st.plotly_chart(fig, use_container_width=True)

# 其他可能需要的共用函數... 