"""
科部等級圖表視覺化模組
提供實習科部教師評核等級的圖表創建功能
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def get_grade_color(grade):
    """根據評核等級返回對應的顏色，小數點使用漸層效果
    
    Args:
        grade (float or str): 評核等級
        
    Returns:
        str: 對應的顏色代碼
    """
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

def get_level_label(grade):
    """根據評核等級返回對應的level標籤
    
    Args:
        grade (float or str): 評核等級
        
    Returns:
        str: 對應的level標籤
    """
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

def create_dept_grade_percentage_chart(df, dept_column):
    """創建實習科部教師評核等級百分比長條圖
    
    Args:
        df (pd.DataFrame): 包含EPA評核資料的DataFrame
        dept_column (str): 科部欄位名稱
        
    Returns:
        tuple: (百分比圖表, 數量圖表)
    """
    try:
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
            return fig, fig
        
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
        
        # 創建顏色映射
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
        
        # 創建百分比圖表 - 使用 go.Figure() 避免 px.bar() 的字體問題
        fig_percentage = go.Figure()
        
        # 為每個評核等級創建一個 trace
        for grade in sorted(complete_df['評核等級'].unique()):
            grade_data = complete_df[complete_df['評核等級'] == grade]
            if not grade_data.empty:
                fig_percentage.add_trace(go.Bar(
                    x=grade_data['科部'],
                    y=grade_data['百分比'],
                    name=str(grade),
                    marker_color=color_map.get(str(grade), '#CCCCCC')
                ))
        
        # 最簡化的布局設定，避免任何字體相關問題
        fig_percentage.update_layout(
            barmode='stack',
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
                tickangle=45
            ),
            yaxis=dict(
                range=[0, 100]
            )
        )
        
        # 添加百分比標籤 - 修正定位邏輯
        # 為每個科部計算累積高度，確保標籤在正確的顏色區塊中央
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
                    fig_percentage.add_annotation(
                        x=dept,
                        y=label_y,
                        text=f"{level_label} ({percentage:.1f}%)",
                        showarrow=False,
                        bgcolor="white",
                        bordercolor="gray",
                        borderwidth=1,
                        opacity=0.8
                    )
                    
                    # 更新累積高度
                    cumulative_height += percentage
            
            # 在每個科部長條圖上方添加總量註解
            fig_percentage.add_annotation(
                x=dept,
                y=100 + 8,  # 在百分比圖上方顯示，位置更高
                text=f"總量: {int(total_quantity)}",
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
        
        # 創建數量圖表 - 使用 go.Figure() 避免 px.bar() 的字體問題
        fig_quantity = go.Figure()
        
        # 為每個評核等級創建一個 trace
        for grade in sorted(quantity_df['評核等級'].unique()):
            grade_data = quantity_df[quantity_df['評核等級'] == grade]
            if not grade_data.empty:
                fig_quantity.add_trace(go.Bar(
                    x=grade_data['科部'],
                    y=grade_data['數量'],
                    name=str(grade),
                    marker_color=color_map.get(str(grade), '#CCCCCC')
                ))
        
        # 最簡化的布局設定，避免任何字體相關問題
        fig_quantity.update_layout(
            barmode='stack',
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
                tickangle=45
            )
        )
        
        # 添加數量標籤
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
                y=total_quantity + (total_quantity * 0.1),  # 在數量圖上方顯示
                text=f"總量: {int(total_quantity)}",
                showarrow=False,
                bgcolor="lightgreen",
                bordercolor="green",
                borderwidth=1,
                opacity=0.9
            )
        
        return fig_percentage, fig_quantity
        
    except Exception as e:
        # 創建錯誤圖表
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"創建圖表時發生錯誤：{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(
            title="圖表創建錯誤",
            height=400
        )
        return error_fig, error_fig

def create_simple_dept_chart(df, dept_column, chart_type="percentage"):
    """創建簡化版的科部圖表（使用 plotly.express）
    
    Args:
        df (pd.DataFrame): 包含EPA評核資料的DataFrame
        dept_column (str): 科部欄位名稱
        chart_type (str): 圖表類型 ("percentage" 或 "quantity")
        
    Returns:
        plotly.graph_objects.Figure: 圖表物件
    """
    try:
        # 計算各科部各等級的數量
        dept_grade_counts = df.groupby([dept_column, '教師評核EPA等級_數值']).size().reset_index(name='count')
        
        if chart_type == "percentage":
            # 計算各科部的總數
            dept_totals = df.groupby(dept_column).size().reset_index(name='total')
            
            # 合併資料計算百分比
            dept_grade_percent = dept_grade_counts.merge(dept_totals, on=dept_column)
            dept_grade_percent['percentage'] = (dept_grade_percent['count'] / dept_grade_percent['total']) * 100
            
            # 創建百分比圖表
            fig = px.bar(
                dept_grade_percent,
                x=dept_column,
                y='percentage',
                color='教師評核EPA等級_數值',
                title="各實習科部教師評核等級百分比分布",
                labels={'percentage': '百分比 (%)', dept_column: '實習科部'},
                color_discrete_sequence=px.colors.qualitative.Set3
            )
        else:
            # 創建數量圖表
            fig = px.bar(
                dept_grade_counts,
                x=dept_column,
                y='count',
                color='教師評核EPA等級_數值',
                title="各實習科部教師評核等級數量分布",
                labels={'count': '數量', dept_column: '實習科部'},
                color_discrete_sequence=px.colors.qualitative.Set3
            )
        
        return fig
        
    except Exception as e:
        # 創建錯誤圖表
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"創建圖表時發生錯誤：{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(
            title="圖表創建錯誤",
            height=400
        )
        return error_fig
