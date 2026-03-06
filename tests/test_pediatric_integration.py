#!/usr/bin/env python3
"""
小兒部評核系統整合測試腳本
"""

import streamlit as st
from analysis_pediatric import show_pediatric_evaluation_section

def test_pediatric_integration():
    """測試小兒部評核系統整合"""
    st.title("🧪 小兒部評核系統整合測試")
    
    st.subheader("測試說明")
    st.write("""
    此測試腳本用於驗證小兒部評核系統是否能正常載入和運行。
    
    **存取方式**:
    1. 在左邊側邊欄選擇「小兒部」
    2. 點擊「住院醫師」分頁
    3. 系統會自動顯示小兒部評核系統
    """)
    
    st.subheader("功能測試")
    
    # 測試小兒部評核系統載入
    if st.button("測試小兒部評核系統載入"):
        try:
            with st.spinner("正在載入小兒部評核系統..."):
                show_pediatric_evaluation_section()
            st.success("✅ 小兒部評核系統載入成功！")
        except Exception as e:
            st.error(f"❌ 載入失敗：{str(e)}")
    
    st.subheader("整合邏輯測試")
    
    # 模擬科別選擇邏輯
    st.write("**科別選擇邏輯測試**")
    
    selected_dept = st.selectbox(
        "選擇科別（模擬側邊欄選擇）",
        ["小兒部", "內科", "外科", "麻醉科", "其他科別"]
    )
    
    if selected_dept == "小兒部":
        st.success("✅ 選擇小兒部 - 將顯示小兒部評核系統")
        st.info("在實際系統中，這會觸發 `show_pediatric_evaluation_section()` 函數")
        
        # 顯示小兒部評核系統
        with st.expander("小兒部評核系統預覽", expanded=True):
            show_pediatric_evaluation_section()
    else:
        st.info(f"選擇 {selected_dept} - 將顯示一般住院醫師分析")
        st.write("在實際系統中，這會顯示對應科別的住院醫師分析功能")
    
    st.subheader("系統狀態檢查")
    
    # 檢查必要的模組
    try:
        from analysis_pediatric import (
            PEDIATRIC_SKILL_REQUIREMENTS,
            load_pediatric_data,
            process_pediatric_data
        )
        st.success("✅ 小兒部評核模組載入成功")
        
        # 顯示技能要求
        st.write("**支援的技能項目**")
        skill_df = st.dataframe(
            pd.DataFrame([
                {'技能項目': skill, '最少次數': data['minimum'], '說明': data['description']}
                for skill, data in PEDIATRIC_SKILL_REQUIREMENTS.items()
            ]),
            width="stretch"
        )
        
    except ImportError as e:
        st.error(f"❌ 模組載入失敗：{str(e)}")
    except Exception as e:
        st.error(f"❌ 其他錯誤：{str(e)}")

def main():
    """主函數"""
    st.set_page_config(
        page_title="小兒部整合測試",
        layout="wide"
    )
    
    test_pediatric_integration()

if __name__ == "__main__":
    import pandas as pd
    main()
