#!/usr/bin/env python3
"""
測試技能顯示格式腳本
"""

import streamlit as st
import pandas as pd
from analysis_pediatric import PEDIATRIC_SKILL_REQUIREMENTS, show_skill_progress

def test_skill_display():
    """測試技能顯示格式"""
    st.title("🧪 技能顯示格式測試")
    
    st.subheader("測試說明")
    st.write("""
    此測試展示優化後的技能顯示格式：
    1. 每個技能先顯示標題
    2. 然後顯示完成度資訊
    3. 使用分隔線區分不同技能
    """)
    
    # 模擬技能完成數據
    skill_counts = {}
    for skill, data in PEDIATRIC_SKILL_REQUIREMENTS.items():
        # 模擬不同的完成狀況
        if skill == "插氣管內管":
            completed = 0
        elif skill == "插臍(動靜脈)導管":
            completed = 0
        elif skill == "腰椎穿刺":
            completed = 1
        elif skill == "插中心靜脈導管(CVC)":
            completed = 0
        elif skill == "腦部超音波":
            completed = 3
        elif skill == "心臟超音波":
            completed = 5
        else:
            completed = 2
        
        skill_counts[skill] = {
            'completed': completed,
            'required': data['minimum'],
            'description': data['description'],
            'progress': min(completed / data['minimum'] * 100, 100)
        }
    
    st.subheader("技能完成進度顯示測試")
    
    # 顯示技能進度
    show_skill_progress(skill_counts, "測試住院醫師")
    
    st.subheader("顯示格式特點")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **✅ 優化後的格式**:
        - 技能標題使用 `###` 標題格式
        - 技能描述使用 `caption` 顯示
        - 完成度資訊清晰分離
        - 使用分隔線區分技能
        - 進度條和狀態指示更清楚
        """)
    
    with col2:
        st.markdown("""
        **📊 顯示內容**:
        - 技能名稱（標題）
        - 技能描述（說明）
        - 進度條（視覺化）
        - 完成狀態（文字）
        - 統計數據（數字）
        """)
    
    st.subheader("技能要求清單")
    
    # 顯示技能要求表格
    skill_data = []
    for skill, data in PEDIATRIC_SKILL_REQUIREMENTS.items():
        skill_data.append({
            '技能項目': skill,
            '最少次數': data['minimum'],
            '說明': data['description']
        })
    
    skill_df = pd.DataFrame(skill_data)
    st.dataframe(skill_df, width="stretch")

def main():
    """主函數"""
    st.set_page_config(
        page_title="技能顯示測試",
        layout="wide"
    )
    
    test_skill_display()

if __name__ == "__main__":
    main()
