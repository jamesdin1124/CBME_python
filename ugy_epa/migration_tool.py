# migration_tool.py
import pandas as pd
from modules.google_connection import fetch_google_form_data
from supabase import create_client
import os
from dotenv import load_dotenv
import streamlit as st

def migrate_to_supabase():
    """將 Google Sheet 資料遷移到 Supabase"""
    try:
        # 載入環境變數
        load_dotenv()
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        
        # 建立 Supabase 連線
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 載入 EPA 評核資料
        st.write("正在載入 EPA 評核資料...")
        epa_df, _ = fetch_google_form_data()
        
        if epa_df is not None:
            # 重命名欄位
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
                '臨床情境': 'clinical_scenario'
            }
            
            # 重命名欄位
            epa_df = epa_df.rename(columns=column_mapping)
            
            # 轉換時間格式
            epa_df['timestamp'] = pd.to_datetime(epa_df['timestamp'])
            
            # 轉換為數值型態
            epa_df['self_evaluation'] = pd.to_numeric(epa_df['self_evaluation'], errors='coerce')
            epa_df['teacher_evaluation'] = pd.to_numeric(epa_df['teacher_evaluation'], errors='coerce')
            
            # 轉換為字典列表
            records = epa_df.to_dict('records')
            
            # 批次插入資料
            st.write(f"開始插入 {len(records)} 筆 EPA 評核資料...")
            for i, record in enumerate(records, 1):
                try:
                    supabase.table('epa_evaluations').insert(record).execute()
                    if i % 10 == 0:  # 每10筆顯示一次進度
                        st.write(f"已處理 {i}/{len(records)} 筆資料")
                except Exception as e:
                    st.error(f"插入第 {i} 筆資料時發生錯誤：{str(e)}")
                    continue
            
            st.success("EPA 評核資料遷移完成！")
        
        # 載入訓練科部資料
        st.write("正在載入訓練科部資料...")
        dept_df, _ = fetch_google_form_data(sheet_title="訓練科部")
        
        if dept_df is not None:
            # 重命名欄位
            dept_mapping = {
                '學號': 'student_id',
                '姓名': 'student_name',
                '日期': 'training_date',
                '科部': 'department'
            }
            
            # 重命名欄位
            dept_df = dept_df.rename(columns=dept_mapping)
            
            # 轉換日期格式
            dept_df['training_date'] = pd.to_datetime(dept_df['training_date'])
            
            # 轉換為字典列表
            dept_records = dept_df.to_dict('records')
            
            # 批次插入資料
            st.write(f"開始插入 {len(dept_records)} 筆訓練科部資料...")
            for i, record in enumerate(dept_records, 1):
                try:
                    supabase.table('training_departments').insert(record).execute()
                    if i % 10 == 0:  # 每10筆顯示一次進度
                        st.write(f"已處理 {i}/{len(dept_records)} 筆資料")
                except Exception as e:
                    st.error(f"插入第 {i} 筆資料時發生錯誤：{str(e)}")
                    continue
            
            st.success("訓練科部資料遷移完成！")
        
        st.success("所有資料遷移完成！")
        
    except Exception as e:
        st.error(f"資料遷移過程中發生錯誤：{str(e)}")

if __name__ == "__main__":
    st.title("Google Sheet 到 Supabase 資料遷移工具")
    
    if st.button("開始資料遷移"):
        migrate_to_supabase()