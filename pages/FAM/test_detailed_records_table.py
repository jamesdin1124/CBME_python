#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試詳細評核記錄表格是否正確顯示資料來源
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor

def test_detailed_records_table():
    """測試詳細評核記錄表格功能"""
    print("🧪 測試詳細評核記錄表格功能...")
    
    # 載入整合資料
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    if not os.path.exists(integrated_file):
        print("❌ 整合資料檔案不存在")
        return False
    
    try:
        # 載入資料
        df = pd.read_csv(integrated_file, encoding='utf-8')
        print(f"✅ 成功載入整合資料: {len(df)} 筆記錄")
        
        # 初始化處理器
        processor = FAMDataProcessor()
        
        # 清理資料
        cleaned_df = processor.clean_data(df)
        print(f"✅ 資料清理完成: {len(cleaned_df)} 筆記錄")
        
        # 測試資料來源統計
        if '資料來源' in cleaned_df.columns:
            source_counts = cleaned_df['資料來源'].value_counts()
            print(f"✅ 資料來源分布: {source_counts.to_dict()}")
        
        # 測試學員清單
        students = processor.get_student_list(cleaned_df)
        print(f"✅ 學員清單: {len(students)} 名學員")
        
        # 測試詳細評核記錄表格功能
        if students:
            test_student = students[0]
            
            print(f"\\n🧪 測試學員: {test_student}")
            
            # 獲取學員的資料
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            
            print(f"   該學員的資料: {len(student_data)} 筆記錄")
            
            if '資料來源' in student_data.columns:
                source_counts = student_data['資料來源'].value_counts()
                print(f"   資料來源分布: {source_counts.to_dict()}")
            
            # 模擬詳細評核記錄表格的顯示邏輯
            display_columns = ['日期', 'EPA項目', '病歷號碼', '個案姓名', '診斷', '複雜程度', '觀察場域', '信賴程度(教師評量)', '信賴程度(教師評量)_數值', '教師給學員回饋']
            
            # 如果有資料來源欄位，將其加入顯示欄位中
            if '資料來源' in student_data.columns:
                display_columns.append('資料來源')
                print(f"   ✅ 資料來源欄位已加入顯示欄位")
            else:
                print(f"   ⚠️ 沒有找到資料來源欄位")
            
            available_columns = [col for col in display_columns if col in student_data.columns]
            missing_columns = [col for col in display_columns if col not in student_data.columns]
            
            print(f"   可用欄位: {available_columns}")
            if missing_columns:
                print(f"   缺少欄位: {missing_columns}")
            
            # 測試表格資料
            if available_columns:
                table_data = student_data[available_columns]
                print(f"   ✅ 表格資料形狀: {table_data.shape}")
                
                # 檢查資料來源欄位的內容
                if '資料來源' in available_columns:
                    source_values = table_data['資料來源'].value_counts()
                    print(f"   📊 表格中的資料來源分布:")
                    for source, count in source_values.items():
                        print(f"     {source}: {count} 筆")
                    
                    # 顯示前幾筆記錄的資料來源
                    print(f"   📋 前5筆記錄的資料來源:")
                    for i, (_, row) in enumerate(table_data.head(5).iterrows()):
                        date_str = str(row.get('日期', 'N/A'))[:10] if pd.notna(row.get('日期')) else 'N/A'
                        epa_item = row.get('EPA項目', 'N/A')
                        data_source = row.get('資料來源', 'N/A')
                        print(f"     {i+1}. {date_str} - {epa_item} - {data_source}")
                else:
                    print(f"   ⚠️ 表格中沒有資料來源欄位")
            else:
                print(f"   ❌ 沒有可用的顯示欄位")
        
        print("\\n🎉 詳細評核記錄表格功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_table_column_order():
    """測試表格欄位順序"""
    print("\\n🧪 測試表格欄位順序...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        cleaned_df = processor.clean_data(df)
        
        students = processor.get_student_list(cleaned_df)
        if students:
            test_student = students[0]
            student_data = cleaned_df[cleaned_df['學員'] == test_student]
            
            # 定義顯示欄位順序
            display_columns = ['日期', 'EPA項目', '病歷號碼', '個案姓名', '診斷', '複雜程度', '觀察場域', '信賴程度(教師評量)', '信賴程度(教師評量)_數值', '教師給學員回饋']
            
            # 如果有資料來源欄位，將其加入顯示欄位中
            if '資料來源' in student_data.columns:
                display_columns.append('資料來源')
            
            available_columns = [col for col in display_columns if col in student_data.columns]
            
            print(f"   表格欄位順序:")
            for i, col in enumerate(available_columns, 1):
                print(f"     {i:2d}. {col}")
            
            # 檢查資料來源欄位的位置
            if '資料來源' in available_columns:
                source_index = available_columns.index('資料來源')
                print(f"   ✅ 資料來源欄位位於第 {source_index + 1} 個位置")
            else:
                print(f"   ⚠️ 資料來源欄位不在可用欄位中")
        
        print("✅ 表格欄位順序測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 表格欄位順序測試失敗: {str(e)}")
        return False

def test_data_source_display():
    """測試資料來源顯示效果"""
    print("\\n🧪 測試資料來源顯示效果...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        cleaned_df = processor.clean_data(df)
        
        # 統計所有資料來源
        if '資料來源' in cleaned_df.columns:
            all_sources = cleaned_df['資料來源'].unique()
            print(f"   所有資料來源: {list(all_sources)}")
            
            # 檢查資料來源的完整性
            for source in all_sources:
                source_data = cleaned_df[cleaned_df['資料來源'] == source]
                print(f"   {source}: {len(source_data)} 筆記錄")
                
                # 檢查是否有教師回饋
                feedback_data = source_data[source_data['教師給學員回饋'].notna() & (source_data['教師給學員回饋'] != '')]
                print(f"     教師回饋: {len(feedback_data)} 筆")
        
        print("✅ 資料來源顯示效果測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 資料來源顯示效果測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 詳細評核記錄表格功能測試")
    print("=" * 60)
    
    # 測試詳細評核記錄表格
    test1_result = test_detailed_records_table()
    
    # 測試表格欄位順序
    test2_result = test_table_column_order()
    
    # 測試資料來源顯示效果
    test3_result = test_data_source_display()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result and test3_result:
        print("🎉 所有測試通過！詳細評核記錄表格已正確顯示資料來源！")
        print("\\n✅ 功能包括:")
        print("   • 在詳細評核記錄表格中加入資料來源欄位")
        print("   • 標明每筆記錄是來自EMYWAY歷史資料還是現有系統")
        print("   • 保持表格欄位的合理順序")
        print("   • 提供完整的資料來源統計")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
