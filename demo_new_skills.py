#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示新增技能項目功能
"""

import streamlit as st
import pandas as pd
import sys
import os

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis_pediatric import PEDIATRIC_SKILL_REQUIREMENTS, calculate_skill_counts

def main():
    st.set_page_config(
        page_title="新增技能項目演示",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 小兒部評核系統 - 新增技能項目演示")
    st.markdown("---")
    
    # 顯示所有技能要求
    st.header("📋 技能要求清單")
    
    # 創建技能要求DataFrame
    skill_data = []
    for skill, details in PEDIATRIC_SKILL_REQUIREMENTS.items():
        skill_data.append({
            '技能項目': skill,
            '最少次數': details['minimum'],
            '描述': details['description']
        })
    
    skill_df = pd.DataFrame(skill_data)
    
    # 按最少次數排序
    skill_df = skill_df.sort_values('最少次數')
    
    # 顯示表格
    st.dataframe(skill_df, use_container_width=True)
    
    # 高亮新增的技能
    st.subheader("🆕 新增技能項目")
    new_skills = ['病歷書寫', 'NRP']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**病歷書寫**\n\n- 訓練期間最少10次\n- 重要臨床技能")
    
    with col2:
        st.info("**NRP (新生兒復甦計畫)**\n\n- 訓練期間最少10次\n- 關鍵急救技能")
    
    # 技能分組統計
    st.subheader("📊 技能分組統計")
    
    # 按最少次數分組
    skill_groups = {}
    for skill, details in PEDIATRIC_SKILL_REQUIREMENTS.items():
        minimum = details['minimum']
        if minimum not in skill_groups:
            skill_groups[minimum] = []
        skill_groups[minimum].append(skill)
    
    # 顯示分組統計
    for minimum in sorted(skill_groups.keys()):
        skills = skill_groups[minimum]
        st.write(f"**{minimum}次 ({len(skills)}個技能)**: {', '.join(skills)}")
    
    # 模擬技能完成情況
    st.subheader("🎯 技能完成情況模擬")
    
    # 模擬數據
    simulated_data = [
        {'評核技術項目': '病歷書寫（訓練期間最少10次）', '受評核人員': '林小明', '評核日期': '2025-01-15'},
        {'評核技術項目': '病歷書寫（訓練期間最少10次）', '受評核人員': '林小明', '評核日期': '2025-01-20'},
        {'評核技術項目': 'NRP（訓練期間最少10次）', '受評核人員': '林小明', '評核日期': '2025-01-18'},
        {'評核技術項目': '腎臟超音波（訓練期間最少5次）', '受評核人員': '林小明', '評核日期': '2025-01-16'},
    ]
    
    # 計算技能完成情況
    skill_counts = calculate_skill_counts(simulated_data)
    
    # 顯示完成情況
    st.write("**林小明 技能完成情況：**")
    for skill, count in skill_counts.items():
        if skill in PEDIATRIC_SKILL_REQUIREMENTS:
            required = PEDIATRIC_SKILL_REQUIREMENTS[skill]['minimum']
            progress = min(count / required, 1.0)
            status = "✅ 已完成" if count >= required else f"⏳ 進行中 ({count}/{required})"
            
            st.write(f"- **{skill}**: {count}次 / {required}次 {status}")
    
    st.markdown("---")
    st.success("✅ 新增技能項目功能已成功整合到小兒部評核系統中！")

if __name__ == "__main__":
    main()
