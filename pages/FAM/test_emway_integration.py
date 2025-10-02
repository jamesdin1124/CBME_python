#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMYWAY資料整合測試腳本
測試整合後的資料載入和顯示功能
"""

import pandas as pd
import os
from fam_data_processor import FAMDataProcessor
from fam_visualization import FAMVisualization

def test_integrated_data():
    """測試整合後的資料"""
    print("🧪 開始測試EMYWAY資料整合...")
    
    # 檢查整合資料檔案
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    if not os.path.exists(integrated_file):
        print("❌ 整合資料檔案不存在")
        return False
    
    try:
        # 載入整合資料
        df = pd.read_csv(integrated_file, encoding='utf-8')
        print(f"✅ 成功載入整合資料: {len(df)} 筆記錄")
        
        # 檢查必要欄位
        required_columns = ['學員', 'EPA項目', '信賴程度(教師評量)', '資料來源']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ 缺少必要欄位: {missing_columns}")
            return False
        
        print("✅ 所有必要欄位都存在")
        
        # 測試資料處理器
        processor = FAMDataProcessor()
        cleaned_df = processor.clean_data(df, debug=True)
        
        print(f"✅ 資料清理完成: {len(cleaned_df)} 筆記錄")
        
        # 測試資料來源分布
        if '資料來源' in cleaned_df.columns:
            source_counts = cleaned_df['資料來源'].value_counts()
            print(f"✅ 資料來源分布: {source_counts.to_dict()}")
        
        # 測試學員清單
        students = processor.get_student_list(cleaned_df)
        print(f"✅ 學員清單: {len(students)} 名學員")
        print(f"   前5名學員: {students[:5]}")
        
        # 測試EPA項目
        epa_items = cleaned_df['EPA項目'].unique()
        print(f"✅ EPA項目: {len(epa_items)} 種")
        print(f"   EPA項目: {list(epa_items)[:5]}")
        
        # 測試個別學員資料
        if students:
            test_student = students[0]
            student_data = processor.get_student_data(cleaned_df, test_student)
            print(f"✅ 測試學員 '{test_student}' 資料: {len(student_data)} 筆記錄")
            
            if '資料來源' in student_data.columns:
                student_sources = student_data['資料來源'].value_counts()
                print(f"   該學員資料來源: {student_sources.to_dict()}")
        
        # 測試統計資料
        stats = processor.get_overall_statistics(cleaned_df)
        print(f"✅ 整體統計:")
        print(f"   總記錄數: {stats['total_records']}")
        print(f"   學員數: {stats['unique_students']}")
        print(f"   EPA項目數: {stats['unique_epa_items']}")
        print(f"   教師數: {stats['unique_teachers']}")
        
        print("\n🎉 所有測試通過！EMYWAY資料整合成功！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return False

def test_data_source_filtering():
    """測試資料來源過濾功能"""
    print("\n🧪 測試資料來源過濾功能...")
    
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    try:
        df = pd.read_csv(integrated_file, encoding='utf-8')
        processor = FAMDataProcessor()
        cleaned_df = processor.clean_data(df)
        
        # 測試不同資料來源的過濾
        if '資料來源' in cleaned_df.columns:
            sources = cleaned_df['資料來源'].unique()
            print(f"✅ 可用資料來源: {list(sources)}")
            
            for source in sources:
                filtered_df = cleaned_df[cleaned_df['資料來源'] == source]
                print(f"   {source}: {len(filtered_df)} 筆記錄")
                
                # 測試每個來源的學員數
                students_in_source = filtered_df['學員'].nunique()
                print(f"    學員數: {students_in_source}")
        
        print("✅ 資料來源過濾測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 資料來源過濾測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 EMYWAY資料整合測試")
    print("=" * 60)
    
    # 測試整合資料
    test1_result = test_integrated_data()
    
    # 測試資料來源過濾
    test2_result = test_data_source_filtering()
    
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！系統已準備就緒！")
        print("\n✅ 整合功能包括:")
        print("   • EMYWAY歷史資料轉換")
        print("   • 與現有系統資料合併")
        print("   • 資料來源標記和過濾")
        print("   • 完整的資料清理和處理")
        print("   • 統計分析和視覺化支援")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
