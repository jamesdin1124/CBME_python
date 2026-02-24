#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試家醫部資料載入功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_csv_data_loading():
    """測試CSV資料載入"""
    try:
        # 讀取CSV檔案
        csv_path = os.path.join(os.path.dirname(__file__), 'EPA匯出原始檔_1140923.csv')
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"✅ 成功讀取CSV檔案")
        print(f"📊 原始資料形狀: {df.shape}")
        print(f"📋 欄位列表: {list(df.columns)}")
        
        # 檢查關鍵欄位
        key_columns = ['學員', 'EPA項目', '日期', '信賴程度(教師評量)']
        for col in key_columns:
            if col in df.columns:
                non_null_count = df[col].notna().sum()
                print(f"✅ {col}: {non_null_count} 筆有效資料")
            else:
                print(f"❌ 缺少欄位: {col}")
        
        # 檢查EPA項目
        if 'EPA項目' in df.columns:
            epa_items = df['EPA項目'].dropna().unique()
            print(f"🎯 EPA項目種類: {len(epa_items)} 種")
            print(f"📝 EPA項目清單: {list(epa_items)}")
        
        # 檢查學員
        if '學員' in df.columns:
            students = df['學員'].dropna().unique()
            print(f"👥 學員人數: {len(students)} 人")
            print(f"📝 學員清單: {list(students)}")
        
        return df
        
    except Exception as e:
        print(f"❌ 讀取CSV檔案失敗: {e}")
        return None

def test_data_processor():
    """測試資料處理器"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        # 讀取資料
        df = test_csv_data_loading()
        if df is None:
            return False
        
        # 初始化處理器
        processor = FAMDataProcessor()
        print("\n🧹 開始資料清理...")
        
        # 清理資料
        cleaned_df = processor.clean_data(df)
        
        print(f"✅ 資料清理完成")
        print(f"📊 清理後資料形狀: {cleaned_df.shape}")
        
        if not cleaned_df.empty:
            # 測試各種功能
            students = processor.get_student_list(cleaned_df)
            print(f"👥 學員清單: {students}")
            
            epa_items = processor.get_epa_items(cleaned_df)
            print(f"🎯 EPA項目清單: {epa_items}")
            
            if students:
                # 測試個別學員資料
                student_data = processor.get_student_data(cleaned_df, students[0])
                print(f"📋 {students[0]} 的資料筆數: {len(student_data)}")
                
                # 測試EPA進度計算
                progress_df = processor.calculate_epa_progress(student_data)
                print(f"📈 EPA進度計算完成，共 {len(progress_df)} 個項目")
        
        return True
        
    except Exception as e:
        print(f"❌ 資料處理器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始家醫部資料載入測試...")
    print("=" * 50)
    
    # 測試CSV資料載入
    print("\n📋 測試CSV資料載入...")
    csv_result = test_csv_data_loading() is not None
    
    # 測試資料處理器
    print("\n📋 測試資料處理器...")
    processor_result = test_data_processor()
    
    # 總結
    print("\n" + "=" * 50)
    if csv_result and processor_result:
        print("🎉 所有測試通過！資料載入和處理功能正常。")
        print("\n💡 如果系統仍顯示「沒有可用的資料」，可能是session state資料傳遞的問題。")
        print("   請在系統中開啟調試模式查看詳細資訊。")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息。")
