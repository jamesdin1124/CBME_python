#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試資料清理修復
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_data_cleaning_fix():
    """測試資料清理修復"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        # 讀取CSV檔案
        csv_path = os.path.join(os.path.dirname(__file__), 'EPA匯出原始檔_1140923.csv')
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"✅ 成功讀取CSV檔案")
        print(f"📊 原始資料形狀: {df.shape}")
        
        # 初始化處理器
        processor = FAMDataProcessor()
        
        # 測試資料清理（開啟調試模式）
        print("\n🧹 開始資料清理（調試模式）...")
        cleaned_df = processor.clean_data(df, debug=True)
        
        print(f"\n✅ 資料清理完成")
        print(f"📊 清理後資料形狀: {cleaned_df.shape}")
        
        if not cleaned_df.empty:
            # 檢查關鍵欄位
            if '學員' in cleaned_df.columns:
                students = cleaned_df['學員'].unique()
                print(f"👥 學員清單: {list(students)}")
            
            if 'EPA項目' in cleaned_df.columns:
                epa_items = cleaned_df['EPA項目'].unique()
                non_empty_epa = [item for item in epa_items if item and item.strip()]
                print(f"🎯 非空EPA項目: {len(non_empty_epa)} 種")
                print(f"📝 EPA項目清單: {non_empty_epa[:10]}")  # 只顯示前10個
            
            # 測試基本功能
            student_list = processor.get_student_list(cleaned_df)
            print(f"👥 處理器獲得的學員清單: {student_list}")
            
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
    print("🚀 開始測試資料清理修復...")
    print("=" * 50)
    
    result = test_data_cleaning_fix()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 資料清理修復成功！現在應該可以正常顯示資料了。")
        print("\n💡 請重新整理家醫部系統頁面查看結果。")
    else:
        print("❌ 資料清理修復失敗，請檢查錯誤訊息。")
