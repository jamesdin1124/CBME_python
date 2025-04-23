import pandas as pd
from datetime import datetime

def process_training_departments(df):
    """處理訓練科部資料
    
    Args:
        df (pd.DataFrame): 包含訓練科部資料的DataFrame
        
    Returns:
        pd.DataFrame: 處理後的訓練科部資料
    """
    try:
        # 確保必要欄位存在
        required_columns = ['學號', '姓名']
        if not all(col in df.columns for col in required_columns):
            raise ValueError("缺少必要欄位：學號或姓名")
            
        # 複製DataFrame以避免修改原始資料
        processed_df = df.copy()
        
        # 將學號轉換為字串型態
        processed_df['學號'] = processed_df['學號'].astype(str)
        
        # 找出日期欄位（假設日期欄位的格式為 YYYY/MM/DD）
        date_columns = [col for col in processed_df.columns 
                       if isinstance(col, str) and len(col.split('/')) == 3]
        
        # 將日期欄位轉換為datetime格式
        for col in date_columns:
            try:
                # 將日期字串轉換為datetime物件
                processed_df[col] = pd.to_datetime(col)
            except:
                continue
                
        return processed_df
        
    except Exception as e:
        raise Exception(f"處理訓練科部資料時發生錯誤：{str(e)}")

def get_student_departments(df, student_id, date=None):
    """獲取特定學生在特定日期的訓練科部
    
    Args:
        df (pd.DataFrame): 處理後的訓練科部資料
        student_id (str): 學生學號
        date (str, optional): 日期字串 (YYYY/MM/DD)
        
    Returns:
        dict: 包含學生訓練科部資訊的字典
    """
    try:
        # 確保學號為字串型態
        student_id = str(student_id)
        
        # 篩選特定學生的資料
        student_data = df[df['學號'] == student_id]
        
        if student_data.empty:
            return {"error": f"找不到學號 {student_id} 的資料"}
            
        # 如果沒有指定日期，返回該學生所有的訓練科部資料
        if date is None:
            # 找出所有日期欄位
            date_columns = [col for col in df.columns 
                          if isinstance(col, str) and len(col.split('/')) == 3]
            
            # 建立日期和科部的對應
            departments = {}
            for col in date_columns:
                dept = student_data[col].iloc[0]
                if pd.notna(dept):  # 只記錄非空值
                    departments[col] = dept
                    
            return {
                "學號": student_id,
                "姓名": student_data['姓名'].iloc[0],
                "訓練科部": departments
            }
        
        # 如果指定了日期
        if date in df.columns:
            dept = student_data[date].iloc[0]
            return {
                "學號": student_id,
                "姓名": student_data['姓名'].iloc[0],
                "日期": date,
                "訓練科部": dept if pd.notna(dept) else None
            }
        else:
            return {"error": f"找不到日期 {date} 的資料"}
            
    except Exception as e:
        return {"error": f"獲取學生訓練科部資料時發生錯誤：{str(e)}"} 