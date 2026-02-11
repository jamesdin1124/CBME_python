import streamlit as st
import httpx
import sqlite3
from datetime import datetime

# 設定頁面配置為寬屏模式
st.set_page_config(
    layout="wide",  # 使用寬屏模式
    page_title="學生評核系統",
    initial_sidebar_state="expanded"  # 預設展開側邊欄
)

import pandas as pd
import os
import re
import sys  # 匯入 sys
from io import BytesIO
from pages.pgy.pgy_students import show_analysis_section
from pages.residents.residents import show_resident_analysis_section
from pages.ANE.anesthesia_residents import show_ANE_R_EPA_peer_analysis_section
from pages.teachers.teacher_analysis import show_teacher_analysis_section, fetch_google_form_data
from pages.ugy.ugy_peers import show_UGY_peer_analysis_section
from pages.ugy.ugy_overview import show_ugy_student_overview
from pages.ugy.ugy_individual import show_ugy_student_analysis
from pages.ugy.ugy_teacher_analysis import show_ugy_teacher_analysis
from config.epa_constants import EPA_LEVEL_MAPPING
from modules.auth import show_login_page, show_user_management, check_permission, USER_ROLES, show_registration_page, filter_data_by_permission, get_user_department
from modules.supabase_connection import SupabaseConnection
from modules.supabase_connection import SupabaseConnection
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from openai import OpenAI
from dotenv import load_dotenv
import traceback # 匯入 traceback
from supabase import create_client

# 載入環境變數
load_dotenv()

# Supabase 連線實例（全域變數，避免重複建立）
_supabase_conn = None

def get_supabase_connection():
    """獲取 Supabase 連線實例"""
    global _supabase_conn
    if _supabase_conn is not None:
        return _supabase_conn
    try:
        _supabase_conn = SupabaseConnection()
        return _supabase_conn
    except Exception as e:
        st.error(f"無法連線 Supabase：{str(e)}")
        return None

def get_openai_client():
    """獲取 OpenAI 客戶端實例並提供更詳細的錯誤訊息，使用自訂 httpx 客戶端"""
    try:
        # 重新載入 .env 檔案以確保取得最新設定
        load_dotenv(override=True)
        
        # 讀取 API 金鑰
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            st.error("❌ 錯誤：未在 .env 檔案中找到 OPENAI_API_KEY。")
            st.error("""
            請在 .env 檔案中設定正確的 OpenAI API 金鑰：
            OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            
            OpenAI API 金鑰應該是以 sk-proj- 或 sk- 開頭的一串英文字母和數字。
            請確保：
            1. 金鑰完整複製（通常約 40-50 個字元）
            2. 沒有換行符號
            3. 沒有多餘的引號或空格
            4. 整個金鑰都在同一行
            """)
            return None
            
        # 清理和驗證 API 金鑰
        api_key = api_key.strip().strip('"').strip("'")
        
        # 檢查金鑰格式
        if not (api_key.startswith("sk-proj-") or api_key.startswith("sk-")):
            st.error("❌ API 金鑰格式不正確：金鑰必須以 'sk-proj-' 或 'sk-' 開頭")
            return None
            
        # 建立 HTTP 客戶端
        http_client = httpx.Client(
            trust_env=False,  # 不使用系統代理設定
            timeout=30.0      # 設定超時時間
        )
        
        # 初始化 OpenAI 客戶端
        client = OpenAI(
            api_key=api_key,
            http_client=http_client
        )
        st.success("✅ OpenAI 客戶端初始化成功")
        
        return client
        
    except Exception as e:
        st.error(f"❌ 初始化過程中發生錯誤：{str(e)}")
        st.error(f"詳細追蹤：\n{traceback.format_exc()}")
        return None

# 初始化 session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def merge_excel_files(uploaded_files):
    """
    合併上傳的多個 Excel 檔案。

    Args:
        uploaded_files (list): Streamlit file_uploader 上傳的檔案列表。

    Returns:
        pandas.DataFrame or None: 合併後的 DataFrame，如果失敗則返回 None。
    """
    try:
        if not uploaded_files:
            st.warning("請上傳Excel檔案！")
            return None

        all_data = []
        all_columns = set() # 記錄所有檔案中出現過的欄位
        epa_related_columns = set() # 記錄所有 EPA 相關欄位 (教師評核, 學員自評, EPA)

        # 第一遍：讀取檔案，預處理，並收集所有欄位名稱
        for uploaded_file in uploaded_files:
            # 讀取 Excel 檔案
            try:
                df = pd.read_excel(uploaded_file)
            except Exception as read_error:
                st.error(f"讀取檔案 {uploaded_file.name} 時發生錯誤: {read_error}")
                continue # 跳過這個檔案

            # 處理檔案名稱，移除括號內的版本號
            clean_filename = re.sub(r'\s*\([0-9]+\)\.xls$', '.xls', uploaded_file.name)
            df['檔案名稱'] = clean_filename # 先加入檔案名稱

            # 記錄原始欄位
            all_columns.update(df.columns)

            # 處理訓練階段期間
            if '訓練階段期間' in df.columns:
                try:
                    # 將期間字串分割成開始和結束日期
                    date_extracted = df['訓練階段期間'].str.extract(r'(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})')
                    df[['開始日期', '結束日期']] = date_extracted

                    # 轉換為日期格式
                    df['開始日期'] = pd.to_datetime(df['開始日期'], errors='coerce')
                    df['結束日期'] = pd.to_datetime(df['結束日期'], errors='coerce')

                    # 計算訓練天數 (僅在日期有效時計算)
                    valid_dates = df['開始日期'].notna() & df['結束日期'].notna()
                    df.loc[valid_dates, '訓練天數'] = (df.loc[valid_dates, '結束日期'] - df.loc[valid_dates, '開始日期']).dt.days + 1
                    # 記錄新增的欄位
                    all_columns.update(['開始日期', '結束日期', '訓練天數'])
                except Exception as date_error:
                    st.warning(f"處理檔案 {uploaded_file.name} 的 '訓練階段期間' 時發生錯誤: {date_error}")
                    # 即使出錯，也確保欄位存在，避免後續合併問題
                    if '開始日期' not in df.columns: df['開始日期'] = pd.NaT
                    if '結束日期' not in df.columns: df['結束日期'] = pd.NaT
                    if '訓練天數' not in df.columns: df['訓練天數'] = pd.NA
                    all_columns.update(['開始日期', '結束日期', '訓練天數'])

            # 預處理欄位值 和 識別 EPA 相關欄位
            cols_to_process = df.columns.tolist()
            for col in cols_to_process:
                # 移除特定文字 (先轉換成字串避免錯誤)
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace("本表單與畢業成績無關，請依學生表現落實評量;", "", regex=False)

                is_epa_col = False
                if '教師評核' in col or '學員自評' in col or 'EPA' in col:
                    is_epa_col = True
                    original_col_name = f"{col} [原始]"
                     # 檢查原始欄位是否已存在 (避免重複添加)
                    if original_col_name not in df.columns:
                         df[original_col_name] = df[col].copy()
                         all_columns.add(original_col_name) # 記錄原始欄位名稱
                    epa_related_columns.add(col) # 記錄 EPA 欄位名稱
                    epa_related_columns.add(original_col_name) # 也記錄原始欄位

                    # 應用 EPA 等級映射 (轉換前確保是字串)
                    df[col] = df[col].apply(lambda x: EPA_LEVEL_MAPPING.get(str(x).strip(), x))
                    # 轉換為數值，無法轉換的變為 NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            all_data.append(df)

        if not all_data:
            st.warning("沒有成功讀取的檔案可供合併。")
            return None

        # 第二遍：確保所有 DataFrame 都有所有欄位，特別是 EPA 相關欄位
        processed_data = []
        for df in all_data:
            # 找出當前 df 缺少的欄位
            missing_cols = all_columns - set(df.columns)
            for col in missing_cols:
                df[col] = pd.NA # 使用 pandas 的 NA 標記缺失值，更通用

             # 特別檢查 EPA 相關欄位，如果缺少則填 NaN (因為它們預期是數值)
            # 注意：上一步的 pd.NA 已經處理了，這裡再確認一次以防萬一
            # for epa_col in epa_related_columns:
            #     if epa_col not in df.columns:
            #         # 如果是轉換後的數值欄位，填 NaN
            #         if not epa_col.endswith(" [原始]"):
            #             df[epa_col] = pd.NA # pd.to_numeric 會處理 pd.NA
            #         else: # 如果是原始欄位，也填 NA
            #             df[epa_col] = pd.NA
            processed_data.append(df)


        # 合併所有DataFrame，sort=False 保持欄位順序，不存在的欄位會自動填充 NaN
        try:
            merged_df = pd.concat(processed_data, ignore_index=True, sort=False)
        except Exception as concat_error:
            st.error(f"合併 DataFrame 時發生錯誤: {concat_error}")
            # 嘗試找出哪個 DataFrame 導致問題
            for i, df_check in enumerate(processed_data):
                 st.write(f"DataFrame {i} (來源: {df_check['檔案名稱'].iloc[0] if not df_check.empty else '未知'}) 欄位: {df_check.columns.tolist()}")
            return None


        # 重新排序欄位，確保 '檔案名稱' 在最前面
        if '檔案名稱' in merged_df.columns:
            cols = merged_df.columns.tolist()
            cols.remove('檔案名稱')
            merged_df = merged_df[['檔案名稱'] + cols]
        else:
             st.warning("合併結果中缺少 '檔案名稱' 欄位。")


        # --- 下載按鈕和儲存到 session state ---
        # 將合併後的資料轉換為 CSV
        try:
            csv = merged_df.to_csv(index=False).encode('utf-8') # 指定 utf-8 編碼
        except Exception as csv_error:
            st.error(f"轉換為 CSV 時發生錯誤: {csv_error}")
            csv = None

        # 將合併後的資料轉換為 Excel
        excel_buffer = BytesIO()
        try:
            merged_df.to_excel(excel_buffer, index=False, engine='openpyxl') # 明確指定引擎
            excel_data = excel_buffer.getvalue()
        except Exception as excel_error:
            st.error(f"轉換為 Excel 時發生錯誤: {excel_error}")
            excel_data = None

        # 建立兩個並排的下載按鈕 (只有在成功轉換時才顯示)
        col1, col2 = st.columns(2)
        with col1:
            if csv:
                st.download_button(
                    label="下載 CSV 檔案",
                    data=csv,
                    file_name="merged_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("無法產生 CSV 檔案。")

        with col2:
            if excel_data:
                st.download_button(
                    label="下載 Excel 檔案",
                    data=excel_data,
                    file_name="merged_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("無法產生 Excel 檔案。")

        # 合併完成後存入 session state
        st.session_state.merged_data = merged_df
        return merged_df

    except Exception as e:
        st.error(f"合併檔案過程中發生未預期的錯誤：{str(e)}")
        import traceback
        st.error(traceback.format_exc()) # 顯示詳細的錯誤追蹤
        return None

def correct_text_with_gpt(text):
    """
    使用 GPT API 修正文字
    
    Args:
        text (str): 需要修正的文字
        
    Returns:
        str: 修正後的文字
    """
    client = get_openai_client()
    if not client:
        st.warning("無法獲取 OpenAI 客戶端，文字修正功能無法使用。")
        return text

    try:
        st.info("正在呼叫 OpenAI API 進行文字修正...")
        
        # 確保提示文本是有效的 UTF-8 字符串
        system_content = "你是一個專業的醫學教育文字編輯助手。你的任務是整理臨床教師對實習醫學生的口頭回饋，使其更有條理且易於閱讀。請保持原意，但可以：\n1. 修正錯別字和語法\n2. 改善句子結構\n3. 適當分段\n4. 使用更專業的醫學用語\n5. 保持評語的建設性和教育意義\n\n請直接返回修改後的文字，不需要其他說明。"
        
        # 顯示用於診斷的信息
        st.info(f"使用者文字字節長度：{len(text.encode('utf-8'))} bytes")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        st.success("✅ OpenAI API 呼叫成功！")
        return response.choices[0].message.content.strip()
    except Exception as e:
        # 安全地獲取錯誤訊息字串
        error_details = f"錯誤類型: {type(e).__name__}"
        try:
            error_message = str(e)
        except Exception:
            error_message = "無法顯示的錯誤訊息 (編碼問題)"

        st.error(f"❌ 呼叫 OpenAI API 時發生錯誤：{error_message} ({error_details})", icon="🚨")
        tb_str = f"詳細追蹤資訊:\n{traceback.format_exc()}"
        st.error(tb_str)
        return text

def init_test_form_db():
    """初始化測試表單資料庫"""
    try:
        conn = sqlite3.connect('test_form.db')
        cursor = conn.cursor()
        
        # 建立測試表單資料表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_form_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            batch TEXT NOT NULL,
            epa_1 INTEGER NOT NULL,
            epa_2 INTEGER NOT NULL,
            epa_3 INTEGER NOT NULL,
            epa_4 INTEGER NOT NULL,
            epa_5 INTEGER NOT NULL,
            comments TEXT,
            submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"初始化資料庫時發生錯誤：{str(e)}")
        return False

def save_to_sqlite(form_data):
    """將表單資料儲存到 SQLite 資料庫"""
    try:
        conn = sqlite3.connect('test_form.db')
        cursor = conn.cursor()
        
        # 插入資料
        cursor.execute('''
        INSERT INTO test_form_submissions 
        (name, batch, epa_1, epa_2, epa_3, epa_4, epa_5, comments, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            form_data['姓名'],
            form_data['梯次'],
            form_data['EPA_1'],
            form_data['EPA_2'],
            form_data['EPA_3'],
            form_data['EPA_4'],
            form_data['EPA_5'],
            form_data['評語'],
            form_data['提交時間']
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"儲存資料到資料庫時發生錯誤：{str(e)}")
        return False

def main():
    # 檢查是否已登入
    if not st.session_state.logged_in:
        # 建立選項卡讓用戶選擇登入或註冊
        login_tab, register_tab = st.tabs(["登入", "申請帳號"])

        with login_tab:
            if show_login_page():
                st.rerun()

        with register_tab:
            st.header("📝 申請帳號")
            st.info("填寫以下資料提交申請，管理員審核通過後即可登入使用。")

            with st.form("application_form"):
                # ── 第一列：真實姓名 ──
                full_name = st.text_input("真實姓名 *", placeholder="請輸入真實姓名")

                # ── 第二列：帳號 ──
                desired_username = st.text_input("帳號 *", placeholder="請輸入希望使用的帳號（英文或數字）")

                # ── 第三、四列：密碼 ──
                col_pw1, col_pw2 = st.columns(2)
                with col_pw1:
                    desired_password = st.text_input("密碼 *", type="password", placeholder="請輸入密碼")
                with col_pw2:
                    confirm_password = st.text_input("再次輸入密碼 *", type="password", placeholder="請再次輸入密碼")

                # ── 第五、六列：Email + 電話 ──
                col_contact1, col_contact2 = st.columns(2)
                with col_contact1:
                    email = st.text_input("Email *", placeholder="example@hospital.com")
                with col_contact2:
                    phone = st.text_input("聯絡電話（公務機）", placeholder="分機號碼或公務手機")

                # ── 第七、八列：科別 + 身份 ──
                col_dept, col_role = st.columns(2)
                with col_dept:
                    department = st.selectbox(
                        "科別 *",
                        options=["", "內科部", "外科部", "婦產部", "小兒部", "家醫部", "麻醉部"],
                        help="請選擇您所屬的科別"
                    )
                with col_role:
                    user_type = st.selectbox(
                        "身份 *",
                        options=["", "department_admin", "teacher", "resident", "pgy", "student"],
                        format_func=lambda x: {
                            "": "請選擇",
                            "department_admin": "科別管理員",
                            "teacher": "主治醫師",
                            "resident": "住院醫師",
                            "pgy": "PGY",
                            "student": "UGY"
                        }.get(x)
                    )

                # ── 住院醫師附加欄位 ──
                resident_level = None
                supervisor_name = None
                if user_type == "resident":
                    col_lv, col_sv = st.columns(2)
                    with col_lv:
                        resident_level = st.selectbox("級職 *", options=["R1", "R2", "R3"])
                    with col_sv:
                        supervisor_name = st.text_input("指導醫師", placeholder="指導您的主治醫師姓名")

                submit = st.form_submit_button("提交申請", use_container_width=True)

                if submit:
                    import hashlib
                    # 驗證必填欄位
                    if not full_name or not desired_username or not desired_password or not email or not user_type:
                        st.error("請填寫所有必填欄位（標記 * 者）")
                    elif not department and user_type not in ['pgy', 'student']:
                        st.error("請選擇科別")
                    elif desired_password != confirm_password:
                        st.error("兩次輸入的密碼不一致，請重新輸入")
                    elif len(desired_password) < 4:
                        st.error("密碼長度至少 4 個字元")
                    elif user_type == "resident" and not resident_level:
                        st.error("住院醫師請選擇級職")
                    else:
                        # 連線 Supabase
                        conn = get_supabase_connection()
                        if not conn:
                            st.error("無法連線資料庫，請聯繫系統管理員")
                        else:
                            # 檢查帳號是否已存在
                            try:
                                existing_user = conn.get_client().table('pediatric_users').select('id').eq('username', desired_username).execute()
                                if existing_user.data:
                                    st.error(f"帳號 「{desired_username}」 已被使用，請更換其他帳號")
                                    st.stop()
                            except Exception:
                                pass  # 查詢失敗時不阻擋，交由管理員後續處理

                            # 檢查是否已有相同 Email 的待審核申請
                            existing = conn.fetch_user_applications({'email': email, 'status': 'pending'})
                            if existing:
                                st.warning("此 Email 已有待審核的申請，請勿重複提交")
                            else:
                                # 密碼 hash
                                password_hash = hashlib.sha256(desired_password.encode()).hexdigest()

                                # 建立申請資料
                                app_data = {
                                    'full_name': full_name,
                                    'desired_username': desired_username,
                                    'password_hash': password_hash,
                                    'email': email,
                                    'phone': phone if phone else None,
                                    'user_type': user_type,
                                    'department': department if department else None,
                                    'resident_level': resident_level,
                                    'supervisor_name': supervisor_name if supervisor_name else None,
                                }

                                result = conn.insert_user_application(app_data)
                                if result:
                                    st.success("✅ 申請已提交！管理員審核通過後即可使用您設定的帳號密碼登入。")
                                    st.balloons()
                                else:
                                    st.error("提交失敗，請稍後再試或聯繫系統管理員")

            # 顯示申請狀態（若使用者輸入 Email）
            st.markdown("---")
            st.subheader("查詢申請狀態")
            query_email = st.text_input("輸入申請時填寫的 Email", key="query_email")
            if st.button("查詢", key="query_btn"):
                if query_email:
                    conn = get_supabase_connection()
                    if conn:
                        apps = conn.fetch_user_applications({'email': query_email})
                        if apps:
                            st.write(f"找到 {len(apps)} 筆申請記錄：")
                            for app in apps:
                                status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(app['status'], "❓")
                                status_text = {"pending": "待審核", "approved": "已核准", "rejected": "已拒絕"}.get(app['status'])

                                with st.container(border=True):
                                    st.write(f"{status_emoji} **狀態**：{status_text}")
                                    st.caption(f"申請時間：{app['created_at'][:10]}")
                                    if app['status'] == 'rejected' and app.get('review_notes'):
                                        st.warning(f"拒絕原因：{app['review_notes']}")
                                    if app['status'] == 'approved':
                                        st.info("帳號已建立，請檢查 Email 或聯繫管理員取得帳號資訊")
                        else:
                            st.info("查無此 Email 的申請記錄")
        return

        return
    
    # 顯示登出按鈕與管理入口
    with st.sidebar:
        if st.button("登出"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.user_name = None
            st.session_state.user_department = None
            st.session_state.student_id = None
            st.rerun()

        # 管理員和科別管理員專屬：管理功能入口
        if st.session_state.get('role') in ['admin', 'department_admin']:
            st.markdown("---")
            st.markdown("### 管理功能")

            # 帳號申請審核
            if st.button("📋 帳號申請審核"):
                st.session_state['show_application_review'] = True
                st.rerun()

            # 返回主頁按鈕
            if st.session_state.get('show_application_review'):
                if st.button("↩️ 返回主頁"):
                    st.session_state.pop('show_application_review', None)
                    st.rerun()

    # 帳號申請審核頁面（admin 和 department_admin 專用）
    if st.session_state.get('show_application_review') and st.session_state.get('role') in ['admin', 'department_admin']:
        from pages.admin.user_application_review import show_user_application_review
        show_user_application_review()
        return

    st.title("學生評核系統")
    
    # 定義科別列表
    departments = [
        "小兒部", 
        "內科部", 
        "外科部", 
        "婦產部", 
        "神經科", 
        "精神部", 
        "家醫部", 
        "急診醫學部", 
        "麻醉部", 
        "放射部", 
        "病理部", 
        "復健部", 
        "皮膚部", 
        "眼科", 
        "耳鼻喉部", 
        "泌尿部", 
        "骨部", 
        "其他科別"
    ]
    
    # 獲取使用者科別
    user_department = st.session_state.get('user_department', None)
    
    # 側邊欄設置
    with st.sidebar:
        st.header("資料來源選擇")
        
        st.header("科別選擇")
        
        # 科別選擇 - 根據權限限制可選擇的科別
        if check_permission(st.session_state.role, 'can_view_all'):
            # 管理員可以選擇所有科別
            available_departments = departments
        elif st.session_state.role == 'teacher' and user_department:
            # 主治醫師只能選擇自己的科別
            available_departments = [user_department]
        else:
            # 其他角色只能選擇自己的科別（如果有的話）
            available_departments = [user_department] if user_department else departments
        
        selected_dept = st.selectbox(
            "請選擇科別",
            available_departments
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
        
        # 顯示已上傳的科別 - 根據權限過濾
        if check_permission(st.session_state.role, 'can_view_all'):
            st.subheader("已上傳的科別")
            uploaded_depts = [dept for dept in departments if f"{dept}_data" in st.session_state]
            if uploaded_depts:
                for dept in uploaded_depts:
                    st.write(f"✅ {dept}")
            else:
                st.write("尚未上傳任何科別資料")
        elif st.session_state.role == 'teacher' and user_department:
            # 主治醫師只能看到自己科的資料
            st.subheader("已上傳的科別")
            if f"{user_department}_data" in st.session_state:
                st.write(f"✅ {user_department}")
            else:
                st.write(f"尚未上傳 {user_department} 的資料")
        
        # 系統管理員可以管理使用者
        if check_permission(st.session_state.role, 'can_manage_users'):
            st.markdown("---")
            show_user_management()
        
        # 添加測試系統連結
        st.markdown("---")
        st.subheader("測試系統")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("填寫表單測試", key="sidebar_form_button"):
                st.markdown('<meta http-equiv="refresh" content="0;URL=test_form">', unsafe_allow_html=True)
        with col2:
            if st.button("查看測試結果", key="sidebar_result_button"):
                st.markdown('<meta http-equiv="refresh" content="0;URL=test_results">', unsafe_allow_html=True)

    # 分頁設置 - 根據權限顯示不同的分頁
    tab_names = []
    
    # 根據角色和權限顯示不同的分頁
    if check_permission(st.session_state.role, 'can_view_all'):
        # 管理員可以看到所有資料
        tab_names.append("UGY")
        tab_names.append("PGY")
        tab_names.append("住院醫師")
        # tab_names.append("老師評分分析")  # 暫時隱藏
    elif check_permission(st.session_state.role, 'can_view_ugy_data'):
        # 主治醫師和住院醫師可以看到UGY資料
        tab_names.append("UGY")
        
        if check_permission(st.session_state.role, 'can_view_pgy_data'):
            tab_names.append("PGY")
        
        if check_permission(st.session_state.role, 'can_view_resident_data'):
            tab_names.append("住院醫師")
        
        # if check_permission(st.session_state.role, 'can_view_analytics'):
        #     tab_names.append("老師評分分析")  # 暫時隱藏
    elif st.session_state.role == 'student':
        # UGY只能看到自己的資料
        tab_names.append("我的評核資料")
    
    if not tab_names:
        st.warning("您沒有權限查看任何資料")
        return
    
    # 根據角色動態創建分頁
    if st.session_state.role == 'student':
        # UGY現在也可能有多個分頁
        tabs = st.tabs(tab_names)
        
        # 根據分頁名稱動態處理內容
        for i, tab_name in enumerate(tab_names):
            with tabs[i]:
                if tab_name == "我的評核資料":
                    st.header("我的評核資料")
                    # 從 session state 中獲取所有科別的資料
                    all_data = []
                    for dept in departments:
                        if f"{dept}_data" in st.session_state:
                            all_data.append(st.session_state[f"{dept}_data"])
                    
                    if all_data:
                        # 合併所有科別的資料
                        current_data = pd.concat(all_data, ignore_index=True)
                        # 過濾出該學生的資料
                        student_data = current_data[current_data['學號'] == st.session_state.get('student_id')]
                        if not student_data.empty:
                            # 顯示基本資訊
                            st.subheader("基本資訊")
                            st.write(f"姓名：{student_data['姓名'].iloc[0]}")
                            st.write(f"學號：{student_data['學號'].iloc[0]}")
                            st.write(f"科別：{student_data['科別'].iloc[0]}")
                            
                            # 顯示 EPA 評分
                            st.subheader("EPA 評分")
                            epa_columns = [col for col in student_data.columns if 'EPA' in col]
                            for epa_col in epa_columns:
                                st.write(f"{epa_col}：{student_data[epa_col].iloc[0]}")
                            
                            # 顯示評語
                            if '評語' in student_data.columns:
                                st.subheader("評語")
                                st.write(student_data['評語'].iloc[0])
                            
                            # 顯示趨勢圖
                            st.subheader("評分趨勢")
                            if len(student_data) > 1:  # 確保有多筆資料才顯示趨勢圖
                                trend_data = student_data[epa_columns].T
                                trend_data.columns = ['評分']
                                st.line_chart(trend_data)
                            
                            # 顯示雷達圖
                            st.subheader("能力雷達圖")
                            if epa_columns:
                                radar_data = student_data[epa_columns].iloc[0]
                                fig = go.Figure()
                                fig.add_trace(go.Scatterpolar(
                                    r=radar_data.values,
                                    theta=radar_data.index,
                                    fill='toself',
                                    name='能力評分'
                                ))
                                fig.update_layout(
                                    polar=dict(
                                        radialaxis=dict(
                                            visible=True,
                                            range=[0, 5]
                                        )
                                    ),
                                    showlegend=False
                                )
                                st.plotly_chart(fig)
                        else:
                            st.warning("找不到您的評核資料")
                    else:
                        st.warning("尚未上傳任何評核資料")
                
                elif tab_name == "UGY":
                    if check_permission(st.session_state.role, 'can_view_ugy_data'):
                        # 根據角色決定顯示的分頁
                        if st.session_state.role == 'student':
                            # 學生帳號只顯示個別學生分析
                            st.header("我的評核資料分析")
                            show_ugy_student_analysis()
                        else:
                            # 其他角色顯示完整的分頁
                            ugy_subtabs = st.tabs(["學生總覽", "個別學生分析", "老師分析"])
                            
                            with ugy_subtabs[0]:
                                st.header("學生總覽")
                                show_ugy_student_overview()
                            
                            with ugy_subtabs[1]:
                                st.header("個別學生分析")
                                show_ugy_student_analysis()
                            
                            with ugy_subtabs[2]:
                                st.header("老師分析")
                                show_ugy_teacher_analysis()
    else:
        # 為非學生角色準備 current_data
        current_data = None
        all_data = []
        for dept in departments:
            if f"{dept}_data" in st.session_state:
                all_data.append(st.session_state[f"{dept}_data"])
        
        if all_data:
            current_data = pd.concat(all_data, ignore_index=True)
        
        # 動態創建分頁
        tabs = st.tabs(tab_names)
        
        # 根據分頁名稱動態處理內容
        for i, tab_name in enumerate(tab_names):
            with tabs[i]:
                if tab_name == "UGY":
                    if check_permission(st.session_state.role, 'can_view_all') or check_permission(st.session_state.role, 'can_view_ugy_data'):
                        # 根據角色決定顯示的分頁
                        if st.session_state.role == 'student':
                            # 學生帳號只顯示個別學生分析
                            st.header("我的評核資料分析")
                            show_ugy_student_analysis()
                        else:
                            # 其他角色顯示完整的分頁
                            ugy_subtabs = st.tabs(["學生總覽", "個別學生分析", "老師分析"])
                            
                            with ugy_subtabs[0]:
                                st.header("學生總覽")
                                show_ugy_student_overview()
                            
                            with ugy_subtabs[1]:
                                st.header("個別學生分析")
                                show_ugy_student_analysis()
                            
                            with ugy_subtabs[2]:
                                st.header("老師分析")
                                show_ugy_teacher_analysis()
                
                elif tab_name == "PGY":
                    if check_permission(st.session_state.role, 'can_view_pgy_data'):
                        st.header("PGY 分析")
                        if current_data is not None:
                            pgy_data = current_data[current_data['檔案名稱'].str.contains('PGY', case=False, na=False)]
                            if not pgy_data.empty:
                                # 根據權限過濾PGY資料
                                filtered_pgy_data = filter_data_by_permission(pgy_data, st.session_state.role, user_department, 'pgy')
                                if not filtered_pgy_data.empty:
                                    show_analysis_section(filtered_pgy_data)
                                else:
                                    st.warning("您沒有權限查看此資料")
                            else:
                                st.warning("沒有 PGY 資料")
                        else:
                            st.warning("請先載入資料")
                
                elif tab_name == "住院醫師":
                    if check_permission(st.session_state.role, 'can_view_resident_data') or check_permission(st.session_state.role, 'can_view_all'):
                        # 檢查是否選擇小兒部
                        if selected_dept == "小兒部":
                            # 直接顯示小兒部評核系統
                            from pages.pediatric.pediatric_analysis import show_pediatric_evaluation_section
                            show_pediatric_evaluation_section()
                        elif selected_dept == "家醫部":
                            # 顯示家醫部專用EPA評核系統
                            from pages.FAM.fam_residents import show_fam_resident_evaluation_section
                            # 將家醫部資料存入session state以供家醫部系統使用
                            if f"{selected_dept}_data" in st.session_state:
                                st.session_state.fam_data = st.session_state[f"{selected_dept}_data"]
                                show_fam_resident_evaluation_section()
                            elif 'merged_data' in st.session_state and st.session_state.merged_data is not None:
                                # 如果使用合併資料，也嘗試使用
                                st.session_state.fam_data = st.session_state.merged_data
                                show_fam_resident_evaluation_section()
                            else:
                                st.warning("請先上傳家醫部EPA評核資料檔案")
                                st.info("💡 提示：請在左側側邊欄選擇「家醫部」科別，然後上傳並合併資料檔案。")
                        else:
                            # 顯示一般住院醫師分析
                            st.header("住院醫師分析")
                            if current_data is not None:
                                r_data = current_data[current_data['檔案名稱'].str.contains('R', case=False, na=False)]
                                if not r_data.empty:
                                    # 根據權限過濾住院醫師資料
                                    filtered_r_data = filter_data_by_permission(r_data, st.session_state.role, user_department, 'resident')
                                    if not filtered_r_data.empty:
                                        if selected_dept == "麻醉部":
                                            show_ANE_R_EPA_peer_analysis_section(filtered_r_data)
                                        else:
                                            show_resident_analysis_section(filtered_r_data)
                                    else:
                                        st.warning("您沒有權限查看此資料")
                                else:
                                    st.warning("沒有住院醫師資料")
                            else:
                                st.warning("請先載入資料")
                
                # elif tab_name == "老師評分分析":  # 暫時隱藏
                #     if check_permission(st.session_state.role, 'can_view_analytics'):
                #         # 添加分析模式選擇
                #         analysis_mode = st.radio(
                #             "選擇分析模式",
                #             ["基本教師分析", "教師評分模式分析", "教師比較分析"],
                #             horizontal=True
                #         )
                #         
                #         if analysis_mode == "基本教師分析":
                #             show_teacher_analysis_section()
                #         elif analysis_mode == "教師評分模式分析":
                #             from pages.teachers.teacher_scoring_analysis import show_teacher_scoring_analysis
                #             show_teacher_scoring_analysis()
                #         elif analysis_mode == "教師比較分析":
                #             from pages.teachers.teacher_scoring_analysis import show_teacher_comparison
                #             show_teacher_comparison()

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

