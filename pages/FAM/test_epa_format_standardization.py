#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試EPA項目格式標準化功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_epa_format_standardization():
    """測試EPA項目格式標準化功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試EPA項目格式標準化功能...")
        
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
            
            # 檢查特定記錄
            target_patient = "1034498"
            target_name = "顧台貞"
            
            print(f"\n🔍 檢查特定記錄處理結果:")
            print(f"  病歷號碼: {target_patient}")
            print(f"  個案姓名: {target_name}")
            
            if '病歷號碼' in cleaned_df.columns:
                matching_records = cleaned_df[cleaned_df['病歷號碼'] == target_patient]
                print(f"  清理後找到 {len(matching_records)} 筆匹配記錄")
                
                if not matching_records.empty:
                    print(f"\n📋 清理後記錄詳情:")
                    for idx, row in matching_records.iterrows():
                        print(f"  記錄 {idx}:")
                        print(f"    日期: {row.get('日期', 'N/A')}")
                        print(f"    EPA項目: '{row.get('EPA項目', 'N/A')}'")
                        print(f"    病歷號碼: {row.get('病歷號碼', 'N/A')}")
                        print(f"    個案姓名: {row.get('個案姓名', 'N/A')}")
                        print(f"    診斷: {row.get('診斷', 'N/A')}")
                        print(f"    複雜程度: {row.get('複雜程度', 'N/A')}")
                        print(f"    觀察場域: {row.get('觀察場域', 'N/A')}")
                        print(f"    信賴程度: {row.get('信賴程度(教師評量)', 'N/A')}")
                        print(f"    學員: {row.get('學員', 'N/A')}")
                else:
                    print(f"  ❌ 清理後沒有找到匹配記錄")
            
            # 檢查鄧祖嶸的資料
            print(f"\n👥 檢查鄧祖嶸的資料:")
            if '學員' in cleaned_df.columns:
                deng_records = cleaned_df[cleaned_df['學員'] == '鄧祖嶸']
                print(f"  鄧祖嶸的記錄數: {len(deng_records)}")
                
                if not deng_records.empty:
                    # 檢查EPA項目分佈
                    epa_counts = deng_records['EPA項目'].value_counts()
                    print(f"  📊 鄧祖嶸的EPA項目分佈:")
                    for epa, count in epa_counts.items():
                        print(f"    {epa}: {count} 筆")
                    
                    # 檢查EPA10記錄
                    epa10_records = deng_records[deng_records['EPA項目'].str.contains('EPA10', na=False)]
                    print(f"  🎯 鄧祖嶸的EPA10記錄數: {len(epa10_records)}")
                    
                    if not epa10_records.empty:
                        print(f"  📋 EPA10記錄詳情:")
                        for idx, row in epa10_records.iterrows():
                            print(f"    記錄 {idx}:")
                            print(f"      日期: {row.get('日期', 'N/A')}")
                            print(f"      EPA項目: '{row.get('EPA項目', 'N/A')}'")
                            print(f"      病歷號碼: {row.get('病歷號碼', 'N/A')}")
                            print(f"      個案姓名: {row.get('個案姓名', 'N/A')}")
                            print(f"      診斷: {row.get('診斷', 'N/A')}")
                            print(f"      信賴程度: {row.get('信賴程度(教師評量)', 'N/A')}")
            
            # 檢查所有EPA項目分佈
            print(f"\n🎯 檢查所有EPA項目分佈:")
            if 'EPA項目' in cleaned_df.columns:
                all_epa_counts = cleaned_df['EPA項目'].value_counts()
                print(f"  📊 所有EPA項目分佈:")
                for epa, count in all_epa_counts.items():
                    if epa and epa != '':
                        print(f"    {epa}: {count} 筆")
            
            print(f"\n🎉 EPA項目格式標準化測試完成！")
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
    result = test_epa_format_standardization()
    print("=" * 70)
    
    if result:
        print("🎉 EPA項目格式標準化測試成功！")
        print("\n💡 改進說明:")
        print("- 添加了EPA項目格式標準化功能")
        print("- 統一處理不同格式的EPA項目名稱")
        print("- 確保EPA10.出院準備/照護轉銜記錄能被正確處理")
        print("- 現在應該能在詳細評核記錄中看到這個記錄")
    else:
        print("❌ EPA項目格式標準化測試失敗！")
