import sqlite3
import os
from datetime import datetime
import hashlib

# 資料庫檔案路徑
DB_FILE = 'clinical_evaluation.db'

def init_db():
    """初始化資料庫"""
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # 建立評分表
        c.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users (username),
                FOREIGN KEY (student_id) REFERENCES users (username)
            )
        ''')
        
        # 建立使用者表
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                name TEXT NOT NULL,
                student_id TEXT,
                department TEXT,
                extension TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

def init_admin():
    """初始化管理者帳號"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # 檢查是否已存在管理者帳號
        c.execute('SELECT * FROM users WHERE role = ?', ('admin',))
        admin = c.fetchone()
        
        if not admin:
            # 建立預設管理者帳號
            admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
            c.execute('''
                INSERT INTO users (username, password, role, name, department)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', admin_password, 'admin', '系統管理員', '管理部'))
            
            conn.commit()
            print("已建立預設管理者帳號")
        
        conn.close()
    except Exception as e:
        print(f"初始化管理者帳號時發生錯誤：{str(e)}")

def add_evaluation(teacher_id, student_id, score, comments):
    """新增評分資料"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO evaluations (teacher_id, student_id, score, comments)
            VALUES (?, ?, ?, ?)
        ''', (teacher_id, student_id, score, comments))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"新增評分資料時發生錯誤：{str(e)}")
        return False

def get_student_evaluations(student_id):
    """獲取學生的所有評分資料"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('''
            SELECT e.*, u.name as teacher_name
            FROM evaluations e
            JOIN users u ON e.teacher_id = u.username
            WHERE e.student_id = ?
            ORDER BY e.created_at DESC
        ''', (student_id,))
        
        evaluations = c.fetchall()
        conn.close()
        
        # 將結果轉換為字典列表
        columns = ['id', 'teacher_id', 'student_id', 'score', 'comments', 'created_at', 'teacher_name']
        return [dict(zip(columns, eval)) for eval in evaluations]
    except Exception as e:
        print(f"獲取學生評分資料時發生錯誤：{str(e)}")
        return []

def get_teacher_evaluations(teacher_id):
    """獲取教師的所有評分資料"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('''
            SELECT e.*, u.name as student_name
            FROM evaluations e
            JOIN users u ON e.student_id = u.username
            WHERE e.teacher_id = ?
            ORDER BY e.created_at DESC
        ''', (teacher_id,))
        
        evaluations = c.fetchall()
        conn.close()
        
        # 將結果轉換為字典列表
        columns = ['id', 'teacher_id', 'student_id', 'score', 'comments', 'created_at', 'student_name']
        return [dict(zip(columns, eval)) for eval in evaluations]
    except Exception as e:
        print(f"獲取教師評分資料時發生錯誤：{str(e)}")
        return []

def get_department_students(department):
    """獲取特定科別的所有學生"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('''
            SELECT username, name, student_id
            FROM users
            WHERE role = 'student' AND department = ?
        ''', (department,))
        
        students = c.fetchall()
        conn.close()
        
        # 將結果轉換為字典列表
        columns = ['username', 'name', 'student_id']
        return [dict(zip(columns, student)) for student in students]
    except Exception as e:
        print(f"獲取科別學生資料時發生錯誤：{str(e)}")
        return []

def add_user(username, password, role, name, student_id=None, department=None, extension=None, email=None):
    """新增使用者"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO users (username, password, role, name, student_id, department, extension, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, role, name, student_id, department, extension, email))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"新增使用者時發生錯誤：{str(e)}")
        return False

def get_user(username):
    """獲取使用者資料"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user:
            columns = ['username', 'password', 'role', 'name', 'student_id', 'department', 'extension', 'email', 'created_at']
            return dict(zip(columns, user))
        return None
    except Exception as e:
        print(f"獲取使用者資料時發生錯誤：{str(e)}")
        return None

def get_all_users():
    """獲取所有使用者資料"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT username, role, name, student_id, department, extension, email, created_at
        FROM users
        ORDER BY created_at DESC
    ''')
    users = []
    for row in c.fetchall():
        users.append({
            'username': row[0],
            'role': row[1],
            'name': row[2],
            'student_id': row[3],
            'department': row[4],
            'extension': row[5],
            'email': row[6],
            'created_at': row[7]
        })
    conn.close()
    return users

def get_all_evaluations():
    """獲取所有評分資料"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT e.id, e.teacher_id, e.student_id, e.score, e.comments, e.created_at,
               t.name as teacher_name, s.name as student_name
        FROM evaluations e
        JOIN users t ON e.teacher_id = t.username
        JOIN users s ON e.student_id = s.username
        ORDER BY e.created_at DESC
    ''')
    evaluations = []
    for row in c.fetchall():
        evaluations.append({
            'id': row[0],
            'teacher_id': row[1],
            'student_id': row[2],
            'score': row[3],
            'comments': row[4],
            'created_at': row[5],
            'teacher_name': row[6],
            'student_name': row[7]
        })
    conn.close()
    return evaluations

def update_user_role(username, new_role):
    """更新使用者權限"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            UPDATE users
            SET role = ?
            WHERE username = ?
        ''', (new_role, username))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"更新使用者權限時發生錯誤：{str(e)}")
        return False

def delete_user(username):
    """刪除使用者"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # 先刪除相關的評分資料
        c.execute('DELETE FROM evaluations WHERE teacher_id = ? OR student_id = ?', (username, username))
        # 再刪除使用者
        c.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"刪除使用者時發生錯誤：{str(e)}")
        return False

def delete_evaluation(eval_id):
    """刪除評分資料"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('DELETE FROM evaluations WHERE id = ?', (eval_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"刪除評分資料時發生錯誤：{str(e)}")
        return False

def reset_admin_password(new_password):
    """重設管理者密碼"""
    try:
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            UPDATE users
            SET password = ?
            WHERE username = 'admin' AND role = 'admin'
        ''', (hashed_password,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"重設管理者密碼時發生錯誤：{str(e)}")
        return False

# 初始化資料庫和管理者帳號
init_db()
init_admin() 