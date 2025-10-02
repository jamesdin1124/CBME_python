import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# 導入系統內建的統一雷達圖模組
try:
    from modules.visualization.unified_radar import (
        UnifiedRadarVisualization,
        RadarChartConfig,
        EPAChartConfig,
        create_radar_chart,
        create_epa_radar_chart,
        create_comparison_radar_chart
    )
    UNIFIED_RADAR_AVAILABLE = True
except ImportError:
    UNIFIED_RADAR_AVAILABLE = False

class FAMVisualization:
    """家醫部EPA資料視覺化"""
    
    def __init__(self):
        # 顏色配置
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#F18F01',
            'warning': '#C73E1D',
            'info': '#6A994E',
            'light': '#F2F2F2',
            'dark': '#2C3E50'
        }
        
        # EPA項目顏色對應
        self.epa_colors = {
            '02門診/社區衛教': '#FF6B6B',
            '03預防注射': '#4ECDC4',
            '05健康檢查': '#45B7D1',
            '07慢病照護': '#96CEB4',
            '08急症照護': '#FFEAA7',
            '09居家整合醫療': '#DDA0DD',
            '11末病照護/安寧緩和': '#98D8C8',
            '12家庭醫學科住院照護': '#F7DC6F',
            '13家庭醫學科門診照護': '#BB8FCE',
            '14社區醫學實習': '#85C1E9',
            '15預防醫學與健康促進': '#F8C471',
            '16家庭醫學科急診照護': '#82E0AA',
            '17長期照護': '#F1948A',
            '18家庭醫學科研習': '#85C1E9'
        }
    
    def create_epa_distribution_chart(self, epa_counts, title="EPA項目分布"):
        """創建EPA項目分布圖"""
        fig = px.bar(
            x=epa_counts.values,
            y=epa_counts.index,
            orientation='h',
            title=title,
            labels={'x': '評核次數', 'y': 'EPA項目'},
            color=epa_counts.values,
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(
            height=400,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_student_distribution_chart(self, student_counts, title="住院醫師評核分布"):
        """創建住院醫師分布圖"""
        fig = px.bar(
            x=student_counts.index,
            y=student_counts.values,
            title=title,
            labels={'x': '住院醫師', 'y': '評核次數'},
            color=student_counts.values,
            color_continuous_scale='blues'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_complexity_distribution_chart(self, complexity_counts, title="複雜程度分布"):
        """創建複雜度分布圖"""
        # 設定複雜度顏色
        complexity_colors = {'高': '#E74C3C', '中': '#F39C12', '低': '#27AE60'}
        
        fig = px.pie(
            values=complexity_counts.values,
            names=complexity_counts.index,
            title=title,
            color=complexity_counts.index,
            color_discrete_map=complexity_colors
        )
        
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_reliability_distribution_chart(self, reliability_counts, title="信賴程度分布"):
        """創建信賴程度分布圖"""
        # 設定信賴程度顏色
        reliability_colors = {
            '獨立執行': '#27AE60',
            '必要時知會教師確認': '#2ECC71',
            '教師在旁必要時協助': '#F39C12',
            '教師在旁逐步共同操作': '#E67E22',
            '學員在旁觀察': '#E74C3C'
        }
        
        fig = px.pie(
            values=reliability_counts.values,
            names=reliability_counts.index,
            title=title,
            color=reliability_counts.index,
            color_discrete_map=reliability_colors
        )
        
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_reliability_radar_chart(self, student_data, student_name, title="信賴程度雷達圖"):
        """創建信賴程度雷達圖 - 優先使用系統內建雷達圖功能"""
        if 'EPA項目' not in student_data.columns or '信賴程度(教師評量)' not in student_data.columns:
            return None
        
        # 優先使用系統內建的雷達圖功能
        if UNIFIED_RADAR_AVAILABLE:
            try:
                # 準備資料給系統內建的雷達圖
                epa_data = self._prepare_epa_data_for_unified_radar(student_data, student_name)
                
                if epa_data is not None:
                    # 為系統內建雷達圖準備適配的資料格式
                    adapted_df = self._adapt_data_for_unified_radar(student_data)
                    
                    if adapted_df is not None:
                        # 使用系統內建的EPA雷達圖
                        config = EPAChartConfig(
                            title=title,
                            scale=5,
                            show_legend=True,
                            student_id=student_name  # 使用正確的參數名稱
                        )
                        
                        radar_viz = UnifiedRadarVisualization()
                        # 使用正確的API參數
                        fig = radar_viz.create_epa_radar_chart(
                            df=adapted_df,  # 傳入適配後的DataFrame
                            config=config   # 傳入配置物件
                        )
                        
                        if fig:
                            return fig
            except Exception as e:
                # 在非Streamlit環境中避免使用st.warning
                try:
                    import streamlit as st
                    st.warning(f"使用系統內建雷達圖時發生錯誤，將使用自定義雷達圖：{str(e)}")
                except:
                    print(f"使用系統內建雷達圖時發生錯誤，將使用自定義雷達圖：{str(e)}")
        
        # 如果系統內建雷達圖不可用，使用自定義實現
        return self._create_custom_reliability_radar_chart(student_data, student_name, title)
    
    def _prepare_epa_data_for_unified_radar(self, student_data, student_name):
        """為系統內建雷達圖準備EPA資料"""
        # 獲取所有EPA項目
        all_epa_items = student_data['EPA項目'].unique()
        valid_epa_items = [item for item in all_epa_items if pd.notna(item) and str(item).strip() and str(item).strip() != '']
        
        if len(valid_epa_items) < 2:
            return None
        
        # 計算每個EPA項目的平均信賴程度
        epa_scores = {}
        for epa_item in valid_epa_items:
            epa_data = student_data[student_data['EPA項目'] == epa_item]
            
            # 優先使用已計算的數值欄位
            if '信賴程度(教師評量)_數值' in epa_data.columns:
                scores = epa_data['信賴程度(教師評量)_數值'].dropna()
            else:
                # 如果沒有數值欄位，使用文字轉換
                scores = []
                for _, row in epa_data.iterrows():
                    reliability = row['信賴程度(教師評量)']
                    if pd.notna(reliability) and str(reliability).strip():
                        score = self._convert_reliability_to_numeric(str(reliability).strip())
                        if score is not None:
                            scores.append(score)
            
            if len(scores) > 0:
                epa_scores[epa_item] = sum(scores) / len(scores)
            else:
                epa_scores[epa_item] = 1.0  # 預設1分
        
        # 確保所有可能的EPA項目都出現在雷達圖中（即使沒有數據也預設為1分）
        # 定義家醫部常見的EPA項目
        common_epa_items = [
            'EPA01.門診戒菸', 'EPA02.門診/社區衛教', 'EPA03.預防注射', 'EPA04.旅遊門診',
            'EPA05.健康檢查', 'EPA06.門診整合醫療', 'EPA07.慢病照護', 'EPA08.急症診療',
            'EPA09.居家整合醫療', 'EPA10.出院準備/照護轉銜', 'EPA11.未病照護/安寧緩和', 'EPA12.悲傷支持'
        ]
        
        # 為沒有數據的EPA項目添加預設分數
        for epa_item in common_epa_items:
            if epa_item not in epa_scores:
                epa_scores[epa_item] = 1.0  # 預設1分
        
        # 限制顯示的EPA項目數量
        if len(epa_scores) > 8:
            sorted_items = sorted(epa_scores.items(), key=lambda x: x[1], reverse=True)
            epa_scores = dict(sorted_items[:8])
        
        return epa_scores
    
    def _adapt_data_for_unified_radar(self, student_data):
        """適配資料格式給系統內建雷達圖"""
        try:
            # 創建適配後的DataFrame
            adapted_df = student_data.copy()
            
            # 重命名欄位以符合系統內建雷達圖的期望
            if 'EPA項目' in adapted_df.columns:
                adapted_df['EPA評核項目'] = adapted_df['EPA項目']
            
            # 確保有信賴程度數值欄位
            if '信賴程度(教師評量)_數值' in adapted_df.columns:
                adapted_df['教師評核EPA等級_數值'] = adapted_df['信賴程度(教師評量)_數值']
            else:
                # 如果沒有數值欄位，創建一個
                adapted_df['教師評核EPA等級_數值'] = adapted_df['信賴程度(教師評量)'].apply(
                    lambda x: self._convert_reliability_to_numeric(str(x)) if pd.notna(x) else None
                )
            
            # 確保有階層欄位（如果沒有，創建一個預設值）
            if '階層' not in adapted_df.columns:
                adapted_df['階層'] = '家醫部'
            
            # 確保有學員姓名欄位
            if '學員' in adapted_df.columns and '學員姓名' not in adapted_df.columns:
                adapted_df['學員姓名'] = adapted_df['學員']
            
            return adapted_df
            
        except Exception as e:
            print(f"適配資料時發生錯誤: {e}")
            return None
    
    def _create_custom_reliability_radar_chart(self, student_data, student_name, title):
        """創建自定義信賴程度雷達圖（備用方案）"""
        # 獲取所有EPA項目
        all_epa_items = student_data['EPA項目'].unique()
        valid_epa_items = [item for item in all_epa_items if pd.notna(item) and str(item).strip() and str(item).strip() != '']
        
        if len(valid_epa_items) < 2:
            return None
        
        # 計算每個EPA項目的平均信賴程度
        epa_scores = {}
        for epa_item in valid_epa_items:
            epa_data = student_data[student_data['EPA項目'] == epa_item]
            
            # 優先使用已計算的數值欄位
            if '信賴程度(教師評量)_數值' in epa_data.columns:
                scores = epa_data['信賴程度(教師評量)_數值'].dropna()
            else:
                # 如果沒有數值欄位，使用文字轉換
                scores = []
                for _, row in epa_data.iterrows():
                    reliability = row['信賴程度(教師評量)']
                    if pd.notna(reliability) and str(reliability).strip():
                        score = self._convert_reliability_to_numeric(str(reliability).strip())
                        if score is not None:
                            scores.append(score)
            
            if len(scores) > 0:
                epa_scores[epa_item] = sum(scores) / len(scores)
            else:
                epa_scores[epa_item] = 1.0  # 預設1分
        
        # 確保所有可能的EPA項目都出現在雷達圖中（即使沒有數據也預設為1分）
        # 定義家醫部常見的EPA項目
        common_epa_items = [
            'EPA01.門診戒菸', 'EPA02.門診/社區衛教', 'EPA03.預防注射', 'EPA04.旅遊門診',
            'EPA05.健康檢查', 'EPA06.門診整合醫療', 'EPA07.慢病照護', 'EPA08.急症診療',
            'EPA09.居家整合醫療', 'EPA10.出院準備/照護轉銜', 'EPA11.未病照護/安寧緩和', 'EPA12.悲傷支持'
        ]
        
        # 為沒有數據的EPA項目添加預設分數
        for epa_item in common_epa_items:
            if epa_item not in epa_scores:
                epa_scores[epa_item] = 1.0  # 預設1分
        
        # 準備雷達圖資料
        categories = list(epa_scores.keys())
        values = [epa_scores[epa] for epa in categories]
        
        # 限制顯示的EPA項目數量
        if len(categories) > 8:
            sorted_items = sorted(epa_scores.items(), key=lambda x: x[1], reverse=True)
            categories = [item[0] for item in sorted_items[:8]]
            values = [item[1] for item in sorted_items[:8]]
        
        # 縮短EPA項目名稱
        short_categories = []
        for cat in categories:
            if len(cat) > 15:
                short_categories.append(cat[:12] + "...")
            else:
                short_categories.append(cat)
        
        # 確保資料是閉合的
        categories_closed = short_categories + [short_categories[0]]
        values_closed = values + [values[0]]
        
        # 創建雷達圖
        fig = go.Figure()
        
        # 添加學員的數據
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            name=student_name,
            fill='toself',
            fillcolor='rgba(255, 0, 0, 0.2)',
            line=dict(color='rgba(255, 0, 0, 1)', width=2),
            hovertemplate='<b>%{theta}</b><br>信賴程度: %{r:.2f}<extra></extra>'
        ))
        
        # 更新布局
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    tickmode='linear',
                    tick0=0,
                    dtick=1,
                    tickfont=dict(size=12),
                    title=dict(text="信賴程度", font=dict(size=14))
                ),
                angularaxis=dict(
                    tickfont=dict(size=10)
                )
            ),
            title=title,
            height=500,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1.0,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            margin=dict(r=120),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode='closest'
        )
        
        return fig
    
    def _convert_reliability_to_numeric(self, reliability_text):
        """將信賴程度文字轉換為數值（5分制）"""
        if pd.isna(reliability_text) or reliability_text == '':
            return None
        
        reliability_text = str(reliability_text).strip()
        
        # 如果已經是數字，直接返回
        try:
            num_value = float(reliability_text)
            if 1 <= num_value <= 5:
                return num_value
        except (ValueError, TypeError):
            pass
        
        # 信賴程度數值映射（5分制）
        reliability_mapping = {
            '獨立執行': 5.0,
            '必要時知會教師確認': 4.0,
            '教師事後重點確認': 4.0,
            '教師在旁必要時協助': 3.0,
            '教師在旁逐步共同操作': 2.0,
            '學員在旁觀察': 1.0,
            '不允許學員觀察': 0.0,
            '請選擇': 0.0
        }
        
        return reliability_mapping.get(reliability_text, None)
    
    def create_epa_comparison_radar_chart(self, students_data, epa_item, title="EPA項目信賴程度比較雷達圖"):
        """創建EPA項目信賴程度比較雷達圖 - 支援同儕比較（使用名字）"""
        if 'EPA項目' not in students_data.columns or '學員' not in students_data.columns:
            return None
        
        if not epa_item or epa_item.strip() == '':
            return None
        
        # 計算每個學員在該EPA項目的平均信賴程度
        student_scores = {}
        for student in students_data['學員'].unique():
            if pd.notna(student) and student and str(student).strip():
                student_data = students_data[students_data['學員'] == student]
                epa_data = student_data[student_data['EPA項目'] == epa_item]
                
                reliability_scores = []
                for _, row in epa_data.iterrows():
                    # 優先使用已計算的數值欄位
                    if '信賴程度(教師評量)_數值' in row:
                        score = row['信賴程度(教師評量)_數值']
                        if pd.notna(score):
                            reliability_scores.append(score)
                    else:
                        # 如果沒有數值欄位，使用文字轉換
                        reliability = row['信賴程度(教師評量)']
                        if pd.notna(reliability) and str(reliability).strip():
                            score = self._convert_reliability_to_numeric(str(reliability).strip())
                            if score is not None:
                                reliability_scores.append(score)
                
                if reliability_scores:
                    student_scores[str(student).strip()] = sum(reliability_scores) / len(reliability_scores)
        
        if not student_scores or len(student_scores) < 2:
            return None  # 至少需要2個學員才能進行比較
        
        # 創建雷達圖（支援多學員同儕比較）
        fig = go.Figure()
        
        # 使用多色彩方案支援多學員比較
        colors = [
            'rgba(255, 0, 0, 1)',      # 紅色
            'rgba(0, 128, 0, 1)',      # 綠色
            'rgba(0, 0, 255, 1)',      # 藍色
            'rgba(255, 165, 0, 1)',    # 橙色
            'rgba(128, 0, 128, 1)',    # 紫色
            'rgba(255, 192, 203, 1)',  # 粉色
            'rgba(0, 255, 255, 1)',    # 青色
            'rgba(255, 20, 147, 1)'    # 深粉色
        ]
        
        fill_colors = [
            'rgba(255, 0, 0, 0.2)',    # 紅色填充
            'rgba(0, 128, 0, 0.2)',    # 綠色填充
            'rgba(0, 0, 255, 0.2)',    # 藍色填充
            'rgba(255, 165, 0, 0.2)',  # 橙色填充
            'rgba(128, 0, 128, 0.2)',  # 紫色填充
            'rgba(255, 192, 203, 0.2)', # 粉色填充
            'rgba(0, 255, 255, 0.2)',  # 青色填充
            'rgba(255, 20, 147, 0.2)'  # 深粉色填充
        ]
        
        # 縮短EPA項目名稱
        short_epa_name = epa_item[:15] + "..." if len(epa_item) > 15 else epa_item
        
        # 為每個學員創建雷達圖數據點
        for i, (student_name, score) in enumerate(student_scores.items()):
            color_idx = i % len(colors)
            
            # 為單個EPA項目創建閉合的雷達圖（三角形）
            fig.add_trace(go.Scatterpolar(
                r=[score, score, score],  # 三個點形成三角形
                theta=[short_epa_name, short_epa_name, short_epa_name],
                fill='toself',
                name=student_name,  # 使用學員名字
                line=dict(color=colors[color_idx], width=3),
                fillcolor=fill_colors[color_idx],
                hovertemplate='<b>%{fullData.name}</b><br>%{theta}<br>信賴程度: %{r:.2f}<extra></extra>',
                showlegend=True
            ))
        
        # 更新布局
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],  # 使用5分制
                    tickmode='linear',
                    tick0=0,
                    dtick=1,
                    tickfont=dict(size=12),
                    title=dict(text="信賴程度", font=dict(size=14))
                )
            ),
            title=title,
            height=500,  # 增加高度以容納更多學員
            showlegend=True,
            legend=dict(
                orientation="v",  # 垂直排列
                yanchor="top",
                y=1.0,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="rgba(0,0,0,0.3)",
                borderwidth=1,
                font=dict(size=10)
            ),
            margin=dict(r=140),  # 增加右邊距，為圖例留出更多空間
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode='closest'
        )
        
        return fig
    
    def create_all_epa_comparison_radar_chart(self, students_data, title="全部EPA項目信賴程度比較雷達圖"):
        """創建包含所有EPA項目的同儕比較雷達圖"""
        if 'EPA項目' not in students_data.columns or '學員' not in students_data.columns:
            return None
        
        # 獲取所有學員和所有EPA項目
        all_students = students_data['學員'].unique()
        all_epa_items = students_data['EPA項目'].unique()
        valid_epa_items = [item for item in all_epa_items if pd.notna(item) and str(item).strip() and str(item).strip() != '']
        
        if len(all_students) < 2 or len(valid_epa_items) < 2:
            return None
        
        # 計算每個學員在所有EPA項目的平均信賴程度
        student_epa_scores = {}
        
        for student in all_students:
            if pd.notna(student) and student and str(student).strip():
                student_data = students_data[students_data['學員'] == student]
                epa_scores = {}
                
                for epa_item in valid_epa_items:
                    epa_data = student_data[student_data['EPA項目'] == epa_item]
                    
                    reliability_scores = []
                    for _, row in epa_data.iterrows():
                        # 優先使用已計算的數值欄位
                        if '信賴程度(教師評量)_數值' in row:
                            score = row['信賴程度(教師評量)_數值']
                            if pd.notna(score):
                                reliability_scores.append(score)
                        else:
                            # 如果沒有數值欄位，使用文字轉換
                            reliability = row['信賴程度(教師評量)']
                            if pd.notna(reliability) and str(reliability).strip():
                                score = self._convert_reliability_to_numeric(str(reliability).strip())
                                if score is not None:
                                    reliability_scores.append(score)
                    
                    if reliability_scores:
                        epa_scores[epa_item] = sum(reliability_scores) / len(reliability_scores)
                    else:
                        epa_scores[epa_item] = 1.0  # 預設1分
                
                student_epa_scores[str(student).strip()] = epa_scores
        
        if not student_epa_scores:
            return None
        
        # 創建雷達圖
        fig = go.Figure()
        
        # 使用多色彩方案支援多學員比較
        colors = [
            'rgba(255, 0, 0, 1)',      # 紅色
            'rgba(0, 128, 0, 1)',      # 綠色
            'rgba(0, 0, 255, 1)',      # 藍色
            'rgba(255, 165, 0, 1)',    # 橙色
            'rgba(128, 0, 128, 1)',    # 紫色
            'rgba(255, 192, 203, 1)',  # 粉色
            'rgba(0, 255, 255, 1)',    # 青色
            'rgba(255, 20, 147, 1)',   # 深粉色
            'rgba(50, 205, 50, 1)',    # 淺綠色
            'rgba(255, 69, 0, 1)'      # 橙紅色
        ]
        
        fill_colors = [
            'rgba(255, 0, 0, 0.2)',    # 紅色填充
            'rgba(0, 128, 0, 0.2)',    # 綠色填充
            'rgba(0, 0, 255, 0.2)',    # 藍色填充
            'rgba(255, 165, 0, 0.2)',  # 橙色填充
            'rgba(128, 0, 128, 0.2)',  # 紫色填充
            'rgba(255, 192, 203, 0.2)', # 粉色填充
            'rgba(0, 255, 255, 0.2)',  # 青色填充
            'rgba(255, 20, 147, 0.2)', # 深粉色填充
            'rgba(50, 205, 50, 0.2)',  # 淺綠色填充
            'rgba(255, 69, 0, 0.2)'    # 橙紅色填充
        ]
        
        # 縮短EPA項目名稱以便顯示
        short_epa_names = []
        for epa_item in valid_epa_items:
            if len(epa_item) > 15:
                short_epa_names.append(epa_item[:12] + "...")
            else:
                short_epa_names.append(epa_item)
        
        # 為每個學員創建雷達圖數據
        for i, (student_name, epa_scores) in enumerate(student_epa_scores.items()):
            color_idx = i % len(colors)
            
            # 準備數據
            values = []
            for epa_item in valid_epa_items:
                values.append(epa_scores.get(epa_item, 1.0))
            
            # 確保資料是閉合的
            values_closed = values + [values[0]]
            categories_closed = short_epa_names + [short_epa_names[0]]
            
            # 添加學員的雷達圖
            fig.add_trace(go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill='toself',
                name=student_name,
                line=dict(color=colors[color_idx], width=2),
                fillcolor=fill_colors[color_idx],
                hovertemplate='<b>%{fullData.name}</b><br>%{theta}<br>信賴程度: %{r:.2f}<extra></extra>',
                showlegend=True
            ))
        
        # 更新布局
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],  # 使用5分制
                    tickmode='linear',
                    tick0=0,
                    dtick=1,
                    tickfont=dict(size=12),
                    title=dict(text="信賴程度", font=dict(size=14))
                ),
                angularaxis=dict(
                    tickfont=dict(size=10)
                )
            ),
            title=title,
            height=600,  # 增加高度以容納更多學員
            showlegend=True,
            legend=dict(
                orientation="v",  # 垂直排列
                yanchor="top",
                y=1.0,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="rgba(0,0,0,0.3)",
                borderwidth=1,
                font=dict(size=10)
            ),
            margin=dict(r=150),  # 增加右邊距，為圖例留出更多空間
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode='closest'
        )
        
        return fig
    
    def create_epa_monthly_trend_chart(self, monthly_trend_data, epa_item, student_name):
        """創建EPA項目月度趨勢折線圖
        
        Args:
            monthly_trend_data: 月度趨勢數據
            epa_item: EPA項目名稱
            student_name: 學員姓名
            
        Returns:
            plotly.graph_objects.Figure: 趨勢圖物件
        """
        try:
            if monthly_trend_data is None or monthly_trend_data.empty:
                return None
            
            # 創建折線圖
            fig = go.Figure()
            
            # 添加主趨勢線
            fig.add_trace(go.Scatter(
                x=monthly_trend_data['年月_顯示'],
                y=monthly_trend_data['平均信賴程度'],
                mode='lines+markers',
                name='平均信賴程度',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8, color='#1f77b4'),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             '月份: %{x}<br>' +
                             '平均信賴程度: %{y:.2f}<br>' +
                             '<extra></extra>'
            ))
            
            # 添加評核次數作為次要Y軸
            fig.add_trace(go.Scatter(
                x=monthly_trend_data['年月_顯示'],
                y=monthly_trend_data['評核次數'],
                mode='lines+markers',
                name='評核次數',
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                marker=dict(size=6, color='#ff7f0e'),
                yaxis='y2',
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             '月份: %{x}<br>' +
                             '評核次數: %{y}<br>' +
                             '<extra></extra>'
            ))
            
            # 更新布局
            fig.update_layout(
                title=dict(
                    text=f"{student_name} - {epa_item} 信賴程度趨勢",
                    x=0.5,
                    font=dict(size=16, color='#2c3e50')
                ),
                xaxis=dict(
                    title="月份",
                    showgrid=True,
                    gridcolor='rgba(128,128,128,0.2)',
                    tickangle=45
                ),
                yaxis=dict(
                    title="平均信賴程度",
                    side="left",
                    range=[0, 5.2],
                    tickmode='linear',
                    tick0=0,
                    dtick=1,
                    showgrid=True,
                    gridcolor='rgba(128,128,128,0.2)',
                    titlefont=dict(color='#1f77b4'),
                    tickfont=dict(color='#1f77b4')
                ),
                yaxis2=dict(
                    title="評核次數",
                    side="right",
                    overlaying="y",
                    showgrid=False,
                    titlefont=dict(color='#ff7f0e'),
                    tickfont=dict(color='#ff7f0e')
                ),
                height=400,
                margin=dict(t=60, b=60, l=60, r=60),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="rgba(0,0,0,0.3)",
                    borderwidth=1
                )
            )
            
            # 添加趨勢線（如果數據點足夠）
            if len(monthly_trend_data) >= 2:
                # 計算線性回歸趨勢
                x_numeric = range(len(monthly_trend_data))
                y_values = monthly_trend_data['平均信賴程度'].values
                
                # 簡單線性回歸
                n = len(x_numeric)
                sum_x = sum(x_numeric)
                sum_y = sum(y_values)
                sum_xy = sum(x * y for x, y in zip(x_numeric, y_values))
                sum_x2 = sum(x * x for x in x_numeric)
                
                if n * sum_x2 - sum_x * sum_x != 0:
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                    intercept = (sum_y - slope * sum_x) / n
                    
                    # 添加趨勢線
                    trend_y = [slope * x + intercept for x in x_numeric]
                    
                    fig.add_trace(go.Scatter(
                        x=monthly_trend_data['年月_顯示'],
                        y=trend_y,
                        mode='lines',
                        name='趨勢線',
                        line=dict(color='rgba(255,0,0,0.6)', width=2, dash='dot'),
                        hovertemplate='<b>趨勢線</b><br>' +
                                     '月份: %{x}<br>' +
                                     '預測信賴程度: %{y:.2f}<br>' +
                                     '<extra></extra>'
                    ))
            
            return fig
            
        except Exception as e:
            print(f"創建EPA月度趨勢圖時發生錯誤: {e}")
            import traceback
            print(f"詳細錯誤信息: {traceback.format_exc()}")
            return None
    
    def create_enhanced_monthly_trend_chart(self, epa_data, epa_item, student_name):
        """創建增強版EPA項目信賴程度趨勢圖，合併兩個系統資料並顯示平均值和標準差"""
        try:
            if epa_data is None or epa_data.empty:
                return None
            
            import plotly.express as px
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            import pandas as pd
            import numpy as np
            
            # 準備數據
            plot_records = []
            
            for _, row in epa_data.iterrows():
                date = row['日期']
                if pd.notna(date):
                    try:
                        date_obj = pd.to_datetime(date)
                        month_str = f"{date_obj.year}年{date_obj.month:02d}月"
                        
                        # 獲取信賴程度數值
                        if '信賴程度(教師評量)_數值' in row:
                            score = row['信賴程度(教師評量)_數值']
                        else:
                            reliability = row['信賴程度(教師評量)']
                            if pd.notna(reliability) and str(reliability).strip():
                                score = self._convert_reliability_to_numeric(str(reliability).strip())
                            else:
                                score = None
                        
                        if pd.notna(score):
                            # 獲取資料來源
                            data_source = row.get('資料來源', '未知來源')
                            
                            plot_records.append({
                                '月份': month_str,
                                '信賴程度': float(score),
                                '資料來源': data_source,
                                '日期': date_obj,
                                '原始日期': date
                            })
                    except:
                        continue
            
            if not plot_records:
                return None
            
            # 轉換為DataFrame
            df_plot = pd.DataFrame(plot_records)
            df_plot = df_plot.sort_values('日期')
            
            # 創建圖表
            fig = go.Figure()
            
            # 合併所有資料來源，按月份計算平均值和標準差
            monthly_stats = df_plot.groupby('月份')['信賴程度'].agg(['mean', 'std', 'count']).reset_index()
            monthly_stats = monthly_stats.sort_values('月份')
            
            # 處理標準差為NaN的情況（只有一個數據點時）
            monthly_stats['std'] = monthly_stats['std'].fillna(0)
            
            # 添加平均值折線
            fig.add_trace(go.Scatter(
                x=monthly_stats['月份'],
                y=monthly_stats['mean'],
                mode='lines+markers',
                name='平均值',
                line=dict(color='#2E86AB', width=3, shape='spline'),
                marker=dict(size=8, color='#2E86AB'),
                hovertemplate='<b>平均值</b><br>' +
                             '月份: %{x}<br>' +
                             '平均信賴程度: %{y:.2f}<br>' +
                             '樣本數: %{customdata}<br>' +
                             '<extra></extra>',
                customdata=monthly_stats['count']
            ))
            
            # 添加標準差上下限區域
            upper_bound = monthly_stats['mean'] + monthly_stats['std']
            lower_bound = monthly_stats['mean'] - monthly_stats['std']
            
            # 確保上下限在合理範圍內
            upper_bound = np.clip(upper_bound, 0, 5)
            lower_bound = np.clip(lower_bound, 0, 5)
            
            # 添加標準差區域（填充）
            fig.add_trace(go.Scatter(
                x=monthly_stats['月份'].tolist() + monthly_stats['月份'].tolist()[::-1],
                y=upper_bound.tolist() + lower_bound.tolist()[::-1],
                fill='toself',
                fillcolor='rgba(46, 134, 171, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='±1標準差',
                hoverinfo='skip'
            ))
            
            # 添加上標準差線
            fig.add_trace(go.Scatter(
                x=monthly_stats['月份'],
                y=upper_bound,
                mode='lines',
                name='+1標準差',
                line=dict(color='rgba(46, 134, 171, 0.6)', width=1, dash='dash'),
                hoverinfo='skip'
            ))
            
            # 添加下標準差線
            fig.add_trace(go.Scatter(
                x=monthly_stats['月份'],
                y=lower_bound,
                mode='lines',
                name='-1標準差',
                line=dict(color='rgba(46, 134, 171, 0.6)', width=1, dash='dash'),
                hoverinfo='skip'
            ))
            
            # 添加所有原始數據點（透明，僅用於顯示數據分布）
            for i, (_, row) in enumerate(df_plot.iterrows()):
                fig.add_trace(go.Scatter(
                    x=[row['月份']],
                    y=[row['信賴程度']],
                    mode='markers',
                    marker=dict(
                        size=4,
                        color='rgba(128, 128, 128, 0.3)',
                        symbol='circle'
                    ),
                    name='原始數據' if i == 0 else '',
                    showlegend=i == 0,
                    hovertemplate='<b>原始數據</b><br>' +
                                 '月份: %{x}<br>' +
                                 '信賴程度: %{y}<br>' +
                                 '來源: ' + row['資料來源'] + '<br>' +
                                 '<extra></extra>'
                ))
            
            # 更新布局
            fig.update_layout(
                title=f'{student_name} - {epa_item} 信賴程度趨勢分析',
                xaxis_title='月份',
                yaxis_title='信賴程度',
                yaxis=dict(range=[0, 5.5], tickmode='linear', tick0=0, dtick=1),
                height=400,
                showlegend=True,
                hovermode='closest',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # 添加水平參考線
            for level in [1, 2, 3, 4, 5]:
                fig.add_hline(
                    y=level,
                    line_dash="dash",
                    line_color="gray",
                    opacity=0.3,
                    annotation_text=f"等級 {level}" if level in [1, 5] else None
                )
            
            return fig
            
        except Exception as e:
            print(f"創建增強版趨勢圖時發生錯誤: {e}")
            import traceback
            print(f"詳細錯誤信息: {traceback.format_exc()}")
            return None
    
    def create_simple_monthly_trend_chart(self, monthly_trend_data, epa_item, student_name, epa_data=None):
        """創建EPA項目信賴程度箱線圖（Boxplot）"""
        try:
            if monthly_trend_data is None or monthly_trend_data.empty:
                return None
            
            import plotly.express as px
            import pandas as pd
            import numpy as np
            
            # 準備原始數據用於boxplot
            boxplot_records = []
            
            if epa_data is not None and not epa_data.empty and '日期' in epa_data.columns:
                # 使用原始數據創建boxplot
                for _, row in epa_data.iterrows():
                    date = row['日期']
                    if pd.notna(date):
                        # 轉換日期格式
                        try:
                            date_obj = pd.to_datetime(date)
                            month_str = f"{date_obj.year}年{date_obj.month:02d}月"
                            
                            # 獲取信賴程度數值
                            if '信賴程度(教師評量)_數值' in row:
                                score = row['信賴程度(教師評量)_數值']
                                if pd.notna(score):
                                    boxplot_records.append({
                                        '月份': month_str,
                                        '信賴程度': float(score)
                                    })
                            else:
                                reliability = row['信賴程度(教師評量)']
                                if pd.notna(reliability) and str(reliability).strip():
                                    score = self._convert_reliability_to_numeric(str(reliability).strip())
                                    if score is not None:
                                        boxplot_records.append({
                                            '月份': month_str,
                                            '信賴程度': float(score)
                                        })
                        except:
                            continue
            
            # 如果沒有原始數據，使用月度平均值創建模擬數據
            if len(boxplot_records) == 0:  # 只有完全沒有原始數據時才使用模擬數據
                boxplot_records = []
                for _, row in monthly_trend_data.iterrows():
                    month = row['年月_顯示']
                    avg_score = row['平均信賴程度']
                    count = int(row['評核次數'])
                    
                    # 為每個月創建模擬的數據點
                    for i in range(count):
                        # 添加小幅隨機變化
                        variation = np.random.normal(0, 0.1)  # 標準差0.1的正態分布
                        simulated_score = max(0, min(5, avg_score + variation))  # 限制在0-5範圍內
                        boxplot_records.append({
                            '月份': month,
                            '信賴程度': simulated_score
                        })
            
            if boxplot_records:
                # 創建DataFrame
                boxplot_df = pd.DataFrame(boxplot_records)
                
                # 確保月份順序正確，包含所有月份（沒有數據的月份也會顯示）
                month_order = ['2025年01月', '2025年02月', '2025年03月', '2025年04月', '2025年05月', '2025年06月', 
                              '2025年07月', '2025年08月', '2025年09月', '2025年10月', '2025年11月', '2025年12月']
                boxplot_df['月份'] = pd.Categorical(boxplot_df['月份'], categories=month_order, ordered=True)
                boxplot_df = boxplot_df.sort_values('月份')
                
                # 創建boxplot
                fig = px.box(
                    boxplot_df,
                    x='月份',
                    y='信賴程度',
                    title=f"{student_name} - {epa_item} 信賴程度分布（箱線圖）",
                    points="all",  # 顯示所有數據點
                    notched=False  # 關閉置信區間
                )
                
                # 更新布局
                fig.update_layout(
                    height=400,
                    xaxis_title="月份",
                    yaxis_title="信賴程度",
                    yaxis=dict(range=[0, 5.2]),
                    showlegend=False,
                    boxmode='group'
                )
                
                # 確保X軸顯示所有月份（包括沒有數據的月份）
                fig.update_xaxes(
                    categoryorder='array',
                    categoryarray=month_order,
                    tickangle=45  # 旋轉標籤避免重疊
                )
                
                # 自定義箱線圖顏色
                fig.update_traces(
                    marker_color='rgba(55,128,191,0.8)',
                    marker_line_color='rgba(55,128,191,1)',
                    marker_line_width=1,
                    line_color='rgba(55,128,191,1)',
                    line_width=2
                )
                
                return fig
            
            return None
            
        except Exception as e:
            print(f"創建EPA信賴程度箱線圖時發生錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return None
    
    def create_epa_progress_chart(self, progress_df, student_name):
        """創建EPA項目完成進度圖"""
        fig = px.bar(
            progress_df,
            x='EPA項目',
            y='完成率(%)',
            title=f"{student_name} - EPA項目完成率",
            color='完成率(%)',
            color_continuous_scale='RdYlGn'
        )
        
        # 添加100%完成線
        fig.add_hline(y=100, line_dash="dash", line_color="red", 
                     annotation_text="完成標準", annotation_position="top right")
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_temporal_progress_chart(self, monthly_data, title="學習進度時間軸"):
        """創建時間序列進度圖"""
        fig = px.line(
            monthly_data,
            x='月份',
            y='評核次數',
            title=title,
            markers=True
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_epa_temporal_chart(self, epa_data, epa_item, student_name):
        """創建特定EPA項目的時間進度圖"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                f"{epa_item} - 累積完成次數",
                f"{epa_item} - 信賴程度變化"
            ),
            vertical_spacing=0.15
        )
        
        # 累積完成次數
        fig.add_trace(
            go.Scatter(
                x=epa_data['日期'],
                y=epa_data['累積次數'],
                mode='lines+markers',
                name='累積完成次數',
                line=dict(color=self.colors['primary'], width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # 信賴程度變化（如果有資料）
        if '信賴程度數值' in epa_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=epa_data['日期'],
                    y=epa_data['信賴程度數值'],
                    mode='lines+markers',
                    name='信賴程度',
                    line=dict(color=self.colors['secondary'], width=3),
                    marker=dict(size=8)
                ),
                row=2, col=1
            )
            
            # 設定信賴程度Y軸
            fig.update_yaxes(
                tickmode='linear',
                tick0=1,
                dtick=1,
                title_text="信賴程度",
                row=2, col=1
            )
        
        fig.update_layout(
            height=600,
            title_text=f"{student_name} - {epa_item} 學習進度",
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        fig.update_xaxes(title_text="日期", row=2, col=1)
        fig.update_yaxes(title_text="累積次數", row=1, col=1)
        
        return fig
    
    def create_complexity_challenge_chart(self, complexity_data, student_name):
        """創建複雜度挑戰圖"""
        complexity_colors = {'高': '#E74C3C', '中': '#F39C12', '低': '#27AE60'}
        
        fig = px.bar(
            x=complexity_data.index,
            y=complexity_data.values,
            title=f"{student_name} - 複雜度挑戰分布",
            color=complexity_data.index,
            color_discrete_map=complexity_colors
        )
        
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="複雜程度",
            yaxis_title="完成次數"
        )
        
        return fig
    
    def create_epa_comparison_chart(self, students_data, epa_item):
        """創建EPA項目同儕比較圖"""
        fig = px.bar(
            x=students_data.index,
            y=students_data.values,
            title=f"各住院醫師 - {epa_item} 完成次數比較",
            color=students_data.values,
            color_continuous_scale='blues'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="住院醫師",
            yaxis_title="完成次數"
        )
        
        return fig
    
    def create_reliability_trend_chart(self, reliability_data, student_name):
        """創建信賴程度趨勢圖"""
        fig = px.line(
            x=reliability_data.index,
            y=reliability_data.values,
            title=f"{student_name} - 信賴程度趨勢",
            markers=True
        )
        
        fig.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="時間",
            yaxis_title="平均信賴程度"
        )
        
        return fig
    
    def create_dashboard_overview(self, stats):
        """創建儀表板概覽圖"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "總評核記錄數",
                "住院醫師人數",
                "EPA項目種類",
                "評核教師人數"
            ),
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}]]
        )
        
        # 總評核記錄數
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=stats['total_records'],
                title={"text": "總評核記錄數"},
                domain={'row': 0, 'column': 0}
            )
        )
        
        # 住院醫師人數
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=stats['unique_students'],
                title={"text": "住院醫師人數"},
                domain={'row': 0, 'column': 1}
            )
        )
        
        # EPA項目種類
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=stats['unique_epa_items'],
                title={"text": "EPA項目種類"},
                domain={'row': 1, 'column': 0}
            )
        )
        
        # 評核教師人數
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=stats['unique_teachers'],
                title={"text": "評核教師人數"},
                domain={'row': 1, 'column': 1}
            )
        )
        
        fig.update_layout(
            height=400,
            title_text="家醫部EPA評核系統概覽",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_heatmap_chart(self, heatmap_data, title="EPA項目完成熱力圖"):
        """創建EPA項目完成熱力圖"""
        fig = px.imshow(
            heatmap_data,
            title=title,
            color_continuous_scale='RdYlGn',
            aspect='auto'
        )
        
        fig.update_layout(
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_reliability_boxplot(self, student_data, student_name):
        """創建信賴程度分布箱線圖"""
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # 準備信賴程度數據
            reliability_data = []
            
            if '信賴程度(教師評量)' in student_data.columns:
                for _, row in student_data.iterrows():
                    reliability_text = row['信賴程度(教師評量)']
                    if pd.notna(reliability_text) and str(reliability_text).strip():
                        # 轉換為數值
                        numeric_value = self._convert_reliability_to_numeric(str(reliability_text).strip())
                        if numeric_value is not None:
                            reliability_data.append({
                                '信賴程度數值': numeric_value,
                                '信賴程度文字': str(reliability_text).strip(),
                                'EPA項目': row.get('EPA項目', 'N/A'),
                                '日期': row.get('日期', 'N/A')
                            })
            
            if not reliability_data:
                return None
            
            # 創建DataFrame
            reliability_df = pd.DataFrame(reliability_data)
            
            # 創建子圖：左側箱線圖，右側分布統計
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('信賴程度分布箱線圖', '信賴程度統計'),
                specs=[[{"type": "box"}, {"type": "table"}]],
                horizontal_spacing=0.1
            )
            
            # 添加箱線圖
            fig.add_trace(
                go.Box(
                    y=reliability_df['信賴程度數值'],
                    name='信賴程度',
                    boxpoints='all',  # 顯示所有數據點
                    jitter=0.3,
                    pointpos=-1.8,
                    marker=dict(
                        color='rgba(55,128,191,0.8)',
                        line=dict(color='rgba(55,128,191,1)', width=1)
                    ),
                    line=dict(color='rgba(55,128,191,1)', width=2)
                ),
                row=1, col=1
            )
            
            # 計算統計數據
            stats_data = []
            stats_data.append(['平均信賴程度', f"{reliability_df['信賴程度數值'].mean():.2f}"])
            stats_data.append(['中位數', f"{reliability_df['信賴程度數值'].median():.2f}"])
            stats_data.append(['標準差', f"{reliability_df['信賴程度數值'].std():.2f}"])
            stats_data.append(['最小值', f"{reliability_df['信賴程度數值'].min():.2f}"])
            stats_data.append(['最大值', f"{reliability_df['信賴程度數值'].max():.2f}"])
            stats_data.append(['總評核次數', str(len(reliability_df))])
            
            # 添加統計表格
            fig.add_trace(
                go.Table(
                    header=dict(
                        values=['統計項目', '數值'],
                        fill_color='rgba(240,240,240,0.8)',
                        align='center',
                        font=dict(size=12, color='black')
                    ),
                    cells=dict(
                        values=list(zip(*stats_data)),
                        fill_color='rgba(255,255,255,0.8)',
                        align='center',
                        font=dict(size=11)
                    )
                ),
                row=1, col=2
            )
            
            # 更新布局
            fig.update_layout(
                title=f"{student_name} - 信賴程度分布分析",
                height=400,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            # 更新箱線圖的Y軸
            fig.update_yaxes(
                title_text="信賴程度數值",
                range=[0, 5.2],
                tickmode='linear',
                tick0=0,
                dtick=1,
                row=1, col=1
            )
            
            # 更新箱線圖的X軸
            fig.update_xaxes(
                title_text="信賴程度分布",
                row=1, col=1
            )
            
            return fig
            
        except Exception as e:
            print(f"創建信賴程度箱線圖時發生錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return None
    
    def _convert_reliability_to_numeric(self, reliability_text):
        """將信賴程度文字轉換為數值（5分制）"""
        if pd.isna(reliability_text) or reliability_text == '':
            return None
        
        reliability_text = str(reliability_text).strip()
        
        # 如果已經是數字，直接返回
        try:
            num_value = float(reliability_text)
            if 1 <= num_value <= 5:
                return num_value
        except (ValueError, TypeError):
            pass
        
        # 信賴程度數值映射（5分制）
        reliability_mapping = {
            '獨立執行': 5.0,
            '必要時知會教師確認': 4.0,
            '教師事後重點確認': 3.0,
            '教師在旁必要時協助': 2.0,
            '教師在旁逐步共同操作': 1.0,
            '學員在旁觀察': 0.0,
            '不允許學員觀察': 0.0,
            '請選擇': 0.0
        }
        
        return reliability_mapping.get(reliability_text, None)
    
    def create_student_epa_scores_boxplot(self, df):
        """創建每個住院醫師整體EPA分數的boxplot"""
        try:
            import plotly.express as px
            import pandas as pd
            import numpy as np
            
            # 準備每個住院醫師的EPA分數數據
            student_epa_data = []
            
            # 獲取所有住院醫師
            students = df['學員'].unique()
            
            for student in students:
                if pd.notna(student) and str(student).strip() != '' and str(student).strip() != 'nan' and str(student).strip() != '學員':
                    student_df = df[df['學員'] == student]
                    
                    # 計算該住院醫師的所有EPA分數
                    if '信賴程度(教師評量)' in student_df.columns:
                        for _, row in student_df.iterrows():
                            reliability_text = row['信賴程度(教師評量)']
                            if pd.notna(reliability_text) and str(reliability_text).strip():
                                # 轉換為數值
                                numeric_value = self._convert_reliability_to_numeric(str(reliability_text).strip())
                                if numeric_value is not None:
                                    student_epa_data.append({
                                        '住院醫師': str(student).strip(),
                                        'EPA分數': numeric_value,
                                        'EPA項目': row.get('EPA項目', 'N/A')
                                    })
            
            if not student_epa_data:
                return None
            
            # 創建DataFrame
            student_epa_df = pd.DataFrame(student_epa_data)
            
            # 創建boxplot
            fig = px.box(
                student_epa_df,
                x='住院醫師',
                y='EPA分數',
                title="各住院醫師EPA分數分布箱線圖",
                points="all",  # 顯示所有數據點
                notched=False  # 關閉置信區間
            )
            
            # 更新布局
            fig.update_layout(
                height=500,
                xaxis_title="住院醫師",
                yaxis_title="EPA分數",
                yaxis=dict(range=[0, 5.2]),
                showlegend=False,
                boxmode='group'
            )
            
            # 自定義箱線圖顏色
            fig.update_traces(
                marker_color='rgba(55,128,191,0.8)',
                marker_line_color='rgba(55,128,191,1)',
                marker_line_width=1,
                line_color='rgba(55,128,191,1)',
                line_width=2
            )
            
            # 旋轉X軸標籤以避免重疊
            fig.update_xaxes(tickangle=45)
            
            return fig
            
        except Exception as e:
            print(f"創建住院醫師EPA分數boxplot時發生錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return None
    
    def create_student_epa_scores_line_chart(self, df):
        """創建每個住院醫師EPA分數隨時間變化的折線圖"""
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            import pandas as pd
            import numpy as np
            
            # 準備每個住院醫師的EPA分數時間序列數據
            line_data = []
            
            # 獲取所有住院醫師
            students = df['學員'].unique()
            
            for student in students:
                if pd.notna(student) and str(student).strip() != '' and str(student).strip() != 'nan' and str(student).strip() != '學員':
                    student_df = df[df['學員'] == student]
                    
                    # 按日期排序
                    if '日期' in student_df.columns:
                        student_df = student_df.sort_values('日期')
                        
                        # 計算每個日期的平均EPA分數
                        date_scores = {}
                        for _, row in student_df.iterrows():
                            date = row['日期']
                            if pd.notna(date):
                                # 轉換為日期字符串
                                if hasattr(date, 'strftime'):
                                    date_str = date.strftime('%Y-%m-%d')
                                else:
                                    date_str = str(date)
                                
                                # 獲取EPA分數
                                if '信賴程度(教師評量)_數值' in row and pd.notna(row['信賴程度(教師評量)_數值']):
                                    score = row['信賴程度(教師評量)_數值']
                                else:
                                    reliability_text = row.get('信賴程度(教師評量)', '')
                                    if pd.notna(reliability_text) and str(reliability_text).strip():
                                        score = self._convert_reliability_to_numeric(str(reliability_text).strip())
                                    else:
                                        score = None
                                
                                if score is not None:
                                    if date_str not in date_scores:
                                        date_scores[date_str] = []
                                    date_scores[date_str].append(score)
                        
                        # 計算每個日期的平均分數
                        for date_str, scores in date_scores.items():
                            if scores:
                                avg_score = sum(scores) / len(scores)
                                line_data.append({
                                    '日期': date_str,
                                    'EPA分數': avg_score,
                                    '住院醫師': str(student).strip()
                                })
            
            if not line_data:
                return None
            
            # 創建DataFrame
            line_df = pd.DataFrame(line_data)
            
            # 轉換日期為datetime類型
            line_df['日期'] = pd.to_datetime(line_df['日期'])
            line_df = line_df.sort_values('日期')
            
            # 創建折線圖
            fig = go.Figure()
            
            # 為每個住院醫師添加一條線
            students = line_df['住院醫師'].unique()
            # 使用更鮮明、對比度更高的顏色
            colors = [
                '#FF0000',  # 紅色 - 鮮明
                '#0000FF',  # 藍色 - 鮮明
                '#00AA00',  # 綠色 - 鮮明
                '#AA00AA',  # 紫色 - 鮮明
                '#FF8800',  # 橙色 - 鮮明
                '#0066CC',  # 深藍色 - 鮮明
                '#CC6600',  # 深橙色 - 鮮明
                '#990099',  # 深紫色 - 鮮明
                '#009900',  # 深綠色 - 鮮明
                '#CC0000'   # 深紅色 - 鮮明
            ]
            
            for i, student in enumerate(students):
                student_data = line_df[line_df['住院醫師'] == student]
                color = colors[i % len(colors)]
                
                fig.add_trace(go.Scatter(
                    x=student_data['日期'],
                    y=student_data['EPA分數'],
                    mode='lines+markers',
                    name=student,
                    line=dict(color=color, width=3),  # 增加線條寬度
                    marker=dict(
                        size=8,  # 增加標記大小
                        color=color,
                        line=dict(width=2, color='white')  # 添加白色邊框增加對比度
                    ),
                    hovertemplate=f'<b>{student}</b><br>' +
                                 '日期: %{x}<br>' +
                                 'EPA分數: %{y:.2f}<extra></extra>'
                ))
            
            # 更新布局
            fig.update_layout(
                title="各住院醫師EPA分數隨時間變化趨勢",
                xaxis_title="日期",
                yaxis_title="EPA分數",
                yaxis=dict(range=[0, 5.2]),
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                ),
                hovermode='x unified'
            )
            
            # 設置X軸格式
            fig.update_xaxes(
                tickformat='%Y-%m-%d',
                tickangle=45
            )
            
            return fig
            
        except Exception as e:
            print(f"創建住院醫師EPA分數折線圖時發生錯誤: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return None
