#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試特定記錄的處理邏輯
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_specific_record():
    """測試特定記錄的處理"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試特定記錄處理...")
        
        # 讀取CSV檔案
        csv_path = os.path.join(os.path.dirname(__file__), '2025-09-24T03-11_export.csv')
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        print(f"✅ 成功讀取CSV檔案: {df.shape}")
        print(f"📋 原始欄位: {list(df.columns)}")
        
        # 查找特定記錄
        target_patient = "1034498"  # 病歷號碼
        target_name = "顧台貞"      # 個案姓名
        
        print(f"\n🔍 查找特定記錄:")
        print(f"  病歷號碼: {target_patient}")
        print(f"  個案姓名: {target_name}")
        
        # 在原始資料中查找
        if '病歷號碼' in df.columns:
            matching_records = df[df['病歷號碼'] == target_patient]
            print(f"  找到 {len(matching_records)} 筆匹配記錄")
            
            if not matching_records.empty:
                print(f"\n📋 原始記錄詳情:")
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
        
        # 初始化處理器並清理資料
        processor = FAMDataProcessor()
        cleaned_df = processor.clean_data(df, debug=True)
        
        print(f"\n✅ 資料清理完成: {cleaned_df.shape}")
        
        # 在清理後的資料中查找
        if '病歷號碼' in cleaned_df.columns:
            matching_records_cleaned = cleaned_df[cleaned_df['病歷號碼'] == target_patient]
            print(f"  清理後找到 {len(matching_records_cleaned)} 筆匹配記錄")
            
            if not matching_records_cleaned.empty:
                print(f"\n📋 清理後記錄詳情:")
                for idx, row in matching_records_cleaned.iterrows():
                    print(f"  記錄 {idx}:")
                    print(f"    日期: {row.get('日期', 'N/A')}")
                    print(f"    EPA項目: '{row.get('EPA項目', 'N/A')}'")
                    print(f"    病歷號碼: {row.get('病歷號碼', 'N/A')}")
                    print(f"    個案姓名: {row.get('個案姓名', 'N/A')}")
                    print(f"    診斷: {row.get('診斷', 'N/A')}")
                    print(f"    複雜程度: {row.get('複雜程度', 'N/A')}")
                    print(f"    觀察場域: {row.get('觀察場域', 'N/A')}")
                    print(f"    信賴程度: {row.get('信賴程度(教師評量)', 'N/A')}")
            else:
                print(f"  ❌ 清理後沒有找到匹配記錄，可能被過濾掉了")
        
        # 檢查鄧祖嶸的資料
        print(f"\n👥 檢查鄧祖嶸的資料:")
        if '學員' in cleaned_df.columns:
            deng_records = cleaned_df[cleaned_df['學員'] == '鄧祖嶸']
            print(f"  鄧祖嶸的記錄數: {len(deng_records)}")
            
            if not deng_records.empty:
                print(f"  📋 鄧祖嶸的記錄:")
                for idx, row in deng_records.iterrows():
                    print(f"    記錄 {idx}:")
                    print(f"      日期: {row.get('日期', 'N/A')}")
                    print(f"      EPA項目: '{row.get('EPA項目', 'N/A')}'")
                    print(f"      病歷號碼: {row.get('病歷號碼', 'N/A')}")
                    print(f"      個案姓名: {row.get('個案姓名', 'N/A')}")
                    print(f"      診斷: {row.get('診斷', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    result = test_specific_record()
    print("=" * 70)
    
    if result:
        print("🎉 特定記錄測試完成！")
    else:
        print("❌ 特定記錄測試失敗！")
