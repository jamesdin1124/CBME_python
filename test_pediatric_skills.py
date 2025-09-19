#!/usr/bin/env python3
"""
小兒科住院醫師技能追蹤測試腳本
"""

import streamlit as st
import pandas as pd
from pediatric_evaluation import (
    PEDIATRIC_SKILL_REQUIREMENTS,
    calculate_skill_counts,
    show_skill_progress,
    show_skill_completion_stats
)

def test_skill_tracking():
    """測試技能追蹤功能"""
    st.title("🧪 小兒科住院醫師技能追蹤測試")
    
    # 創建測試資料
    test_data = {
        '受評核人員': ['林盈秀', '林盈秀', '林盈秀', '林盈秀', '林盈秀', '張三', '張三'],
        '評核日期': ['2025/9/1', '2025/9/2', '2025/9/3', '2025/9/4', '2025/9/5', '2025/9/1', '2025/9/2'],
        '評核教師': ['丁肇壯', '王小明', '丁肇壯', '王小明', '丁肇壯', '李老師', '李老師'],
        '評核技術項目': [
            '腎臟超音波（訓練期間最少5次）',
            '心臟超音波（訓練期間最少5次）',
            '腎臟超音波（訓練期間最少5次）',
            '插氣管內管（訓練期間最少3次）',
            '腎臟超音波（訓練期間最少5次）',
            '腹部超音波（訓練期間最少5次）',
            '插中心靜脈導管(CVC)（訓練期間最少3次）'
        ],
        '熟練程度': ['熟練', '基本熟練', '熟練', '部分熟練', '熟練', '基本熟練', '初學'],
        '操作技術教師回饋': [
            '基本操作已經熟練',
            '需要更多練習',
            '表現良好',
            '需要指導',
            '非常熟練',
            '還需要加強',
            '需要更多練習'
        ]
    }
    
    test_df = pd.DataFrame(test_data)
    
    st.subheader("測試資料")
    st.dataframe(test_df)
    
    # 測試技能要求清單
    st.subheader("技能要求清單")
    skill_df = pd.DataFrame([
        {'技能項目': skill, '最少次數': data['minimum'], '說明': data['description']}
        for skill, data in PEDIATRIC_SKILL_REQUIREMENTS.items()
    ])
    st.dataframe(skill_df, use_container_width=True)
    
    # 測試個別住院醫師技能追蹤
    st.subheader("個別住院醫師技能追蹤測試")
    
    residents = test_df['受評核人員'].unique()
    selected_resident = st.selectbox("選擇住院醫師", residents)
    
    if selected_resident:
        resident_data = test_df[test_df['受評核人員'] == selected_resident]
        
        st.write(f"**{selected_resident} 的評核記錄**")
        st.dataframe(resident_data)
        
        # 計算技能完成次數
        skill_counts = calculate_skill_counts(resident_data)
        
        if skill_counts:
            st.write("**技能完成狀況**")
            
            # 顯示技能進度
            for skill, data in skill_counts.items():
                if data['completed'] > 0:  # 只顯示有記錄的技能
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{skill}**")
                        progress = data['progress'] / 100
                        st.progress(progress)
                        
                        if data['completed'] >= data['required']:
                            st.success(f"✅ 已完成 ({data['completed']}/{data['required']})")
                        else:
                            remaining = data['required'] - data['completed']
                            st.warning(f"⚠️ 還需 {remaining} 次 ({data['completed']}/{data['required']})")
                    
                    with col2:
                        st.metric("已完成", data['completed'])
                    
                    with col3:
                        st.metric("需完成", data['required'])
            
            # 顯示統計
            total_skills = len(skill_counts)
            completed_skills = sum(1 for data in skill_counts.values() if data['completed'] >= data['required'])
            completion_rate = (completed_skills / total_skills * 100) if total_skills > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("總技能數", total_skills)
            with col2:
                st.metric("已完成技能", completed_skills)
            with col3:
                st.metric("進行中技能", total_skills - completed_skills)
            with col4:
                st.metric("完成率", f"{completion_rate:.1f}%")
        else:
            st.info("該住院醫師目前沒有技能評核記錄")

def test_skill_matching():
    """測試技能匹配功能"""
    st.subheader("技能匹配測試")
    
    test_items = [
        '腎臟超音波（訓練期間最少5次）',
        '心臟超音波（訓練期間最少5次）',
        '插氣管內管（訓練期間最少3次）',
        '插中心靜脈導管(CVC)（訓練期間最少3次）',
        '腹部超音波（訓練期間最少5次）',
        '其他技能項目'
    ]
    
    st.write("**測試項目**")
    for item in test_items:
        st.write(f"- {item}")
    
    st.write("**匹配結果**")
    for item in test_items:
        matched_skills = []
        for skill in PEDIATRIC_SKILL_REQUIREMENTS.keys():
            if skill in item:
                matched_skills.append(skill)
        
        if matched_skills:
            st.write(f"✅ {item} → 匹配到: {', '.join(matched_skills)}")
        else:
            st.write(f"❌ {item} → 無匹配技能")

def main():
    """主測試函數"""
    st.set_page_config(
        page_title="小兒科技能追蹤測試",
        layout="wide"
    )
    
    # 創建分頁
    tab1, tab2 = st.tabs(["技能追蹤測試", "技能匹配測試"])
    
    with tab1:
        test_skill_tracking()
    
    with tab2:
        test_skill_matching()

if __name__ == "__main__":
    main()
