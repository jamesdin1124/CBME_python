#!/usr/bin/env python3
"""
批次建立兒科醫師帳號
- 帳號 (username) = DOC碼
- 密碼 (password) = DOC碼
- 沒有 DOC碼的醫師暫時跳過
"""

import hashlib
import sys
import os

# 加入專案根目錄到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.supabase_connection import SupabaseConnection


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# 兒科醫師資料
DOCTORS = [
    # (姓名, DOC碼, email, 職級)
    ("林建銘", "DOC31098", "ming.sandra@gmail.com", "VS"),
    ("王志堅", "DOC31018", "ndmcccw@yahoo.com.tw", "VS"),
    ("朱德明", "DOC31029", "dermingchu618@gmail.com", "VS"),
    ("陳錫洲", "DOC31055", "chensjou@yahoo.com.tw", "VS"),
    ("王富民", "DOC31099", "m86010442@gmail.com", "VS"),
    ("胡智棻", "DOC31040", "caperhu@gmail.com", "VS"),
    ("謝國祥", "DOC31046", "hkh0720717@gmail.com", "VS"),
    ("周雅玲", "DOC31047", "diddi0331@gmail.com", "VS"),
    ("徐萬夫", "DOC31050", "Kisetsu1110@gmail.com", "VS"),
    ("張佳寧", "DOC31044", "lizy0529@hotmail.com", "VS"),
    ("王德勳", "DOC31054", "okishimashuji317@gmail.com", "VS"),
    ("何昇遠", "DOC31061", "syho1212@gmail.com", "VS"),
    ("丁肇壯", "DOC31060", "jamesdin1124@gmail.com", "VS"),
    ("江哲銘", "DOC31063", "M493ming@gmail.com", "VS"),
    ("吳柏緯", "DOC31003", "yves922@gmail.com", "VS"),  # 原資料有 gmail,com 已修正
    ("方泓翔", "DOC31636", "Spty871029@hotmail.com", "Fellow"),
    ("陳映辰", "DOC31009", "agtta793@gmail.com", "Fellow"),
    # ("游家祥", None, "phil790419@gmail.com", "Fellow"),  # 無 DOC碼，跳過
    # ("張嘉緯", None, "meatball348@hotmail.com", "Fellow"),  # 無 DOC碼，跳過
    ("朱君浩", "DOC31017", "topeverley@gmail.com", "CR"),
    ("白立凡", "DOC31022", "lifanpai@gmail.com", "Fellow"),
    ("蒙彥傑", "DOC31021", "crazyricky20@gmail.com", "Fellow"),
    ("胡鈞傑", "DOC31024", "k0987153081@gmail.com", "Fellow"),
    ("曾梓翔", "DOC31023", "fatjohnson0822@hotmail.com", "Fellow"),
    # ("吳宗翰", None, "komica321@gmail.com", "Fellow"),  # 無 DOC碼，跳過
    ("曾富睿", "DOC31025", "poloeloha@gmail.com", "CR"),
    ("游翔皓", "DOC31030", "s609abc09@gmail.com", "R"),
    ("呂昱暘", "DOC31031", "md.luyuyan@gmail.com", "R"),
    ("林盈秀", "DOC32002", "kgaclin100299@gmail.com", "R"),
    ("黃靖雯", "DOC32001", "jinwin007@gmail.com", "R"),
    ("李以琳", "DOC32006", "yinc2249@gmail.com", "R"),
    ("張元譯", "DOC32004", "danny16168@gmail.com", "R"),
]


def map_role_to_user_type(role):
    """將職級對應到系統 user_type"""
    mapping = {
        "VS": "teacher",       # 主治醫師 → teacher
        "Fellow": "teacher",   # Fellow → teacher
        "CR": "teacher",       # Chief Resident → teacher
        "R": "resident",       # Resident → resident
    }
    return mapping.get(role, "resident")


def map_role_to_resident_level(role):
    """將職級對應到 resident_level（DB 只允許 R1, R2, R3）"""
    # VS, Fellow, CR → teacher，不需要 resident_level
    # R → 暫不設定，需確認具體年級後再更新
    return None


def main():
    conn = SupabaseConnection()

    success_count = 0
    fail_count = 0
    skip_count = 0

    print("=" * 60)
    print("批次建立兒科醫師帳號")
    print("=" * 60)

    for name, doc_code, email, role in DOCTORS:
        if not doc_code:
            print(f"⚠️  跳過 {name}（無 DOC碼）")
            skip_count += 1
            continue

        user_type = map_role_to_user_type(role)
        resident_level = map_role_to_resident_level(role)

        user_data = {
            "username": doc_code,
            "full_name": name,
            "email": email,
            "user_type": user_type,
            "department": "小兒部",
            "is_active": True,
            "password_hash": hash_password(doc_code),  # 預設密碼 = DOC碼
        }

        if resident_level:
            user_data["resident_level"] = resident_level

        result = conn.upsert_pediatric_user(user_data)

        if result:
            print(f"✅ {name} ({doc_code}) - {role} → {user_type} - 建立成功")
            success_count += 1
        else:
            print(f"❌ {name} ({doc_code}) - 建立失敗")
            fail_count += 1

    print("=" * 60)
    print(f"完成！成功: {success_count}  失敗: {fail_count}  跳過: {skip_count}")
    print(f"（3 位無 DOC碼的醫師: 游家祥、張嘉緯、吳宗翰 需另行處理）")
    print("=" * 60)


if __name__ == "__main__":
    main()
