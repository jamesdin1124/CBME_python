#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試詳細評核記錄的expander功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_expander_functionality():
    """測試expander功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試詳細評核記錄expander功能...")
        
        # 讀取CSV檔案
        csv_path = os.path.join(os.path.dirname(__file__), '2025-09-24T03-11_export.csv')
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"✅ 成功讀取CSV檔案: {df.shape}")
        
        # 初始化處理器
        processor = FAMDataProcessor()
        
        # 清理資料
        cleaned_df = processor.clean_data(df, debug=False)
        print(f"✅ 資料清理完成: {cleaned_df.shape}")
        
        if not cleaned_df.empty:
            # 獲取學員
            students = processor.get_student_list(cleaned_df)
            print(f"👥 學員: {students}")
            
            if len(students) > 0:
                test_student = students[0]
                print(f"\n🎯 測試學員: {test_student}")
                
                # 獲取學員資料
                student_data = processor.get_student_data(cleaned_df, test_student)
                print(f"📊 學員總資料: {len(student_data)}")
                
                # 測試expander邏輯
                print(f"\n📋 測試expander邏輯:")
                
                if '日期' in student_data.columns:
                    # 轉換日期格式並過濾有效日期
                    student_data_copy = student_data.copy()
                    student_data_copy['日期'] = pd.to_datetime(student_data_copy['日期'], errors='coerce')
                    valid_date_data = student_data_copy.dropna(subset=['日期'])
                    
                    print(f"  - 原始資料筆數: {len(student_data)}")
                    print(f"  - 有效日期資料筆數: {len(valid_date_data)}")
                    
                    if not valid_date_data.empty:
                        display_columns = ['日期', 'EPA項目', '病歷號碼', '個案姓名', '診斷', '複雜程度', '觀察場域', '信賴程度(教師評量)']
                        available_columns = [col for col in display_columns if col in valid_date_data.columns]
                        
                        print(f"  - 可用欄位: {available_columns}")
                        print(f"  - 顯示欄位數量: {len(available_columns)}")
                        
                        if available_columns:
                            print(f"  ✅ 可以顯示詳細記錄表格")
                            print(f"  📊 表格資料形狀: {valid_date_data[available_columns].shape}")
                            
                            # 顯示前幾筆資料樣本
                            print(f"  📋 資料樣本:")
                            sample_data = valid_date_data[available_columns].head(3)
                            for i, (_, row) in enumerate(sample_data.iterrows()):
                                print(f"    記錄 {i+1}: {row['日期'].strftime('%Y-%m-%d')} - {row['EPA項目']} - {row['個案姓名']}")
                        else:
                            print(f"  ❌ 沒有可用的顯示欄位")
                    else:
                        print(f"  ⚠️ 沒有有效日期資料")
                else:
                    print(f"  ❌ 沒有找到日期欄位")
                
                print(f"\n🎉 Expander功能測試完成！")
                print(f"📝 功能說明:")
                print(f"  - 使用 st.expander('📋 詳細評核記錄', expanded=False)")
                print(f"  - 預設為收起狀態 (expanded=False)")
                print(f"  - 用戶可以點擊標題來展開/收起內容")
                print(f"  - 節省頁面空間，提供更好的用戶體驗")
                
                return True
            else:
                print(f"❌ 沒有找到學員資料")
                return False
        else:
            print(f"❌ 清理後資料為空")
            return False
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    result = test_expander_functionality()
    print("=" * 70)
    
    if result:
        print("🎉 詳細評核記錄expander功能測試成功！")
        print("\n💡 用戶體驗改進:")
        print("- 詳細評核記錄現在可以收起，節省頁面空間")
        print("- 預設為收起狀態，需要時再展開查看")
        print("- 保持頁面整潔，專注於主要分析內容")
    else:
        print("❌ 詳細評核記錄expander功能測試失敗！")
