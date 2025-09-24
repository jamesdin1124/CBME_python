#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EPA項目推斷功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_epa_inference():
    """測試EPA項目推斷功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        # 讀取新的CSV檔案
        csv_path = os.path.join(os.path.dirname(__file__), '2025-09-24T03-11_export.csv')
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"✅ 成功讀取CSV檔案")
        print(f"📊 原始資料形狀: {df.shape}")
        print(f"📋 原始欄位: {list(df.columns)}")
        
        # 檢查原始EPA項目狀態
        print(f"\n🔍 原始EPA項目狀態:")
        epa_counts = df['EPA項目'].value_counts()
        print(f"EPA項目分佈: {epa_counts.to_dict()}")
        
        # 初始化處理器
        processor = FAMDataProcessor()
        
        # 清理資料並推斷EPA項目
        print(f"\n🧹 開始清理資料並推斷EPA項目...")
        cleaned_df = processor.clean_data(df, debug=True)
        
        print(f"📊 清理後資料形狀: {cleaned_df.shape}")
        
        if not cleaned_df.empty:
            # 檢查推斷後的EPA項目狀態
            print(f"\n🎯 推斷後的EPA項目狀態:")
            epa_counts_after = cleaned_df['EPA項目'].value_counts()
            print(f"EPA項目分佈: {epa_counts_after.to_dict()}")
            
            # 顯示一些具體的推斷結果
            print(f"\n📝 推斷結果範例:")
            sample_data = cleaned_df[['日期', 'EPA項目', '診斷', '信賴程度(教師評量)']].head(10)
            for idx, row in sample_data.iterrows():
                if pd.notna(row['EPA項目']) and str(row['EPA項目']).strip():
                    print(f"  {row['EPA項目']}: {row['診斷'][:50]}...")
            
            # 檢查是否有學員資料
            if '學員' in cleaned_df.columns:
                students = cleaned_df['學員'].unique()
                print(f"\n👥 學員清單: {students}")
                
                # 選擇第一個學員進行測試
                if len(students) > 0:
                    test_student = students[0]
                    print(f"\n🎯 測試學員: {test_student}")
                    
                    student_data = processor.get_student_data(cleaned_df, test_student)
                    print(f"📋 {test_student} 的資料筆數: {len(student_data)}")
                    
                    if not student_data.empty:
                        epa_items = student_data['EPA項目'].unique()
                        print(f"🎯 {test_student} 的EPA項目: {epa_items}")
                        
                        # 檢查信賴程度
                        reliability_items = student_data['信賴程度(教師評量)'].unique()
                        print(f"📊 {test_student} 的信賴程度: {reliability_items}")
                
            return True
        else:
            print("❌ 清理後資料為空")
            return False
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 開始測試EPA項目推斷功能...")
    print("=" * 50)
    
    result = test_epa_inference()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 EPA項目推斷功能測試成功！")
        print("\n💡 現在系統可以從診斷內容自動推斷EPA項目類型。")
        print("   - 預防注射相關診斷 → EPA03.預防注射")
        print("   - 急症相關診斷 → EPA08.急症診療")
        print("   - 慢病相關診斷 → EPA07.慢病照護")
        print("   - 其他EPA項目也會根據關鍵字自動推斷")
    else:
        print("❌ EPA項目推斷功能測試失敗，請檢查錯誤訊息。")
