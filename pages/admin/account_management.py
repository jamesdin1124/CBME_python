"""
帳號管理頁面（全科別通用）
管理員可手動建立帳號或透過 CSV 批次匯入。
資料同時寫入 users.json 與 Supabase pediatric_users 表。
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime

from modules.auth import (
    create_user_dual_write, load_users, hash_password,
    USER_ROLES, save_users,
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
    'teacher': '主治醫師',
    'resident': '住院醫師',
}


def show_account_management():
    """帳號管理主入口（僅 admin 可存取）"""
    st.markdown("## 帳號管理")
    st.caption("建立與管理系統帳號。新帳號會同時儲存到本地與 Supabase。")

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

        # 住院醫師專屬欄位
        st.markdown("---")
        st.markdown("**住院醫師專屬（其他角色可略過）**")
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            resident_level = st.selectbox("住院醫師級別", [None, 'R1', 'R2', 'R3'],
                                          format_func=lambda x: '未選擇' if x is None else x)
        with r_col2:
            enrollment_year = st.number_input(
                "入學年度", min_value=2018, max_value=2035,
                value=datetime.now().year, step=1)

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
            success, msg = create_user_dual_write(
                username=username.strip(),
                password_plaintext=password,
                role=role,
                name=full_name.strip(),
                department=department,
                email=email.strip() or None,
                extension=extension.strip() or None,
                resident_level=resident_level if role == 'resident' else None,
                enrollment_year=enrollment_year if role == 'resident' else None,
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
    header = "帳號,密碼,姓名,角色,科部,email,分機,住院醫師級別,入學年度\n"
    example = (
        "dr_wang,Changeme123,王大明,teacher,小兒部,wang@hospital.com,1234,,\n"
        "lin_ys,Changeme123,林盈秀,resident,小兒部,lin@hospital.com,5678,R1,2024\n"
    )
    return (header + example).encode('utf-8-sig')


def _validate_csv(df):
    """驗證 CSV 各行的基本格式"""
    errors = []
    valid_roles = set(CREATABLE_ROLES.keys())
    valid_depts = set(DEPARTMENTS)
    valid_levels = {'R1', 'R2', 'R3', ''}

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
        level = row.get('住院醫師級別', '').strip()
        if level and level not in valid_levels:
            errors.append(f"第 {row_num} 行：住院醫師級別 '{level}' 無效")

    return errors


def _execute_csv_import(df):
    """執行 CSV 批次匯入"""
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

        resident_level = row.get('住院醫師級別', '').strip() or None
        enrollment_year_str = row.get('入學年度', '').strip()
        enrollment_year = None
        if enrollment_year_str:
            try:
                enrollment_year = int(enrollment_year_str)
            except ValueError:
                pass

        success, msg = create_user_dual_write(
            username=username,
            password_plaintext=row['密碼'].strip(),
            role=role,
            name=row['姓名'].strip(),
            department=row['科部'].strip(),
            email=row.get('email', '').strip() or None,
            extension=row.get('分機', '').strip() or None,
            resident_level=resident_level if role == 'resident' else None,
            enrollment_year=enrollment_year if role == 'resident' else None,
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

    # 從 users.json 讀取
    local_users = load_users()

    if not local_users:
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

    # 轉為列表
    rows = []
    for uname, udata in local_users.items():
        role = udata.get('role', '')
        dept = udata.get('department', '')

        if filter_role != '全部' and role != filter_role:
            continue
        if filter_dept != '全部' and dept != filter_dept:
            continue

        rows.append({
            '帳號': uname,
            '姓名': udata.get('name', ''),
            '角色': USER_ROLES.get(role, role),
            '科部': dept or '未設定',
            'email': udata.get('email', ''),
            '分機': udata.get('extension', ''),
        })

    if not rows:
        st.info("沒有符合條件的帳號")
        return

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(f"共 {len(rows)} 筆")

    # 重設密碼區塊
    st.markdown("---")
    st.markdown("#### 帳號操作")

    with st.expander("重設密碼"):
        with st.form("reset_password_form", clear_on_submit=True):
            target_user = st.selectbox(
                "選擇帳號",
                [u for u in local_users.keys()],
            )
            new_pw = st.text_input("新密碼", type="password")
            new_pw_confirm = st.text_input("確認新密碼", type="password")
            reset_btn = st.form_submit_button("重設密碼")

        if reset_btn:
            if not new_pw or new_pw != new_pw_confirm:
                st.error("密碼為空或兩次不一致")
            elif len(new_pw) < 4:
                st.error("密碼至少 4 個字元")
            else:
                users = load_users()
                if target_user in users:
                    users[target_user]['password'] = hash_password(new_pw)
                    save_users(users)
                    # 同步到 Supabase
                    try:
                        from modules.supabase_connection import SupabaseConnection
                        conn = SupabaseConnection()
                        conn.upsert_pediatric_user({
                            'username': target_user,
                            'full_name': users[target_user].get('name', target_user),
                            'user_type': users[target_user].get('role', 'resident'),
                            'password_hash': hash_password(new_pw),
                        })
                    except Exception:
                        pass
                    st.success(f"已重設 {target_user} 的密碼")
                else:
                    st.error("帳號不存在")

    with st.expander("變更角色 / 科部"):
        with st.form("change_role_form", clear_on_submit=True):
            target_user2 = st.selectbox(
                "選擇帳號",
                [u for u in local_users.keys()],
                key="role_change_user",
            )
            new_role = st.selectbox(
                "新角色",
                list(USER_ROLES.keys()),
                format_func=lambda r: USER_ROLES[r],
            )
            new_dept = st.selectbox("新科部", DEPARTMENTS)
            change_btn = st.form_submit_button("變更")

        if change_btn:
            users = load_users()
            if target_user2 in users:
                users[target_user2]['role'] = new_role
                users[target_user2]['department'] = new_dept
                save_users(users)
                # 同步到 Supabase
                try:
                    from modules.supabase_connection import SupabaseConnection
                    conn = SupabaseConnection()
                    conn.upsert_pediatric_user({
                        'username': target_user2,
                        'full_name': users[target_user2].get('name', target_user2),
                        'user_type': new_role if new_role != 'student' else 'resident',
                        'department': new_dept,
                    })
                except Exception:
                    pass
                st.success(f"已將 {target_user2} 變更為 {USER_ROLES[new_role]}（{new_dept}）")
            else:
                st.error("帳號不存在")
