import json
import hashlib
import os

def hash_password(password):
    """將密碼進行雜湊處理"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_initial_admin():
    """建立初始管理員帳號"""
    # 檢查是否已存在使用者資料
    if os.path.exists('users.json'):
        print("使用者資料已存在，請直接使用現有帳號登入")
        return
    
    # 建立初始管理員資料
    admin_data = {
        'admin': {
            'password': hash_password('admin123'),  # 預設密碼
            'role': 'admin',
            'name': '系統管理員'
        }
    }
    
    # 儲存到檔案
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(admin_data, f, ensure_ascii=False, indent=4)
    
    print("初始管理員帳號已建立")
    print("使用者名稱：admin")
    print("密碼：admin123")
    print("請在首次登入後立即修改密碼！")

if __name__ == "__main__":
    create_initial_admin() 