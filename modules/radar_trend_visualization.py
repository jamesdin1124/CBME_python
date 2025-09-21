"""
雷達圖和趨勢圖視覺化模組
提供各階層雷達圖和EPA評核項目趨勢圖的創建功能
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import hashlib
from modules.visualization import plot_radar_chart, plot_epa_trend_px

def create_layer_radar_chart(df, selected_layers=None):
    """創建各階層雷達圖（合併顯示）
    
    Args:
        df (pd.DataFrame): 包含EPA評核資料的DataFrame
        selected_layers (list): 選定的階層列表
        
    Returns:
        plotly.graph_objects.Figure: 雷達圖物件
    """
    try:
        if df.empty:
            # 創建空圖表
            fig = go.Figure()
            fig.add_annotation(
                text="沒有可用的資料繪製雷達圖",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title="各階層EPA評核雷達圖比較",
                height=500
            )
            return fig
        
        # 使用原始的 plot_radar_chart 函數
        radar_fig = plot_radar_chart(
            df=df, 
            plot_types=['layers'],
            title="各階層EPA評核雷達圖比較",
            labels={
                'layer': '階層 {}',
                'teacher_avg': '教師評核平均',
                'student_avg': '學員自評平均',
            }
        )
        
        # 更新布局設定
        radar_fig.update_layout(
            height=500,
            margin=dict(t=50, b=50, l=50, r=50),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        
        return radar_fig
        
    except Exception as e:
        # 創建錯誤圖表
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"創建雷達圖時發生錯誤：{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(
            title="雷達圖創建錯誤",
            height=500
        )
        return error_fig

def create_epa_trend_charts(df, selected_layers=None, layer_batch_orders=None, global_sorted_batches=None):
    """創建EPA評核項目趨勢圖
    
    Args:
        df (pd.DataFrame): 包含EPA評核資料的DataFrame
        selected_layers (list): 選定的階層列表
        layer_batch_orders (dict): 各階層的梯次排序
        global_sorted_batches (list): 全域梯次排序
        
    Returns:
        list: 趨勢圖物件列表
    """
    try:
        trend_figures = []
        
        if not selected_layers:
            return trend_figures
        
        for layer in selected_layers:
            layer_df_for_trend = df[df['階層'] == layer]
            
            if layer_df_for_trend.empty:
                # 創建警告圖表
                warning_fig = go.Figure()
                warning_fig.add_annotation(
                    text=f"階層 {layer} 沒有足夠的資料繪製趨勢圖",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="orange")
                )
                warning_fig.update_layout(
                    title=f"階層 {layer} 的EPA評核趨勢",
                    height=450
                )
                trend_figures.append(warning_fig)
                continue
            
            try:
                # 獲取該階層的梯次排序
                batch_order = layer_batch_orders.get(layer, global_sorted_batches) if layer_batch_orders else global_sorted_batches
                
                # 使用原始的 plot_epa_trend_px 函數
                trend_fig = plot_epa_trend_px(
                    df=layer_df_for_trend,
                    x_col='梯次',
                    y_col='教師評核EPA等級_數值',
                    group_col='EPA評核項目',
                    title=''
                )
                
                # 更新布局設定
                trend_fig.update_layout(
                    xaxis=dict(categoryorder='array', categoryarray=batch_order) if batch_order else {},
                    height=450,
                    margin=dict(t=30, b=30, l=30, r=30)
                )
                
                trend_figures.append(trend_fig)
                
            except Exception as e:
                # 創建錯誤圖表
                error_fig = go.Figure()
                error_fig.add_annotation(
                    text=f"繪製階層 {layer} 的趨勢圖時發生錯誤: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="red")
                )
                error_fig.update_layout(
                    title=f"階層 {layer} 的EPA評核趨勢",
                    height=450
                )
                trend_figures.append(error_fig)
        
        return trend_figures
        
    except Exception as e:
        # 創建錯誤圖表
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"創建趨勢圖時發生錯誤：{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(
            title="趨勢圖創建錯誤",
            height=450
        )
        return [error_fig]

def create_simple_layer_radar_chart(df, selected_layers=None):
    """創建簡化版的階層雷達圖（使用 plotly.express）
    
    Args:
        df (pd.DataFrame): 包含EPA評核資料的DataFrame
        selected_layers (list): 選定的階層列表
        
    Returns:
        plotly.graph_objects.Figure: 雷達圖物件
    """
    try:
        if df.empty or '階層' not in df.columns:
            # 創建空圖表
            fig = go.Figure()
            fig.add_annotation(
                text="沒有可用的階層資料繪製雷達圖",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title="各階層EPA評核雷達圖比較",
                height=500
            )
            return fig
        
        # 計算各階層的平均分數
        layer_avg = df.groupby('階層')['教師評核EPA等級_數值'].mean().reset_index()
        
        if layer_avg.empty:
            # 創建空圖表
            fig = go.Figure()
            fig.add_annotation(
                text="沒有可用的評核資料繪製雷達圖",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title="各階層EPA評核雷達圖比較",
                height=500
            )
            return fig
        
        # 創建雷達圖
        fig = go.Figure()
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
        
        for i, (_, row) in enumerate(layer_avg.iterrows()):
            layer_name = row['階層']
            avg_score = row['教師評核EPA等級_數值']
            
            fig.add_trace(go.Scatterpolar(
                r=[avg_score],
                theta=[layer_name],
                fill='toself',
                name=f'階層 {layer_name}',
                line_color=colors[i % len(colors)],
                marker_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )
            ),
            showlegend=True,
            title="各階層平均評核分數雷達圖",
            height=500
        )
        
        return fig
        
    except Exception as e:
        # 創建錯誤圖表
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"創建簡化雷達圖時發生錯誤：{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(
            title="雷達圖創建錯誤",
            height=500
        )
        return error_fig

def create_simple_epa_trend_chart(df):
    """創建簡化版的EPA評核項目趨勢圖
    
    Args:
        df (pd.DataFrame): 包含EPA評核資料的DataFrame
        
    Returns:
        plotly.graph_objects.Figure: 趨勢圖物件
    """
    try:
        if df.empty or 'EPA評核項目' not in df.columns:
            # 創建空圖表
            fig = go.Figure()
            fig.add_annotation(
                text="沒有可用的EPA評核項目資料繪製趨勢圖",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title="EPA評核項目趨勢圖",
                height=450
            )
            return fig
        
        # 按梯次和EPA項目分組計算平均分數
        trend_data = df.groupby(['梯次', 'EPA評核項目'])['教師評核EPA等級_數值'].mean().reset_index()
        
        if trend_data.empty:
            # 創建空圖表
            fig = go.Figure()
            fig.add_annotation(
                text="沒有可用的趨勢資料繪製趨勢圖",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(
                title="EPA評核項目趨勢圖",
                height=450
            )
            return fig
        
        # 創建趨勢圖
        fig = px.line(
            trend_data,
            x='梯次',
            y='教師評核EPA等級_數值',
            color='EPA評核項目',
            title="EPA評核項目趨勢圖",
            markers=True
        )
        
        fig.update_layout(
            height=450,
            margin=dict(t=30, b=30, l=30, r=30)
        )
        
        return fig
        
    except Exception as e:
        # 創建錯誤圖表
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"創建簡化趨勢圖時發生錯誤：{str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(
            title="趨勢圖創建錯誤",
            height=450
        )
        return error_fig
