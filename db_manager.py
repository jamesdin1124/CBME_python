import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定頁面配置
st.set_page_config(
    page_title="資料庫管理介面",
    page_icon="🗄️",
    layout="wide"
)

def get_db_connection():
    """建立資料庫連線"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', '5432')
    )

def get_table_data(table_name):
    """獲取表格資料"""
    conn = get_db_connection()
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_table_schema(table_name):
    """獲取表格結構"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default,
            CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'YES' ELSE 'NO' END as is_primary_key
        FROM information_schema.columns c
        LEFT JOIN information_schema.table_constraints tc 
            ON tc.table_name = c.table_name 
            AND tc.constraint_type = 'PRIMARY KEY'
        LEFT JOIN information_schema.constraint_column_usage ccu 
            ON ccu.constraint_name = tc.constraint_name 
            AND ccu.column_name = c.column_name
        WHERE c.table_name = %s
        ORDER BY c.ordinal_position;
    """, (table_name,))
    schema = cursor.fetchall()
    conn.close()
    return schema

def init_db():
    """初始化資料庫表格"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 建立使用者表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(50) PRIMARY KEY,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            student_id VARCHAR(50),
            department VARCHAR(100),
            extension VARCHAR(20),
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 建立評分表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id SERIAL PRIMARY KEY,
            teacher_id VARCHAR(50) NOT NULL,
            student_id VARCHAR(50) NOT NULL,
            score INTEGER NOT NULL,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES users(username),
            FOREIGN KEY (student_id) REFERENCES users(username)
        )
    ''')
    
    # 建立預設管理者帳號
    cursor.execute('''
        INSERT INTO users (username, password, role, name, department)
        VALUES ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin', '系統管理員', '管理部')
        ON CONFLICT (username) DO NOTHING
    ''')
    
    conn.commit()
    conn.close()

def main():
    st.title("資料庫管理介面")
    
    # 初始化資料庫
    if st.button("初始化資料庫"):
        init_db()
        st.success("資料庫初始化完成！")
    
    # 建立分頁
    tab1, tab2 = st.tabs(["資料檢視", "表格結構"])
    
    with tab1:
        st.header("資料檢視")
        
        # 選擇要查看的表格
        table_name = st.selectbox(
            "選擇表格",
            ["users", "evaluations"]
        )
        
        # 顯示表格資料
        df = get_table_data(table_name)
        st.dataframe(df, width="stretch")
        
        # 顯示資料統計
        st.subheader("資料統計")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("資料筆數", len(df))
        with col2:
            st.metric("欄位數量", len(df.columns))
    
    with tab2:
        st.header("表格結構")
        
        # 選擇要查看的表格
        table_name = st.selectbox(
            "選擇表格",
            ["users", "evaluations"],
            key="schema_table"
        )
        
        # 顯示表格結構
        schema = get_table_schema(table_name)
        schema_df = pd.DataFrame(
            schema,
            columns=["欄位名稱", "資料類型", "可為空", "預設值", "主鍵"]
        )
        st.dataframe(schema_df, width="stretch")
        
        # 顯示表格說明
        if table_name == "users":
            st.markdown("""
            ### users 表格說明
            - `username`: 使用者帳號（主鍵）
            - `password`: 密碼（雜湊後）
            - `role`: 使用者角色
            - `name`: 姓名
            - `student_id`: 學號（可為空）
            - `department`: 科別
            - `extension`: 分機
            - `email`: 電子郵件
            - `created_at`: 建立時間
            """)
        elif table_name == "evaluations":
            st.markdown("""
            ### evaluations 表格說明
            - `id`: 評分編號（自動遞增）
            - `teacher_id`: 教師帳號（外鍵）
            - `student_id`: 學生帳號（外鍵）
            - `score`: 分數
            - `comments`: 評語
            - `created_at`: 建立時間
            """)

if __name__ == "__main__":
    main() 