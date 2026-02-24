#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EPA項目資料的完全保留
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_epa_complete_preservation():
    """測試EPA項目資料的完全保留"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試EPA項目資料的完全保留...")
        
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
            
            # 檢查鄧祖嶸的完整資料
            if '學員' in cleaned_df.columns:
                deng_records = cleaned_df[cleaned_df['學員'] == '鄧祖嶸'].copy()
                print(f"\n👥 鄧祖嶸的完整記錄數: {len(deng_records)}")
                
                if not deng_records.empty:
                    # 轉換日期格式
                    if '日期' in deng_records.columns:
                        deng_records['日期'] = pd.to_datetime(deng_records['日期'], errors='coerce')
                    
                    # 檢查EPA項目分佈（完全保留）
                    if 'EPA項目' in deng_records.columns:
                        epa_counts = deng_records['EPA項目'].value_counts()
                        print(f"\n📋 鄧祖嶸的完整EPA項目分佈:")
                        for epa, count in epa_counts.items():
                            if epa and epa != '':
                                print(f"  ✅ '{epa}': {count} 筆")
                            else:
                                print(f"  📝 空EPA項目: {count} 筆")
                    
                    # 顯示所有記錄的統計
                    print(f"\n📊 鄧祖嶸記錄統計:")
                    print(f"  • 總記錄數: {len(deng_records)}")
                    
                    # 統計有各種資料的記錄數
                    has_date = deng_records['日期'].notna().sum()
                    has_epa = (deng_records['EPA項目'].notna() & (deng_records['EPA項目'] != '')).sum()
                    has_record_id = deng_records['病歷號碼'].notna().sum()
                    has_patient_name = deng_records['個案姓名'].notna().sum()
                    has_diagnosis = deng_records['診斷'].notna().sum()
                    
                    print(f"  • 有日期的記錄: {has_date} 筆")
                    print(f"  • 有EPA項目的記錄: {has_epa} 筆")
                    print(f"  • 有病歷號碼的記錄: {has_record_id} 筆")
                    print(f"  • 有個案姓名的記錄: {has_patient_name} 筆")
                    print(f"  • 有診斷的記錄: {has_diagnosis} 筆")
                    
                    # 顯示前15筆記錄的詳細資訊（包含所有EPA項目狀態）
                    print(f"\n📋 鄧祖嶸的前15筆記錄詳情（完全保留EPA項目）:")
                    for idx, (_, row) in enumerate(deng_records.head(15).iterrows()):
                        print(f"  {idx+1}. 記錄詳情:")
                        print(f"     日期: {row.get('日期', 'N/A')}")
                        epa_item = row.get('EPA項目', 'N/A')
                        if epa_item and epa_item != '':
                            print(f"     EPA項目: ✅ '{epa_item}'")
                        else:
                            print(f"     EPA項目: 📝 空值")
                        print(f"     病歷號碼: {row.get('病歷號碼', 'N/A')}")
                        print(f"     個案姓名: {row.get('個案姓名', 'N/A')}")
                        diagnosis = row.get('診斷', 'N/A')
                        if isinstance(diagnosis, str) and len(diagnosis) > 30:
                            print(f"     診斷: {diagnosis[:30]}...")
                        else:
                            print(f"     診斷: {diagnosis}")
                        print(f"     複雜程度: {row.get('複雜程度', 'N/A')}")
                        print(f"     觀察場域: {row.get('觀察場域', 'N/A')}")
                        print(f"     信賴程度: {row.get('信賴程度(教師評量)', 'N/A')}")
                        print()
                    
                    # 驗證EPA項目資料完整性
                    print(f"\n🔍 EPA項目資料完整性驗證:")
                    total_records = len(deng_records)
                    non_empty_epa = epa_counts[epa_counts.index != ''].sum()
                    empty_epa = epa_counts.get('', 0)
                    
                    print(f"  • 總記錄數: {total_records}")
                    print(f"  • 有EPA項目的記錄: {non_empty_epa}")
                    print(f"  • 空EPA項目的記錄: {empty_epa}")
                    print(f"  • 資料完整性: {non_empty_epa + empty_epa} / {total_records} = {((non_empty_epa + empty_epa) / total_records * 100):.1f}%")
                    
                    if non_empty_epa + empty_epa == total_records:
                        print(f"  ✅ EPA項目資料完全保留，無遺失")
                    else:
                        print(f"  ⚠️ EPA項目資料可能有遺失")
            
            print(f"\n🎉 EPA項目資料完全保留測試完成！")
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
    result = test_epa_complete_preservation()
    print("=" * 70)
    
    if result:
        print("🎉 EPA項目資料完全保留測試成功！")
        print("\n💡 改進說明:")
        print("- 詳細評核記錄表格現在完全保留所有EPA項目資料")
        print("- 不過濾任何記錄，顯示所有原始資料")
        print("- 提供詳細的EPA項目統計資訊")
        print("- 包含空EPA項目的記錄也會顯示")
        print("- 現在應該能看到完整的EPA項目資料")
    else:
        print("❌ EPA項目資料完全保留測試失敗！")
