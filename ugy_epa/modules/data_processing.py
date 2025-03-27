import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st

def process_epa_level(value):
    """處理單一 EPA 等級值的轉換
    
    Args:
        value: 輸入的 EPA 等級字串
        
    Returns:
        float: 轉換後的數值
    """
    # 如果輸入值是空值，返回 None
    if pd.isna(value):
        return None
        
    # 將輸入轉換為字串並去除前後空白
    value = str(value).strip()
    
    # 使用預定義的映射進行轉換
    return epa_level_mapping.get(value, None)

# epa_level_mapping 字典保持不變
epa_level_mapping = {
    # 整合重複的尺規格式
    '不允許學員觀察': 1,
    '學員在旁觀察': 1.5,
    '允許學員在旁觀察': 1.5,
    '教師在旁逐步共同操作': 2,
    '教師在旁必要時協助': 2.5,
    '教師可立即到場協助，事後逐項確認': 3,
    '教師可立即到場協助，事後重點確認': 3.3,
    '教師可稍後到場協助，必要時事後確認': 3.6,
    '教師on call提供監督': 4,
    '教師不需on call，事後提供回饋及監督': 4.5,
    '學員可對其他資淺的學員進行監督與教學': 5,
    
    # 整合重複的 Level 格式
    'Level I': 1, ' Level I': 1, 'Level1': 1, 'Level 1': 1,
    'Level 1&2': 1.5, 'Level1&2': 1.5, 'LevelI&2': 1.5, 'Level&2': 1.5,
    'Level II': 2, ' Level II': 2, 'Level2': 2, 'Level 2': 2,
    'Level2&3': 2.5, 'Level 2&3': 2.5, 'Leve 2&3': 2.5,
    'Level 2a': 2, 'Level2a': 2, 'Level 2b': 2.5, 'Level2b': 2.5,
    'Level III': 3, ' Level III': 3, 'Level3': 3, 'Level 3': 3,
    'Level 3a': 3, 'Level3a': 3, 'Level 3b': 3.3, 'Level3b': 3.3,
    'Level3c': 3.6, 'Level 3c': 3.6,
    'Level 3&4': 3.5, 'Level3&4': 3.5, 'Leve 3&4': 3.5, 'Lvel 3&4': 3.5,
    'Level IV': 4, ' Level IV': 4, 'Level4': 4, 'Level 4': 4,
    'Level4&5': 4.5, 'Level 4&5': 4.5,
    'Level 5': 5, 'Level V': 5, ' Level V': 5, 'Level5': 5
}

def convert_date_to_batch(date_str):
    """將日期字串轉換為梯次編號（以兩週為一梯）
    
    Args:
        date_str (str): 日期字串，格式為 'YYYY/MM/DD' 或 'YYYY-MM-DD'
        
    Returns:
        str: 梯次名稱，使用該梯第一個星期一的日期
    """
    try:
        # 處理可能的日期格式
        if isinstance(date_str, str):
            date_str = date_str.replace('/', '-')
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        elif isinstance(date_str, datetime):
            date_obj = date_str
        else:
            return '未知梯次'

        # 計算與基準日期（2020-07-01）的天數差
        base_date = datetime(2020, 7, 1)
        days_diff = (date_obj - base_date).days
        
        # 計算屬於第幾個兩週期（每14天一個週期）
        two_week_period = days_diff // 14
        
        # 計算該梯次的起始日期
        period_start = base_date + pd.Timedelta(days=two_week_period * 14)
        
        # 找出該梯次的第一個星期一
        days_until_monday = (7 - period_start.weekday()) % 7
        if days_until_monday == 0:  # 如果已經是星期一
            first_monday = period_start
        else:
            first_monday = period_start + pd.Timedelta(days=days_until_monday)
            
        # 檢查日期是否落在下一個星期一之前
        next_period_monday = first_monday + pd.Timedelta(days=14)
        
        # 如果日期超過了這一梯的第一個星期一，但還沒到下一梯的第一個星期一
        # 就算在這一梯
        if date_obj >= first_monday and date_obj < next_period_monday:
            return first_monday.strftime('%Y/%m/%d')
        
        # 如果日期在這一梯的第一個星期一之前，要算入前一梯
        if date_obj < first_monday:
            prev_monday = first_monday - pd.Timedelta(days=14)
            return prev_monday.strftime('%Y/%m/%d')
            
        # 返回格式化的日期字串
        return first_monday.strftime('%Y/%m/%d')
        
    except Exception as e:
        print(f"日期轉換錯誤: {e}")
        return '未知梯次'

def convert_tw_time(time_str):
    """將中文時間格式轉換為標準日期時間格式
    
    Args:
        time_str (str): 包含中文上午/下午的時間字串，例如 "2025/3/11 上午 8:15:25"
        
    Returns:
        datetime: 轉換後的日期時間物件
    """
    # 移除所有空格
    time_str = time_str.strip()
    # 轉換上午/下午時間
    if '上午' in time_str:
        time_str = time_str.replace('上午', 'AM')
    elif '下午' in time_str:
        time_str = time_str.replace('下午', 'PM')
    return pd.to_datetime(time_str, format='%Y/%m/%d %p %I:%M:%S')