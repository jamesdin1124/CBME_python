#!/usr/bin/env python3
"""
小兒科住院醫師技能追蹤功能演示
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date

# 小兒科住院醫師技能基本要求
PEDIATRIC_SKILL_REQUIREMENTS = {
    '插氣管內管': {'minimum': 3, 'description': '訓練期間最少3次'},
    '插臍(動靜脈)導管': {'minimum': 1, 'description': '訓練期間最少1次'},
    '腰椎穿刺': {'minimum': 3, 'description': 'PGY2/R1 訓練期間最少3次'},
    '插中心靜脈導管(CVC)': {'minimum': 3, 'description': '訓練期間最少3次'},
    '肋膜液或是腹水抽取': {'minimum': 1, 'description': '訓練期間最少1次'},
    '插胸管': {'minimum': 2, 'description': '訓練期間最少2次'},
    '放置動脈導管': {'minimum': 2, 'description': '訓練期間最少2次'},
    '經皮式中央靜脈導管(PICC)': {'minimum': 3, 'description': '訓練期間最少3次'},
    '腦部超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '心臟超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '腹部超音波': {'minimum': 5, 'description': '訓練期間最少5次'},
    '腎臟超音波': {'minimum': 5, 'description': '訓練期間最少5次'}
}

def create_demo_data():
    """創建演示資料"""
    demo_data = {
        '受評核人員': [
            '林盈秀', '林盈秀', '林盈秀', '林盈秀', '林盈秀', '林盈秀', '林盈秀',
            '張三', '張三', '張三', '張三', '張三',
            '李四', '李四', '李四'
        ],
        '評核日期': [
            '2025/9/1', '2025/9/2', '2025/9/3', '2025/9/4', '2025/9/5', '2025/9/6', '2025/9/7',
            '2025/9/1', '2025/9/2', '2025/9/3', '2025/9/4', '2025/9/5',
            '2025/9/1', '2025/9/2', '2025/9/3'
        ],
        '評核教師': [
            '丁肇壯', '王小明', '丁肇壯', '王小明', '丁肇壯', '王小明', '丁肇壯',
            '李老師', '李老師', '李老師', '李老師', '李老師',
            '陳醫師', '陳醫師', '陳醫師'
        ],
        '評核技術項目': [
            '腎臟超音波（訓練期間最少5次）',
            '心臟超音波（訓練期間最少5次）',
            '腎臟超音波（訓練期間最少5次）',
            '插氣管內管（訓練期間最少3次）',
            '腎臟超音波（訓練期間最少5次）',
            '腹部超音波（訓練期間最少5次）',
            '腎臟超音波（訓練期間最少5次）',
            '腹部超音波（訓練期間最少5次）',
            '插中心靜脈導管(CVC)（訓練期間最少3次）',
            '腹部超音波（訓練期間最少5次）',
            '插中心靜脈導管(CVC)（訓練期間最少3次）',
            '腹部超音波（訓練期間最少5次）',
            '插氣管內管（訓練期間最少3次）',
            '插氣管內管（訓練期間最少3次）',
            '插氣管內管（訓練期間最少3次）'
        ],
        '熟練程度': [
            '熟練', '基本熟練', '熟練', '部分熟練', '熟練', '基本熟練', '熟練',
            '基本熟練', '初學', '基本熟練', '初學', '基本熟練',
            '熟練', '熟練', '熟練'
        ],
        '操作技術教師回饋': [
            '基本操作已經熟練，對於都普勒檢查判讀可再查閱相關書籍',
            '需要更多練習',
            '表現良好',
            '需要指導',
            '非常熟練',
            '還需要加強',
            '基本操作已經熟練',
            '還需要加強',
            '需要更多練習',
            '還需要加強',
            '需要更多練習',
            '還需要加強',
            '表現優秀',
            '表現優秀',
            '表現優秀'
        ]
    }
    
    return pd.DataFrame(demo_data)

def calculate_skill_counts(resident_data):
    """計算住院醫師各項技能完成次數"""
    skill_counts = {}
    
    # 從評核技術項目欄位中提取技能資訊
    if '評核技術項目' in resident_data.columns:
        technical_items = resident_data['評核技術項目'].dropna()
        
        for skill in PEDIATRIC_SKILL_REQUIREMENTS.keys():
            # 計算該技能出現的次數
            count = 0
            for item in technical_items:
                if skill in str(item):
                    count += 1
            
            skill_counts[skill] = {
                'completed': count,
                'required': PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum'],
                'description': PEDIATRIC_SKILL_REQUIREMENTS[skill]['description'],
                'progress': min(count / PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum'] * 100, 100)
            }
    
    return skill_counts

def show_skill_dashboard():
    """顯示技能追蹤儀表板"""
    st.title("🎯 小兒科住院醫師技能追蹤演示")
    st.markdown("---")
    
    # 載入演示資料
    demo_df = create_demo_data()
    
    st.subheader("📊 演示資料概覽")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("總評核記錄", len(demo_df))
    with col2:
        st.metric("住院醫師數", len(demo_df['受評核人員'].unique()))
    with col3:
        st.metric("評核教師數", len(demo_df['評核教師'].unique()))
    
    # 選擇住院醫師
    st.subheader("👥 選擇住院醫師進行技能追蹤")
    residents = sorted(demo_df['受評核人員'].unique())
    selected_resident = st.selectbox("選擇住院醫師", residents)
    
    if selected_resident:
        # 篩選該人員的資料
        resident_data = demo_df[demo_df['受評核人員'] == selected_resident]
        
        st.subheader(f"技能追蹤 - {selected_resident}")
        
        # 顯示該住院醫師的評核記錄
        with st.expander("評核記錄詳情", expanded=False):
            st.dataframe(resident_data, use_container_width=True)
        
        # 計算技能完成次數
        skill_counts = calculate_skill_counts(resident_data)
        
        # 顯示技能完成狀況
        show_skill_progress(skill_counts, selected_resident)
        
        # 顯示技能完成度統計
        show_skill_completion_stats(skill_counts)

def show_skill_progress(skill_counts, resident_name):
    """顯示技能進度條"""
    st.subheader("📈 技能完成進度")
    
    # 創建進度條
    for skill, data in skill_counts.items():
        if data['completed'] > 0:  # 只顯示有記錄的技能
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{skill}**")
                st.caption(data['description'])
                
                # 進度條
                progress = data['progress'] / 100
                st.progress(progress)
                
                # 狀態指示
                if data['completed'] >= data['required']:
                    st.success(f"✅ 已完成 ({data['completed']}/{data['required']})")
                else:
                    remaining = data['required'] - data['completed']
                    st.warning(f"⚠️ 還需 {remaining} 次 ({data['completed']}/{data['required']})")
            
            with col2:
                st.metric("已完成", data['completed'])
            
            with col3:
                st.metric("需完成", data['required'])

def show_skill_completion_stats(skill_counts):
    """顯示技能完成度統計"""
    st.subheader("📊 技能完成度統計")
    
    # 計算統計資料
    total_skills = len(skill_counts)
    completed_skills = sum(1 for data in skill_counts.values() if data['completed'] >= data['required'])
    in_progress_skills = total_skills - completed_skills
    
    # 顯示統計卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總技能數", total_skills)
    
    with col2:
        st.metric("已完成技能", completed_skills)
    
    with col3:
        st.metric("進行中技能", in_progress_skills)
    
    with col4:
        completion_rate = (completed_skills / total_skills * 100) if total_skills > 0 else 0
        st.metric("完成率", f"{completion_rate:.1f}%")
    
    # 技能完成度圖表
    if skill_counts:
        # 準備圖表資料
        skills = list(skill_counts.keys())
        completed = [data['completed'] for data in skill_counts.values()]
        required = [data['required'] for data in skill_counts.values()]
        
        # 創建長條圖
        fig = go.Figure()
        
        # 已完成次數
        fig.add_trace(go.Bar(
            name='已完成',
            x=skills,
            y=completed,
            marker_color='lightgreen'
        ))
        
        # 需要完成次數
        fig.add_trace(go.Bar(
            name='需要完成',
            x=skills,
            y=required,
            marker_color='lightcoral',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="技能完成次數對比",
            xaxis_title="技能項目",
            yaxis_title="次數",
            barmode='group',
            height=500,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 技能完成度圓餅圖
        fig_pie = go.Figure(data=[go.Pie(
            labels=['已完成', '進行中'],
            values=[completed_skills, in_progress_skills],
            marker_colors=['lightgreen', 'lightcoral']
        )])
        
        fig_pie.update_layout(
            title="技能完成狀況分布",
            height=400
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)

def show_skill_requirements():
    """顯示技能要求清單"""
    st.subheader("📋 小兒科住院醫師技能基本要求")
    
    # 創建技能要求表格
    skill_data = []
    for skill, data in PEDIATRIC_SKILL_REQUIREMENTS.items():
        skill_data.append({
            '技能項目': skill,
            '最少次數': data['minimum'],
            '說明': data['description']
        })
    
    skill_df = pd.DataFrame(skill_data)
    st.dataframe(skill_df, use_container_width=True)
    
    # 技能分類統計
    st.subheader("技能分類統計")
    
    # 按最少次數分類
    category_stats = skill_df.groupby('最少次數').size().reset_index(name='技能數量')
    category_stats['分類'] = category_stats['最少次數'].apply(
        lambda x: f"需要{x}次" if x == 1 else f"需要{x}次"
    )
    
    fig = px.pie(
        category_stats,
        values='技能數量',
        names='分類',
        title="技能要求次數分布"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    """主函數"""
    st.set_page_config(
        page_title="小兒科技能追蹤演示",
        layout="wide"
    )
    
    # 創建分頁
    tab1, tab2, tab3 = st.tabs(["技能追蹤儀表板", "技能要求清單", "系統說明"])
    
    with tab1:
        show_skill_dashboard()
    
    with tab2:
        show_skill_requirements()
    
    with tab3:
        st.subheader("🔧 系統說明")
        
        st.markdown("""
        ### 功能特色
        
        1. **自動技能識別**: 系統會自動從「評核技術項目」欄位中識別對應的技能
        2. **進度追蹤**: 即時顯示每個技能的完成進度和剩餘次數
        3. **視覺化展示**: 使用進度條和圖表直觀顯示技能完成狀況
        4. **統計分析**: 提供技能完成率統計和趨勢分析
        
        ### 技能項目
        
        系統支援以下12項小兒科住院醫師基本技能：
        
        - **插氣管內管** (最少3次)
        - **插臍(動靜脈)導管** (最少1次)
        - **腰椎穿刺** (PGY2/R1 最少3次)
        - **插中心靜脈導管(CVC)** (最少3次)
        - **肋膜液或是腹水抽取** (最少1次)
        - **插胸管** (最少2次)
        - **放置動脈導管** (最少2次)
        - **經皮式中央靜脈導管(PICC)** (最少3次)
        - **腦部超音波** (最少5次)
        - **心臟超音波** (最少5次)
        - **腹部超音波** (最少5次)
        - **腎臟超音波** (最少5次)
        
        ### 使用方法
        
        1. 在評核表單的「評核技術項目」欄位中選擇或填寫技能項目
        2. 系統會自動識別並計算該技能的完成次數
        3. 在技能追蹤頁面查看個人技能完成進度
        4. 使用統計分析功能了解整體技能完成狀況
        """)

if __name__ == "__main__":
    main()
