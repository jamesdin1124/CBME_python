import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns
import re

# 工具函數
def extract_spreadsheet_id(url):
    """從 Google 試算表 URL 中提取 spreadsheet ID"""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None

def extract_gid(url):
    """從 Google 試算表 URL 中提取 gid"""
    match = re.search(r'gid=(\d+)', url)
    return int(match.group(1)) if match else None

# 導入統一的雷達圖模組
from modules.visualization.unified_radar import (
    UnifiedRadarVisualization,
    RadarChartConfig,
    EPAChartConfig,
    RadarChartComponent,
    create_radar_chart,
    create_epa_radar_chart,
    create_comparison_radar_chart
)

# 向後相容的雷達圖函數（重定向到統一模組）
def create_radar_chart_legacy(categories, values, title="雷達圖", scale=5, fill=True, color=None):
    """
    向後相容的雷達圖函數 - 重定向到統一模組
    
    參數:
    - categories: 雷達圖的各個維度名稱
    - values: 對應每個維度的數值
    - title: 圖表標題
    - scale: 雷達圖的最大刻度
    - fill: 是否填充雷達圖區域
    - color: 雷達圖的顏色
    
    返回:
    - fig: plotly 圖表物件
    """
    return create_radar_chart(categories, values, title, scale)

def display_radar_chart(df, value_columns, name_column=None, title="能力評估雷達圖", scale=5):
    """
    顯示雷達圖的高階函數 - 使用統一模組
    
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

def display_comparison_radar_charts(df, value_columns, group_column, title="比較雷達圖", scale=5, key_prefix="", 
                                   highlight_group=None, avg_color='lightgray', highlight_color='red'):
    """
    顯示多個對象的雷達圖比較 - 使用統一模組
    
    參數:
    - df: 包含資料的 DataFrame
    - value_columns: 要在雷達圖中顯示的數值欄位列表
    - group_column: 用於分組的欄位名稱（如學生姓名、教師姓名等）
    - title: 圖表標題
    - scale: 雷達圖的最大刻度
    - key_prefix: Streamlit 元件的 key 前綴，避免重複
    - highlight_group: 要特別強調的組別（如特定學員）
    - avg_color: 平均值的顏色
    - highlight_color: 強調組別的顏色
    """
    if not key_prefix:
        key_prefix = f"radar_comp_{id(df)}_"
        
    if group_column not in df.columns:
        st.warning(f"分組欄位 '{group_column}' 不存在於資料中")
        return
        
    # 獲取所有分組值
    groups = df[group_column].unique().tolist()
    
    # 讓使用者選擇要比較的對象
    selected_groups = st.multiselect(
        f"選擇要比較的{group_column}",
        options=groups,
        default=groups[:min(3, len(groups))],  # 預設選擇前3個
        key=f"{key_prefix}groups"
    )
    
    # 是否顯示整體平均
    show_average = st.checkbox("顯示整體平均", value=True, key=f"{key_prefix}avg")
    
    # 如果沒有選擇任何對象，顯示警告
    if not selected_groups:
        st.warning("請至少選擇一個對象進行比較")
        return
    
    # 使用統一模組創建比較雷達圖
    fig = create_comparison_radar_chart(df, value_columns, group_column, title, scale)
    
    # 顯示圖表
    st.plotly_chart(fig, use_container_width=True)

def radar_chart_component(data, title="能力評估", key_prefix="radar", student_column=None):
    """
    雷達圖元件，包含更多互動選項 - 使用統一模組
    
    參數:
    - data: DataFrame 資料
    - title: 元件標題
    - key_prefix: 用於生成唯一 key 的前綴
    - student_column: 學生欄位名稱，如果提供，則會將學生以紅色強調顯示
    """
    # 使用統一模組的元件
    radar_viz = UnifiedRadarVisualization()
    component = RadarChartComponent(radar_viz)
    
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
    if selected_columns:
        if group_by != "無":
            # 使用比較模式
            component.display_comparison_radar(data, title, key_prefix)
        else:
            # 使用簡單雷達圖模式
            component.display_simple_radar(data, title, key_prefix)
    else:
        st.warning("請選擇至少一個維度")

# 新增函數：顯示統計分析圖表
def display_statistical_charts(df, value_column, group_column=None, chart_type="boxplot", title=None, key_prefix=""):
    """
    顯示統計分析圖表（箱型圖、小提琴圖、直方圖等）
    
    參數:
    - df: 包含資料的 DataFrame
    - value_column: 要分析的數值欄位
    - group_column: 用於分組的欄位名稱（可選）
    - chart_type: 圖表類型，可選 "boxplot", "violinplot", "histogram", "barplot"
    - title: 圖表標題
    - key_prefix: Streamlit 元件的 key 前綴，避免重複
    """
    if not key_prefix:
        key_prefix = f"stat_{id(df)}_"
    
    # 設定中文字型
    plt.rcParams['axes.unicode_minus'] = False
    
    # 創建圖形
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 根據圖表類型繪製不同的圖表
    if chart_type == "boxplot":
        if group_column:
            sns.boxplot(x=group_column, y=value_column, data=df, ax=ax)
            # 添加數據點以顯示分布
            sns.stripplot(x=group_column, y=value_column, data=df, 
                         size=4, color=".3", linewidth=0, alpha=0.3, ax=ax)
        else:
            sns.boxplot(y=value_column, data=df, ax=ax)
            sns.stripplot(y=value_column, data=df, 
                         size=4, color=".3", linewidth=0, alpha=0.3, ax=ax)
    
    elif chart_type == "violinplot":
        if group_column:
            sns.violinplot(x=group_column, y=value_column, data=df, inner='quartile', ax=ax)
        else:
            sns.violinplot(y=value_column, data=df, inner='quartile', ax=ax)
    
    elif chart_type == "histogram":
        sns.histplot(df[value_column], bins=10, kde=True, ax=ax)
        # 添加平均值和中位數線
        mean_val = df[value_column].mean()
        median_val = df[value_column].median()
        ax.axvline(mean_val, color='red', linestyle='--', label=f'平均值: {mean_val:.2f}')
        ax.axvline(median_val, color='green', linestyle='-.', label=f'中位數: {median_val:.2f}')
        ax.legend()
    
    elif chart_type == "barplot":
        if group_column:
            sns.barplot(x=group_column, y=value_column, data=df, ax=ax)
        else:
            st.warning("長條圖需要指定分組欄位")
            return
    
    # 設定圖表標題
    if title:
        ax.set_title(title, fontsize=16)
    
    # 設定軸標籤
    if group_column:
        ax.set_xlabel(group_column, fontsize=12)
    ax.set_ylabel(value_column, fontsize=12)
    
    # 旋轉 x 軸標籤以避免重疊
    if group_column:
        plt.xticks(rotation=45, ha='right')
    
    # 添加網格線以便於閱讀
    ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # 調整布局
    plt.tight_layout()
    
    # 顯示圖表
    st.pyplot(fig)

# 新增函數：顯示統計分析元件
def statistical_analysis_component(data, title="統計分析", key_prefix="stat"):
    """
    統計分析元件，包含多種圖表選項
    
    參數:
    - data: DataFrame 資料
    - title: 元件標題
    - key_prefix: 用於生成唯一 key 的前綴
    """
    with st.expander(f"{title}", expanded=True):
        # 選擇要分析的數值欄位
        numeric_columns = data.select_dtypes(include=['number']).columns.tolist()
        if not numeric_columns:
            st.warning("資料中沒有數值型欄位可供分析")
            return
            
        selected_value = st.selectbox(
            "選擇要分析的數值欄位", 
            numeric_columns,
            key=f"{key_prefix}_value"
        )
        
        # 選擇分組欄位
        categorical_columns = data.select_dtypes(include=['object']).columns.tolist()
        group_by = st.selectbox(
            "選擇分組欄位（可選）", 
            ["無"] + categorical_columns,
            key=f"{key_prefix}_group"
        )
        
        # 選擇圖表類型
        chart_type = st.selectbox(
            "選擇圖表類型",
            ["箱型圖", "小提琴圖", "直方圖", "長條圖"],
            key=f"{key_prefix}_chart"
        )
        
        # 轉換圖表類型
        chart_type_map = {
            "箱型圖": "boxplot",
            "小提琴圖": "violinplot",
            "直方圖": "histogram",
            "長條圖": "barplot"
        }
        
        # 顯示圖表
        if group_by != "無":
            display_statistical_charts(
                data, 
                selected_value, 
                group_by, 
                chart_type_map[chart_type], 
                title=f"{selected_value} 依 {group_by} 分組的{chart_type}",
                key_prefix=key_prefix
            )
        else:
            display_statistical_charts(
                data, 
                selected_value, 
                None, 
                chart_type_map[chart_type], 
                title=f"{selected_value} 的{chart_type}",
                key_prefix=key_prefix
            )
        
        # 顯示基本統計資訊
        st.write("#### 基本統計資訊")
        if group_by != "無":
            # 分組統計
            stats = data.groupby(group_by)[selected_value].agg([
                ('平均數', 'mean'),
                ('中位數', 'median'),
                ('標準差', 'std'),
                ('最小值', 'min'),
                ('最大值', 'max'),
                ('計數', 'count')
            ]).round(2)
            st.dataframe(stats.style.background_gradient(cmap='YlGnBu', subset=['平均數', '中位數']))
        else:
            # 整體統計
            stats = data[selected_value].agg([
                ('平均數', 'mean'),
                ('中位數', 'median'),
                ('標準差', 'std'),
                ('最小值', 'min'),
                ('最大值', 'max'),
                ('計數', 'count')
            ]).round(2)
            st.dataframe(pd.DataFrame(stats).T)

# 向後相容的EPA雷達圖函數（重定向到統一模組）
def display_student_epa_radar_matplotlib(df, epa_column, value_column, student_column, title="學員 EPA 雷達圖分析", scale=5, key_prefix=""):
    """
    使用 Matplotlib 繪製學員 EPA 雷達圖分析 - 重定向到統一模組
    
    參數:
    - df: 包含資料的 DataFrame
    - epa_column: EPA 評核項目欄位名稱
    - value_column: 等級數值欄位名稱
    - student_column: 學生欄位名稱
    - title: 圖表標題
    - scale: 雷達圖的最大刻度
    - key_prefix: Streamlit 元件的 key 前綴
    """
    # 使用統一模組創建EPA雷達圖
    radar_viz = UnifiedRadarVisualization()
    
    with st.expander(f"{title}", expanded=True):
        # 獲取所有學員姓名
        all_students = sorted(df[student_column].unique().tolist())
        
        # 選擇要分析的學生
        selected_student = st.selectbox(
            "選擇要分析的學生",
            all_students,
            key=f"{key_prefix}student"
        )
        
        # 篩選學生資料
        student_df = df[df[student_column] == selected_student]
        
        if not student_df.empty:
            # 使用統一模組創建學生EPA雷達圖
            config = EPAChartConfig(
                title=f"{selected_student} EPA 雷達圖",
                scale=scale,
                student_id=selected_student
            )
            fig = radar_viz.create_epa_radar_chart(student_df, config)
            st.plotly_chart(fig, use_container_width=True)
            
            # 顯示比較表格
            st.write("#### 學生與整體平均比較")
            overall_avg = df.groupby(epa_column)[value_column].mean()
            student_avg = student_df.groupby(epa_column)[value_column].mean()
            
            comparison_data = []
            for epa_item in overall_avg.index:
                student_score = student_avg.get(epa_item, 0)
                overall_score = overall_avg[epa_item]
                comparison_data.append({
                    'EPA項目': epa_item,
                    f'{selected_student} 平均': student_score,
                    '整體平均': overall_score,
                    '差異': student_score - overall_score
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df.style.background_gradient(cmap='RdYlGn', subset=['差異']))
        else:
            st.warning(f"找不到學生 {selected_student} 的資料")

def display_all_students_epa_radar(df, epa_column, value_column, student_column, title="所有學員 EPA 雷達圖分析", scale=5):
    """
    顯示所有學員的 EPA 雷達圖分析 - 使用統一模組
    
    參數:
    - df: 包含資料的 DataFrame
    - epa_column: EPA 評核項目欄位名稱
    - value_column: 等級數值欄位名稱
    - student_column: 學生欄位名稱
    - title: 圖表標題
    - scale: 雷達圖的最大刻度
    """
    st.write(f"### {title}")
    
    # 使用統一模組
    radar_viz = UnifiedRadarVisualization()
    
    # 獲取所有學員姓名
    all_students = sorted(df[student_column].unique().tolist())
    
    # 為每個學員創建雷達圖
    for student in all_students:
        st.write(f"#### {student}")
        
        # 篩選該學員的資料
        student_data = df[df[student_column] == student]
        
        if not student_data.empty:
            # 創建兩欄布局
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # 使用統一模組創建學生EPA雷達圖
                config = EPAChartConfig(
                    title=f"{student} EPA 雷達圖",
                    scale=scale,
                    student_id=student
                )
                fig = radar_viz.create_epa_radar_chart(student_data, config)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 顯示比較表格
                overall_avg = df.groupby(epa_column)[value_column].mean()
                student_avg = student_data.groupby(epa_column)[value_column].mean()
                
                comparison_data = []
                for epa_item in overall_avg.index:
                    student_score = student_avg.get(epa_item, 0)
                    overall_score = overall_avg[epa_item]
                    comparison_data.append({
                        'EPA項目': epa_item,
                        f'{student} 平均': student_score,
                        '整體平均': overall_score,
                        '差異': student_score - overall_score
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df.style.background_gradient(cmap='RdYlGn', subset=['差異']))
        else:
            st.warning(f"{student} 沒有 EPA 項目資料")

# 向後相容的別名 - 直接使用統一模組的函數
# create_radar_chart 已經從統一模組導入，不需要重新定義
