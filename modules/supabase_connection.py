import os
from supabase import create_client, Client
from dotenv import load_dotenv

class SupabaseConnection:
    """
    Supabase 資料庫連接類別
    用於處理與 Supabase 資料庫的連接和操作
    """
    
    def __init__(self):
        """
        初始化 Supabase 連接
        從環境變數中讀取 Supabase URL 和 API Key
        """
        load_dotenv()
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("請在 .env 檔案中設置 SUPABASE_URL 和 SUPABASE_KEY")
            
        self.client: Client = create_client(self.url, self.key)
    
    def get_client(self) -> Client:
        """
        獲取 Supabase 客戶端實例
        
        Returns:
            Client: Supabase 客戶端實例
        """
        return self.client
    
    def test_connection(self) -> bool:
        """
        測試與 Supabase 的連接是否正常
        
        Returns:
            bool: 連接是否成功
        """
        try:
            # 嘗試執行一個簡單的查詢來測試連接
            self.client.table('users').select('count').execute()
            return True
        except Exception as e:
            print(f"Supabase 連接測試失敗: {str(e)}")
            return False 