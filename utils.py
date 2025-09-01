import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns

def create_radar_chart(categories, values, title="雷達圖", scale=5, fill=True, color=None):
    """
    建立通用雷達圖函數
    
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
    # 確保資料是閉合的雷達圖（首尾相連）
    categories = list(categories)
    values = list(values)
    
    # 添加第一個點到最後，形成閉合
    categories.append(categories[0])
    values.append(values[0])
    
    # 建立 plotly 雷達圖
    fig = go.Figure()
    
    # 設定線條顏色
    line_dict = dict(color=color) if color else dict()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself' if fill else None,
        name=title,
        line=line_dict,
        fillcolor=color,
        opacity=0.7 if color else 0.5
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

# 新增函數：顯示多個雷達圖比較
def display_comparison_radar_charts(df, value_columns, group_column, title="比較雷達圖", scale=5, key_prefix="", 
                                   highlight_group=None, avg_color='lightgray', highlight_color='red'):
    """
    顯示多個對象的雷達圖比較
    
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
        
    # 創建 plotly 雷達圖
    fig = go.Figure()
    
    # 如果需要顯示整體平均且有選擇對象
    if show_average and len(selected_groups) > 0:
        # 計算整體平均值
        avg_values = [df[col].mean() for col in value_columns]
        
        # 確保資料是閉合的雷達圖（首尾相連）
        categories = list(value_columns)
        avg_values = list(avg_values)
        categories.append(categories[0])
        avg_values.append(avg_values[0])
        
        # 添加到圖表 - 使用淡灰色
        fig.add_trace(go.Scatterpolar(
            r=avg_values,
            theta=categories,
            fill='toself',
            name='整體平均',
            line=dict(color=avg_color, dash='dash'),
            fillcolor=avg_color,
            opacity=0.3
        ))
    
    # 為每個選定的對象添加雷達圖
    for group in selected_groups:
        # 篩選該對象的資料
        group_data = df[df[group_column] == group]
        
        # 計算平均值
        values = [group_data[col].mean() for col in value_columns]
        
        # 確保資料是閉合的雷達圖（首尾相連）
        categories = list(value_columns)
        values = list(values)
        categories.append(categories[0])
        values.append(values[0])
        
        # 判斷是否為要強調的組別
        is_highlight = highlight_group and group == highlight_group
        
        # 設定顏色 - 如果是強調組別則使用紅色，否則使用預設顏色
        color = highlight_color if is_highlight else None
        
        # 添加到圖表
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
                range=[0, scale]
            )
        ),
        title=title,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    # 顯示圖表
    st.plotly_chart(fig, use_container_width=True)

# 新增函數：顯示雷達圖元件
def radar_chart_component(data, title="能力評估", key_prefix="radar", student_column=None):
    """
    雷達圖元件，包含更多互動選項
    
    參數:
    - data: DataFrame 資料
    - title: 元件標題
    - key_prefix: 用於生成唯一 key 的前綴
    - student_column: 學生欄位名稱，如果提供，則會將學生以紅色強調顯示
    """
    with st.expander(f"{title} 雷達圖分析", expanded=True):
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
                # 如果是學生分析，則選擇要強調的學生
                highlight_group = None
                if student_column and student_column == group_by:
                    students = data[student_column].unique().tolist()
                    highlight_group = st.selectbox(
                        "選擇要強調的學生", 
                        ["無"] + students,
                        key=f"{key_prefix}_highlight"
                    )
                    if highlight_group == "無":
                        highlight_group = None
                
                # 使用比較模式
                display_comparison_radar_charts(
                    data, 
                    selected_columns, 
                    group_by, 
                    title=title,
                    scale=scale,
                    key_prefix=key_prefix,
                    highlight_group=highlight_group,
                    avg_color='lightgray',  # 平均值使用淡灰色
                    highlight_color='red'   # 強調學生使用紅色
                )
            else:
                # 使用單一雷達圖模式
                values = [data[col].mean() for col in selected_columns]
                fig = create_radar_chart(selected_columns, values, title, scale)
                st.plotly_chart(fig, use_container_width=True)
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
    plt.rcParams['font.sans-serif'] = ['sans-serif']
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

# 新增函數：顯示學員 EPA 雷達圖（從 UGY_EPA.py 整合）
def display_student_epa_radar_matplotlib(df, epa_column, value_column, student_column, title="學員 EPA 雷達圖分析", scale=5, key_prefix=""):
    """
    使用 Matplotlib 繪製學員 EPA 雷達圖分析
    
    參數:
    - df: 包含資料的 DataFrame
    - epa_column: EPA 評核項目欄位名稱
    - value_column: 等級數值欄位名稱
    - student_column: 學生欄位名稱
    - title: 圖表標題
    - scale: 雷達圖的最大刻度
    - key_prefix: Streamlit 元件的 key 前綴
    """
    if not key_prefix:
        key_prefix = f"student_epa_mpl_{id(df)}_"
    
    with st.expander(f"{title}", expanded=True):
        # 獲取所有學員姓名
        all_students = sorted(df[student_column].unique().tolist())
        
        # 選擇要分析的學生
        selected_student = st.selectbox(
            "選擇要分析的學生",
            all_students,
            key=f"{key_prefix}student"
        )
        
        # 計算整體平均
        overall_epa_avg = df.groupby(epa_column)[value_column].mean()
        
        # 檢查是否有足夠的資料繪製雷達圖
        if len(overall_epa_avg) >= 3:  # 雷達圖至少需要3個點
            # 準備雷達圖資料
            overall_categories = overall_epa_avg.index.tolist()
            overall_values = overall_epa_avg.values.tolist()
            
            # 確保資料是閉合的（首尾相連）
            overall_categories.append(overall_categories[0])
            overall_values.append(overall_values[0])
            
            # 計算角度 - 確保與類別數量一致
            angles = np.linspace(0, 2*np.pi, len(overall_categories), endpoint=True)
            
            # 設定中文字型
            plt.rcParams['font.sans-serif'] = ['sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 篩選該學員的資料
            student_data = df[df[student_column] == selected_student]
            
            # 計算該學員每個 EPA 項目的平均等級
            student_epa_avg = student_data.groupby(epa_column)[value_column].mean()
            
            # 檢查是否有足夠的資料繪製雷達圖
            if len(student_epa_avg) >= 3:  # 雷達圖至少需要3個點
                # 獲取與整體相同的 EPA 項目
                student_values = []
                for item in overall_categories[:-1]:  # 不包括閉合點
                    if item in student_epa_avg:
                        student_values.append(student_epa_avg[item])
                    else:
                        student_values.append(0)
                
                # 閉合學員資料
                student_values.append(student_values[0])
                
                # 創建學員雷達圖
                fig = plt.figure(figsize=(8, 8))
                ax = fig.add_subplot(111, polar=True)
                
                # 繪製學員雷達圖 - 黑色粗線
                ax.plot(angles, student_values, 'o-', linewidth=3, color='black', label=f'{selected_student}')
                ax.fill(angles, student_values, alpha=0.25, color='gray')
                
                # 繪製整體平均雷達圖進行比較
                ax.plot(angles, overall_values, 'o-', linewidth=1, color='red', label='整體平均')
                ax.fill(angles, overall_values, alpha=0.1, color='red')
                
                # 設定刻度和標籤
                ax.set_thetagrids(np.degrees(angles[:-1]), overall_categories[:-1], fontsize=10)
                ax.set_ylim(0, scale)  # 設定刻度範圍
                ax.set_yticks(range(1, scale+1))
                ax.set_yticklabels([str(i) for i in range(1, scale+1)])
                ax.set_rlabel_position(0)
                
                # 添加標題和圖例
                plt.title(f'{selected_student} EPA 項目評核', size=14)
                plt.legend(loc='upper right', fontsize='medium')
                
                # 調整布局，確保標籤不被裁剪
                plt.tight_layout()
                
                # 顯示學員雷達圖
                st.pyplot(fig)
                
                # 顯示學生與整體平均的比較表格
                st.write("#### 學生與整體平均比較")
                
                # 創建比較表格
                comparison_data = {
                    'EPA項目': overall_categories[:-1],  # 不包括閉合點
                    f'{selected_student} 平均': student_values[:-1],  # 不包括閉合點
                    '整體平均': overall_values[:-1],  # 不包括閉合點
                    '差異': [student_values[i] - overall_values[i] for i in range(len(overall_values)-1)]  # 不包括閉合點
                }
                
                comparison_df = pd.DataFrame(comparison_data)
                
                # 顯示表格，差異欄位使用顏色漸層
                st.dataframe(comparison_df.style.background_gradient(cmap='RdYlGn', subset=['差異']))
            else:
                st.warning(f"{selected_student} 的 EPA 項目數量不足，無法繪製雷達圖（至少需要3個不同項目）")
        else:
            st.warning(f"整體 EPA 項目數量不足，無法繪製雷達圖（至少需要3個不同項目）")

# 新增函數：顯示所有學員 EPA 雷達圖（從 UGY_EPA.py 整合）
def display_all_students_epa_radar(df, epa_column, value_column, student_column, title="所有學員 EPA 雷達圖分析", scale=5):
    """
    顯示所有學員的 EPA 雷達圖分析
    
    參數:
    - df: 包含資料的 DataFrame
    - epa_column: EPA 評核項目欄位名稱
    - value_column: 等級數值欄位名稱
    - student_column: 學生欄位名稱
    - title: 圖表標題
    - scale: 雷達圖的最大刻度
    """
    st.write(f"### {title}")
    
    # 獲取所有學員姓名
    all_students = sorted(df[student_column].unique().tolist())
    
    # 計算整體平均
    overall_epa_avg = df.groupby(epa_column)[value_column].mean()
    
    # 檢查是否有足夠的資料繪製雷達圖
    if len(overall_epa_avg) >= 3:  # 雷達圖至少需要3個點
        # 準備雷達圖資料
        overall_categories = overall_epa_avg.index.tolist()
        overall_values = overall_epa_avg.values.tolist()
        
        # 確保資料是閉合的（首尾相連）
        overall_categories.append(overall_categories[0])
        overall_values.append(overall_values[0])
        
        # 計算角度 - 確保與類別數量一致
        angles = np.linspace(0, 2*np.pi, len(overall_categories), endpoint=True)
        
        # 設定中文字型
        plt.rcParams['font.sans-serif'] = ['sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 為每個學員創建雷達圖和資料表格
        for student in all_students:
            st.write(f"#### {student}")
            
            # 創建兩欄布局
            col1, col2 = st.columns([1, 1])
            
            # 篩選該學員的資料
            student_data = df[df[student_column] == student]
            
            # 計算該學員每個 EPA 項目的平均等級
            student_epa_avg = student_data.groupby(epa_column)[value_column].mean()
            
            # 在左欄顯示雷達圖
            with col1:
                # 檢查是否有足夠的資料繪製雷達圖
                if len(student_epa_avg) >= 3:  # 雷達圖至少需要3個點
                    # 獲取與整體相同的 EPA 項目
                    student_values = []
                    for item in overall_categories[:-1]:  # 不包括閉合點
                        if item in student_epa_avg:
                            student_values.append(student_epa_avg[item])
                        else:
                            student_values.append(0)
                    
                    # 閉合學員資料
                    student_values.append(student_values[0])
                    
                    # 創建學員雷達圖
                    fig = plt.figure(figsize=(6, 6))
                    ax = fig.add_subplot(111, polar=True)
                    
                    # 繪製學員雷達圖 - 黑色粗線
                    ax.plot(angles, student_values, 'o-', linewidth=3, color='black', label=f'{student}')
                    ax.fill(angles, student_values, alpha=0.25, color='gray')
                    
                    # 繪製整體平均雷達圖進行比較
                    ax.plot(angles, overall_values, 'o-', linewidth=1, color='red', label='整體平均')
                    ax.fill(angles, overall_values, alpha=0.1, color='red')
                    
                    # 設定刻度和標籤
                    ax.set_thetagrids(np.degrees(angles[:-1]), overall_categories[:-1], fontsize=8)
                    ax.set_ylim(0, scale)  # 設定刻度範圍
                    ax.set_yticks(range(1, scale+1))
                    ax.set_yticklabels([str(i) for i in range(1, scale+1)])
                    ax.set_rlabel_position(0)
                    
                    # 添加標題和圖例
                    plt.title(f'{student} EPA 項目評核', size=12)
                    plt.legend(loc='upper right', fontsize='small')
                    
                    # 調整布局，確保標籤不被裁剪
                    plt.tight_layout()
                    
                    # 顯示學員雷達圖
                    st.pyplot(fig)
                else:
                    st.warning(f"{student} 的 EPA 項目數量不足，無法繪製雷達圖（至少需要3個不同項目）")
            
            # 在右欄顯示資料表格
            with col2:
                # 創建比較表格
                if len(student_epa_avg) > 0:
                    # 獲取與整體相同的 EPA 項目
                    comparison_data = []
                    for item in overall_categories[:-1]:  # 不包括閉合點
                        if item in student_epa_avg:
                            comparison_data.append({
                                'EPA項目': item,
                                f'{student} 平均': student_epa_avg[item],
                                '整體平均': overall_epa_avg[item],
                                '差異': student_epa_avg[item] - overall_epa_avg[item]
                            })
                    
                    if comparison_data:
                        comparison_df = pd.DataFrame(comparison_data)
                        st.dataframe(comparison_df.style.background_gradient(cmap='RdYlGn', subset=['差異']))
                    else:
                        st.warning(f"{student} 沒有可比較的 EPA 項目資料")
                else:
                    st.warning(f"{student} 沒有 EPA 項目資料")
    else:
        st.warning(f"整體 EPA 項目數量不足，無法繪製雷達圖（至少需要3個不同項目）")

# 其他可能需要的共用函數... 