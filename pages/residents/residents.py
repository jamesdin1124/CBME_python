import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_resident_analysis_section(df=None):
    st.header("住院醫師學習分析")
    
    if df is None:
        st.warning("請先載入資料")
        return
    
    # 重新命名欄位以符合上傳的 Excel 格式
    expected_columns = [
        "時間戳記", "評核教師", "評核日期", "操作項目", 
        "受評核人員", "操作時級職", "病歷號", "可信賴程度"
    ]
    
    # 檢查是否包含所需欄位
    if not all(col in df.columns for col in expected_columns):
        st.error("上傳的檔案格式不符，請確認是否包含所有必要欄位：\n" + "\n".join(expected_columns))
        return
    
    # 基本資料統計
    st.subheader("基本統計資料")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總評核次數", len(df))
    with col2:
        st.metric("住院醫師人數", df['受評核人員'].nunique())
    with col3:
        st.metric("評核教師人數", df['評核教師'].nunique())
    
    # 資料篩選器
    st.subheader("資料篩選")
    col1, col2 = st.columns(2)
    with col1:
        selected_resident = st.multiselect(
            "選擇住院醫師",
            options=sorted(df['受評核人員'].unique()),
            default=None
        )
    with col2:
        selected_level = st.multiselect(
            "選擇級職",
            options=sorted(df['操作時級職'].unique()),
            default=None
        )
    
    # 篩選資料
    filtered_df = df.copy()
    if selected_resident:
        filtered_df = filtered_df[filtered_df['受評核人員'].isin(selected_resident)]
    if selected_level:
        filtered_df = filtered_df[filtered_df['操作時級職'].isin(selected_level)]
    
    # 顯示篩選後的資料
    st.subheader("評核紀錄")
    st.dataframe(
        filtered_df,
        column_config={
            "時間戳記": st.column_config.DatetimeColumn("時間戳記", format="YYYY/MM/DD HH:mm"),
            "評核日期": st.column_config.DateColumn("評核日期", format="YYYY/MM/DD"),
            "可信賴程度": st.column_config.NumberColumn("可信賴程度", help="1-5分"),
        },
        hide_index=True
    )
    
    # 可信賴程度分析
    st.subheader("可信賴程度分析")
    col1, col2 = st.columns(2)
    
    # 定義可信賴程度的順序
    trust_level_order = ["1 僅能觀察", "2 當助手", "3 協助下完成", "4 可獨力完成", "5 可指導他人"]
    # 定義級職的順序
    position_order = ["R1", "R2", "R3"]
    
    with col1:
        # 各級職可信賴程度平均值
        fig_level = px.box(
            filtered_df,
            x="操作時級職",
            y="可信賴程度",
            title="各級職可信賴程度分布",
            category_orders={"操作時級職": position_order},
            labels={"操作時級職": "操作時級職", "可信賴程度": "可信賴程度"}
        )
        fig_level.update_yaxes(
            categoryorder="array",
            categoryarray=trust_level_order
        )
        st.plotly_chart(fig_level)
    
    with col2:
        # 建立可信賴程度的對照表
        trust_level_mapping = {
            "僅能觀察": 1,
            "當助手": 2,
            "協助下完成": 3,
            "可獨力完成": 4,
            "可指導他人": 5,
            "1 僅能觀察": 1,
            "2 當助手": 2,
            "3 協助下完成": 3,
            "4 可獨力完成": 4,
            "5 可指導他人": 5
        }
        
        # 複製並轉換資料
        plotting_df = filtered_df.copy()
        plotting_df['可信賴程度'] = plotting_df['可信賴程度'].map(trust_level_mapping)
        
        # 計算每個操作項目最後三次評核的平均可信賴程度
        last_three_avg = (
            plotting_df.sort_values('評核日期')
            .groupby('操作項目')
            .tail(3)  # 取每個操作項目最後三次評核
            .groupby('操作項目')['可信賴程度']
            .mean()
            .reset_index()
        )
        
        # 繪製操作項目最後三次平均可信賴程度的圖表
        fig_item = px.bar(
            last_three_avg,
            x="操作項目",
            y="可信賴程度",
            title="各操作項目最後三次評核平均可信賴程度",
            labels={"操作項目": "操作項目", "可信賴程度": "可信賴程度"}
        )
        
        # 更新Y軸設定
        fig_item.update_yaxes(
            range=[0.5, 5.5],
            ticktext=["1 僅能觀察", "2 當助手", "3 協助下完成", "4 可獨力完成", "5 可指導他人"],
            tickvals=[1, 2, 3, 4, 5],
            tickmode="array"
        )
        
        # 更新X軸標籤角度
        fig_item.update_layout(
            xaxis_tickangle=-45,
            height=400
        )
        
        # 顯示圖表
        st.plotly_chart(fig_item, width="stretch")
    
    # 定義必要操作項目和最少次數
    required_procedures = {
        "插氣管內管": 3,
        "Umbilical catheterization (動靜脈)": 1,
        "腰椎穿刺(R1)": 3,
        "CVP": 3,
        "肋膜液或腹水抽取": 1,
        "插胸管": 2,
        "經皮式中央靜脈導管": 3,
        "放置動脈導管": 2,
        "腎臟超音波": 5,
        "腦部超音波": 5,
        "腹部超音波": 5,
        "心臟超音波": 5
    }

    # 新增操作項目完成進度分析
    st.subheader("操作項目完成進度")
    
    if selected_resident:
        for resident in selected_resident:
            st.write(f"### {resident} 的操作項目完成狀況")
            
            # 計算該住院醫師每個項目的完成次數
            resident_df = plotting_df[plotting_df['受評核人員'] == resident]
            procedure_counts = resident_df['操作項目'].value_counts().to_dict()
            
            # 創建進度表格資料
            progress_data = []
            for procedure, required_count in required_procedures.items():
                # 取得該操作項目的所有評核記錄
                procedure_records = resident_df[resident_df['操作項目'] == procedure]
                
                # 計算完成次數和百分比
                completed_count = procedure_counts.get(procedure, 0)
                completion_percentage = (completed_count / required_count) * 100
                
                # 計算最後三次評核的平均可信賴程度
                last_three_avg = 0
                if not procedure_records.empty:
                    last_three = procedure_records.nlargest(3, '評核日期')
                    if not last_three.empty:
                        last_three_avg = last_three['可信賴程度'].mean()
                        last_three_avg = round(last_three_avg, 1)
                
                # 取得所有病歷號並排序
                chart_numbers = procedure_records['病歷號'].sort_values().tolist()
                chart_numbers_str = ', '.join(map(str, chart_numbers)) if chart_numbers else '-'
                
                # 設定完成度的顏色標記
                status = f"{completion_percentage:.0f}%"
                if completion_percentage >= 100:
                    status = f"🌟 {status}"
                elif completion_percentage >= 50:
                    status = f"📈 {status}"
                else:
                    status = f"📊 {status}"
                
                progress_data.append({
                    "操作項目": procedure,
                    "完成次數": completed_count,
                    "要求次數": required_count,
                    "達成狀態": status,
                    "近三次平均": last_three_avg,
                    "病歷號": chart_numbers_str
                })
            
            # 顯示進度表格
            progress_df = pd.DataFrame(progress_data)
            st.dataframe(
                progress_df,
                column_config={
                    "操作項目": st.column_config.TextColumn(
                        "操作項目",
                        help="需要完成的技術項目"
                    ),
                    "完成次數": st.column_config.NumberColumn(
                        "完成次數",
                        help="已完成的操作次數"
                    ),
                    "要求次數": st.column_config.NumberColumn(
                        "要求次數",
                        help="最少需要完成的次數"
                    ),
                    "達成狀態": st.column_config.TextColumn(
                        "達成狀態",
                        help="🌟: 已超過要求次數 | 📈: 達成50%以上 | 📊: 進行中"
                    ),
                    "近三次平均": st.column_config.NumberColumn(
                        "近三次平均",
                        help="最後三次評核的平均可信賴程度",
                        format="%.1f"
                    ),
                    "病歷號": st.column_config.TextColumn(
                        "病歷號",
                        help="所有相關病歷號",
                        width="large"  # 設定欄位寬度
                    )
                },
                hide_index=True
            )
            
            # 計算總體完成進度
            total_completed_percentage = sum(
                min(procedure_counts.get(procedure, 0) / required_count, 1.0) 
                for procedure, required_count in required_procedures.items()
            ) / len(required_procedures) * 100
            
            # 顯示總體進度
            st.progress(min(total_completed_percentage / 100, 1.0))
            st.write(f"總體完成進度：{total_completed_percentage:.0f}%")
            
            # 如果總進度達到100%，顯示祝賀訊息
            if total_completed_percentage >= 100:
                st.balloons()
                st.success("🎉 恭喜！已完成所有必要操作項目的最低要求！")
    else:
        st.info("請在上方選擇住院醫師以查看其操作項目完成進度") 

    # 新增單一操作項目分析
    st.subheader("單一操作項目分析")
    
    # 選擇要分析的操作項目
    selected_procedure = st.selectbox(
        "選擇操作項目",
        options=sorted(df['操作項目'].unique())
    )
    
    # 篩選選定的操作項目資料
    procedure_df = plotting_df[plotting_df['操作項目'] == selected_procedure].copy()
    
    # 計算每位住院醫師在每個級職的平均值
    avg_by_level = procedure_df.groupby(['受評核人員', '操作時級職'])['可信賴程度'].mean().reset_index()
    
    # 繪製該操作項目的散點圖和折線圖
    fig_procedure = go.Figure()
    
    # 取得所有住院醫師列表（不受篩選影響）
    all_residents = sorted(df['受評核人員'].unique())
    
    # 為每位住院醫師添加散點和折線
    for resident in all_residents:
        resident_data = procedure_df[procedure_df['受評核人員'] == resident]
        resident_avg = avg_by_level[avg_by_level['受評核人員'] == resident]
        
        # 添加散點
        fig_procedure.add_trace(go.Scatter(
            x=resident_data['操作時級職'],
            y=resident_data['可信賴程度'],
            mode='markers',
            name=f'{resident} (評核點)',
            legendgroup=resident,
            marker=dict(size=10),
            showlegend=True
        ))
        
        # 添加折線（連接平均值）
        if not resident_avg.empty:  # 只有在有資料時才添加折線
            fig_procedure.add_trace(go.Scatter(
                x=resident_avg['操作時級職'],
                y=resident_avg['可信賴程度'],
                mode='lines+markers',
                name=f'{resident} (平均)',
                legendgroup=resident,
                line=dict(width=2),
                marker=dict(size=8, symbol='diamond'),
                showlegend=True
            ))
    
    # 更新圖表設定
    fig_procedure.update_layout(
        title=f"{selected_procedure} 各級職可信賴程度分布",
        xaxis=dict(
            title="操作時級職",
            ticktext=["R1", "R2", "R3"],
            tickvals=["R1", "R2", "R3"],
            tickmode="array",
            categoryorder='array',
            categoryarray=["R1", "R2", "R3"]
        ),
        yaxis=dict(
            title="可信賴程度",
            range=[0.5, 5.5],
            ticktext=["1 僅能觀察", "2 當助手", "3 協助下完成", "4 可獨力完成", "5 可指導他人"],
            tickvals=[1, 2, 3, 4, 5],
            tickmode="array"
        ),
        height=600,  # 加大圖表高度
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            groupclick="toggleitem"  # 允許單獨切換每條線的顯示
        ),
        hovermode='closest'
    )
    
    # 顯示圖表
    st.plotly_chart(fig_procedure, width="stretch")
    
    # 顯示該操作項目的統計資訊
    st.subheader(f"{selected_procedure} 統計資訊")
    col1, col2 = st.columns(2)
    
    with col1:
        # 計算每位住院醫師的評核次數（顯示所有住院醫師）
        eval_counts = pd.DataFrame(index=all_residents)
        procedure_counts = procedure_df['受評核人員'].value_counts()
        eval_counts['次數'] = procedure_counts
        eval_counts = eval_counts.fillna(0).astype(int)
        eval_counts = eval_counts.reset_index().rename(columns={'index': '住院醫師'})
        st.write("評核次數：")
        st.dataframe(eval_counts)
    
    with col2:
        # 計算每位住院醫師的平均可信賴程度（顯示所有住院醫師）
        avg_trust = pd.DataFrame(index=all_residents)
        procedure_avg = procedure_df.groupby('受評核人員')['可信賴程度'].mean()
        avg_trust['平均分數'] = procedure_avg
        avg_trust = avg_trust.fillna(0).round(2)
        avg_trust = avg_trust.reset_index().rename(columns={'index': '住院醫師'})
        st.write("平均可信賴程度：")
        st.dataframe(avg_trust) 