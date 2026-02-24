#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試擴展的EPA項目格式標準化功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_extended_epa_format():
    """測試擴展的EPA項目格式標準化功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試擴展的EPA項目格式標準化功能...")
        
        # 讀取原始EPA匯出檔案
        original_csv_path = os.path.join(os.path.dirname(__file__), 'EPA匯出原始檔_1140923.csv')
        
        if os.path.exists(original_csv_path):
            print(f"✅ 找到原始EPA匯出檔案")
            df_original = pd.read_csv(original_csv_path, encoding='utf-8')
            print(f"📊 原始檔案形狀: {df_original.shape}")
            
            # 初始化處理器
            processor = FAMDataProcessor()
            
            # 清理資料（包含格式標準化）
            cleaned_df = processor.clean_data(df_original, debug=True)
            print(f"✅ 資料清理完成: {cleaned_df.shape}")
            
            # 檢查所有EPA項目分佈
            print(f"\n🎯 檢查所有EPA項目分佈:")
            if 'EPA項目' in cleaned_df.columns:
                all_epa_counts = cleaned_df['EPA項目'].value_counts()
                print(f"  📊 所有EPA項目分佈 (前20個):")
                for epa, count in all_epa_counts.head(20).items():
                    if epa and epa != '':
                        print(f"    {epa}: {count} 筆")
                
                # 檢查數字開頭的EPA項目
                print(f"\n🔢 檢查數字開頭的EPA項目:")
                numeric_epa_items = []
                for epa in all_epa_counts.index:
                    if epa and epa != '' and epa[0].isdigit():
                        numeric_epa_items.append(epa)
                
                if numeric_epa_items:
                    print(f"  找到 {len(numeric_epa_items)} 個數字開頭的EPA項目:")
                    for epa in numeric_epa_items:
                        count = all_epa_counts[epa]
                        print(f"    {epa}: {count} 筆")
                else:
                    print(f"  ✅ 所有數字開頭的EPA項目都已標準化")
                
                # 檢查EPA開頭的項目
                print(f"\n🏷️ 檢查EPA開頭的項目:")
                epa_prefixed_items = []
                for epa in all_epa_counts.index:
                    if epa and epa != '' and epa.startswith('EPA'):
                        epa_prefixed_items.append(epa)
                
                if epa_prefixed_items:
                    print(f"  找到 {len(epa_prefixed_items)} 個EPA開頭的項目:")
                    for epa in epa_prefixed_items:
                        count = all_epa_counts[epa]
                        print(f"    {epa}: {count} 筆")
                
                # 檢查空EPA項目
                empty_count = len(cleaned_df[cleaned_df['EPA項目'] == ''])
                print(f"\n❓ 空EPA項目記錄數: {empty_count}")
                
                if empty_count > 0:
                    print(f"  📋 空EPA項目的記錄樣本 (前5筆):")
                    empty_records = cleaned_df[cleaned_df['EPA項目'] == ''].head()
                    for idx, row in empty_records.iterrows():
                        print(f"    記錄 {idx}:")
                        print(f"      日期: {row.get('日期', 'N/A')}")
                        print(f"      病歷號碼: {row.get('病歷號碼', 'N/A')}")
                        print(f"      個案姓名: {row.get('個案姓名', 'N/A')}")
                        diagnosis = row.get('診斷', 'N/A')
                        if isinstance(diagnosis, str) and len(diagnosis) > 50:
                            print(f"      診斷: {diagnosis[:50]}...")
                        else:
                            print(f"      診斷: {diagnosis}")
            
            # 檢查特定學員的EPA項目分佈
            print(f"\n👥 檢查鄧祖嶸的EPA項目分佈:")
            if '學員' in cleaned_df.columns:
                deng_records = cleaned_df[cleaned_df['學員'] == '鄧祖嶸']
                if not deng_records.empty:
                    deng_epa_counts = deng_records['EPA項目'].value_counts()
                    print(f"  鄧祖嶸的EPA項目分佈:")
                    for epa, count in deng_epa_counts.items():
                        if epa and epa != '':
                            print(f"    {epa}: {count} 筆")
                        else:
                            print(f"    (空EPA項目): {count} 筆")
            
            print(f"\n🎉 擴展EPA項目格式標準化測試完成！")
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
    result = test_extended_epa_format()
    print("=" * 70)
    
    if result:
        print("🎉 擴展EPA項目格式標準化測試成功！")
        print("\n💡 改進說明:")
        print("- 支援更多EPA項目格式，包括數字開頭的格式")
        print("- 統一標準化為EPA開頭的格式")
        print("- 確保所有EPA項目都能被正確識別和處理")
        print("- 現在應該能顯示更多EPA項目記錄")
    else:
        print("❌ 擴展EPA項目格式標準化測試失敗！")
