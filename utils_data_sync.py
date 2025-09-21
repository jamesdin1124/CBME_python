import pandas as pd
from modules.google_connection import fetch_google_form_data
from supabase import create_client
import os
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime, timezone
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

def get_last_sync_time(supabase, table_name):
    """獲取最後同步時間"""
    try:
        response = supabase.table(table_name)\
            .select("timestamp")\
            .order('timestamp', desc=True)\
            .limit(1)\
            .execute()
        
        if response.data:
            return pd.to_datetime(response.data[0]['timestamp'])
        return None
    except Exception as e:
        st.error(f"獲取最後同步時間失敗：{str(e)}")
        return None

def sanitize_float(value):
    """處理浮點數值，確保符合 JSON 規範"""
    try:
        if pd.isna(value):
            return None
        float_val = float(value)
        # 檢查是否為無限大或 NaN
        if pd.isinf(float_val) or pd.isna(float_val):
            return None
        return float_val
    except:
        return None

def convert_tw_time(time_str):
    """轉換中文時間格式"""
    try:
        if pd.isna(time_str):
            return None
        # 處理上午/下午
        if '上午' in time_str:
            time_str = time_str.replace('上午', 'AM')
        elif '下午' in time_str:
            time_str = time_str.replace('下午', 'PM')
        
        # 使用 pandas 的時間解析
        return pd.to_datetime(time_str, format='%Y/%m/%d %p %I:%M:%S')
    except Exception as e:
        st.error(f"時間轉換錯誤：{str(e)}")
        return None

def process_training_date(date_str):
    """處理訓練科部日期格式"""
    try:
        if pd.isna(date_str):
            return None
        # 嘗試不同的日期格式
        try:
            # 如果是 "年/月/日" 格式
            return pd.to_datetime(date_str, format='%Y/%m/%d')
        except:
            try:
                # 如果是 "月/日/年" 格式
                return pd.to_datetime(date_str, format='%m/%d/%Y')
            except:
                # 最後嘗試自動解析
                return pd.to_datetime(date_str)
    except Exception as e:
        st.error(f"日期轉換錯誤：{str(e)}")
        return None

def sync_to_supabase():
    """同步 Google Sheet 資料到 Supabase"""
    try:
        # 載入環境變數
        load_dotenv()
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            st.error("請確認 .env 檔案中有設定 SUPABASE_URL 和 SUPABASE_KEY")
            return
        
        # 建立 Supabase 連線
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 檢查連線是否成功
        try:
            # 嘗試讀取資料表結構
            response = supabase.table('epa_evaluations').select("*").limit(1).execute()
            st.success("成功連線到 Supabase")
        except Exception as e:
            st.error(f"無法連線到 Supabase：{str(e)}")
            st.error("請確認：")
            st.error("1. SUPABASE_URL 和 SUPABASE_KEY 是否正確")
            st.error("2. 資料表 'epa_evaluations' 是否已建立")
            return
        
        # ========== EPA 評核資料同步 ==========
        st.write("正在同步 EPA 評核資料...")
        
        # 獲取最後同步時間
        last_sync_time = get_last_sync_time(supabase, 'epa_evaluations')
        if last_sync_time:
            st.info(f"上次同步時間：{last_sync_time}")
        else:
            st.info("資料表中目前沒有資料")
        
        # 載入 EPA 評核資料
        epa_df, _ = fetch_google_form_data()
        
        if epa_df is not None and not epa_df.empty:
            # 更新欄位對應
            column_mapping = {
                '時間戳記': 'timestamp',
                '學號': 'student_id',
                '學員姓名': 'student_name',
                '梯次': 'batch',
                'EPA評核項目': 'epa_item',
                '學員自評EPA等級': 'self_evaluation',
                '教師評核EPA等級': 'teacher_evaluation',
                '教師': 'teacher_name',
                '回饋': 'feedback',
                '臨床情境': 'clinical_scenario',
                '地點': 'location'  # 新增地點欄位對應
            }
            
            # 重命名欄位
            epa_df = epa_df.rename(columns=column_mapping)
            
            # 確保所有必要欄位都存在，如果不存在則新增並設為 None
            for col in column_mapping.values():
                if col not in epa_df.columns:
                    epa_df[col] = None
            
            # 處理時間格式
            epa_df['timestamp'] = epa_df['timestamp'].apply(convert_tw_time)
            
            # 處理數值欄位
            epa_df['self_evaluation'] = epa_df['self_evaluation'].apply(sanitize_float)
            epa_df['teacher_evaluation'] = epa_df['teacher_evaluation'].apply(sanitize_float)
            
            # 確保字串欄位不是 nan
            string_columns = ['student_id', 'student_name', 'batch', 'epa_item', 
                            'teacher_name', 'feedback', 'clinical_scenario', 'location']
            for col in string_columns:
                epa_df[col] = epa_df[col].fillna('')
            
            # 獲取最後同步時間
            last_sync = supabase.table('epa_evaluations')\
                .select("timestamp")\
                .order('timestamp', desc=True)\
                .limit(1)\
                .execute()
            
            if last_sync.data:
                last_sync_time = pd.to_datetime(last_sync.data[0]['timestamp'])
                new_records = epa_df[epa_df['timestamp'] > last_sync_time]
                st.write(f"發現 {len(new_records)} 筆新資料")
            else:
                new_records = epa_df
                st.write(f"首次同步，共有 {len(new_records)} 筆資料")
            
            # 只取前五筆資料
            new_records = new_records.head(5)
            st.write(f"將上傳前 5 筆資料：")
            st.write(new_records)
            
            # 批次插入資料
            if not new_records.empty:
                # 確保時間戳記格式正確（加入時區資訊）
                new_records['timestamp'] = pd.to_datetime(new_records['timestamp']).dt.tz_localize('Asia/Taipei')
                new_records['timestamp'] = new_records['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S%z')
                
                # 將 student_id 轉換為字串類型
                new_records['student_id'] = new_records['student_id'].astype(str)
                
                # 處理數值欄位，將 NaN 轉換為 None
                new_records['self_evaluation'] = pd.to_numeric(new_records['self_evaluation'], errors='coerce')
                new_records['teacher_evaluation'] = pd.to_numeric(new_records['teacher_evaluation'], errors='coerce')
                
                # 將空字串轉換為 None
                for col in ['clinical_scenario', 'location', 'batch', 'feedback']:
                    new_records[col] = new_records[col].replace('', None)
                
                # 處理 NaN 值
                new_records = new_records.replace({pd.NA: None, pd.NaT: None, float('nan'): None})
                
                # 轉換為字典列表
                records = new_records.to_dict('records')
                
                st.write("準備上傳的資料（已整理）：")
                st.write(records)
                
                success_count = 0
                with st.progress(0) as progress_bar:
                    for i, record in enumerate(records):
                        try:
                            st.write(f"正在處理第 {i+1} 筆資料：")
                            st.write(record)
                            
                            # 移除 None 值的欄位
                            record = {k: v for k, v in record.items() if v is not None}
                            
                            # 嘗試插入資料
                            result = supabase.table('epa_evaluations').insert(record).execute()
                            
                            if hasattr(result, 'data') and result.data:
                                success_count += 1
                                st.success(f"第 {i+1} 筆資料上傳成功")
                            else:
                                st.error(f"第 {i+1} 筆資料上傳失敗")
                                st.write("API 回應：", result)
                            
                            # 更新進度
                            progress_bar.progress((i + 1) / len(records))
                            
                        except Exception as e:
                            st.error(f"處理第 {i+1} 筆資料時發生錯誤：{str(e)}")
                            st.write("問題資料：", record)
                            continue
                
                st.success(f"成功上傳 {success_count} 筆 EPA 評核資料（共嘗試 {len(records)} 筆）")
                
                # 驗證資料是否確實存在
                verification = supabase.table('epa_evaluations').select("count", count='exact').execute()
                st.write(f"資料庫中實際資料筆數：{verification.count}")
            else:
                st.info("沒有新的 EPA 評核資料需要同步")
        else:
            st.error("無法載入 EPA 評核資料")
        
        st.success("EPA 評核資料同步完成！")
        
        # 顯示同步統計
        st.subheader("同步統計")
        epa_count = supabase.table('epa_evaluations').select("count", count='exact').execute()
        
        st.write(f"EPA 評核資料總筆數：{epa_count.count}")
        
    except Exception as e:
        st.error(f"資料同步過程中發生錯誤：{str(e)}")
        st.exception(e)  # 顯示完整的錯誤追蹤

if __name__ == "__main__":
    st.title("Google Sheet 到 Supabase 資料同步工具")
    
    # 同步頻率選項
    sync_frequency = st.selectbox(
        "選擇同步頻率",
        ["手動同步", "每天同步", "每週同步"]
    )
    
    if sync_frequency == "手動同步":
        if st.button("開始同步"):
            sync_to_supabase()
    else:
        st.info(f"已設定{sync_frequency}，系統將自動執行同步")
        # 這裡可以加入排程邏輯
