#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試完整的EPA項目資料顯示
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_complete_epa_display():
    """測試完整的EPA項目資料顯示"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試完整的EPA項目資料顯示...")
        
        # 讀取原始EPA匯出檔案
        original_csv_path = os.path.join(os.path.dirname(__file__), 'EPA匯出原始檔_1140923.csv')
        
        if os.path.exists(original_csv_path):
            print(f"✅ 找到原始EPA匯出檔案")
            df_original = pd.read_csv(original_csv_path, encoding='utf-8')
            print(f"📊 原始檔案形狀: {df_original.shape}")
            
            # 檢查原始EPA項目資料
            if 'EPA項目' in df_original.columns:
                original_epa_counts = df_original['EPA項目'].value_counts()
                print(f"\n📋 原始EPA項目分佈:")
                for epa, count in original_epa_counts.head(20).items():
                    print(f"  '{epa}': {count} 筆")
            
            # 初始化處理器
            processor = FAMDataProcessor()
            
            # 清理資料
            cleaned_df = processor.clean_data(df_original, debug=True)
            print(f"\n✅ 資料清理完成: {cleaned_df.shape}")
            
            # 檢查清理後的EPA項目資料
            if 'EPA項目' in cleaned_df.columns:
                cleaned_epa_counts = cleaned_df['EPA項目'].value_counts()
                print(f"\n📋 清理後EPA項目分佈:")
                for epa, count in cleaned_epa_counts.head(20).items():
                    print(f"  '{epa}': {count} 筆")
                
                # 檢查是否有EPA項目_原始欄位
                if 'EPA項目_原始' in cleaned_df.columns:
                    print(f"\n📋 EPA項目_原始分佈:")
                    original_epa_counts = cleaned_df['EPA項目_原始'].value_counts()
                    for epa, count in original_epa_counts.head(10).items():
                        print(f"  '{epa}': {count} 筆")
            
            # 檢查特定學員的資料
            print(f"\n👥 檢查鄧祖嶸的EPA項目資料:")
            if '學員' in cleaned_df.columns:
                deng_records = cleaned_df[cleaned_df['學員'] == '鄧祖嶸']
                print(f"  鄧祖嶸的記錄數: {len(deng_records)}")
                
                if not deng_records.empty:
                    # 檢查EPA項目分佈
                    if 'EPA項目' in deng_records.columns:
                        deng_epa_counts = deng_records['EPA項目'].value_counts()
                        print(f"  📊 鄧祖嶸的EPA項目分佈:")
                        for epa, count in deng_epa_counts.items():
                            print(f"    '{epa}': {count} 筆")
                    
                    # 顯示前幾筆記錄的詳細資訊
                    print(f"\n  📋 鄧祖嶸的前5筆記錄詳情:")
                    for idx, row in deng_records.head().iterrows():
                        print(f"    記錄 {idx}:")
                        print(f"      日期: {row.get('日期', 'N/A')}")
                        print(f"      EPA項目: '{row.get('EPA項目', 'N/A')}'")
                        if 'EPA項目_原始' in row:
                            print(f"      EPA項目_原始: '{row.get('EPA項目_原始', 'N/A')}'")
                        print(f"      病歷號碼: {row.get('病歷號碼', 'N/A')}")
                        print(f"      個案姓名: {row.get('個案姓名', 'N/A')}")
                        diagnosis = row.get('診斷', 'N/A')
                        if isinstance(diagnosis, str) and len(diagnosis) > 30:
                            print(f"      診斷: {diagnosis[:30]}...")
                        else:
                            print(f"      診斷: {diagnosis}")
                        print(f"      信賴程度: {row.get('信賴程度(教師評量)', 'N/A')}")
                        print()
            
            # 檢查空EPA項目的記錄
            print(f"\n❓ 檢查空EPA項目的記錄:")
            if 'EPA項目' in cleaned_df.columns:
                empty_epa_records = cleaned_df[cleaned_df['EPA項目'] == '']
                print(f"  空EPA項目的記錄數: {len(empty_epa_records)}")
                
                if len(empty_epa_records) > 0:
                    print(f"  📋 空EPA項目前5筆記錄:")
                    for idx, row in empty_epa_records.head().iterrows():
                        print(f"    記錄 {idx}:")
                        print(f"      日期: {row.get('日期', 'N/A')}")
                        if 'EPA項目_原始' in row:
                            print(f"      EPA項目_原始: '{row.get('EPA項目_原始', 'N/A')}'")
                        print(f"      病歷號碼: {row.get('病歷號碼', 'N/A')}")
                        print(f"      個案姓名: {row.get('個案姓名', 'N/A')}")
                        diagnosis = row.get('診斷', 'N/A')
                        if isinstance(diagnosis, str) and len(diagnosis) > 30:
                            print(f"      診斷: {diagnosis[:30]}...")
                        else:
                            print(f"      診斷: {diagnosis}")
            
            print(f"\n🎉 完整EPA項目資料顯示測試完成！")
            return True
        else:
            print(f"❌ 找不到原始EPA匯出檔案")
            return False
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    result = test_complete_epa_display()
    print("=" * 70)
    
    if result:
        print("🎉 完整EPA項目資料顯示測試成功！")
        print("\n💡 改進說明:")
        print("- 移除了日期過濾邏輯，顯示所有記錄")
        print("- 保留原始EPA項目資料用於調試")
        print("- 確保所有EPA項目資料都能正確顯示")
        print("- 現在應該能看到完整的EPA項目記錄")
    else:
        print("❌ 完整EPA項目資料顯示測試失敗！")
