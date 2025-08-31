import streamlit as st
import hashlib
import json
import os
from modules.auth import USER_ROLES, PERMISSIONS, check_permission
from database import add_user, get_user, add_evaluation, get_student_evaluations, get_teacher_evaluations, get_department_students, get_all_users, get_all_evaluations, update_user_role, delete_user, delete_evaluation, reset_admin_password

# 設定頁面配置
st.set_page_config(
    page_title="臨床教師評核系統 - 登入",
    page_icon="🏥",
    layout="centered"
)

def hash_password(password):
    """將密碼進行雜湊處理"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    """驗證使用者身份"""
    user = get_user(username)
    hashed_input = hash_password(password)
    
    # 添加除錯訊息
    if user:
        st.write(f"資料庫中的密碼雜湊：{user['password']}")
        st.write(f"輸入的密碼雜湊：{hashed_input}")
    
    if user and user['password'] == hashed_input:
        return user['role']
    return None

def show_login_page():
    """顯示登入頁面"""
    st.title("臨床教師評核系統 - 登入")
    
    # 建立兩個分頁：登入和註冊
    login_tab, register_tab = st.tabs(["登入", "註冊"])
    
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("使用者名稱")
            password = st.text_input("密碼", type="password")
            submitted = st.form_submit_button("登入")
            
            if submitted:
                if not username or not password:
                    st.error("請輸入使用者名稱和密碼")
                    return
                
                role = authenticate_user(username, password)
                if role:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['role'] = role
                    user = get_user(username)
                    st.session_state['user_name'] = user['name']
                    st.session_state['department'] = user.get('department')
                    st.success(f"歡迎回來，{st.session_state['user_name']}！")
                    st.rerun()
                else:
                    st.error("使用者名稱或密碼錯誤")
    
    with register_tab:
        with st.form("registration_form"):
            username = st.text_input("使用者名稱 (帳號)", help="請設定您的登入帳號")
            password = st.text_input("密碼", type="password")
            confirm_password = st.text_input("確認密碼", type="password")
            name = st.text_input("姓名", help="請填寫您的真實姓名")
            role = st.selectbox("身份", options=list(USER_ROLES.keys()), format_func=lambda x: USER_ROLES[x])
            student_id = st.text_input("學號", help="學生必填，其他角色可選填")
            department = st.selectbox("科別", options=[
                "小兒科", "內科", "外科", "婦產科", "神經科", "精神科", "家醫科",
                "急診醫學科", "麻醉科", "放射科", "病理科", "復健科", "皮膚科",
                "眼科", "耳鼻喉科", "泌尿科", "骨科", "其他科別"
            ])
            extension = st.text_input("分機", help="請填寫您的聯絡分機")
            email = st.text_input("電子郵件", help="請填寫您的聯絡信箱")
            
            submitted = st.form_submit_button("申請帳號")
            
            if submitted:
                # 驗證必填欄位
                if not all([username, password, confirm_password, name, role]):
                    st.error("請填寫所有必填欄位")
                    return
                
                # 驗證密碼
                if password != confirm_password:
                    st.error("兩次輸入的密碼不一致")
                    return
                
                # 驗證學生學號
                if role == 'student' and not student_id:
                    st.error("學生必須填寫學號")
                    return
                
                # 檢查使用者名稱是否已存在
                if get_user(username):
                    st.error("使用者名稱已存在")
                    return
                
                # 建立新使用者
                if add_user(
                    username=username,
                    password=hash_password(password),
                    role=role,
                    name=name,
                    student_id=student_id,
                    department=department,
                    extension=extension,
                    email=email
                ):
                    st.success("帳號申請成功！請等待管理員審核。")
                else:
                    st.error("帳號申請失敗，請稍後再試。")

def show_admin_dashboard():
    """顯示管理員儀表板"""
    st.header("系統管理員功能")
    
    # 建立分頁
    tab1, tab2, tab3 = st.tabs(["使用者管理", "評分資料", "系統設定"])
    
    with tab1:
        st.subheader("使用者管理")
        
        # 顯示所有使用者
        users = get_all_users()
        if users:
            for user in users:
                with st.expander(f"{user['name']} ({USER_ROLES[user['role']]})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"帳號：{user['username']}")
                        st.write(f"身份：{USER_ROLES[user['role']]}")
                        st.write(f"科別：{user['department']}")
                        if user['student_id']:
                            st.write(f"學號：{user['student_id']}")
                        st.write(f"分機：{user['extension']}")
                        st.write(f"電子郵件：{user['email']}")
                        st.write(f"建立時間：{user['created_at']}")
                    
                    with col2:
                        # 更新使用者權限
                        new_role = st.selectbox(
                            "更新權限",
                            options=list(USER_ROLES.keys()),
                            index=list(USER_ROLES.keys()).index(user['role']),
                            key=f"role_{user['username']}"
                        )
                        if new_role != user['role']:
                            if st.button("更新權限", key=f"update_role_{user['username']}"):
                                if update_user_role(user['username'], new_role):
                                    st.success("權限更新成功")
                                    st.rerun()
                                else:
                                    st.error("權限更新失敗")
                        
                        # 刪除使用者
                        if st.button("刪除使用者", key=f"delete_{user['username']}"):
                            if delete_user(user['username']):
                                st.success("使用者已刪除")
                                st.rerun()
                            else:
                                st.error("刪除使用者失敗")
        else:
            st.info("目前沒有使用者資料")
    
    with tab2:
        st.subheader("所有評分資料")
        
        # 顯示所有評分資料
        evaluations = get_all_evaluations()
        if evaluations:
            for eval in evaluations:
                with st.expander(f"{eval['teacher_name']} 評分 {eval['student_name']} - {eval['created_at']}"):
                    st.write(f"教師：{eval['teacher_name']}")
                    st.write(f"學生：{eval['student_name']}")
                    st.write(f"分數：{eval['score']}")
                    st.write(f"評語：{eval['comments']}")
                    
                    # 刪除評分
                    if st.button("刪除評分", key=f"delete_eval_{eval['id']}"):
                        if delete_evaluation(eval['id']):
                            st.success("評分已刪除")
                            st.rerun()
                        else:
                            st.error("刪除評分失敗")
        else:
            st.info("目前沒有評分資料")
    
    with tab3:
        st.subheader("系統設定")
        
        # 重設管理者密碼
        with st.form("reset_admin_password"):
            st.write("重設管理者密碼")
            new_password = st.text_input("新密碼", type="password")
            confirm_password = st.text_input("確認新密碼", type="password")
            
            if st.form_submit_button("重設密碼"):
                if new_password != confirm_password:
                    st.error("兩次輸入的密碼不一致")
                else:
                    if reset_admin_password(new_password):
                        st.success("密碼重設成功")
                    else:
                        st.error("密碼重設失敗")

def show_teacher_dashboard():
    """顯示教師儀表板"""
    st.header("教師功能")
    
    # 顯示該科學生資料
    st.subheader("學生資料")
    department = st.session_state.get('department')
    if department:
        students = get_department_students(department)
        if students:
            st.write(f"科別：{department}")
            for student in students:
                st.write(f"- {student['name']} (學號：{student['student_id']})")
        else:
            st.info("目前沒有學生資料")
    else:
        st.warning("您尚未設定科別")
    
    # 評分表單
    st.subheader("評分表單")
    with st.form("grading_form"):
        # 選擇學生
        if department and students:
            student_options = {f"{s['name']} ({s['student_id']})": s['username'] for s in students}
            selected_student = st.selectbox("選擇學生", options=list(student_options.keys()))
            student_id = student_options[selected_student]
        else:
            st.warning("無法載入學生列表")
            student_id = None
        
        # 輸入分數
        score = st.slider("評分", 0, 100, 80)
        
        # 輸入評語
        comments = st.text_area("評語")
        
        if st.form_submit_button("提交評分") and student_id:
            if add_evaluation(
                teacher_id=st.session_state['username'],
                student_id=student_id,
                score=score,
                comments=comments
            ):
                st.success("評分已提交")
            else:
                st.error("評分提交失敗")
    
    # 顯示已提交的評分
    st.subheader("已提交的評分")
    evaluations = get_teacher_evaluations(st.session_state['username'])
    if evaluations:
        for eval in evaluations:
            with st.expander(f"{eval['student_name']} - {eval['created_at']}"):
                st.write(f"分數：{eval['score']}")
                st.write(f"評語：{eval['comments']}")
    else:
        st.info("尚未提交任何評分")

def show_student_dashboard():
    """顯示學生儀表板"""
    st.header("學生功能")
    
    # 顯示個人資料
    st.subheader("個人資料")
    user = get_user(st.session_state['username'])
    if user:
        st.write(f"姓名：{user['name']}")
        st.write(f"學號：{user['student_id']}")
        st.write(f"科別：{user['department']}")
        st.write(f"分機：{user['extension']}")
        st.write(f"電子郵件：{user['email']}")
    
    # 顯示評分資料
    st.subheader("評分資料")
    evaluations = get_student_evaluations(st.session_state['username'])
    if evaluations:
        for eval in evaluations:
            with st.expander(f"{eval['teacher_name']} - {eval['created_at']}"):
                st.write(f"分數：{eval['score']}")
                st.write(f"評語：{eval['comments']}")
    else:
        st.info("尚未收到任何評分")

def main():
    # 初始化 session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # 如果已登入，顯示主頁面
    if st.session_state.logged_in:
        st.title(f"歡迎，{st.session_state['user_name']}")
        
        # 顯示登出按鈕
        if st.button("登出"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.user_name = None
            st.session_state.department = None
            st.rerun()
        
        # 根據身份顯示不同的功能
        role = st.session_state.role
        
        if role == 'admin':
            show_admin_dashboard()
        elif role == 'teacher':
            show_teacher_dashboard()
        elif role == 'student':
            show_student_dashboard()
    
    # 如果未登入，顯示登入頁面
    else:
        show_login_page()

if __name__ == "__main__":
    main() 