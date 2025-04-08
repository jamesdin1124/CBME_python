import streamlit as st
import pandas as pd
import os
import re
from io import BytesIO
from student_analysis import show_analysis_section
import sys
from resident_analysis import show_resident_analysis_section
from ANE_R_EPA_analysis import show_ANE_R_EPA_peer_analysis_section
from teacher_analysis import show_teacher_analysis_section, fetch_google_form_data
from UGY_peer_analysis import show_UGY_peer_analysis_section
from ugy_epa.UGY_EPA_main import show_UGY_EPA_section
from modules.epa_constants import EPA_LEVEL_MAPPING
from modules.auth import show_login_page, show_user_management, check_permission, USER_ROLES, show_registration_page

# 設定頁面配置為寬屏模式
st.set_page_config(
    layout="wide",  # 使用寬屏模式
    page_title="臨床教師評核系統",
    initial_sidebar_state="expanded"  # 預設展開側邊欄
)

# 初始化 session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def merge_excel_files(uploaded_files):
    # ... 現有代碼 ...
    try:
        if not uploaded_files:
            st.warning("請上傳Excel檔案！")
            return None
            
        # 合併所有Excel檔案
        all_data = []
        for uploaded_file in uploaded_files:
            # ... 處理檔案的代碼 ...
            df = pd.read_excel(uploaded_file)
            
            # 處理檔案名稱，移除括號內的版本號
            clean_filename = re.sub(r'\s*\([0-9]+\)\.xls$', '.xls', uploaded_file.name)
            
            # 處理訓練階段期間
            if '訓練階段期間' in df.columns:
                # 將期間字串分割成開始和結束日期
                df[['開始日期', '結束日期']] = df['訓練階段期間'].str.extract(r'(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})')
                
                # 轉換為日期格式
                df['開始日期'] = pd.to_datetime(df['開始日期'])
                df['結束日期'] = pd.to_datetime(df['結束日期'])
                
                # 計算訓練天數
                df['訓練天數'] = (df['結束日期'] - df['開始日期']).dt.days + 1
            
            # 轉換欄位（如果存在）
            for col in df.columns:
                # 移除特定文字
                df[col] = df[col].replace("本表單與畢業成績無關，請依學生表現落實評量;", "")
                
                if '教師評核' in col:
                    # 確保轉換後的值是數值型態
                    df[col] = df[col].apply(lambda x: EPA_LEVEL_MAPPING.get(str(x).strip(), x))
                    # 強制轉換為數值型態
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                elif '學員自評' in col:
                    df[col] = df[col].apply(lambda x: EPA_LEVEL_MAPPING.get(str(x), x))
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                elif 'EPA' in col:
                    df[col] = df[col].apply(lambda x: EPA_LEVEL_MAPPING.get(str(x), x))
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 加入處理過的檔案名稱欄位
            df['檔案名稱'] = clean_filename
            all_data.append(df)
        
        # 直接合併所有DataFrame，保留所有欄位
        merged_df = pd.concat(all_data, ignore_index=True, sort=False)
        
        # 確保檔案名稱欄位在最前面
        cols = merged_df.columns.tolist()
        cols.remove('檔案名稱')
        merged_df = merged_df[['檔案名稱'] + cols]
        
        # 將合併後的資料轉換為 CSV
        csv = merged_df.to_csv(index=False)
        
        # 將合併後的資料轉換為 Excel
        excel_buffer = BytesIO()
        merged_df.to_excel(excel_buffer, index=False)
        excel_data = excel_buffer.getvalue()
        
        # 建立兩個並排的下載按鈕
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="下載 CSV 檔案",
                data=csv,
                file_name="merged_data.csv",
                mime="text/csv"
            )
        
        with col2:
            st.download_button(
                label="下載 Excel 檔案",
                data=excel_data,
                file_name="merged_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # 合併完成後存入 session state
        st.session_state.merged_data = merged_df
        
        return merged_df
        
    except Exception as e:
        st.error(f"合併檔案時發生錯誤：{str(e)}")
        return None

def main():
    # 檢查是否已登入
    if not st.session_state.logged_in:
        # 建立選項卡讓用戶選擇登入或註冊
        login_tab, register_tab = st.tabs(["登入", "申請帳號"])
        
        with login_tab:
            if show_login_page():
                st.rerun()
        
        with register_tab:
            if show_registration_page():
                st.success("帳號申請成功！請等待管理員審核後即可登入。")
                # 不需要立即重新運行，讓用戶看到成功訊息
        
        return
    
    # 顯示登出按鈕
    with st.sidebar:
        if st.button("登出"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.user_name = None
            st.rerun()
    
    st.title("臨床教師評核系統")
    
    # 定義科別列表
    departments = [
        "小兒科", 
        "內科", 
        "外科", 
        "婦產科", 
        "神經科", 
        "精神科", 
        "家醫科", 
        "急診醫學科", 
        "麻醉科", 
        "放射科", 
        "病理科", 
        "復健科", 
        "皮膚科", 
        "眼科", 
        "耳鼻喉科", 
        "泌尿科", 
        "骨科", 
        "其他科別"
    ]
    
    # 側邊欄設置
    with st.sidebar:
        st.header("資料來源選擇")
        
        st.header("科別選擇")
        
        # 科別選擇
        selected_dept = st.selectbox(
            "請選擇科別",
            departments
        )
        
        # 根據權限顯示上傳區域
        if check_permission(st.session_state.role, 'can_upload_files'):
            st.subheader(f"{selected_dept}評核資料")
            
            # 檔案上傳區域
            uploaded_files = st.file_uploader(
                f"請上傳{selected_dept} Excel檔案",
                type=['xlsx', 'xls'],
                accept_multiple_files=True,
                key=f"{selected_dept}_files"
            )
            
            if st.button(f"合併{selected_dept}檔案") and uploaded_files:
                result = merge_excel_files(uploaded_files)
                if result is not None:
                    st.success(f"{selected_dept}檔案合併成功！")
                    # 將資料存入 session state，使用科別作為 key
                    st.session_state[f"{selected_dept}_data"] = result
                    st.session_state.merged_data = result
                else:
                    st.error(f"{selected_dept}檔案合併失敗！")
        
        # 顯示已上傳的科別
        if check_permission(st.session_state.role, 'can_view_all'):
            st.subheader("已上傳的科別")
            uploaded_depts = [dept for dept in departments if f"{dept}_data" in st.session_state]
            if uploaded_depts:
                for dept in uploaded_depts:
                    st.write(f"✅ {dept}")
            else:
                st.write("尚未上傳任何科別資料")
        
        # 系統管理員可以管理使用者
        if check_permission(st.session_state.role, 'can_manage_users'):
            st.markdown("---")
            show_user_management()

    # 分頁設置 - 根據權限顯示不同的分頁
    tabs = []
    tab_names = []
    
    if check_permission(st.session_state.role, 'can_view_all'):
        tabs.append("UGY EPA")
        tab_names.append("UGY EPA")
        tabs.append("UGY整合")
        tab_names.append("UGY整合")
        tabs.append("PGY")
        tab_names.append("PGY")
        tabs.append("R")
        tab_names.append("R")
        tabs.append("老師評分分析")
        tab_names.append("老師評分分析")
    
    if not tabs:
        st.warning("您沒有權限查看任何資料")
        return
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_names)
    
    # 獲取當前資料
    current_data = st.session_state.get('merged_data', None)
    
    with tab1:
        if check_permission(st.session_state.role, 'can_view_all'):
            show_UGY_EPA_section()
    
    with tab2:
        if check_permission(st.session_state.role, 'can_view_all'):
            st.header("UGY整合分析")
            if current_data is not None:
                st.session_state.ugy_data = current_data
                show_UGY_peer_analysis_section(current_data)
            else:
                st.warning("請先載入資料")
    
    with tab3:
        if check_permission(st.session_state.role, 'can_view_all'):
            st.header("PGY 分析")
            if current_data is not None:
                pgy_data = current_data[current_data['檔案名稱'].str.contains('PGY', case=False, na=False)]
                if not pgy_data.empty:
                    show_analysis_section(pgy_data)
                else:
                    st.warning("沒有 PGY 資料")
            else:
                st.warning("請先載入資料")
    
    with tab4:
        if check_permission(st.session_state.role, 'can_view_all'):
            st.header("R 分析")
            if current_data is not None:
                r_data = current_data[current_data['檔案名稱'].str.contains('R', case=False, na=False)]
                if not r_data.empty:
                    if selected_dept == "麻醉科":
                        show_ANE_R_EPA_peer_analysis_section(r_data)
                    else:
                        show_resident_analysis_section(r_data)
                else:
                    st.warning("沒有住院醫師資料")
            else:
                st.warning("請先載入資料")
    
    with tab5:
        if check_permission(st.session_state.role, 'can_view_all'):
            show_teacher_analysis_section()

if __name__ == "__main__":
    main()

# streamlit run new_dashboard.py

# GitHub 更新指令說明
# 1. 初次設定
# git init  # 初始化 git 倉庫
# git remote add origin <repository_url>  # 連接遠端倉庫

# 2. 更新流程
# git add .  # 加入所有修改的檔案
# git commit -m "更新說明"  # 提交修改並加入說明
# git push origin main  # 推送到 GitHub 主分支

# 3. 如果遇到衝突
# git pull origin main  # 先拉取最新版本
# 解決衝突後再執行步驟 2

# 4. 查看狀態
# git status  # 檢查檔案狀態
# git log  # 查看提交歷史 
