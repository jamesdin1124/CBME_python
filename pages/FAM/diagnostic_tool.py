#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
家醫部系統診斷工具

用於診斷和修復家醫部系統的資料載入問題
"""

import streamlit as st
import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def show_diagnostic_tool():
    """顯示診斷工具介面"""
    st.title("🔧 家醫部系統診斷工具")
    st.markdown("---")
    
    st.info("此工具用於診斷家醫部EPA評核系統的資料載入問題")
    
    # Session State 檢查
    st.subheader("📋 Session State 檢查")
    
    # 檢查相關的session state keys
    data_keys = [key for key in st.session_state.keys() if 'data' in key.lower()]
    
    if data_keys:
        st.write("✅ 找到以下資料相關的session state keys:")
        for key in data_keys:
            data = st.session_state[key]
            if isinstance(data, pd.DataFrame):
                st.write(f"  - **{key}**: DataFrame, 形狀: {data.shape}")
            else:
                st.write(f"  - **{key}**: {type(data)}")
    else:
        st.warning("❌ 沒有找到任何資料相關的session state keys")
    
    # 檢查特定的家醫部資料
    st.subheader("🏥 家醫部資料檢查")
    
    fam_data_found = False
    
    # 檢查 fam_data
    if 'fam_data' in st.session_state:
        st.write("✅ 找到 `fam_data`")
        fam_data = st.session_state.fam_data
        if isinstance(fam_data, pd.DataFrame):
            st.write(f"  - 資料形狀: {fam_data.shape}")
            st.write(f"  - 欄位: {list(fam_data.columns)}")
            fam_data_found = True
        else:
            st.write(f"  - 資料類型: {type(fam_data)}")
    else:
        st.write("❌ 沒有找到 `fam_data`")
    
    # 檢查 家醫部_data
    if '家醫部_data' in st.session_state:
        st.write("✅ 找到 `家醫部_data`")
        fam_data = st.session_state['家醫部_data']
        if isinstance(fam_data, pd.DataFrame):
            st.write(f"  - 資料形狀: {fam_data.shape}")
            st.write(f"  - 欄位: {list(fam_data.columns)}")
            fam_data_found = True
        else:
            st.write(f"  - 資料類型: {type(fam_data)}")
    else:
        st.write("❌ 沒有找到 `家醫部_data`")
    
    # 檢查 merged_data
    if 'merged_data' in st.session_state:
        st.write("✅ 找到 `merged_data`")
        merged_data = st.session_state.merged_data
        if isinstance(merged_data, pd.DataFrame):
            st.write(f"  - 資料形狀: {merged_data.shape}")
            st.write(f"  - 欄位: {list(merged_data.columns)}")
            fam_data_found = True
        else:
            st.write(f"  - 資料類型: {type(merged_data)}")
    else:
        st.write("❌ 沒有找到 `merged_data`")
    
    # 資料修復建議
    st.subheader("🔧 修復建議")
    
    if not fam_data_found:
        st.error("❌ 沒有找到家醫部資料")
        st.write("**建議步驟：**")
        st.write("1. 確認已選擇「家醫部」科別")
        st.write("2. 上傳家醫部EPA評核資料檔案")
        st.write("3. 點擊「合併家醫部檔案」按鈕")
        st.write("4. 確認看到「家醫部檔案合併成功！」訊息")
    else:
        st.success("✅ 找到家醫部資料")
        
        # 提供資料修復按鈕
        if st.button("🔧 修復資料傳遞"):
            try:
                # 嘗試修復資料傳遞
                if '家醫部_data' in st.session_state:
                    st.session_state.fam_data = st.session_state['家醫部_data']
                    st.success("✅ 已將 `家醫部_data` 複製到 `fam_data`")
                elif 'merged_data' in st.session_state:
                    st.session_state.fam_data = st.session_state.merged_data
                    st.success("✅ 已將 `merged_data` 複製到 `fam_data`")
                
                st.info("請重新整理頁面或返回家醫部系統查看結果")
                
            except Exception as e:
                st.error(f"❌ 修復失敗: {e}")
    
    # 資料預覽
    if fam_data_found:
        st.subheader("📊 資料預覽")
        
        # 選擇要預覽的資料
        preview_key = None
        if 'fam_data' in st.session_state and isinstance(st.session_state.fam_data, pd.DataFrame):
            preview_key = 'fam_data'
        elif '家醫部_data' in st.session_state and isinstance(st.session_state['家醫部_data'], pd.DataFrame):
            preview_key = '家醫部_data'
        elif 'merged_data' in st.session_state and isinstance(st.session_state.merged_data, pd.DataFrame):
            preview_key = 'merged_data'
        
        if preview_key:
            df = st.session_state[preview_key]
            
            # 顯示基本統計
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("總記錄數", len(df))
            with col2:
                if '學員' in df.columns:
                    st.metric("學員人數", df['學員'].nunique())
                else:
                    st.metric("學員人數", "N/A")
            with col3:
                if 'EPA項目' in df.columns:
                    st.metric("EPA項目種類", df['EPA項目'].nunique())
                else:
                    st.metric("EPA項目種類", "N/A")
            
            # 顯示前幾筆資料
            st.write("**前5筆資料預覽：**")
            display_columns = ['學員', 'EPA項目', '日期', '信賴程度(教師評量)']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                st.dataframe(df[available_columns].head(), use_container_width=True)
            else:
                st.dataframe(df.head(), use_container_width=True)

# 主要功能
if __name__ == "__main__":
    show_diagnostic_tool()
