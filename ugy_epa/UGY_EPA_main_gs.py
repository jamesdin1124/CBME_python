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

# 字體設定已移除，使用系統預設字體以避免 Streamlit Cloud 字體缺失問題

# 在檔案開頭宣告全域變數
proceeded_EPA_df = None

# 添加一個改進的實習科部資料處理函數
def safe_process_departments(df):
    """安全地處理訓練科部資料，包含錯誤處理和資料驗證
    
    Args:
        df (pd.DataFrame): 訓練科部資料DataFrame
        
    Returns:
        pd.DataFrame or None: 處理後的資料，如果失敗則返回None
    """
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
        
        st.success(f"成功處理 {len(processed_df)} 筆學生資料，找到 {len(potential_dept_columns)} 個科部欄位")
        return processed_df
        
    except Exception as e:
        st.error(f"處理訓練科部資料時發生錯誤：{str(e)}")
        return None

def create_dept_grade_percentage_chart(df, dept_column):
    """創建實習科部教師評核等級百分比長條圖
    
    Args:
        df (pd.DataFrame): 包含EPA評核資料的DataFrame
        dept_column (str): 科部欄位名稱
        
    Returns:
        plotly.graph_objects.Figure: 百分比長條圖
    """
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        # 過濾有效的科部和評核等級資料
        valid_data = df[[dept_column, '教師評核EPA等級_數值']].dropna()
        
        if valid_data.empty:
            # 如果沒有有效資料，創建一個空的圖表
            fig = go.Figure()
            fig.add_annotation(
                text="沒有可用的科部或評核等級資料",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title="實習科部教師評核等級百分比分析",
                xaxis_title="實習科部",
                yaxis_title="百分比 (%)",
                height=400
            )
            return fig
        
        # 計算每個科部各評核等級的百分比
        dept_grade_counts = valid_data.groupby([dept_column, '教師評核EPA等級_數值']).size().reset_index(name='count')
        
        # 計算每個科部的總評核數
        dept_totals = valid_data.groupby(dept_column).size().reset_index(name='total')
        
        # 合併資料計算百分比
        dept_grade_percentage = dept_grade_counts.merge(dept_totals, on=dept_column)
        dept_grade_percentage['percentage'] = (dept_grade_percentage['count'] / dept_grade_percentage['total'] * 100).round(1)
        
        # 獲取所有科部和評核等級
        all_depts = sorted(valid_data[dept_column].unique())
        all_grades = sorted(valid_data['教師評核EPA等級_數值'].unique())
        
        # 創建完整的資料矩陣（包含0值）
        complete_data = []
        for dept in all_depts:
            for grade in all_grades:
                # 查找該科部該等級的資料
                existing_data = dept_grade_percentage[
                    (dept_grade_percentage[dept_column] == dept) & 
                    (dept_grade_percentage['教師評核EPA等級_數值'] == grade)
                ]
                
                if not existing_data.empty:
                    complete_data.append({
                        '科部': dept,
                        '評核等級': grade,
                        '百分比': existing_data['percentage'].iloc[0],
                        '數量': existing_data['count'].iloc[0]
                    })
                else:
                    complete_data.append({
                        '科部': dept,
                        '評核等級': grade,
                        '百分比': 0.0,
                        '數量': 0
                    })
        
        complete_df = pd.DataFrame(complete_data)
        
        # 強制將評核等級轉換為字串類型，確保plotly將其視為分類變數
        complete_df['評核等級'] = complete_df['評核等級'].astype(str)
        
        # 自定義顏色映射，處理小數點評核等級
        def get_grade_color(grade):
            """根據評核等級返回對應的顏色，小數點使用漸層效果"""
            try:
                grade_float = float(grade)
                base_grade = int(grade_float)
                decimal_part = grade_float - base_grade
                
                # 基礎顏色映射 - 同階層相近色系
                base_colors = {
                    1: '#FF6B9D',  # 粉紅色 - Level 1
                    2: '#FFD93D',  # 黃色 - Level 2
                    3: '#4CAF50',  # 綠色 - Level 3
                    4: '#2196F3',  # 藍色 - Level 4
                    5: '#9C27B0'   # 紫色 - Level 5
                }
                
                if base_grade in base_colors:
                    base_color = base_colors[base_grade]
                    
                    # 如果有小數點，創建同階層相近顏色
                    if decimal_part > 0:
                        # 使用同階層的相近顏色，而不是跨階層漸變
                        if base_grade == 1:
                            # Level 1 階層：粉紅色系
                            if decimal_part <= 0.5:
                                return '#FF8FA3'  # 稍深的粉紅色
                            else:
                                return '#FF6B9D'  # 基礎粉紅色
                        elif base_grade == 2:
                            # Level 2 階層：黃色系
                            if decimal_part <= 0.5:
                                return '#FFE135'  # 稍深的黃色
                            else:
                                return '#FFD93D'  # 基礎黃色
                        elif base_grade == 3:
                            # Level 3 階層：綠色系
                            if decimal_part <= 0.5:
                                return '#66BB6A'  # 稍深的綠色
                            else:
                                return '#4CAF50'  # 基礎綠色
                        elif base_grade == 4:
                            # Level 4 階層：藍色系
                            if decimal_part <= 0.5:
                                return '#42A5F5'  # 稍深的藍色
                            else:
                                return '#2196F3'  # 基礎藍色
                        elif base_grade == 5:
                            # Level 5 階層：紫色系
                            return '#9C27B0'  # 基礎紫色
                        
                        # 如果沒有特定規則，返回基礎顏色
                        return base_color
                    else:
                        return base_color
                else:
                    return '#CCCCCC'  # 預設顏色
            except:
                return '#CCCCCC'  # 預設顏色
        
        # 創建長條圖，使用自定義顏色
        # 先為每個評核等級準備顏色
        unique_grades = sorted(complete_df['評核等級'].unique())
        
        color_map = {}
        for grade in unique_grades:
            # 將字串轉換回float來計算顏色
            try:
                grade_float = float(grade)
                color = get_grade_color(grade_float)
            except:
                color = '#CCCCCC'  # 預設顏色
            color_map[grade] = color
        
        # 創建圖表
        fig = px.bar(
            complete_df,
            x='科部',
            y='百分比',
            color='評核等級',
            barmode='stack',
            title="各實習科部教師評核等級百分比分布",
            labels={
                '科部': '實習科部',
                '百分比': '百分比 (%)',
                '評核等級': '評核等級'
            },
            color_discrete_map=color_map
        )
        
        # 強制更新顏色配置
        # 直接使用我們已經創建好的顏色映射
        for i, trace in enumerate(fig.data):
            # 根據trace的順序和我們已知的評核等級順序來確定顏色
            # 假設trace的順序與unique_grades的順序一致
            if i < len(unique_grades):
                grade_name = unique_grades[i]
                grade_color = color_map[grade_name]
                
                # 設定顏色
                if hasattr(trace, 'marker') and hasattr(trace.marker, 'color'):
                    trace.marker.color = grade_color
                else:
                    trace.marker = dict(color=grade_color)
                
                # 強制更新trace的顏色
                trace.update(marker_color=grade_color)
        

        
        # 更新圖表樣式
        fig.update_layout(
            height=500,
            margin=dict(t=80, b=80, l=80, r=80),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                title="實習科部",
                tickangle=45
            ),
            yaxis=dict(
                title="百分比 (%)",
                range=[0, 100]
            )
        )
        
        # 添加百分比標籤 - 修正定位邏輯
        # 為每個科部計算累積高度，確保標籤在正確的顏色區塊中央
        
        # 定義評核等級到level標籤的映射
        def get_level_label(grade):
            """根據評核等級返回對應的level標籤"""
            try:
                grade_float = float(grade)
                if grade_float == 1.0:
                    return "Level 1a"
                elif grade_float == 1.5:
                    return "Level 1b"
                elif grade_float == 2.0:
                    return "Level 2a"
                elif grade_float == 2.5:
                    return "Level 2b"
                elif grade_float == 3.0:
                    return "Level 3a"
                elif grade_float == 3.3:
                    return "Level 3b"
                elif grade_float == 3.6:
                    return "Level 3c"
                elif grade_float == 4.0:
                    return "Level 4a"
                elif grade_float == 4.5:
                    return "Level 4b"
                elif grade_float == 5.0:
                    return "Level 5"
                else:
                    return f"Level {grade}"
            except:
                return f"Level {grade}"
        
        for dept in complete_df['科部'].unique():
            dept_data = complete_df[complete_df['科部'] == dept]
            cumulative_height = 0
            total_quantity = dept_data['數量'].sum()  # 計算該科部總量
            
            for _, row in dept_data.iterrows():
                percentage = row['百分比']
                grade = row['評核等級']
                if percentage > 0:
                    # 計算標籤的y位置：當前區塊的中央
                    label_y = cumulative_height + (percentage / 2)
                    
                    # 獲取level標籤
                    level_label = get_level_label(grade)
                    
                    # 添加百分比標籤（包含level標籤）
                    fig.add_annotation(
                        x=dept,
                        y=label_y,
                        text=f"{level_label} ({percentage:.1f}%)",
                        font=dict(size=10, color="black", weight="bold"),
                        showarrow=False,
                        bgcolor="white",
                        bordercolor="gray",
                        borderwidth=1,
                        opacity=0.8
                    )
                    
                    # 更新累積高度
                    cumulative_height += percentage
            
            # 在每個科部長條圖上方添加總量註解
            fig.add_annotation(
                x=dept,
                y=100 + 8,  # 在百分比圖上方顯示，位置更高
                text=f"總量: {int(total_quantity)}",
                font=dict(size=12, color="black", weight="bold"),
                showarrow=False,
                bgcolor="lightgreen",
                bordercolor="green",
                borderwidth=1,
                opacity=0.9
            )
        
        # 創建數量堆疊長條圖
        # 準備數量資料
        quantity_df = complete_df.copy()
        quantity_df['數量'] = quantity_df['數量'].astype(float)
        
        # 創建數量圖表
        fig_quantity = px.bar(
            quantity_df,
            x='科部',
            y='數量',
            color='評核等級',
            barmode='stack',
            title="各實習科部教師評核等級數量分布",
            labels={
                '科部': '實習科部',
                '數量': '數量',
                '評核等級': '評核等級'
            },
            color_discrete_map=color_map
        )
        
        # 更新數量圖表樣式
        fig_quantity.update_layout(
            height=500,
            margin=dict(t=80, b=80, l=80, r=80),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                title="實習科部",
                tickangle=45
            ),
            yaxis=dict(
                title="數量"
            )
        )
        
        # 為數量圖表添加標籤和總量
        for dept in quantity_df['科部'].unique():
            dept_data = quantity_df[quantity_df['科部'] == dept]
            cumulative_height = 0
            total_quantity = dept_data['數量'].sum()  # 計算該科部總量
            
            for _, row in dept_data.iterrows():
                quantity = row['數量']
                grade = row['評核等級']
                if quantity > 0:
                    # 計算標籤的y位置：當前區塊的中央
                    label_y = cumulative_height + (quantity / 2)
                    
                    # 獲取level標籤
                    level_label = get_level_label(grade)
                    
                    # 添加數量標籤（包含level標籤）
                    fig_quantity.add_annotation(
                        x=dept,
                        y=label_y,
                        text=f"{level_label} ({int(quantity)})",
                        font=dict(size=10, color="black", weight="bold"),
                        showarrow=False,
                        bgcolor="white",
                        bordercolor="gray",
                        borderwidth=1,
                        opacity=0.8
                    )
                    
                    # 更新累積高度
                    cumulative_height += quantity
            
            # 在每個科部長條圖上方添加總量註解
            fig_quantity.add_annotation(
                x=dept,
                y=total_quantity + 8,  # 在長條圖上方顯示，位置更高
                text=f"總量: {int(total_quantity)}",
                font=dict(size=12, color="black", weight="bold"),
                showarrow=False,
                bgcolor="lightblue",
                bordercolor="blue",
                borderwidth=1,
                opacity=0.9
            )
        
        # 返回兩個圖表，讓調用者決定如何顯示
        return fig, fig_quantity
        
    except Exception as e:
        # 如果出錯，創建錯誤圖表
        fig = go.Figure()
        fig.add_annotation(
            text=f"創建圖表時發生錯誤：{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            title="實習科部教師評核等級百分比分析",
            height=400,
            
        )
        
        # 創建第二個錯誤圖表
        fig_quantity = go.Figure()
        fig_quantity.add_annotation(
            text=f"創建圖表時發生錯誤：{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        fig_quantity.update_layout(
            title="實習科部教師評核等級數量分析",
            height=400,
            
        )
        
        return fig, fig_quantity

def create_dept_grade_distribution_chart(df, dept_name):
    """創建單一科部的評核等級分布圖
    
    Args:
        df (pd.DataFrame): 包含該科部EPA評核資料的DataFrame
        dept_name (str): 科部名稱
        
    Returns:
        plotly.graph_objects.Figure: 評核等級分布圖
    """
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        # 過濾有效的評核等級資料
        valid_data = df[['教師評核EPA等級_數值']].dropna()
        
        if valid_data.empty:
            # 如果沒有有效資料，創建一個空的圖表
            fig = go.Figure()
            fig.add_annotation(
                text="沒有可用的評核等級資料",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title=f"{dept_name} 評核等級分布",
                height=400
            )
            return fig
        
        # 計算各評核等級的數量
        grade_counts = valid_data['教師評核EPA等級_數值'].value_counts().sort_index()
        total_count = len(valid_data)
        
        # 計算百分比
        grade_percentages = (grade_counts / total_count * 100).round(1)
        
        # 創建長條圖
        fig = go.Figure()
        
        # 定義評核等級的鮮明顏色（支援小數點漸層）
        def get_grade_color(grade):
            """根據評核等級返回對應的顏色，小數點使用漸層效果"""
            try:
                grade_float = float(grade)
                base_grade = int(grade_float)
                decimal_part = grade_float - base_grade
                
                # 基礎顏色映射 - 同階層相近色系
                base_colors = {
                    1: '#FF6B9D',  # 粉紅色 - Level 1
                    2: '#FFD93D',  # 黃色 - Level 2
                    3: '#4CAF50',  # 綠色 - Level 3
                    4: '#2196F3',  # 藍色 - Level 4
                    5: '#9C27B0'   # 紫色 - Level 5
                }
                
                if base_grade in base_colors:
                    base_color = base_colors[base_grade]
                    
                    # 如果有小數點，創建同階層相近顏色
                    if decimal_part > 0:
                        # 使用同階層的相近顏色，而不是跨階層漸變
                        if base_grade == 1:
                            # Level 1 階層：粉紅色系
                            if decimal_part <= 0.5:
                                return '#FF8FA3'  # 稍深的粉紅色
                            else:
                                return '#FF6B9D'  # 基礎粉紅色
                        elif base_grade == 2:
                            # Level 2 階層：黃色系
                            if decimal_part <= 0.5:
                                return '#FFE135'  # 稍深的黃色
                            else:
                                return '#FFD93D'  # 基礎黃色
                        elif base_grade == 3:
                            # Level 3 階層：綠色系
                            if decimal_part <= 0.5:
                                return '#66BB6A'  # 稍深的綠色
                            else:
                                return '#4CAF50'  # 基礎綠色
                        elif base_grade == 4:
                            # Level 4 階層：藍色系
                            if decimal_part <= 0.5:
                                return '#42A5F5'  # 稍深的藍色
                            else:
                                return '#2196F3'  # 基礎藍色
                        elif base_grade == 5:
                            # Level 5 階層：紫色系
                            return '#9C27B0'  # 基礎紫色
                        
                        # 如果沒有特定規則，返回基礎顏色
                        return base_color
                    else:
                        return base_color
                else:
                    return '#CCCCCC'  # 預設顏色
            except:
                return '#CCCCCC'  # 預設顏色
        
        # 為每個評核等級生成顏色
        colors = [get_grade_color(grade) for grade in grade_counts.index]
        
        # 添加數量長條（使用對應等級的顏色）
        fig.add_trace(go.Bar(
            x=grade_counts.index,
            y=grade_counts.values,
            name='數量',
            yaxis='y',
            marker_color=colors,
            text=grade_counts.values,
            textposition='outside'
        ))
        
        # 添加百分比長條（使用對應等級的顏色，但透明度較低）
        rgba_colors = []
        for color in colors:
            if color.startswith('rgb('):
                # 解析rgb顏色
                rgb_values = color[4:-1].split(', ')
                r, g, b = int(rgb_values[0]), int(rgb_values[1]), int(rgb_values[2])
                rgba_colors.append(f"rgba({r}, {g}, {b}, 0.7)")
            else:
                # 如果是hex顏色，轉換為rgba
                if color.startswith('#'):
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    rgba_colors.append(f"rgba({r}, {g}, {b}, 0.7)")
                else:
                    rgba_colors.append("rgba(204, 204, 204, 0.7)")  # 預設顏色
        
        fig.add_trace(go.Bar(
            x=grade_percentages.index,
            y=grade_percentages.values,
            name='百分比',
            yaxis='y2',
            marker_color=rgba_colors,
            text=[f"{p:.1f}%" for p in grade_percentages.values],
            textposition='outside'
        ))
        
        # 更新圖表樣式
        fig.update_layout(
            title=f"{dept_name} 評核等級分布分析 (總評核數: {total_count})",
            height=500,
            margin=dict(t=80, b=80, l=80, r=80),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                title="評核等級",
                tickmode='linear',
                tick0=1,
                dtick=1
            ),
            yaxis=dict(
                title="數量",
                side="left"
            ),
            yaxis2=dict(
                title="百分比 (%)",
                side="right",
                overlaying="y",
                range=[0, 100]
            )
        )
        
        return fig
        
    except Exception as e:
        # 如果出錯，創建錯誤圖表
        fig = go.Figure()
        fig.add_annotation(
            text=f"創建圖表時發生錯誤：{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            title=f"{dept_name} 評核等級分布",
            height=400,
            
        )
        return fig

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
            
            st.success(f"成功合併訓練科部資料，共處理 {len(epa_data)} 筆EPA資料")
            return epa_data
            
        except Exception as e:
            st.warning(f"合併過程中發生錯誤：{str(e)}，將返回原始EPA資料")
            return epa_data
            
    except Exception as e:
        st.error(f"合併EPA和訓練科部資料時發生錯誤：{str(e)}")
        return epa_df

# 定義階層顏色（供雷達圖與表格用）
layer_colors = {
    'C1': 'rgba(255, 107, 107, 0.8)',    # 鮮紅色 - C1階層
    'C2': 'rgba(78, 205, 196, 0.8)',     # 青綠色 - C2階層
    'PGY': 'rgba(255, 165, 0, 0.8)',     # 橙色 - PGY階層
    'R': 'rgba(107, 207, 127, 0.8)',     # 綠色 - R階層
    'Fellow': 'rgba(255, 217, 61, 0.8)'  # 黃色 - Fellow階層
    # 可依需求擴充
}

# 產生隨機顏色（若階層未定義顏色時使用）
import hashlib
def get_random_color(seed_str, alpha=0.8):
    # 預定義的鮮明顏色列表
    bright_colors = [
        '#FF6B6B',  # 鮮紅色
        '#4ECDC4',  # 青綠色
        '#45B7D1',  # 藍色
        '#96CEB4',  # 薄荷綠
        '#FFEAA7',  # 淺黃色
        '#DDA0DD',  # 梅紅色
        '#98D8C8',  # 海綠色
        '#F7DC6F',  # 金黃色
        '#BB8FCE',  # 紫色
        '#85C1E9',  # 天藍色
        '#F8C471',  # 橙色
        '#82E0AA'   # 淺綠色
    ]
    
    # 使用seed_str的hash值來選擇顏色
    hash_value = int(hashlib.md5(str(seed_str).encode()).hexdigest(), 16)
    color_index = hash_value % len(bright_colors)
    selected_color = bright_colors[color_index]
    
    # 轉換hex顏色為rgba格式
    r = int(selected_color[1:3], 16)
    g = int(selected_color[3:5], 16)
    b = int(selected_color[5:7], 16)
    
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
                
                selected_epa_items = st.multiselect(
                    "選擇EPA評核項目 (可複選)",
                    options=all_epa_items,
                    default=all_epa_items,
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
                
                selected_epa_items = st.multiselect(
                    "選擇EPA評核項目 (可複選)",
                    options=all_epa_items,
                    default=all_epa_items,
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
                st.subheader("實習科部教師評核等級百分比分析")
                
                # 確定科部欄位名稱
                dept_column = '實習科部' if '實習科部' in filtered_by_layer_df.columns else '訓練科部'
                
                # 創建百分比和數量長條圖（重新創建以確保一致性）
                dept_grade_percentage_fig, dept_grade_quantity_fig = create_dept_grade_percentage_chart(filtered_by_layer_df, dept_column)
                
                # 顯示百分比圖表（第二個）
                st.plotly_chart(dept_grade_percentage_fig, use_container_width=True, key="dept_grade_percentage_chart")
            else:
                st.warning(f"沒有教師評核EPA等級數值資料，無法進行百分比分析")
        
        # ===== 3. EPA評核雷達圖 =====
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
        
        # ===== 4. EPA評核趨勢分析 =====
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

# ==================== 主應用程式流程 ====================

def show_UGY_EPA_section():
    """主要應用程式流程"""
    global proceeded_EPA_df  # 使用全域變數
    st.title("UGY EPA分析")

    # 檢查是否需要重新載入/處理資料
    if 'processed_df' not in st.session_state or st.button("重新載入 Google Sheet 資料"):
        # 執行資料載入與處理流程
        raw_df, sheet_titles = load_sheet_data(show_info=False)
        
        # 除錯訊息已隱藏
        # st.write("除錯訊息：")
        # st.write(f"1. 工作表列表：{sheet_titles}")
        # st.write(f"2. 原始資料是否為空：{raw_df is None or raw_df.empty}")
        
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

            # 除錯訊息已隱藏
            # st.write(f"3. EPA原始資料是否為空：{epa_raw_df is None or epa_raw_df.empty}")
            # if epa_raw_df is not None:
            #     st.write(f"4. EPA原始資料欄位：{epa_raw_df.columns.tolist()}")

            if epa_raw_df is not None:
                with st.expander("載入的原始EPA資料", expanded=False):
                    st.dataframe(epa_raw_df)
                
                current_processed_df = process_data(epa_raw_df.copy()) # 傳入副本進行處理
                
                # 除錯訊息已隱藏
                # st.write(f"5. 處理後資料是否為空：{current_processed_df is None or current_processed_df.empty}")
                # if current_processed_df is not None:
                #     st.write(f"6. 處理後資料欄位：{current_processed_df.columns.tolist()}")
                
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

        # ========== 個別學生分析篩選器 ==========
        st.markdown("---")
        st.markdown("<h2 style='color:#1E90FF; font-size:24px;'>個別學生分析篩選設定</h2>", unsafe_allow_html=True)
        
        # 建立個別學生分析的篩選資料副本
        student_filter_df = proceeded_EPA_df.copy()
        
        # 1. 實習科部篩選 (可複選)
        if '實習科部' in student_filter_df.columns or '訓練科部' in student_filter_df.columns:
            dept_column = '實習科部' if '實習科部' in student_filter_df.columns else '訓練科部'
            all_depts = sorted(student_filter_df[dept_column].unique().tolist())
            
            selected_depts_student = st.multiselect(
                "選擇實習科部 (可複選)",
                options=all_depts,
                default=all_depts,
                format_func=lambda x: f"科部: {x}",
                key="student_dept_selector"
            )
            
            if not selected_depts_student:
                st.warning("請選擇至少一個實習科部")
                return
            
            # 按科部篩選
            student_filter_df = student_filter_df[student_filter_df[dept_column].isin(selected_depts_student)].copy()
        
        # 2. 階層篩選 (可複選)
        if '階層' in student_filter_df.columns:
            all_layers_student = sorted(student_filter_df['階層'].unique().tolist())
            
            selected_layers_student = st.multiselect(
                "選擇階層 (可複選)",
                options=all_layers_student,
                default=all_layers_student,
                format_func=lambda x: f"階層: {x}",
                key="student_layer_selector"
            )
            
            if not selected_layers_student:
                st.warning("請選擇至少一個階層")
                return
            
            # 按階層篩選
            student_filter_df = student_filter_df[student_filter_df['階層'].isin(selected_layers_student)].copy()
        
        # 3. EPA評核項目篩選 (可複選)
        if 'EPA評核項目' in student_filter_df.columns:
            all_epa_items_student = sorted(student_filter_df['EPA評核項目'].unique().tolist())
            
            selected_epa_items_student = st.multiselect(
                "選擇EPA評核項目 (可複選)",
                options=all_epa_items_student,
                default=all_epa_items_student,
                format_func=lambda x: f"項目: {x}",
                key="student_epa_selector"
            )
            
            if not selected_epa_items_student:
                st.warning("請選擇至少一個EPA評核項目")
                return
            
            # 按EPA評核項目篩選
            student_filter_df = student_filter_df[student_filter_df['EPA評核項目'].isin(selected_epa_items_student)].copy()
        
        # 顯示篩選後的統計資訊
        if not student_filter_df.empty:
            st.success(f"篩選後資料：{len(student_filter_df)} 筆記錄")
        else:
            st.warning("篩選後沒有符合條件的資料")
            return
        
        # ========== 個別學生分析開始 ==========
        # 先顯示每個階層、每個EPA項目的平均及95%CI
        if '階層' in student_filter_df.columns:
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


        # 檢查必要欄位，優先使用學號，如果沒有則使用學員姓名
        if '學號' in student_filter_df.columns:
            student_id_column = '學號'
            required_columns_student = ['梯次', '學員姓名', 'EPA評核項目', '教師評核EPA等級', '學號']
        elif '學員姓名' in student_filter_df.columns:
            student_id_column = '學員姓名'
            required_columns_student = ['梯次', '學員姓名', 'EPA評核項目', '教師評核EPA等級']
            # 如果沒有學號欄位，創建一個虛擬的學號欄位（使用姓名）
            student_filter_df['學號'] = student_filter_df['學員姓名']
        else:
            st.error("資料中缺少學號或學員姓名欄位，無法顯示學生雷達圖")
            return
            
        missing_columns_student = [col for col in required_columns_student if col not in student_filter_df.columns]
        
        if missing_columns_student:
            st.error(f"資料中缺少以下欄位，無法顯示學生雷達圖：{', '.join(missing_columns_student)}")
        else:
            standard_epa_categories = sorted(student_filter_df['EPA評核項目'].unique().tolist())
            total_students = len(student_filter_df[student_id_column].dropna().unique())
            # 確保梯次欄位存在才計算梯次數量
            num_batches_display = len(student_filter_df['梯次'].unique()) if '梯次' in student_filter_df.columns else "N/A"

            st.success(f"已選擇 {num_batches_display} 個梯次，共有 {total_students} 名不重複學生")
            
            # 獲取所有學生列表
            student_ids_in_batches = student_filter_df[student_id_column].dropna().unique()
            students_to_show = sorted([str(student_id) for student_id in student_ids_in_batches])
            
            # 添加學生選擇器
            st.subheader("選擇要查看的學生")
            
            # 創建學生選項列表，包含姓名和ID
            student_options = []
            student_display_names = {}
            
            for student_id in students_to_show:
                student_data = student_filter_df[student_filter_df[student_id_column].astype(str) == student_id]
                if not student_data.empty and '學員姓名' in student_data.columns:
                    student_name = student_data['學員姓名'].iloc[0]
                    display_name = f"{student_name} ({student_id})"
                else:
                    display_name = f"學生 {student_id}"
                
                student_options.append(student_id)
                student_display_names[student_id] = display_name
            
            selected_student = st.selectbox(
                "請選擇學生：",
                options=student_options,
                format_func=lambda x: student_display_names.get(x, x),
                help="選擇要查看EPA評核資料的學生"
            )
            
            # 只有選擇學生後才顯示資料
            if selected_student:
                st.markdown("---")
                st.subheader(f"學生EPA評核雷達圖分析")
                
                # 獲取選中學生的資料
                student_df_all_batches = student_filter_df[student_filter_df[student_id_column].astype(str) == selected_student].copy()
                if '教師' in student_df_all_batches.columns: # 篩選有教師評核的資料
                    student_df_all_batches = student_df_all_batches[student_df_all_batches['教師'].notna() & (student_df_all_batches['教師'] != '')]
                
                if student_df_all_batches.empty:
                    st.warning(f"學生 {selected_student} 沒有可用的教師評核資料")
                else:
                    # 顯示學生姓名
                    student_name = student_df_all_batches['學員姓名'].iloc[0] if not student_df_all_batches.empty and '學員姓名' in student_df_all_batches.columns else selected_student
                    st.subheader(f"學生: {student_name} ({selected_student})")
                    
                    # 顯示學生基本統計資訊
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("總評核數", len(student_df_all_batches))
                    with col2:
                        unique_epa_items = len(student_df_all_batches['EPA評核項目'].unique()) if 'EPA評核項目' in student_df_all_batches.columns else 0
                        st.metric("EPA項目數", unique_epa_items)
                    with col3:
                        unique_batches = len(student_df_all_batches['梯次'].unique()) if '梯次' in student_df_all_batches.columns else 0
                        st.metric("梯次數", unique_batches)
                    with col4:
                        if '教師評核EPA等級_數值' in student_df_all_batches.columns:
                            avg_score = student_df_all_batches['教師評核EPA等級_數值'].mean()
                            st.metric("平均分數", f"{avg_score:.2f}")
                        else:
                            st.metric("平均分數", "N/A")
                    
                    # 顯示該學生的資料
                    with st.expander("學生評核資料", expanded=True):
                        st.dataframe(student_df_all_batches)
                    

                    
                    # 顯示學生分析資料
                    display_student_data(
                        student_df_all_batches, 
                        selected_student, 
                        standard_categories=standard_epa_categories
                    )
            else:
                st.info("請從上方選擇要查看的學生")
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