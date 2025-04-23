from supabase import create_client
import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 取得環境變數
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 建立連線
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 測試連線
try:
    # 嘗試一個簡單的查詢
    response = supabase.table('epa_evaluations').select("*").limit(1).execute()
    print("連線成功！")
    print(f"回應資料：{response.data}")
except Exception as e:
    print(f"連線失敗：{str(e)}")
