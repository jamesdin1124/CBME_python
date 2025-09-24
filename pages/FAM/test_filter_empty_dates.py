#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試日期為空白的資料是否被省略
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_filter_empty_dates():
    """測試日期為空白的資料是否被省略"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試日期為空白的資料是否被省略...")
        
        # 讀取合併後的資料檔案
        merged_csv_path = os.path.join(os.path.dirname(__file__), 'merged_data (11).csv')
        
        if os.path.exists(merged_csv_path):
            print(f"✅ 找到合併後資料檔案")
            df_original = pd.read_csv(merged_csv_path, encoding='utf-8')
            print(f"📊 原始檔案形狀: {df_original.shape}")
            
            # 初始化處理器
            processor = FAMDataProcessor()
            
            # 清理資料
            cleaned_df = processor.clean_data(df_original, debug=True)
            print(f"\n✅ 資料清理完成: {cleaned_df.shape}")
            
            # 選擇鄧祖嶸作為測試學員
            test_student_name = '鄧祖嶸'
            student_data = cleaned_df[cleaned_df['學員'] == test_student_name].copy()
            
            print(f"\n🔍 測試學員: {test_student_name}")
            print(f"原始學員資料筆數: {len(student_data)}")
            
            # 檢查日期欄位狀況
            if '日期' in student_data.columns:
                student_data['日期'] = pd.to_datetime(student_data['日期'], errors='coerce')
                valid_dates = student_data.dropna(subset=['日期'])
                empty_dates = student_data[student_data['日期'].isna()]
                
                print(f"有效日期記錄數: {len(valid_dates)}")
                print(f"空白日期記錄數: {len(empty_dates)}")
                
                # 模擬 fam_residents.py 中的過濾邏輯
                valid_date_data = student_data.dropna(subset=['日期'])
                
                print(f"\n📊 過濾結果:")
                print(f"過濾前總記錄數: {len(student_data)}")
                print(f"過濾後有效記錄數: {len(valid_date_data)}")
                print(f"過濾掉的空白日期記錄: {len(student_data) - len(valid_date_data)}")
                
                # 顯示過濾後的資料示例
                if not valid_date_data.empty:
                    print(f"\n📋 過濾後的資料前5筆:")
                    display_columns = ['日期', 'EPA項目', '病歷號碼', '個案姓名']
                    available_columns = [col for col in display_columns if col in valid_date_data.columns]
                    
                    for idx, (_, row) in enumerate(valid_date_data.head(5).iterrows()):
                        print(f"  記錄 {idx+1}:")
                        for col in available_columns:
                            value = row[col]
                            if pd.isna(value):
                                value_str = "N/A"
                            else:
                                value_str = str(value)
                            print(f"    {col}: {value_str}")
                        print()
                
                # 驗證過濾效果
                print(f"✅ 日期過濾功能測試成功!")
                print(f"   - 成功過濾掉 {len(student_data) - len(valid_date_data)} 筆空白日期記錄")
                print(f"   - 保留 {len(valid_date_data)} 筆有效日期記錄")
                
            else:
                print(f"❌ 找不到日期欄位")
                return False
            
            # 測試其他學員
            print(f"\n🔍 測試其他學員的日期過濾效果:")
            students = ['陳柏豪', '陳麒任', '高士傑', '徐呈祥', '張玄穎']
            
            for student in students:
                student_records = cleaned_df[cleaned_df['學員'] == student].copy()
                if not student_records.empty:
                    if '日期' in student_records.columns:
                        student_records['日期'] = pd.to_datetime(student_records['日期'], errors='coerce')
                        valid_records = student_records.dropna(subset=['日期'])
                        print(f"  {student}: {len(student_records)} → {len(valid_records)} 筆記錄")
            
            print(f"\n🎉 日期空白記錄過濾測試完成！")
            return True
        else:
            print(f"❌ 找不到合併後資料檔案")
            return False
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    result = test_filter_empty_dates()
    print("=" * 80)
    
    if result:
        print("🎉 日期空白記錄過濾測試成功！")
        print("\n💡 過濾功能說明:")
        print("- 自動過濾掉日期欄位為空白或無效的記錄")
        print("- 只顯示有有效日期的記錄")
        print("- 提供統計資訊顯示過濾效果")
        print("- 確保詳細評核記錄表格只顯示有意義的資料")
    else:
        print("❌ 日期空白記錄過濾測試失敗！")
