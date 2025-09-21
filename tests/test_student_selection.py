#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試學生選擇功能的腳本
驗證不同角色的權限和學生選擇功能
"""

import streamlit as st
import pandas as pd
from modules.auth import check_permission, USER_ROLES

def test_student_selection_logic():
    """測試學生選擇邏輯"""
    
    st.title("學生選擇功能測試")
    
    # 模擬測試資料
    test_data = pd.DataFrame({
        '學員姓名': ['張三', '李四', '王五', '趙六', '陳七'],
        '學號': ['408010001', '408010002', '408010003', '408010004', '408010005'],
        '科別': ['小兒部', '內科', '外科', '婦產科', '神經科'],
        'EPA評核項目': ['EPA1', 'EPA2', 'EPA3', 'EPA4', 'EPA5'],
        '教師評核EPA等級_數值': [3, 4, 2, 5, 3]
    })
    
    st.subheader("測試資料")
    st.dataframe(test_data)
    
    # 測試不同角色的學生選擇邏輯
    roles_to_test = ['admin', 'teacher', 'resident', 'student']
    
    for role in roles_to_test:
        st.markdown("---")
        st.subheader(f"測試角色：{USER_ROLES.get(role, role)}")
        
        # 模擬 session state
        st.session_state.role = role
        st.session_state.user_name = '張三'  # 假設登入使用者是張三
        
        # 檢查權限
        can_view_ugy = check_permission(role, 'can_view_ugy_data')
        st.write(f"可以查看 UGY 資料：{can_view_ugy}")
        
        if can_view_ugy:
            # 模擬學生選擇邏輯
            all_students = sorted(test_data['學員姓名'].unique().tolist())
            logged_in_user_name = st.session_state.get('user_name', None)
            
            if role == 'student':
                # 學生帳號只能看到自己的資料
                if logged_in_user_name and logged_in_user_name in all_students:
                    selected_student = logged_in_user_name
                    st.success(f"學生帳號：已自動選擇您的資料 - {selected_student}")
                else:
                    st.warning(f"找不到您的資料，登入姓名：{logged_in_user_name}")
            else:
                # 其他角色可以自由選擇學生
                st.info("住院醫師、主治醫師、管理員可以自由選擇學生")
                
                # 顯示可選擇的學生
                st.write("可選擇的學生：")
                for i, student in enumerate(all_students):
                    st.write(f"{i+1}. {student}")
                
                # 模擬選擇第一個學生
                selected_student = all_students[0]
                st.info(f"已選擇學生：{selected_student}")
        else:
            st.warning("沒有權限查看 UGY 資料")

def test_permission_matrix():
    """測試權限矩陣"""
    
    st.title("權限矩陣測試")
    
    # 定義測試的權限
    permissions_to_test = [
        'can_view_all',
        'can_view_ugy_data', 
        'can_view_pgy_data',
        'can_view_resident_data',
        'can_view_analytics',
        'can_manage_users'
    ]
    
    # 定義角色
    roles = ['admin', 'teacher', 'resident', 'student']
    
    # 創建權限矩陣表格
    permission_data = []
    for role in roles:
        row = {'角色': USER_ROLES.get(role, role)}
        for permission in permissions_to_test:
            has_permission = check_permission(role, permission)
            row[permission] = '✅' if has_permission else '❌'
        permission_data.append(row)
    
    permission_df = pd.DataFrame(permission_data)
    st.dataframe(permission_df, use_container_width=True)
    
    # 解釋權限
    st.subheader("權限說明")
    st.write("""
    - **can_view_all**: 可以查看所有資料
    - **can_view_ugy_data**: 可以查看 UGY 資料
    - **can_view_pgy_data**: 可以查看 PGY 資料  
    - **can_view_resident_data**: 可以查看住院醫師資料
    - **can_view_analytics**: 可以查看分析功能
    - **can_manage_users**: 可以管理使用者
    """)

if __name__ == "__main__":
    # 設定頁面配置
    st.set_page_config(
        page_title="學生選擇功能測試",
        layout="wide"
    )
    
    # 執行測試
    test_student_selection_logic()
    st.markdown("---")
    test_permission_matrix()
