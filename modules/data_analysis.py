import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
from .visualization import (
    plot_epa_radar,
    plot_trend_analysis,
    plot_teacher_comparison,
    plot_epa_distributions,
    plot_epa_trend,
    plot_epa_distribution,
    plot_epa_boxplot,
    display_epa_stats
)

def analyze_epa_data(df):
    """分析 EPA 評核資料"""
    if df is None or df.empty:
        st.warning("沒有可分析的資料")
        return
    
    
    # 1. 基本統計資訊
    st.write("# 基本統計資訊")
    
    # 計算評核總數
    total_assessments = len(df)
    
    # 計算不同學員階層的評核數量
    if '學員階層' in df.columns:
        level_counts = df['學員階層'].value_counts()
        
        # 顯示評核總數和各階層評核數量
        col1, col2 = st.columns(2)
        with col1:
            st.metric("評核總數", total_assessments)
        
        with col2:
            st.write("各階層評核數量")
            st.dataframe(level_counts)
    else:
        st.metric("評核總數", total_assessments)
    
    # 2. EPA 項目分析
    if 'EPA評核項目' in df.columns:
        st.write("# EPA 項目分析")
        
        # 計算每個 EPA 項目的平均等級
        epa_means = df.groupby('EPA評核項目')['等級數值'].mean()
        
        # 繪製雷達圖
        fig = plot_epa_radar(
            df,
            categories=epa_means.index.tolist(),
            values=epa_means.values.tolist(),
            title="EPA 項目平均等級"
        )
        st.pyplot(fig)
        
        # 顯示統計資訊
        st.write("EPA 項目統計資訊")
        stats = display_epa_stats(df, 'EPA評核項目', '等級數值')
        st.dataframe(stats)
    
    # 3. EPA 等級分析
    if '等級數值' in df.columns:
        
        
        # 使用雷達圖呈現 EPA 項目平均等級
        if 'EPA評核項目' in df.columns:
            st.write("### EPA 梯次平均雷達圖")
            
            # 創建兩欄布局
            col1, col2 = st.columns([1, 1])
            
            # 計算每個 EPA 項目的整體平均等級
            epa_item_avg = df.groupby('EPA評核項目')['等級數值'].mean()
            
            # 在左欄顯示雷達圖
            with col1:
                # 檢查是否有足夠的資料繪製雷達圖
                if len(epa_item_avg) >= 3:  # 雷達圖至少需要3個點
                    # 準備雷達圖資料
                    categories = epa_item_avg.index.tolist()
                    values = epa_item_avg.values.tolist()
                    
                    # 確保資料是閉合的（首尾相連）
                    categories.append(categories[0])
                    values.append(values[0])
                    
                    # 計算角度 - 確保與類別數量一致
                    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=True)
                    
                    # 設定中文字型
                    plt.rcParams['axes.unicode_minus'] = False
                    
                    # 創建雷達圖
                    fig = plt.figure(figsize=(8, 8))
                    ax = fig.add_subplot(111, polar=True)
                    
                    # 繪製整體平均雷達圖 - 使用黑色粗線
                    ax.plot(angles, values, 'o-', linewidth=3, color='black', label='整體平均')
                    ax.fill(angles, values, alpha=0.25, color='gray')
                    
                    # 如果有學員階層欄位，繪製不同階層的平均
                    if '學員階層' in df.columns:
                        # 獲取所有階層
                        all_levels = sorted(df['學員階層'].unique())
                        
                        # 定義不同階層的顏色
                        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan']
                        
                        # 為每個階層繪製雷達圖
                        for i, level in enumerate(all_levels):
                            # 篩選該階層的資料
                            level_data = df[df['學員階層'] == level]
                            
                            # 計算該階層每個 EPA 項目的平均等級
                            level_epa_avg = level_data.groupby('EPA評核項目')['等級數值'].mean()
                            
                            # 獲取與整體相同的 EPA 項目
                            level_values = []
                            for item in categories[:-1]:  # 不包括閉合點
                                if item in level_epa_avg:
                                    level_values.append(level_epa_avg[item])
                                else:
                                    level_values.append(0)
                            
                            # 閉合階層資料
                            level_values.append(level_values[0])
                            
                            # 選擇顏色
                            color = colors[i % len(colors)]
                            
                            # 繪製階層雷達圖
                            ax.plot(angles, level_values, 'o-', linewidth=2, color=color, label=f'{level}')
                            ax.fill(angles, level_values, alpha=0.1, color=color)
                    
                    # 設定刻度和標籤
                    ax.set_thetagrids(np.degrees(angles[:-1]), categories[:-1], fontsize=9)
                    ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                    ax.set_yticks([1, 2, 3, 4, 5])
                    ax.set_yticklabels(['1', '2', '3', '4', '5'])
                    ax.set_rlabel_position(0)
                    
                    # 添加標題和圖例
                    plt.title('各 EPA 項目平均等級雷達圖', size=14)
                    plt.legend(loc='upper right', fontsize='small')
                    
                    # 調整布局，確保標籤不被裁剪
                    plt.tight_layout()
                    
                    # 顯示雷達圖
                    st.pyplot(fig)
                else:
                    st.warning("EPA 項目數量不足，無法繪製雷達圖（至少需要3個不同項目）")
            
            # 在右欄顯示每個梯次各個 EPA 項目的平均等級
            with col2:
                if '梯次' in df.columns:
                    st.write("##### 各梯次 EPA 項目平均等級")
                    
                    # 計算每個梯次每個 EPA 項目的平均等級
                    batch_epa_avg = df.groupby(['梯次', 'EPA評核項目'])['等級數值'].mean().unstack()
                    
                    # 檢查是否有資料
                    if not batch_epa_avg.empty:
                        # 顯示表格
                        st.dataframe(batch_epa_avg.style.background_gradient(cmap='YlGnBu', axis=None))
                        
                        # 繪製折線圖，顯示各 EPA 項目隨梯次的變化趨勢
                        st.write("##### EPA 項目隨梯次變化趨勢")
                        
                        # 創建折線圖
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # 為每個 EPA 項目繪製一條折線及其 95% 信賴區間
                        for item in batch_epa_avg.columns:
                            # 獲取該 EPA 項目在每個梯次的平均值
                            means = batch_epa_avg[item]
                            
                            # 計算每個梯次該 EPA 項目的標準差和樣本數
                            std_devs = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].std()
                            counts = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].count()
                            
                            # 計算 95% 信賴區間
                            # 信賴區間 = 平均值 ± 1.96 * (標準差 / sqrt(樣本數))
                            ci_lower = []
                            ci_upper = []
                            
                            for idx in means.index:
                                if idx in std_devs.index and idx in counts.index:
                                    std = std_devs[idx]
                                    count = counts[idx]
                                    
                                    # 處理可能的 NaN 值或樣本數為 1 的情況
                                    if pd.isna(std) or count <= 1:
                                        # 如果標準差為 NaN 或樣本數為 1，則使用平均值作為上下限
                                        ci_lower.append(means[idx])
                                        ci_upper.append(means[idx])
                                    else:
                                        # 計算 95% 信賴區間
                                        margin = 1.96 * (std / np.sqrt(count))
                                        ci_lower.append(max(0, means[idx] - margin))  # 確保下限不小於 0
                                        ci_upper.append(min(5, means[idx] + margin))  # 確保上限不大於 5
                                else:
                                    # 如果沒有標準差或樣本數資料，則使用平均值作為上下限
                                    ci_lower.append(means[idx])
                                    ci_upper.append(means[idx])
                            
                            # 繪製平均值折線
                            ax.plot(means.index, means.values, 'o-', linewidth=2, label=item)
                            
                            # 繪製 95% 信賴區間（半透明區域）
                            ax.fill_between(means.index, ci_lower, ci_upper, alpha=0.2)
                        
                        # 設定圖表屬性
                        ax.set_xlabel('梯次', fontsize=12)
                        ax.set_ylabel('EPA 等級', fontsize=12)
                        ax.set_title('EPA 項目隨梯次變化趨勢 (含 95% 信賴區間)', fontsize=14)
                        ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                        ax.grid(True, linestyle='--', alpha=0.7)
                        
                        # 如果項目太多，將圖例放在圖表下方
                        if len(batch_epa_avg.columns) > 5:
                            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize='small')
                        else:
                            ax.legend(loc='best', fontsize='small')
                        
                        # 調整布局，確保標籤不被裁剪
                        plt.tight_layout()
                        
                        # 顯示折線圖
                        st.pyplot(fig)
                    else:
                        st.warning("沒有足夠的資料來顯示各梯次 EPA 項目平均等級")
                else:
                    st.warning("資料中缺少梯次欄位，無法顯示各梯次 EPA 項目平均等級")
    
    # 4. 學員雷達圖分析 - 直接呈現所有學生資料
    if '姓名' in df.columns:
        st.write("### 所有學員 EPA 項目雷達圖分析")
        
        # 獲取所有學員姓名
        all_students = sorted(df['姓名'].unique().tolist())
        
        # 計算整體平均
        overall_epa_avg = df.groupby('EPA評核項目')['等級數值'].mean()
        
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
            plt.rcParams['axes.unicode_minus'] = False
            
            # 為每個學員創建雷達圖和資料表格
            for student in all_students:
                st.write(f"#### {student}")
                
                # 創建兩欄布局
                col1, col2 = st.columns([1, 1])
                
                # 篩選該學員的資料
                student_data = df[df['姓名'] == student]
                
                # 計算該學員每個 EPA 項目的平均等級
                student_epa_avg = student_data.groupby('EPA評核項目')['等級數值'].mean()
                
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
                        ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                        ax.set_yticks([1, 2, 3, 4, 5])
                        ax.set_yticklabels(['1', '2', '3', '4', '5'])
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
                
                # 在右欄顯示表格資料（可展開）
                with col2:
                    # 準備顯示的資料表格
                    if '評語' in student_data.columns and 'EPA評核項目' in student_data.columns and '等級' in student_data.columns:
                        # 選擇要顯示的欄位
                        display_df = student_data[['EPA評核項目', '評語', '等級', '評核老師']]
                        
                        # 使用 expander 讓表格可展開
                        with st.expander("點擊展開詳細評核資料", expanded=False):
                            st.dataframe(display_df)
                    else:
                        st.warning("缺少必要欄位，無法顯示完整評核資料")
                
                # 新增：顯示學員在不同梯次各 EPA 項目的趨勢折線圖
                st.write("##### 各 EPA 項目隨時間變化趨勢")
                
                # 檢查是否有梯次欄位
                if '梯次' in student_data.columns:
                    # 按梯次和 EPA 項目分組計算平均等級
                    trend_data = student_data.groupby(['梯次', 'EPA評核項目'])['等級數值'].mean().unstack()
                    
                    # 檢查是否有足夠的資料繪製趨勢圖
                    if not trend_data.empty and len(trend_data) > 1:  # 至少需要兩個時間點
                        # 繪製趨勢折線圖
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # 為每個 EPA 項目繪製一條折線及其 95% 信賴區間
                        for item in trend_data.columns:
                            # 獲取該 EPA 項目在每個梯次的平均值
                            means = trend_data[item]
                            
                            # 計算每個梯次該 EPA 項目的標準差和樣本數
                            std_devs = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].std()
                            counts = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].count()
                            
                            # 計算 95% 信賴區間
                            # 信賴區間 = 平均值 ± 1.96 * (標準差 / sqrt(樣本數))
                            ci_lower = []
                            ci_upper = []
                            
                            for idx in means.index:
                                if idx in std_devs.index and idx in counts.index:
                                    std = std_devs[idx]
                                    count = counts[idx]
                                    
                                    # 處理可能的 NaN 值或樣本數為 1 的情況
                                    if pd.isna(std) or count <= 1:
                                        # 如果標準差為 NaN 或樣本數為 1，則使用平均值作為上下限
                                        ci_lower.append(means[idx])
                                        ci_upper.append(means[idx])
                                    else:
                                        # 計算 95% 信賴區間
                                        margin = 1.96 * (std / np.sqrt(count))
                                        ci_lower.append(max(0, means[idx] - margin))  # 確保下限不小於 0
                                        ci_upper.append(min(5, means[idx] + margin))  # 確保上限不大於 5
                                else:
                                    # 如果沒有標準差或樣本數資料，則使用平均值作為上下限
                                    ci_lower.append(means[idx])
                                    ci_upper.append(means[idx])
                            
                            # 繪製平均值折線
                            ax.plot(means.index, means.values, 'o-', linewidth=2, label=item)
                            
                            # 繪製 95% 信賴區間（半透明區域）
                            ax.fill_between(means.index, ci_lower, ci_upper, alpha=0.2)
                        
                        # 設定圖表屬性
                        ax.set_xlabel('梯次', fontsize=12)
                        ax.set_ylabel('EPA 等級', fontsize=12)
                        ax.set_title(f'{student} 各 EPA 項目隨時間變化趨勢', fontsize=14)
                        ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                        ax.grid(True, linestyle='--', alpha=0.7)
                        
                        # 如果項目太多，將圖例放在圖表下方
                        if len(trend_data.columns) > 5:
                            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize='small')
                        else:
                            ax.legend(loc='best', fontsize='small')
                        
                        # 調整布局，確保標籤不被裁剪
                        plt.tight_layout()
                        
                        # 顯示趨勢折線圖
                        st.pyplot(fig)
                    else:
                        st.info(f"{student} 在不同梯次的資料不足，無法繪製趨勢圖（至少需要兩個不同梯次的資料）")
                elif '評核時間' in student_data.columns:
                    # 如果沒有梯次欄位但有評核時間，可以按月份分組
                    student_data['月份'] = student_data['評核時間'].dt.strftime('%Y-%m')
                    
                    # 按月份和 EPA 項目分組計算平均等級
                    trend_data = student_data.groupby(['月份', 'EPA評核項目'])['等級數值'].mean().unstack()
                    
                    # 檢查是否有足夠的資料繪製趨勢圖
                    if not trend_data.empty and len(trend_data) > 1:  # 至少需要兩個時間點
                        # 繪製趨勢折線圖
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        # 為每個 EPA 項目繪製一條折線及其 95% 信賴區間
                        for item in trend_data.columns:
                            # 獲取該 EPA 項目在每個梯次的平均值
                            means = trend_data[item]
                            
                            # 計算每個梯次該 EPA 項目的標準差和樣本數
                            std_devs = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].std()
                            counts = df[df['EPA評核項目'] == item].groupby('梯次')['等級數值'].count()
                            
                            # 計算 95% 信賴區間
                            # 信賴區間 = 平均值 ± 1.96 * (標準差 / sqrt(樣本數))
                            ci_lower = []
                            ci_upper = []
                            
                            for idx in means.index:
                                if idx in std_devs.index and idx in counts.index:
                                    std = std_devs[idx]
                                    count = counts[idx]
                                    
                                    # 處理可能的 NaN 值或樣本數為 1 的情況
                                    if pd.isna(std) or count <= 1:
                                        # 如果標準差為 NaN 或樣本數為 1，則使用平均值作為上下限
                                        ci_lower.append(means[idx])
                                        ci_upper.append(means[idx])
                                    else:
                                        # 計算 95% 信賴區間
                                        margin = 1.96 * (std / np.sqrt(count))
                                        ci_lower.append(max(0, means[idx] - margin))  # 確保下限不小於 0
                                        ci_upper.append(min(5, means[idx] + margin))  # 確保上限不大於 5
                                else:
                                    # 如果沒有標準差或樣本數資料，則使用平均值作為上下限
                                    ci_lower.append(means[idx])
                                    ci_upper.append(means[idx])
                            
                            # 繪製平均值折線
                            ax.plot(means.index, means.values, 'o-', linewidth=2, label=item)
                            
                            # 繪製 95% 信賴區間（半透明區域）
                            ax.fill_between(means.index, ci_lower, ci_upper, alpha=0.2)
                        
                        # 設定圖表屬性
                        ax.set_xlabel('月份', fontsize=12)
                        ax.set_ylabel('EPA 等級', fontsize=12)
                        ax.set_title(f'{student} 各 EPA 項目隨時間變化趨勢', fontsize=14)
                        ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                        ax.grid(True, linestyle='--', alpha=0.7)
                        
                        # 如果項目太多，將圖例放在圖表下方
                        if len(trend_data.columns) > 5:
                            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize='small')
                        else:
                            ax.legend(loc='best', fontsize='small')
                        
                        # 調整布局，確保標籤不被裁剪
                        plt.tight_layout()
                        
                        # 顯示趨勢折線圖
                        st.pyplot(fig)
                    else:
                        st.info(f"{student} 在不同時間的資料不足，無法繪製趨勢圖（至少需要兩個不同時間點的資料）")
                else:
                    st.warning("缺少梯次或評核時間欄位，無法繪製時間趨勢圖")
                
                # 添加分隔線
                st.markdown("---")

    # 5. 老師與同儕評分差異分析
    st.write("# 老師評分差異分析")

    # 檢查必要欄位是否存在
    required_cols = ['評核老師', '等級數值', 'EPA評核項目']
    if all(col in df.columns for col in required_cols):
        # 選擇要顯示的欄位並建立表格
        display_df = df[required_cols].copy()
        

    else:
        # 如果缺少必要欄位則顯示警告
        missing_cols = [col for col in required_cols if col not in df.columns]
        st.warning(f"缺少以下必要欄位，無法顯示評分明細：{', '.join(missing_cols)}")

    # 老師個別評分分析
    st.write("### 個別老師評分分析")
    
    # 檢查是否有評核老師欄位
    if '評核老師' in df.columns:
        # 取得所有老師列表
        teachers = df['評核老師'].unique().tolist()
        
        # 讓使用者選擇要分析的老師
        selected_teacher = st.selectbox(
            "選擇要分析的老師",
            teachers,
            key="teacher_select"
        )
        
        # 篩選選定老師的資料
        teacher_data = df[df['評核老師'] == selected_teacher]
        
        if not teacher_data.empty:
            st.write(f"#### {selected_teacher} 的評分分布")
            
            # 使用 matplotlib 和 seaborn 繪製箱型圖 - 將老師的評分與整體評分放在一起比較
            st.write("##### EPA 項目評分分布比較 (老師 vs 整體)")
            
            # 設定中文字型
            plt.rcParams['axes.unicode_minus'] = False
            
            # 創建圖形 - 使用更大的尺寸以容納更多資料
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # 創建一個新的DataFrame，添加來源標籤
            teacher_plot_data = teacher_data.copy()
            teacher_plot_data['來源'] = f'{selected_teacher}'
            
            all_plot_data = df.copy()
            all_plot_data['來源'] = '所有老師'
            
            # 合併資料
            plot_data = pd.concat([teacher_plot_data, all_plot_data])
            
            # 使用 seaborn 繪製箱型圖，按來源分組
            sns.boxplot(x='EPA評核項目', y='等級數值', hue='來源', data=plot_data, 
                       palette={'所有老師': 'lightgray', f'{selected_teacher}': 'steelblue'}, ax=ax)
            
            # 設定圖表屬性
            ax.set_title(f'{selected_teacher} vs 所有老師的 EPA 項目評分分布比較', fontsize=16)
            ax.set_xlabel('EPA評核項目', fontsize=12)
            ax.set_ylabel('評分等級', fontsize=12)
            ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
            
            # 旋轉 x 軸標籤以避免重疊
            plt.xticks(rotation=45, ha='right')
            
            # 添加網格線以便於閱讀
            ax.grid(True, linestyle='--', alpha=0.7, axis='y')
            
            # 調整圖例位置
            ax.legend(loc='upper right', fontsize='medium')
            
            # 調整布局
            plt.tight_layout()
            
            # 顯示圖表
            st.pyplot(fig)
            
            # 顯示統計資訊比較表格
            st.write("#### 評分統計資訊比較")
            
            # 計算老師的統計資訊
            teacher_stats = teacher_data.groupby('EPA評核項目')['等級數值'].agg([
                ('老師平均分數', 'mean'),
                ('老師中位數', 'median'),
                ('老師標準差', 'std'),
                ('老師評分次數', 'count')
            ]).round(2)
            
            # 計算整體的統計資訊
            all_stats = df.groupby('EPA評核項目')['等級數值'].agg([
                ('整體平均分數', 'mean'),
                ('整體中位數', 'median'),
                ('整體標準差', 'std'),
                ('整體評分次數', 'count')
            ]).round(2)
            
            # 合併統計資訊
            combined_stats = pd.concat([teacher_stats, all_stats], axis=1)
            
            # 計算差異
            if not combined_stats.empty:
                combined_stats['平均分數差異'] = combined_stats['老師平均分數'] - combined_stats['整體平均分數']
                combined_stats['中位數差異'] = combined_stats['老師中位數'] - combined_stats['整體中位數']
                
                # 新增：進行統計顯著性檢定
                st.write("#### 統計顯著性檢定")
                
                # 創建結果DataFrame
                significance_results = pd.DataFrame(index=teacher_stats.index, 
                                                  columns=['t檢定p值', 't檢定結果', 'Mann-Whitney U檢定p值', 'Mann-Whitney U檢定結果'])
                
                # 對每個EPA項目進行檢定
                for epa_item in teacher_stats.index:
                    # 獲取該EPA項目的老師評分和整體評分
                    teacher_scores = teacher_data[teacher_data['EPA評核項目'] == epa_item]['等級數值']
                    all_scores = df[df['EPA評核項目'] == epa_item]['等級數值']
                    
                    # 只有當樣本數足夠時才進行檢定
                    if len(teacher_scores) >= 5 and len(all_scores) >= 5:
                        # 進行t檢定（假設兩組數據有不同的方差）
                        try:
                            t_stat, p_value_t = stats.ttest_ind(teacher_scores, all_scores, equal_var=False)
                            significance_results.loc[epa_item, 't檢定p值'] = round(p_value_t, 4)
                            significance_results.loc[epa_item, 't檢定結果'] = "顯著差異" if p_value_t < 0.05 else "無顯著差異"
                        except:
                            significance_results.loc[epa_item, 't檢定p值'] = "計算錯誤"
                            significance_results.loc[epa_item, 't檢定結果'] = "無法判定"
                        
                        # 進行Mann-Whitney U檢定（非參數檢定，不假設正態分布）
                        try:
                            u_stat, p_value_u = stats.mannwhitneyu(teacher_scores, all_scores, alternative='two-sided')
                            significance_results.loc[epa_item, 'Mann-Whitney U檢定p值'] = round(p_value_u, 4)
                            significance_results.loc[epa_item, 'Mann-Whitney U檢定結果'] = "顯著差異" if p_value_u < 0.05 else "無顯著差異"
                        except:
                            significance_results.loc[epa_item, 'Mann-Whitney U檢定p值'] = "計算錯誤"
                            significance_results.loc[epa_item, 'Mann-Whitney U檢定結果'] = "無法判定"
                    else:
                        significance_results.loc[epa_item, 't檢定p值'] = "樣本不足"
                        significance_results.loc[epa_item, 't檢定結果'] = "無法檢定"
                        significance_results.loc[epa_item, 'Mann-Whitney U檢定p值'] = "樣本不足"
                        significance_results.loc[epa_item, 'Mann-Whitney U檢定結果'] = "無法檢定"
                
                # 顯示檢定結果
                st.dataframe(significance_results)
                
                # 解釋檢定結果
                st.write("##### 統計檢定說明")
                st.write("""
                - **t檢定**：比較兩組數據的平均值是否有顯著差異，假設數據近似正態分布。
                - **Mann-Whitney U檢定**：非參數檢定，比較兩組數據的分布是否有顯著差異，不要求數據正態分布。
                - **p值 < 0.05**：表示有95%的信心認為兩組數據存在顯著差異。
                - **樣本不足**：表示老師的評分樣本數少於5，不足以進行可靠的統計檢定。
                """)
                
                # 計算效應量 (Cohen's d)
                st.write("#### 效應量分析 (Cohen's d)")
                
                effect_size_results = pd.DataFrame(index=teacher_stats.index, 
                                                 columns=['效應量(Cohen\'s d)', '效應大小解釋'])
                
                for epa_item in teacher_stats.index:
                    teacher_scores = teacher_data[teacher_data['EPA評核項目'] == epa_item]['等級數值']
                    all_scores = df[df['EPA評核項目'] == epa_item]['等級數值']
                    
                    if len(teacher_scores) >= 5 and len(all_scores) >= 5:
                        try:
                            # 計算Cohen's d
                            teacher_mean = teacher_scores.mean()
                            all_mean = all_scores.mean()
                            teacher_std = teacher_scores.std()
                            all_std = all_scores.std()
                            
                            # 計算合併標準差
                            n1 = len(teacher_scores)
                            n2 = len(all_scores)
                            pooled_std = np.sqrt(((n1-1)*teacher_std**2 + (n2-1)*all_std**2) / (n1+n2-2))
                            
                            # 計算Cohen's d
                            d = abs(teacher_mean - all_mean) / pooled_std
                            effect_size_results.loc[epa_item, '效應量(Cohen\'s d)'] = round(d, 2)
                            
                            # 解釋效應大小
                            if d < 0.2:
                                effect_size_results.loc[epa_item, '效應大小解釋'] = "微小差異"
                            elif d < 0.5:
                                effect_size_results.loc[epa_item, '效應大小解釋'] = "小差異"
                            elif d < 0.8:
                                effect_size_results.loc[epa_item, '效應大小解釋'] = "中等差異"
                            else:
                                effect_size_results.loc[epa_item, '效應大小解釋'] = "大差異"
                        except:
                            effect_size_results.loc[epa_item, '效應量(Cohen\'s d)'] = "計算錯誤"
                            effect_size_results.loc[epa_item, '效應大小解釋'] = "無法判定"
                    else:
                        effect_size_results.loc[epa_item, '效應量(Cohen\'s d)'] = "樣本不足"
                        effect_size_results.loc[epa_item, '效應大小解釋'] = "無法計算"
                
                # 顯示效應量結果
                st.dataframe(effect_size_results)
                
                # 解釋效應量
                st.write("##### 效應量說明")
                st.write("""
                - **Cohen's d**：測量兩組數據平均值差異的標準化大小。
                - **解釋標準**：
                  - d < 0.2：微小差異
                  - 0.2 ≤ d < 0.5：小差異
                  - 0.5 ≤ d < 0.8：中等差異
                  - d ≥ 0.8：大差異
                """)
                
                # 顯示合併的統計資訊表格
                st.write("#### 詳細統計資訊比較")
                st.dataframe(combined_stats.style.background_gradient(cmap='RdYlGn', subset=['平均分數差異', '中位數差異']))
                
               
            
            
            # 新增：顯示所有老師的評分比較
            st.write("### 所有老師評分比較")
            
            # 檢查是否有足夠的資料進行比較
            if len(teachers) > 1:
                # 設定中文字型
                plt.rcParams['axes.unicode_minus'] = False
                
                # 創建圖形 - 使用更大的尺寸以容納更多資料
                fig, ax = plt.subplots(figsize=(14, 8))
                
                
                
                # 顯示所有老師的評分統計資訊
                all_teachers_stats = df.groupby(['評核老師', 'EPA評核項目'])['等級數值'].agg([
                    ('平均分數', 'mean'),
                    ('中位數', 'median'),
                    ('標準差', 'std'),
                    ('評分次數', 'count')
                ]).round(2)
                
                # 使用 unstack 將老師作為列，EPA 項目作為欄
                avg_scores_by_teacher = df.groupby(['評核老師', 'EPA評核項目'])['等級數值'].mean().unstack()
                
                # 顯示平均分數表格
                st.write("##### 各老師對各 EPA 項目的平均評分")
                st.dataframe(avg_scores_by_teacher.style.background_gradient(cmap='YlGnBu', axis=None))
                
                # 顯示評分次數表格
                count_by_teacher = df.groupby(['評核老師', 'EPA評核項目'])['等級數值'].count().unstack()
                st.write("##### 各老師對各 EPA 項目的評分次數")
                st.dataframe(count_by_teacher)
                

            else:
                st.info("只有一位老師的評分資料，無法進行比較")
                
            
            # 檢查是否有足夠的資料進行分析
            if 'EPA評核項目' in df.columns and '等級數值' in df.columns:
                # 計算每個EPA項目的詳細統計資料
                epa_stats = df.groupby('EPA評核項目')['等級數值'].agg([
                    ('平均數', 'mean'),
                    ('中位數', 'median'),
                    ('標準差', 'std'),
                    ('第一四分位數', lambda x: x.quantile(0.25)),
                    ('第三四分位數', lambda x: x.quantile(0.75)),
                    ('最小值', 'min'),
                    ('最大值', 'max'),
                    ('評分次數', 'count')
                ]).round(2)
                
                # 顯示統計資料表格
                st.write("#### 各EPA項目的統計資料")
                st.dataframe(epa_stats.style.background_gradient(cmap='YlGnBu', subset=['平均數', '中位數']))
                
                # 繪製箱型圖，顯示所有EPA項目的分布情況
                st.write("#### 各EPA項目的分數分布箱型圖")
                
                # 設定中文字型
                plt.rcParams['axes.unicode_minus'] = False
                
                # 創建圖形
                fig, ax = plt.subplots(figsize=(14, 8))
                
                # 使用seaborn繪製箱型圖
                sns.boxplot(x='EPA評核項目', y='等級數值', data=df, ax=ax)
                
                # 添加數據點以顯示分布
                sns.stripplot(x='EPA評核項目', y='等級數值', data=df, 
                             size=4, color=".3", linewidth=0, alpha=0.3, ax=ax)
                
                # 設定圖表屬性
                ax.set_title('各EPA項目的評分分布', fontsize=16)
                ax.set_xlabel('EPA評核項目', fontsize=12)
                ax.set_ylabel('評分等級', fontsize=12)
                ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                
                # 旋轉 x 軸標籤以避免重疊
                plt.xticks(rotation=45, ha='right')
                
                # 添加網格線以便於閱讀
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                
                # 調整布局
                plt.tight_layout()
                
                # 顯示圖表
                st.pyplot(fig)
                
                # 繪製小提琴圖，更好地顯示分布形狀
                st.write("#### 各EPA項目的分數分布小提琴圖")
                
                # 創建圖形
                fig, ax = plt.subplots(figsize=(14, 8))
                
                # 使用seaborn繪製小提琴圖
                sns.violinplot(x='EPA評核項目', y='等級數值', data=df, inner='quartile', ax=ax)
                
                # 設定圖表屬性
                ax.set_title('各EPA項目的評分分布小提琴圖', fontsize=16)
                ax.set_xlabel('EPA評核項目', fontsize=12)
                ax.set_ylabel('評分等級', fontsize=12)
                ax.set_ylim(0, 5)  # EPA 等級範圍為 0-5
                
                # 旋轉 x 軸標籤以避免重疊
                plt.xticks(rotation=45, ha='right')
                
                # 添加網格線以便於閱讀
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                
                # 調整布局
                plt.tight_layout()
                
                # 顯示圖表
                st.pyplot(fig)
                
                # 顯示每個EPA項目的分數分布直方圖
                st.write("#### 各EPA項目的分數分布直方圖")
                
                # 獲取所有EPA項目
                epa_items = sorted(df['EPA評核項目'].unique())
                
                # 計算需要的行數（每行最多3個圖表）
                n_items = len(epa_items)
                n_cols = 3
                n_rows = (n_items + n_cols - 1) // n_cols
                
                # 創建子圖
                fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
                axes = axes.flatten() if n_rows > 1 or n_cols > 1 else [axes]
                
                # 為每個EPA項目繪製直方圖
                for i, item in enumerate(epa_items):
                    if i < len(axes):
                        # 篩選該EPA項目的資料
                        item_data = df[df['EPA評核項目'] == item]['等級數值']
                        
                        # 繪製直方圖
                        sns.histplot(item_data, bins=10, kde=True, ax=axes[i])
                        
                        # 添加平均值和中位數線
                        mean_val = item_data.mean()
                        median_val = item_data.median()
                        axes[i].axvline(mean_val, color='red', linestyle='--', label=f'平均值: {mean_val:.2f}')
                        axes[i].axvline(median_val, color='green', linestyle='-.', label=f'中位數: {median_val:.2f}')
                        
                        # 設定圖表屬性
                        axes[i].set_title(f'{item}', fontsize=10)
                        axes[i].set_xlabel('評分等級')
                        axes[i].set_ylabel('頻率')
                        axes[i].set_xlim(0, 5)
                        axes[i].legend(fontsize='small')
                
                # 隱藏多餘的子圖
                for j in range(i + 1, len(axes)):
                    axes[j].set_visible(False)
                
                # 調整布局
                plt.tight_layout()
                
                # 顯示圖表
                st.pyplot(fig)
            else:
                st.warning("缺少必要欄位，無法進行EPA項目統計分析")

def calculate_statistics(df):
    """計算基本統計資訊"""
    # ... 統計計算相關程式碼 ...
    pass

def perform_statistical_tests(teacher_data, all_data):
    """執行統計檢定"""
    # ... 統計檢定相關程式碼 ...
    pass 