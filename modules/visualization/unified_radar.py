"""
統一的雷達圖視覺化模組
整合所有雷達圖功能，提供統一的API介面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import hashlib
import traceback
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

class ChartType(Enum):
    """雷達圖類型枚舉"""
    SIMPLE = "simple"           # 簡單雷達圖
    EPA = "epa"                 # EPA專用雷達圖
    STUDENT = "student"         # 學生專用雷達圖
    COMPARISON = "comparison"   # 比較雷達圖
    LAYER = "layer"            # 階層雷達圖

class ChartMode(Enum):
    """圖表模式枚舉"""
    PLOTLY = "plotly"          # Plotly版本
    MATPLOTLIB = "matplotlib"  # Matplotlib版本

@dataclass
class RadarChartConfig:
    """雷達圖配置類別"""
    title: str = "雷達圖"
    scale: int = 5
    fill: bool = True
    color: Optional[str] = None
    opacity: float = 0.7
    show_legend: bool = True
    height: int = 500
    width: int = 800

@dataclass
class EPAChartConfig(RadarChartConfig):
    """EPA雷達圖配置類別"""
    plot_types: List[str] = None
    student_id: Optional[str] = None
    standard_categories: Optional[List[str]] = None
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.plot_types is None:
            self.plot_types = ['layers']
        if self.labels is None:
            self.labels = {
                'layer': '階層 {}',
                'teacher_avg': '教師評核平均',
                'student_avg': '學員自評平均',
                'individual': '學員 {}'
            }

class UnifiedRadarVisualization:
    """統一的雷達圖視覺化類別"""
    
    def __init__(self):
        """初始化雷達圖視覺化類別"""
        self.default_colors = {
            'C1': 'rgba(255, 100, 100, 0.7)',
            'C2': 'rgba(100, 100, 255, 0.7)',
            'PGY': 'rgba(100, 200, 100, 0.7)',
            'R': 'rgba(255, 200, 100, 0.7)',
            'teacher_avg': 'rgba(255, 200, 200, 0.6)',
            'student_avg': 'rgba(200, 200, 255, 0.6)',
            'individual': 'rgba(0, 0, 0, 0.8)'
        }
        
        self.epa_colors = {
            '病歷紀錄': '#EF553B',
            '當班處置': '#00CC96',
            '住院接診': '#636EFA',
            '新增項目1': '#FFA15A',
            '新增項目2': '#AB63FA'
        }
    
    def get_random_color(self, seed_str: str, alpha: float = 0.7) -> str:
        """根據字符串生成確定性隨機顏色"""
        hash_value = int(hashlib.md5(str(seed_str).encode()).hexdigest(), 16)
        r = (hash_value & 0xFF) % 200
        g = ((hash_value >> 8) & 0xFF) % 200
        b = ((hash_value >> 16) & 0xFF) % 200
        return f'rgba({r}, {g}, {b}, {alpha})'
    
    def create_simple_radar_chart(self, 
                                categories: List[str], 
                                values: List[float], 
                                config: RadarChartConfig) -> go.Figure:
        """創建簡單雷達圖"""
        try:
            # 確保資料是閉合的
            categories_closed = categories + [categories[0]]
            values_closed = values + [values[0]]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill='toself' if config.fill else None,
                name=config.title,
                line=dict(color=config.color) if config.color else dict(),
                fillcolor=config.color,
                opacity=config.opacity
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, config.scale]
                    )
                ),
                title=config.title,
                showlegend=config.show_legend,
                height=config.height
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"創建簡單雷達圖時發生錯誤: {str(e)}")
    
    def create_epa_radar_chart(self, 
                             df: pd.DataFrame, 
                             config: EPAChartConfig) -> go.Figure:
        """創建EPA專用雷達圖"""
        try:
            if df is None or df.empty:
                return self._create_error_figure("沒有可用的EPA資料")
            
            # 檢測使用模式
            if config.student_id is not None:
                return self._create_student_epa_chart(df, config)
            elif config.plot_types is not None:
                return self._create_full_epa_chart(df, config)
            else:
                return self._create_error_figure("EPA雷達圖參數不足")
                
        except Exception as e:
            return self._create_error_figure(f"創建EPA雷達圖時發生錯誤: {str(e)}")
    
    def _create_student_epa_chart(self, df: pd.DataFrame, config: EPAChartConfig) -> go.Figure:
        """創建學生EPA雷達圖"""
        try:
            # 篩選學生資料
            student_df = df.copy()  # 假設已經篩選過
            
            if student_df.empty:
                return self._create_error_figure(f"找不到學生 {config.student_id} 的資料")
            
            # 獲取學生姓名
            student_name = ""
            if '學員姓名' in student_df.columns and not student_df.empty:
                valid_names = student_df['學員姓名'].dropna()
                if not valid_names.empty:
                    student_name = valid_names.iloc[0]
            
            student_label = f"{config.student_id}"
            if student_name:
                student_label += f" ({student_name})"
            
            # 決定EPA項目順序
            if config.standard_categories is None:
                config.standard_categories = sorted(df['EPA評核項目'].unique().tolist())
            
            # 檢查項目數量
            if len(config.standard_categories) < 3:
                original_count = len(config.standard_categories)
                config.standard_categories = list(config.standard_categories)
                for i in range(3 - original_count):
                    config.standard_categories.append(f"空白項目{i+1}")
            
            # 建立學生評分值
            student_values = []
            categories = []
            score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in student_df.columns else '教師評核EPA等級'
            
            for category in config.standard_categories:
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
            fig.add_trace(go.Scatterpolar(
                r=student_values_closed,
                theta=categories_closed,
                fill='toself',
                name=config.labels['individual'].format(student_label)
            ))
            
            # 添加階層平均（如果可用）
            student_layer = None
            if '階層' in student_df.columns and not student_df.empty:
                student_layer = student_df['階層'].iloc[0]
            
            if student_layer and hasattr(self, 'proceeded_EPA_df') and self.proceeded_EPA_df is not None:
                layer_df = self.proceeded_EPA_df[self.proceeded_EPA_df['階層'] == student_layer]
                if not layer_df.empty:
                    full_score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in self.proceeded_EPA_df.columns else '教師評核EPA等級'
                    layer_values = []
                    for category in categories:
                        layer_data = layer_df[layer_df['EPA評核項目'] == category]
                        if not layer_data.empty:
                            layer_avg = layer_data[full_score_column].mean()
                            layer_values.append(layer_avg)
                        else:
                            layer_values.append(1)
                    
                    layer_values_closed = layer_values + [layer_values[0]]
                    layer_color = self.default_colors.get(student_layer, self.get_random_color(student_layer, 0.7))
                    fig.add_trace(go.Scatterpolar(
                        r=layer_values_closed,
                        theta=categories_closed,
                        fill='none',
                        name=f'{student_layer} 階層平均',
                        line=dict(dash='dash', color=layer_color)
                    ))
            
            # 設定圖表樣式
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, config.scale])),
                showlegend=config.show_legend,
                height=config.height,
                margin=dict(t=50, b=50, l=50, r=50),
                title=f"學生 {student_label} 的EPA評核雷達圖"
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"創建學生EPA雷達圖時發生錯誤: {str(e)}")
    
    def _create_full_epa_chart(self, df: pd.DataFrame, config: EPAChartConfig) -> go.Figure:
        """創建完整EPA雷達圖"""
        try:
            fig = go.Figure()
            
            categories = df['EPA評核項目'].unique()
            # 檢查項目數量
            if len(categories) < 3:
                original_count = len(categories)
                categories = list(categories)
                for i in range(3 - original_count):
                    categories.append(f"空白項目{i+1}")
            
            categories_closed = list(categories) + [categories[0]]
            
            # 檢查分數欄位
            teacher_score_column = '教師評核EPA等級_數值' if '教師評核EPA等級_數值' in df.columns else '教師評核EPA等級'
            student_score_column = '學員自評EPA等級_數值' if '學員自評EPA等級_數值' in df.columns else '學員自評EPA等級'
            
            # 繪製各階層平均
            if 'layers' in config.plot_types:
                layers = df['階層'].unique()
                for layer in layers:
                    layer_data = df[df['階層'] == layer]
                    avg_scores = []
                    
                    for category in categories:
                        avg = layer_data[layer_data['EPA評核項目'] == category][teacher_score_column].mean()
                        avg_scores.append(avg)
                    
                    avg_scores.append(avg_scores[0])  # 封閉雷達圖
                    avg_scores = [max(1, score) for score in avg_scores]  # 將0值替換為1
                    
                    fig.add_trace(go.Scatterpolar(
                        r=avg_scores,
                        theta=categories_closed,
                        name=config.labels['layer'].format(layer),
                        fill='toself',
                        fillcolor=self.default_colors.get(layer, 'rgba(200, 200, 200, 0.6)'),
                        line=dict(
                            color=self.default_colors.get(layer, 'rgba(200, 200, 200, 0.8)'),
                            width=2
                        )
                    ))
            
            # 繪製教師評核整體平均
            if 'teacher_avg' in config.plot_types:
                teacher_avg_scores = []
                for category in categories:
                    avg = df[df['EPA評核項目'] == category][teacher_score_column].mean()
                    teacher_avg_scores.append(avg)
                
                teacher_avg_scores.append(teacher_avg_scores[0])
                teacher_avg_scores = [max(1, score) for score in teacher_avg_scores]
                
                fig.add_trace(go.Scatterpolar(
                    r=teacher_avg_scores,
                    theta=categories_closed,
                    name=config.labels['teacher_avg'],
                    fill='toself',
                    fillcolor=self.default_colors['teacher_avg'],
                    line=dict(color='rgba(255, 0, 0, 0.8)')
                ))
            
            # 繪製學生自評整體平均
            if 'student_avg' in config.plot_types:
                student_avg_scores = []
                for category in categories:
                    avg = df[df['EPA評核項目'] == category][student_score_column].mean()
                    student_avg_scores.append(avg)
                
                student_avg_scores.append(student_avg_scores[0])
                student_avg_scores = [max(1, score) for score in student_avg_scores]
                
                fig.add_trace(go.Scatterpolar(
                    r=student_avg_scores,
                    theta=categories_closed,
                    name=config.labels['student_avg'],
                    fill='toself',
                    fillcolor=self.default_colors['student_avg'],
                    line=dict(color='rgba(0, 0, 255, 0.8)')
                ))
            
            # 更新版面配置
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, config.scale],
                        ticktext=['0', '1', '2', '3', '4', '5'],
                        tickvals=[0, 1, 2, 3, 4, 5]
                    )
                ),
                showlegend=config.show_legend,
                title=config.title,
                height=config.height
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"創建完整EPA雷達圖時發生錯誤: {str(e)}")
    
    def create_comparison_radar_chart(self, 
                                    df: pd.DataFrame, 
                                    value_columns: List[str], 
                                    group_column: str, 
                                    config: RadarChartConfig,
                                    selected_groups: Optional[List[str]] = None,
                                    highlight_group: Optional[str] = None) -> go.Figure:
        """創建比較雷達圖"""
        try:
            if group_column not in df.columns:
                return self._create_error_figure(f"分組欄位 '{group_column}' 不存在於資料中")
            
            groups = df[group_column].unique().tolist()
            if selected_groups is None:
                selected_groups = groups[:min(3, len(groups))]
            
            if not selected_groups:
                return self._create_error_figure("請至少選擇一個對象進行比較")
            
            fig = go.Figure()
            
            # 計算整體平均值
            avg_values = [df[col].mean() for col in value_columns]
            categories = list(value_columns)
            avg_values = list(avg_values)
            categories.append(categories[0])
            avg_values.append(avg_values[0])
            
            # 添加整體平均
            fig.add_trace(go.Scatterpolar(
                r=avg_values,
                theta=categories,
                fill='toself',
                name='整體平均',
                line=dict(color='lightgray', dash='dash'),
                fillcolor='lightgray',
                opacity=0.3
            ))
            
            # 為每個選定的對象添加雷達圖
            for group in selected_groups:
                group_data = df[df[group_column] == group]
                values = [group_data[col].mean() for col in value_columns]
                
                categories = list(value_columns)
                values = list(values)
                categories.append(categories[0])
                values.append(values[0])
                
                is_highlight = highlight_group and group == highlight_group
                color = 'red' if is_highlight else None
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=str(group),
                    line=dict(color=color),
                    fillcolor=color,
                    opacity=0.7 if is_highlight else 0.5
                ))
            
            # 更新布局
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, config.scale]
                    )
                ),
                title=config.title,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                height=config.height
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"創建比較雷達圖時發生錯誤: {str(e)}")
    
    def create_matplotlib_radar_chart(self, 
                                    categories: List[str], 
                                    values: List[float], 
                                    config: RadarChartConfig) -> plt.Figure:
        """創建Matplotlib版本的雷達圖"""
        try:
            # 確保資料是閉合的
            categories_closed = categories + [categories[0]]
            values_closed = values + [values[0]]
            
            # 計算角度
            angles = np.linspace(0, 2*np.pi, len(categories_closed), endpoint=True)
            
            # 設定中文字型
            plt.rcParams['axes.unicode_minus'] = False
            
            # 創建圖形
            fig = plt.figure(figsize=(config.width/100, config.height/100))
            ax = fig.add_subplot(111, polar=True)
            
            # 繪製雷達圖
            ax.plot(angles, values_closed, 'o-', linewidth=2, color=config.color or 'blue', label=config.title)
            ax.fill(angles, values_closed, alpha=0.25, color=config.color or 'blue')
            
            # 設定刻度和標籤
            ax.set_thetagrids(np.degrees(angles[:-1]), categories[:-1])
            ax.set_ylim(0, config.scale)
            ax.set_yticks(range(1, config.scale+1))
            ax.set_yticklabels([str(i) for i in range(1, config.scale+1)])
            ax.set_rlabel_position(0)
            
            # 添加標題和圖例
            plt.title(config.title, size=14)
            if config.show_legend:
                plt.legend(loc='upper right', fontsize='medium')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            # 創建錯誤圖形
            fig = plt.figure(figsize=(8, 6))
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"創建雷達圖時發生錯誤: {str(e)}", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title("雷達圖創建錯誤")
            return fig
    
    # ═══════════════════════════════════════════════════════
    # Phase 4 新增：個人/群組/比較雷達圖（通用 API）
    # ═══════════════════════════════════════════════════════

    def create_individual_radar(self, student_scores: Dict[str, float],
                                epa_labels: List[str],
                                title: str = "個人能力雷達圖",
                                student_name: str = None,
                                scale: int = 5,
                                height: int = 500) -> go.Figure:
        """
        建立個人能力雷達圖（依 EPA 項目顯示平均分數）。

        Args:
            student_scores: {EPA項目名稱: 平均分數} 字典
            epa_labels: EPA 項目標籤列表（決定順序）
            title: 圖表標題
            student_name: 學員姓名
            scale: 量表上限
            height: 圖表高度

        Returns:
            go.Figure
        """
        try:
            if not student_scores or not epa_labels:
                return self._create_error_figure("無個人資料")

            categories = list(epa_labels)
            values = [student_scores.get(cat, 0) for cat in categories]

            # 至少 3 軸
            while len(categories) < 3:
                categories.append(f"項目{len(categories)+1}")
                values.append(0)

            categories_closed = categories + [categories[0]]
            values_closed = values + [values[0]]

            fig = go.Figure()
            _name = student_name or '個人'
            fig.add_trace(go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill='toself',
                name=_name,
                fillcolor='rgba(99, 110, 250, 0.3)',
                line=dict(color='#636EFA', width=2),
            ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, scale])),
                title=title,
                showlegend=True,
                height=height,
            )
            return fig

        except Exception as e:
            return self._create_error_figure(f"建立個人雷達圖失敗: {str(e)}")

    def create_group_radar(self, group_data: pd.DataFrame,
                           epa_col: str, score_col: str,
                           group_col: str = None,
                           title: str = "群組 EPA 雷達圖",
                           scale: int = 5,
                           height: int = 500) -> go.Figure:
        """
        建立群組平均雷達圖（可多組疊加）。

        Args:
            group_data: 群組資料 DataFrame
            epa_col: EPA 項目欄位名
            score_col: 分數欄位名
            group_col: 分組欄位（如 '階層'），None 則為單一群組
            title: 圖表標題
            scale: 量表上限
            height: 圖表高度

        Returns:
            go.Figure
        """
        try:
            if group_data is None or group_data.empty:
                return self._create_error_figure("無群組資料")

            df = group_data.dropna(subset=[score_col]).copy()
            categories = sorted(df[epa_col].unique().tolist())

            while len(categories) < 3:
                categories.append(f"項目{len(categories)+1}")

            categories_closed = categories + [categories[0]]
            fig = go.Figure()

            if group_col and group_col in df.columns:
                groups = sorted(df[group_col].unique())
            else:
                df['_group'] = '全體'
                group_col = '_group'
                groups = ['全體']

            color_list = [
                'rgba(255, 100, 100, 0.7)', 'rgba(100, 100, 255, 0.7)',
                'rgba(100, 200, 100, 0.7)', 'rgba(255, 200, 100, 0.7)',
                'rgba(200, 100, 200, 0.7)', 'rgba(100, 200, 200, 0.7)',
            ]

            for i, grp in enumerate(groups):
                grp_df = df[df[group_col] == grp]
                vals = []
                for cat in categories:
                    cat_data = grp_df[grp_df[epa_col] == cat][score_col]
                    vals.append(cat_data.mean() if not cat_data.empty else 0)

                vals_closed = vals + [vals[0]]
                color = self.default_colors.get(str(grp), color_list[i % len(color_list)])

                fig.add_trace(go.Scatterpolar(
                    r=vals_closed,
                    theta=categories_closed,
                    fill='toself',
                    name=str(grp),
                    fillcolor=color.replace('0.7', '0.25') if '0.7' in color else color,
                    line=dict(color=color, width=2),
                ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, scale])),
                title=title,
                showlegend=True,
                height=height,
            )
            return fig

        except Exception as e:
            return self._create_error_figure(f"建立群組雷達圖失敗: {str(e)}")

    def create_individual_vs_group_radar(self, student_scores: Dict[str, float],
                                         group_data: pd.DataFrame,
                                         epa_col: str, score_col: str,
                                         epa_labels: List[str] = None,
                                         student_name: str = None,
                                         group_label: str = '群組平均',
                                         title: str = None,
                                         scale: int = 5,
                                         height: int = 500) -> go.Figure:
        """
        個人 vs 群組平均比較雷達圖（核心功能）。

        個人以粗實線 + 填色顯示，群組平均以虛線顯示。

        Args:
            student_scores: {EPA項目: 分數} 字典
            group_data: 群組資料 DataFrame
            epa_col: EPA 項目欄位名
            score_col: 分數欄位名
            epa_labels: EPA 項目標籤列表
            student_name: 學員姓名
            group_label: 群組標籤
            title: 圖表標題
            scale: 量表上限
            height: 圖表高度

        Returns:
            go.Figure
        """
        try:
            _title = title or f"{student_name or '個人'} vs {group_label}"

            # 決定 EPA 項目順序
            if epa_labels:
                categories = list(epa_labels)
            elif group_data is not None and not group_data.empty:
                categories = sorted(group_data[epa_col].unique().tolist())
            elif student_scores:
                categories = list(student_scores.keys())
            else:
                return self._create_error_figure("無資料")

            while len(categories) < 3:
                categories.append(f"項目{len(categories)+1}")

            categories_closed = categories + [categories[0]]
            fig = go.Figure()

            # 群組平均（背景 — 虛線）
            if group_data is not None and not group_data.empty:
                grp_df = group_data.dropna(subset=[score_col])
                group_vals = []
                for cat in categories:
                    cat_data = grp_df[grp_df[epa_col] == cat][score_col]
                    group_vals.append(cat_data.mean() if not cat_data.empty else 0)

                group_vals_closed = group_vals + [group_vals[0]]
                fig.add_trace(go.Scatterpolar(
                    r=group_vals_closed,
                    theta=categories_closed,
                    fill='toself',
                    name=group_label,
                    fillcolor='rgba(200, 200, 200, 0.15)',
                    line=dict(color='rgba(150, 150, 150, 0.8)', width=2, dash='dash'),
                ))

            # 個人（前景 — 實線）
            if student_scores:
                student_vals = [student_scores.get(cat, 0) for cat in categories]
                student_vals_closed = student_vals + [student_vals[0]]
                fig.add_trace(go.Scatterpolar(
                    r=student_vals_closed,
                    theta=categories_closed,
                    fill='toself',
                    name=student_name or '個人',
                    fillcolor='rgba(99, 110, 250, 0.3)',
                    line=dict(color='#636EFA', width=3),
                ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, scale])),
                title=_title,
                showlegend=True,
                height=height,
            )
            return fig

        except Exception as e:
            return self._create_error_figure(f"建立個人vs群組雷達圖失敗: {str(e)}")

    def create_peer_comparison_radar(self, multi_student_scores: Dict[str, Dict[str, float]],
                                     epa_labels: List[str],
                                     title: str = "同儕比較雷達圖",
                                     scale: int = 5,
                                     height: int = 500) -> go.Figure:
        """
        多人同儕比較雷達圖。

        Args:
            multi_student_scores: {學員名稱: {EPA項目: 分數}} 巢狀字典
            epa_labels: EPA 項目標籤列表
            title: 圖表標題
            scale: 量表上限
            height: 圖表高度

        Returns:
            go.Figure
        """
        try:
            if not multi_student_scores or not epa_labels:
                return self._create_error_figure("無同儕資料")

            categories = list(epa_labels)
            while len(categories) < 3:
                categories.append(f"項目{len(categories)+1}")

            categories_closed = categories + [categories[0]]
            fig = go.Figure()

            color_list = [
                '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
                '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52',
            ]

            for i, (name, scores) in enumerate(multi_student_scores.items()):
                vals = [scores.get(cat, 0) for cat in categories]
                vals_closed = vals + [vals[0]]
                color = color_list[i % len(color_list)]

                fig.add_trace(go.Scatterpolar(
                    r=vals_closed,
                    theta=categories_closed,
                    fill='toself',
                    name=str(name),
                    fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)',
                    line=dict(color=color, width=2),
                    opacity=0.8,
                ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, scale])),
                title=title,
                showlegend=True,
                height=height,
            )
            return fig

        except Exception as e:
            return self._create_error_figure(f"建立同儕比較雷達圖失敗: {str(e)}")

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

# Streamlit元件類別
class RadarChartComponent:
    """Streamlit雷達圖元件"""
    
    def __init__(self, radar_viz: UnifiedRadarVisualization):
        self.radar_viz = radar_viz
    
    def display_simple_radar(self, 
                           data: pd.DataFrame, 
                           title: str = "能力評估", 
                           key_prefix: str = "radar"):
        """顯示簡單雷達圖元件"""
        with st.expander(f"{title} 雷達圖分析", expanded=True):
            # 選擇要顯示的維度
            all_columns = data.select_dtypes(include=['number']).columns.tolist()
            selected_columns = st.multiselect(
                "選擇要顯示的維度", 
                all_columns,
                default=all_columns[:5] if len(all_columns) > 5 else all_columns,
                key=f"{key_prefix}_dims"
            )
            
            # 設定雷達圖刻度
            scale = st.slider("最大刻度", 1, 10, 5, key=f"{key_prefix}_scale")
            
            # 顯示雷達圖
            if selected_columns:
                values = [data[col].mean() for col in selected_columns]
                config = RadarChartConfig(
                    title=title,
                    scale=scale
                )
                fig = self.radar_viz.create_simple_radar_chart(selected_columns, values, config)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("請選擇至少一個維度")
    
    def display_comparison_radar(self, 
                               data: pd.DataFrame, 
                               title: str = "比較雷達圖", 
                               key_prefix: str = "comp_radar"):
        """顯示比較雷達圖元件"""
        with st.expander(f"{title}", expanded=True):
            # 選擇要顯示的維度
            all_columns = data.select_dtypes(include=['number']).columns.tolist()
            selected_columns = st.multiselect(
                "選擇要顯示的維度", 
                all_columns,
                default=all_columns[:5] if len(all_columns) > 5 else all_columns,
                key=f"{key_prefix}_dims"
            )
            
            # 選擇分組欄位
            categorical_columns = data.select_dtypes(include=['object']).columns.tolist()
            group_by = st.selectbox(
                "選擇分組欄位", 
                ["無"] + categorical_columns,
                key=f"{key_prefix}_group"
            )
            
            # 設定雷達圖刻度
            scale = st.slider("最大刻度", 1, 10, 5, key=f"{key_prefix}_scale")
            
            # 顯示雷達圖
            if selected_columns and group_by != "無":
                groups = data[group_by].unique().tolist()
                selected_groups = st.multiselect(
                    f"選擇要比較的{group_by}",
                    options=groups,
                    default=groups[:min(3, len(groups))],
                    key=f"{key_prefix}_groups"
                )
                
                if selected_groups:
                    config = RadarChartConfig(
                        title=title,
                        scale=scale
                    )
                    fig = self.radar_viz.create_comparison_radar_chart(
                        data, selected_columns, group_by, config, selected_groups
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("請至少選擇一個對象進行比較")
            else:
                st.warning("請選擇維度和分組欄位")

# 便利函數
def create_radar_chart(categories: List[str], 
                      values: List[float], 
                      title: str = "雷達圖", 
                      scale: int = 5) -> go.Figure:
    """便利函數：創建簡單雷達圖"""
    radar_viz = UnifiedRadarVisualization()
    config = RadarChartConfig(title=title, scale=scale)
    return radar_viz.create_simple_radar_chart(categories, values, config)

def create_epa_radar_chart(df: pd.DataFrame, 
                          plot_types: List[str] = None, 
                          student_id: str = None, 
                          title: str = "EPA 雷達圖") -> go.Figure:
    """便利函數：創建EPA雷達圖"""
    radar_viz = UnifiedRadarVisualization()
    config = EPAChartConfig(
        title=title,
        plot_types=plot_types or ['layers'],
        student_id=student_id
    )
    return radar_viz.create_epa_radar_chart(df, config)

def create_comparison_radar_chart(df: pd.DataFrame, 
                                 value_columns: List[str], 
                                 group_column: str, 
                                 title: str = "比較雷達圖", 
                                 scale: int = 5) -> go.Figure:
    """便利函數：創建比較雷達圖"""
    radar_viz = UnifiedRadarVisualization()
    config = RadarChartConfig(title=title, scale=scale)
    return radar_viz.create_comparison_radar_chart(df, value_columns, group_column, config)
