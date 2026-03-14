"""
UGY 學生帳號管理模組

功能：
- 批次建立 UGY 學生帳號（身分證=帳號, 學號=密碼）
- 從 CSV/Excel 匯入學生名冊
- 單筆新增/編輯學生
- 學生名單查詢（供表單自動完成使用）
"""

import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime


def _get_supabase_conn():
    from modules.supabase_connection import SupabaseConnection
    return SupabaseConnection()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ═══════════════════════════════════════════════════════
# 學生 CRUD
# ═══════════════════════════════════════════════════════

def get_all_ugy_students():
    """取得所有 UGY 學生（active）"""
    try:
        conn = _get_supabase_conn()
        result = conn.client.table('pediatric_users').select('*').eq(
            'user_type', 'student'
        ).eq('is_active', True).execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"查詢 UGY 學生失敗：{str(e)}")
        return []


def get_ugy_student_names():
    """取得 UGY 學生姓名清單（供表單下拉/自動完成）"""
    students = get_all_ugy_students()
    return sorted([s['full_name'] for s in students if s.get('full_name')])


def search_ugy_students(query):
    """模糊搜尋學生姓名"""
    students = get_all_ugy_students()
    if not query:
        return students
    query_lower = query.lower()
    return [s for s in students if query_lower in s.get('full_name', '').lower()]


def create_ugy_student(national_id, student_id, full_name,
                       cohort=None, department=None, email=None):
    """
    建立單筆 UGY 學生帳號
    帳號 = 身分證字號（username）
    密碼 = 學號（password → SHA-256 hash）
    """
    try:
        conn = _get_supabase_conn()

        # 檢查是否已存在
        existing = conn.client.table('pediatric_users').select('username').eq(
            'username', national_id
        ).execute()
        if existing.data and len(existing.data) > 0:
            return False, f"帳號已存在：{national_id}（{full_name}）"

        user_data = {
            'username': national_id,
            'full_name': full_name,
            'user_type': 'student',
            'password_hash': hash_password(student_id),
            'is_active': True,
            'student_id': student_id,
            'department': department,
            'email': email,
        }
        # 存放 cohort（梯次）在 extension 欄位
        if cohort:
            user_data['extension'] = cohort

        result = conn.client.table('pediatric_users').insert(user_data).execute()
        if result.data:
            return True, f"建立成功：{full_name}"
        return False, "建立失敗（無資料回傳）"

    except Exception as e:
        return False, f"建立失敗：{str(e)}"


def batch_create_ugy_students(df):
    """
    批次建立 UGY 學生帳號

    DataFrame 需包含欄位：
    - 身分證字號（必填）→ username
    - 學號（必填）→ password & student_id
    - 姓名（必填）→ full_name
    - 梯次（選填）→ extension
    - 科部（選填）→ department
    - Email（選填）→ email
    """
    results = {'success': 0, 'failed': 0, 'skipped': 0, 'details': []}

    # 欄位對照
    col_map = {
        '身分證字號': 'national_id', '身份證字號': 'national_id',
        '身分證': 'national_id', '帳號': 'national_id',
        '學號': 'student_id',
        '姓名': 'full_name', '學員姓名': 'full_name', '學生姓名': 'full_name',
        '梯次': 'cohort', '階層': 'cohort',
        '科部': 'department', '實習科部': 'department',
        'Email': 'email', 'email': 'email', '電子郵件': 'email',
    }

    # 標準化欄位名
    renamed = {}
    for orig_col in df.columns:
        for k, v in col_map.items():
            if k in str(orig_col):
                renamed[orig_col] = v
                break
    df = df.rename(columns=renamed)

    required = ['national_id', 'student_id', 'full_name']
    missing = [c for c in required if c not in df.columns]
    if missing:
        return None, f"缺少必要欄位：{missing}（需要：身分證字號、學號、姓名）"

    for _, row in df.iterrows():
        nid = str(row['national_id']).strip()
        sid = str(row['student_id']).strip()
        name = str(row['full_name']).strip()

        if not nid or not sid or not name or nid == 'nan':
            results['skipped'] += 1
            results['details'].append(f"跳過：資料不完整（{name}）")
            continue

        success, msg = create_ugy_student(
            national_id=nid,
            student_id=sid,
            full_name=name,
            cohort=str(row.get('cohort', '')).strip() if pd.notna(row.get('cohort')) else None,
            department=str(row.get('department', '')).strip() if pd.notna(row.get('department')) else None,
            email=str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None,
        )
        if success:
            results['success'] += 1
        else:
            if '已存在' in msg:
                results['skipped'] += 1
            else:
                results['failed'] += 1
        results['details'].append(msg)

    return results, None


def reset_student_password(username, new_password):
    """重設學生密碼"""
    try:
        conn = _get_supabase_conn()
        result = conn.client.table('pediatric_users').update(
            {'password_hash': hash_password(new_password)}
        ).eq('username', username).eq('user_type', 'student').execute()
        if result.data:
            return True, "密碼重設成功"
        return False, "找不到該學生"
    except Exception as e:
        return False, f"重設失敗：{str(e)}"


# ═══════════════════════════════════════════════════════
# 管理介面
# ═══════════════════════════════════════════════════════

def show_ugy_student_management():
    """UGY 學生帳號管理頁面（供 admin 使用）"""
    st.subheader("📋 UGY 學生帳號管理")

    mgmt_tab1, mgmt_tab2, mgmt_tab3 = st.tabs([
        "批次匯入", "單筆新增", "學生清單"
    ])

    # ── 批次匯入 ──
    with mgmt_tab1:
        st.markdown("### 批次匯入學生名冊")
        st.info("請上傳包含 **身分證字號**、**學號**、**姓名** 的 Excel 或 CSV 檔案。\n\n"
                "帳號 = 身分證字號，密碼 = 學號")

        uploaded = st.file_uploader(
            "上傳學生名冊", type=['xlsx', 'csv'],
            key='ugy_batch_upload'
        )

        if uploaded:
            if uploaded.name.endswith('.csv'):
                preview_df = pd.read_csv(uploaded)
            else:
                preview_df = pd.read_excel(uploaded)

            st.write(f"共 {len(preview_df)} 筆資料，欄位：{list(preview_df.columns)}")
            st.dataframe(preview_df.head(10), use_container_width=True)

            if st.button("確認批次建立帳號", type="primary", key='btn_batch_create'):
                with st.spinner("批次建立中..."):
                    results, err = batch_create_ugy_students(preview_df)
                    if err:
                        st.error(err)
                    else:
                        col1, col2, col3 = st.columns(3)
                        col1.metric("成功", results['success'])
                        col2.metric("跳過（已存在）", results['skipped'])
                        col3.metric("失敗", results['failed'])
                        with st.expander("詳細結果"):
                            for d in results['details']:
                                st.write(d)

    # ── 單筆新增 ──
    with mgmt_tab2:
        st.markdown("### 單筆新增 UGY 學生")
        with st.form("add_single_ugy", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("姓名 *")
                new_nid = st.text_input("身分證字號（帳號）*")
            with col2:
                new_sid = st.text_input("學號（密碼）*")
                new_cohort = st.selectbox("階層", ['C1', 'C2', ''])
            new_dept = st.selectbox("實習科部", ['', '內科部', '外科部', '婦產部', '小兒部'])
            new_email = st.text_input("Email（選填）")

            if st.form_submit_button("建立帳號", type="primary"):
                if not new_name or not new_nid or not new_sid:
                    st.error("請填寫姓名、身分證字號、學號")
                else:
                    ok, msg = create_ugy_student(
                        national_id=new_nid, student_id=new_sid,
                        full_name=new_name, cohort=new_cohort or None,
                        department=new_dept or None, email=new_email or None,
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    # ── 學生清單 ──
    with mgmt_tab3:
        st.markdown("### 目前 UGY 學生清單")
        students = get_all_ugy_students()
        if students:
            sdf = pd.DataFrame(students)
            display_cols = ['full_name', 'student_id', 'username', 'department', 'extension', 'email']
            display_cols = [c for c in display_cols if c in sdf.columns]
            col_rename = {
                'full_name': '姓名', 'student_id': '學號',
                'username': '帳號（身分證）', 'department': '科部',
                'extension': '梯次', 'email': 'Email'
            }
            sdf_display = sdf[display_cols].rename(columns=col_rename)
            st.dataframe(sdf_display, use_container_width=True)
            st.write(f"共 {len(students)} 位學生")

            # 密碼重設
            with st.expander("重設學生密碼"):
                reset_user = st.selectbox(
                    "選擇學生",
                    options=[s['username'] for s in students],
                    format_func=lambda x: f"{next((s['full_name'] for s in students if s['username'] == x), x)} ({x})"
                )
                new_pw = st.text_input("新密碼", type="password")
                if st.button("重設密碼"):
                    if new_pw:
                        ok, msg = reset_student_password(reset_user, new_pw)
                        st.success(msg) if ok else st.error(msg)
                    else:
                        st.error("請輸入新密碼")
        else:
            st.info("尚無 UGY 學生帳號，請先匯入學生名冊。")
