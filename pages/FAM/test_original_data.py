#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查原始EPA匯出檔案
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_original_data():
    """檢查原始EPA匯出檔案"""
    try:
        print("🚀 開始檢查原始EPA匯出檔案...")
        
        # 檢查原始EPA匯出檔案
        original_csv_path = os.path.join(os.path.dirname(__file__), 'EPA匯出原始檔_1140923.csv')
        
        if os.path.exists(original_csv_path):
            print(f"✅ 找到原始EPA匯出檔案")
            df_original = pd.read_csv(original_csv_path, encoding='utf-8')
            print(f"📊 原始檔案形狀: {df_original.shape}")
            print(f"📋 原始檔案欄位: {list(df_original.columns)}")
            
            # 查找特定記錄
            target_patient = "1034498"
            target_name = "顧台貞"
            
            print(f"\n🔍 在原始檔案中查找特定記錄:")
            print(f"  病歷號碼: {target_patient}")
            print(f"  個案姓名: {target_name}")
            
            # 檢查病歷號碼欄位
            if '病歷號碼' in df_original.columns:
                matching_records = df_original[df_original['病歷號碼'] == target_patient]
                print(f"  找到 {len(matching_records)} 筆匹配記錄")
                
                if not matching_records.empty:
                    print(f"\n📋 原始檔案中的記錄詳情:")
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
                print(f"  ❌ 原始檔案中沒有病歷號碼欄位")
            
            # 檢查個案姓名欄位
            if '個案姓名' in df_original.columns:
                name_matching_records = df_original[df_original['個案姓名'] == target_name]
                print(f"\n🔍 按個案姓名查找: {len(name_matching_records)} 筆匹配記錄")
                
                if not name_matching_records.empty:
                    print(f"📋 按個案姓名找到的記錄:")
                    for idx, row in name_matching_records.iterrows():
                        print(f"  記錄 {idx}:")
                        print(f"    日期: {row.get('日期', 'N/A')}")
                        print(f"    EPA項目: '{row.get('EPA項目', 'N/A')}'")
                        print(f"    病歷號碼: {row.get('病歷號碼', 'N/A')}")
                        print(f"    個案姓名: {row.get('個案姓名', 'N/A')}")
                        print(f"    診斷: {row.get('診斷', 'N/A')}")
                        print(f"    學員: {row.get('學員', 'N/A')}")
            
            # 檢查鄧祖嶸的資料
            print(f"\n👥 檢查鄧祖嶸的資料:")
            if '學員' in df_original.columns:
                deng_records = df_original[df_original['學員'] == '鄧祖嶸']
                print(f"  鄧祖嶸的記錄數: {len(deng_records)}")
                
                if not deng_records.empty:
                    print(f"  📋 鄧祖嶸的記錄 (前5筆):")
                    for idx, row in deng_records.head().iterrows():
                        print(f"    記錄 {idx}:")
                        print(f"      日期: {row.get('日期', 'N/A')}")
                        print(f"      EPA項目: '{row.get('EPA項目', 'N/A')}'")
                        print(f"      病歷號碼: {row.get('病歷號碼', 'N/A')}")
                        print(f"      個案姓名: {row.get('個案姓名', 'N/A')}")
                        print(f"      診斷: {row.get('診斷', 'N/A')}")
            
            # 檢查EPA10相關記錄
            print(f"\n🎯 檢查EPA10相關記錄:")
            if 'EPA項目' in df_original.columns:
                epa10_records = df_original[df_original['EPA項目'].str.contains('EPA10', na=False)]
                print(f"  EPA10相關記錄數: {len(epa10_records)}")
                
                if not epa10_records.empty:
                    print(f"  📋 EPA10記錄:")
                    for idx, row in epa10_records.iterrows():
                        print(f"    記錄 {idx}:")
                        print(f"      EPA項目: '{row.get('EPA項目', 'N/A')}'")
                        print(f"      病歷號碼: {row.get('病歷號碼', 'N/A')}")
                        print(f"      個案姓名: {row.get('個案姓名', 'N/A')}")
                        print(f"      診斷: {row.get('診斷', 'N/A')}")
                        print(f"      學員: {row.get('學員', 'N/A')}")
        else:
            print(f"❌ 找不到原始EPA匯出檔案")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    result = test_original_data()
    print("=" * 70)
    
    if result:
        print("🎉 原始資料檢查完成！")
    else:
        print("❌ 原始資料檢查失敗！")
