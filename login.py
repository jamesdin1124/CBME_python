import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import re

# 設定頁面配置
st.set_page_config(
    page_title="UGY EPA 系統",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自訂 CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .test-link {
        color: #1E90FF;
        text-decoration: none;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
        background-color: #f0f0f0;
        display: inline-block;
        margin: 5px;
    }
    .test-link:hover {
        background-color: #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("UGY EPA 系統登入")
    
    # 創建兩欄布局
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 正式系統")
        # 登入表單
        with st.form("login_form"):
            username = st.text_input("使用者名稱")
            password = st.text_input("密碼", type="password")
            submit_button = st.form_submit_button("登入")
            
            if submit_button:
                if username == "admin" and password == "admin":
                    st.success("登入成功！")
                    st.session_state.logged_in = True
                    st.experimental_rerun()
                else:
                    st.error("使用者名稱或密碼錯誤！")
    
    with col2:
        st.markdown("### 測試系統")
        st.markdown("""
            <div style="margin-top: 20px;">
                <a href="/test_form" class="test-link">填寫表單測試</a>
                <a href="/test_results" class="test-link">表單結果測試</a>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 