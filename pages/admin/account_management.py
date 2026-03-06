"""
帳號管理頁面（全科別通用）— 純 Supabase 版本
管理員可手動建立帳號或透過 CSV 批次匯入。
所有資料儲存於 Supabase pediatric_users 表。
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from modules.auth import (
    create_user, hash_password, USER_ROLES, update_user_role, deactivate_user,
)

# 科部選項（與 new_dashboard.py 一致）
DEPARTMENTS = [
    "小兒部", "內科部", "外科部", "婦產部", "神經科",
    "精神部", "家醫部", "急診醫學部", "麻醉部", "放射部",
    "病理部", "復健部", "皮膚部", "眼科", "耳鼻喉部",
    "泌尿部", "骨部", "其他科別",
]

# 可建立的角色（排除 student，學生用申請頁自行註冊）
CREATABLE_ROLES = {
    'admin': '系統管理員',
    'department_admin': '科別管理員',
    'teacher': '主治醫師',
    'resident': '住院醫師',
}


def _get_supabase_conn():
    """取得 Supabase 連線實例"""
    from modules.supabase_connection import SupabaseConnection
    return SupabaseConnection()


def show_account_management():
    """帳號管理主入口（僅 admin 可存取）"""
    st.markdown("## 帳號管理")
    st.caption("建立與管理系統帳號。所有帳號儲存於 Supabase。")

    tab_create, tab_csv, tab_list = st.tabs([
        "手動建立帳號", "CSV 批次匯入", "帳號總覽",
    ])

    with tab_create:
        _show_manual_creation()
    with tab_csv:
        _show_csv_import()
    with tab_list:
        _show_account_list()


# ─── 手動建立帳號 ───────────────────────────────────────

def _show_manual_creation():
    st.subheader("手動建立帳號")

    with st.form("create_account_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input("帳號 *", placeholder="例：dr_wang")
            password = st.text_input("密碼 *", type="password")
            password_confirm = st.text_input("確認密碼 *", type="password")
            full_name = st.text_input("姓名 *", placeholder="例：王大明")

        with col2:
            role = st.selectbox(
                "角色 *",
                list(CREATABLE_ROLES.keys()),
                format_func=lambda r: CREATABLE_ROLES[r],
            )
            department = st.selectbox("科部 *", DEPARTMENTS)
            email = st.text_input("電子郵件（選填）")
            extension = st.text_input("分機號碼（選填）")

        submitted = st.form_submit_button("建立帳號", type="primary")

    if submitted:
        # 驗證
        errors = []
        if not username or not username.strip():
            errors.append("帳號為必填")
        if not password:
            errors.append("密碼為必填")
        elif len(password) < 4:
            errors.append("密碼至少 4 個字元")
        if password != password_confirm:
            errors.append("兩次密碼不一致")
        if not full_name or not full_name.strip():
            errors.append("姓名為必填")

        if errors:
            for e in errors:
                st.error(e)
        else:
            success, msg = create_user(
                username=username.strip(),
                password=password,
                role=role,
                name=full_name.strip(),
                department=department,
                email=email.strip() or None,
            )
            if success:
                st.success(f"帳號建立成功：{full_name.strip()}（{CREATABLE_ROLES[role]}，{department}）")
            else:
                st.error(f"建立失敗：{msg}")


# ─── CSV 批次匯入 ───────────────────────────────────────

def _show_csv_import():
    st.subheader("CSV 批次匯入")

    # 範本下載
    st.markdown("**Step 1：下載 CSV 範本**")
    template_csv = _generate_csv_template()
    st.download_button(
        label="下載 CSV 範本",
        data=template_csv,
        file_name="account_template.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.markdown("**Step 2：上傳填好的 CSV**")
    uploaded = st.file_uploader("選擇 CSV 檔案", type=['csv'], key="csv_upload")

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded, dtype=str).fillna('')
        except Exception as e:
            st.error(f"無法解析 CSV：{e}")
            return

        required_cols = {'帳號', '密碼', '姓名', '角色', '科部'}
        if not required_cols.issubset(set(df.columns)):
            st.error(f"CSV 缺少必要欄位：{required_cols - set(df.columns)}")
            return

        # 預覽
        st.markdown("**Step 3：預覽資料**")
        preview_df = df.copy()
        preview_df['密碼'] = '******'
        st.dataframe(preview_df, use_container_width=True)
        st.info(f"共 {len(df)} 筆資料")

        # 驗證
        validation_errors = _validate_csv(df)
        if validation_errors:
            st.warning("以下資料有問題，匯入時將跳過：")
            for err in validation_errors:
                st.write(f"- {err}")

        # 匯入按鈕
        if st.button("確認匯入", type="primary", key="csv_import_btn"):
            _execute_csv_import(df)


def _generate_csv_template():
    """產生 CSV 範本"""
    header = "帳號,密碼,姓名,角色,科部,email\n"
    example = (
        "dr_wang,Changeme123,王大明,teacher,小兒部,wang@hospital.com\n"
        "lin_ys,Changeme123,林盈秀,resident,小兒部,lin@hospital.com\n"
    )
    return (header + example).encode('utf-8-sig')


def _validate_csv(df):
    """驗證 CSV 各行的基本格式"""
    errors = []
    valid_roles = set(CREATABLE_ROLES.keys())
    valid_depts = set(DEPARTMENTS)

    for idx, row in df.iterrows():
        row_num = idx + 2  # CSV 第 2 行起
        if not row['帳號'].strip():
            errors.append(f"第 {row_num} 行：帳號為空")
        if not row['密碼'].strip():
            errors.append(f"第 {row_num} 行：密碼為空")
        if not row['姓名'].strip():
            errors.append(f"第 {row_num} 行：姓名為空")
        if row['角色'].strip() not in valid_roles:
            errors.append(f"第 {row_num} 行：角色 '{row['角色']}' 無效（需為 {valid_roles}）")
        if row['科部'].strip() not in valid_depts:
            errors.append(f"第 {row_num} 行：科部 '{row['科部']}' 不在可選列表中")

    return errors


def _execute_csv_import(df):
    """執行 CSV 批次匯入（寫入 Supabase）"""
    success_count = 0
    fail_count = 0
    fail_details = []

    progress = st.progress(0)
    status = st.empty()
    total = len(df)

    for idx, row in df.iterrows():
        progress.progress((idx + 1) / total)
        username = row['帳號'].strip()
        status.text(f"匯入中：{username}（{idx + 1}/{total}）")

        if not username or not row['密碼'].strip() or not row['姓名'].strip():
            fail_count += 1
            fail_details.append(f"{username or '(空帳號)'}：必填欄位為空")
            continue

        role = row['角色'].strip()
        if role not in CREATABLE_ROLES:
            fail_count += 1
            fail_details.append(f"{username}：角色無效")
            continue

        success, msg = create_user(
            username=username,
            password=row['密碼'].strip(),
            role=role,
            name=row['姓名'].strip(),
            department=row['科部'].strip(),
            email=row.get('email', '').strip() or None,
        )

        if success:
            success_count += 1
        else:
            fail_count += 1
            fail_details.append(f"{username}：{msg}")

    progress.progress(1.0)
    status.empty()

    if success_count > 0:
        st.success(f"匯入完成：成功 {success_count} 筆")
    if fail_count > 0:
        st.warning(f"失敗 {fail_count} 筆")
        with st.expander("查看失敗詳情"):
            for d in fail_details:
                st.write(f"- {d}")


# ─── 帳號總覽 ───────────────────────────────────────────

def _show_account_list():
    st.subheader("帳號總覽")

    try:
        conn = _get_supabase_conn()
        # 包含停用帳號
        all_users = conn.fetch_all_users(active_only=False)
    except Exception as e:
        st.error(f"讀取使用者列表失敗：{str(e)}")
        return

    if not all_users:
        st.info("目前沒有任何帳號")
        return

    # 篩選條件
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_role = st.selectbox(
            "依角色篩選",
            ['全部'] + list(USER_ROLES.keys()),
            format_func=lambda r: '全部' if r == '全部' else USER_ROLES.get(r, r),
        )
    with col_f2:
        filter_dept = st.selectbox(
            "依科部篩選",
            ['全部'] + DEPARTMENTS,
        )

    # 過濾
    filtered = []
    for u in all_users:
        role = u.get('user_type', '')
        dept = u.get('department', '')
        if filter_role != '全部' and role != filter_role:
            continue
        if filter_dept != '全部' and dept != filter_dept:
            continue
        filtered.append(u)

    if not filtered:
        st.info("沒有符合條件的帳號")
        return

    # 轉為 DataFrame 顯示
    rows = []
    for u in filtered:
        rows.append({
            '帳號': u.get('username', ''),
            '姓名': u.get('full_name', ''),
            '角色': USER_ROLES.get(u.get('user_type', ''), u.get('user_type', '')),
            '科部': u.get('department', '') or '未設定',
            'Email': u.get('email', '') or '',
            '狀態': '啟用中' if u.get('is_active', True) else '已停用',
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(f"共 {len(rows)} 筆")

    # 帳號操作區
    st.markdown("---")
    st.markdown("#### 帳號操作")

    active_users = [u for u in filtered if u.get('is_active', True)]
    if not active_users:
        st.info("沒有啟用中的帳號可操作")
        return

    username_options = [u['username'] for u in active_users]

    # 重設密碼
    with st.expander("重設密碼"):
        with st.form("reset_password_form", clear_on_submit=True):
            target_user = st.selectbox("選擇帳號", username_options, key="reset_pw_user")
            new_pw = st.text_input("新密碼", type="password")
            new_pw_confirm = st.text_input("確認新密碼", type="password")
            reset_btn = st.form_submit_button("重設密碼")

        if reset_btn:
            if not new_pw or new_pw != new_pw_confirm:
                st.error("密碼為空或兩次不一致")
            elif len(new_pw) < 4:
                st.error("密碼至少 4 個字元")
            else:
                try:
                    conn = _get_supabase_conn()
                    result = conn.client.table('pediatric_users').update({
                        'password_hash': hash_password(new_pw),
                    }).eq('username', target_user).execute()
                    if result.data:
                        st.success(f"已重設 {target_user} 的密碼")
                    else:
                        st.error("帳號不存在")
                except Exception as e:
                    st.error(f"重設失敗：{str(e)}")

    # 變更角色 / 科部
    with st.expander("變更角色 / 科部"):
        with st.form("change_role_form", clear_on_submit=True):
            target_user2 = st.selectbox("選擇帳號", username_options, key="role_change_user")
            new_role = st.selectbox(
                "新角色",
                list(USER_ROLES.keys()),
                format_func=lambda r: USER_ROLES[r],
            )
            new_dept = st.selectbox("新科部", DEPARTMENTS)
            change_btn = st.form_submit_button("變更")

        if change_btn:
            try:
                conn = _get_supabase_conn()
                result = conn.client.table('pediatric_users').update({
                    'user_type': new_role,
                    'department': new_dept,
                }).eq('username', target_user2).execute()
                if result.data:
                    st.success(f"已將 {target_user2} 變更為 {USER_ROLES[new_role]}（{new_dept}）")
                else:
                    st.error("帳號不存在")
            except Exception as e:
                st.error(f"變更失敗：{str(e)}")

    # 停用帳號
    with st.expander("停用帳號"):
        with st.form("deactivate_form", clear_on_submit=True):
            target_user3 = st.selectbox("選擇帳號", username_options, key="deactivate_user")
            deactivate_btn = st.form_submit_button("停用帳號")

        if deactivate_btn:
            success, msg = deactivate_user(target_user3)
            if success:
                st.success(f"已停用帳號：{target_user3}")
                st.rerun()
            else:
                st.error(msg)
