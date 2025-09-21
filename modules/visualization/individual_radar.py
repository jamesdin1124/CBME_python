"""
個別學生雷達圖模組
提供個別學生分析中的雷達圖功能，包含各階層平均分數對比
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import List, Dict, Optional, Tuple
from modules.visualization.unified_radar import (
    UnifiedRadarVisualization,
    EPAChartConfig,
    create_epa_radar_chart
)

class IndividualStudentRadarVisualization:
    """個別學生雷達圖視覺化類別"""
    
    def __init__(self):
        """初始化個別學生雷達圖視覺化類別"""
        self.radar_viz = UnifiedRadarVisualization()
        
        # 階層顏色配置
        self.layer_colors = {
            'C1': 'rgba(255, 100, 100, 0.7)',
            'C2': 'rgba(100, 100, 255, 0.7)',
            'PGY': 'rgba(100, 200, 100, 0.7)',
            'R': 'rgba(255, 200, 100, 0.7)',
            '住院醫師': 'rgba(255, 150, 150, 0.7)',
            '主治醫師': 'rgba(150, 150, 255, 0.7)'
        }
    
    def get_random_color(self, seed_str: str, alpha: float = 0.7) -> str:
        """根據字符串生成確定性隨機顏色"""
        import hashlib
        hash_value = int(hashlib.md5(str(seed_str).encode()).hexdigest(), 16)
        r = (hash_value & 0xFF) % 200
        g = ((hash_value >> 8) & 0xFF) % 200
        b = ((hash_value >> 16) & 0xFF) % 200
        return f'rgba({r}, {g}, {b}, {alpha})'
    
    def create_individual_student_radar_with_layers(self, 
                                                  student_df: pd.DataFrame, 
                                                  student_id: str,
                                                  all_data_df: Optional[pd.DataFrame] = None,
                                                  standard_categories: Optional[List[str]] = None,
                                                  show_all_layers: bool = True,
                                                  show_student_layer_only: bool = False) -> go.Figure:
        """創建個別學生雷達圖，包含各階層平均分數對比
        
        Args:
            student_df: 學生資料
            student_id: 學生ID
            all_data_df: 所有學生資料（用於計算階層平均）
            standard_categories: 標準EPA項目類別
            show_all_layers: 是否顯示所有階層
            show_student_layer_only: 是否只顯示學生所屬階層
            
        Returns:
            plotly.graph_objects.Figure: 雷達圖物件
        """
        try:
            if student_df.empty:
                return self._create_error_figure("沒有學生資料")
            
            # 獲取學生所屬階層
            student_layer = None
            if '階層' in student_df.columns and not student_df.empty:
                student_layer = student_df['階層'].iloc[0]
            
            # 獲取學生姓名
            student_name = ""
            if '學員姓名' in student_df.columns and not student_df.empty:
                valid_names = student_df['學員姓名'].dropna()
                if not valid_names.empty:
                    student_name = valid_names.iloc[0]
            
            student_label = f"{student_id}"
            if student_name:
                student_label += f" ({student_name})"
            
            # 決定EPA項目順序
            if standard_categories is None:
                standard_categories = sorted(student_df['EPA評核項目'].unique().tolist())
            
            # 檢查項目數量
            if len(standard_categories) < 3:
                original_count = len(standard_categories)
                standard_categories = list(standard_categories)
                for i in range(3 - original_count):
                    standard_categories.append(f"空白項目{i+1}")
            
            # 建立學生評分值
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
                    categories.append(category)
                    student_values.append(1)
            
            if len(categories) < 2:
                return self._create_error_figure(f"學生 {student_label} 的評核項目不足")
            
            # 確保資料是閉合的
            categories_closed = categories + [categories[0]]
            student_values_closed = student_values + [student_values[0]]
            
            # 創建雷達圖
            fig = go.Figure()
            
            # 添加學生資料
            fig.add_trace(go.Scatterpolar(
                r=student_values_closed,
                theta=categories_closed,
                fill='toself',
                name=f'學員 {student_label}',
                line=dict(color='rgba(0, 0, 0, 0.8)', width=3),
                fillcolor='rgba(0, 0, 0, 0.2)',
                opacity=0.8
            ))
            
            # 添加階層平均（如果提供了所有資料）
            if all_data_df is not None and not all_data_df.empty:
                # 決定要顯示的階層
                layers_to_show = []
                if show_student_layer_only and student_layer:
                    layers_to_show = [student_layer]
                elif show_all_layers:
                    layers_to_show = sorted(all_data_df['階層'].unique().tolist())
                else:
                    # 顯示學生階層和其他主要階層
                    if student_layer:
                        layers_to_show = [student_layer]
                    # 添加其他主要階層
                    all_layers = sorted(all_data_df['階層'].unique().tolist())
                    for layer in all_layers:
                        if layer != student_layer and layer in ['C1', 'C2', 'PGY', 'R']:
                            layers_to_show.append(layer)
                
                # 為每個階層添加平均線
                for layer in layers_to_show:
                    layer_df = all_data_df[all_data_df['階層'] == layer]
                    if not layer_df.empty:
                        full_score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in all_data_df.columns else '教師評核EPA等級'
                        layer_values = []
                        
                        for category in categories:
                            layer_data = layer_df[layer_df['EPA評核項目'] == category]
                            if not layer_data.empty:
                                layer_avg = layer_data[full_score_column].mean()
                                layer_values.append(layer_avg)
                            else:
                                layer_values.append(1)
                        
                        layer_values_closed = layer_values + [layer_values[0]]
                        layer_color = self.layer_colors.get(layer, self.get_random_color(layer, 0.7))
                        
                        # 決定線條樣式
                        line_style = 'solid' if layer == student_layer else 'dash'
                        line_width = 3 if layer == student_layer else 2
                        
                        fig.add_trace(go.Scatterpolar(
                            r=layer_values_closed,
                            theta=categories_closed,
                            fill='none',
                            name=f'{layer} 階層平均',
                            line=dict(
                                dash=line_style, 
                                color=layer_color,
                                width=line_width
                            ),
                            opacity=0.8
                        ))
            
            # 設定圖表樣式
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True, 
                        range=[0, 5],
                        ticktext=['0', '1', '2', '3', '4', '5'],
                        tickvals=[0, 1, 2, 3, 4, 5]
                    )
                ),
                showlegend=True,
                height=500,
                margin=dict(t=50, b=50, l=50, r=50),
                title=f"學生 {student_label} 的EPA評核雷達圖",
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"創建個別學生雷達圖時發生錯誤: {str(e)}")
    
    def create_layer_comparison_radar(self, 
                                    all_data_df: pd.DataFrame,
                                    standard_categories: Optional[List[str]] = None,
                                    selected_layers: Optional[List[str]] = None) -> go.Figure:
        """創建階層比較雷達圖
        
        Args:
            all_data_df: 所有學生資料
            standard_categories: 標準EPA項目類別
            selected_layers: 選定的階層列表
            
        Returns:
            plotly.graph_objects.Figure: 雷達圖物件
        """
        try:
            if all_data_df.empty:
                return self._create_error_figure("沒有資料")
            
            # 決定EPA項目順序
            if standard_categories is None:
                standard_categories = sorted(all_data_df['EPA評核項目'].unique().tolist())
            
            # 決定要顯示的階層
            if selected_layers is None:
                selected_layers = sorted(all_data_df['階層'].unique().tolist())
            
            # 檢查項目數量
            if len(standard_categories) < 3:
                original_count = len(standard_categories)
                standard_categories = list(standard_categories)
                for i in range(3 - original_count):
                    standard_categories.append(f"空白項目{i+1}")
            
            categories_closed = list(standard_categories) + [standard_categories[0]]
            
            # 創建雷達圖
            fig = go.Figure()
            
            # 檢查分數欄位
            teacher_score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in all_data_df.columns else '教師評核EPA等級'
            
            # 為每個階層添加雷達圖
            for layer in selected_layers:
                layer_df = all_data_df[all_data_df['階層'] == layer]
                if not layer_df.empty:
                    avg_scores = []
                    
                    for category in standard_categories:
                        avg = layer_df[layer_df['EPA評核項目'] == category][teacher_score_column].mean()
                        avg_scores.append(avg)
                    
                    avg_scores.append(avg_scores[0])  # 封閉雷達圖
                    avg_scores = [max(1, score) for score in avg_scores]  # 將0值替換為1
                    
                    fig.add_trace(go.Scatterpolar(
                        r=avg_scores,
                        theta=categories_closed,
                        name=f'階層 {layer}',
                        fill='toself',
                        fillcolor=self.layer_colors.get(layer, 'rgba(200, 200, 200, 0.6)'),
                        line=dict(
                            color=self.layer_colors.get(layer, 'rgba(200, 200, 200, 0.8)'),
                            width=2
                        )
                    ))
            
            # 更新版面配置
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 5],
                        ticktext=['0', '1', '2', '3', '4', '5'],
                        tickvals=[0, 1, 2, 3, 4, 5]
                    )
                ),
                showlegend=True,
                title="各階層EPA評核雷達圖比較",
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                )
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"創建階層比較雷達圖時發生錯誤: {str(e)}")
    
    def _create_error_figure(self, error_message: str) -> go.Figure:
        """創建錯誤圖表"""
        fig = go.Figure()
        fig.add_annotation(
            text=error_message,
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            title="雷達圖創建錯誤",
            height=500
        )
        return fig

# 便利函數
def create_individual_student_radar_with_layers(student_df: pd.DataFrame, 
                                             student_id: str,
                                             all_data_df: Optional[pd.DataFrame] = None,
                                             standard_categories: Optional[List[str]] = None,
                                             show_all_layers: bool = True,
                                             show_student_layer_only: bool = False) -> go.Figure:
    """便利函數：創建個別學生雷達圖，包含各階層平均分數對比"""
    radar_viz = IndividualStudentRadarVisualization()
    return radar_viz.create_individual_student_radar_with_layers(
        student_df, student_id, all_data_df, standard_categories, 
        show_all_layers, show_student_layer_only
    )

def create_layer_comparison_radar(all_data_df: pd.DataFrame,
                                standard_categories: Optional[List[str]] = None,
                                selected_layers: Optional[List[str]] = None) -> go.Figure:
    """便利函數：創建階層比較雷達圖"""
    radar_viz = IndividualStudentRadarVisualization()
    return radar_viz.create_layer_comparison_radar(all_data_df, standard_categories, selected_layers)
