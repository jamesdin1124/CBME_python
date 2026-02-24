#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試有效記錄的顯示
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_valid_records_display():
    """測試有效記錄的顯示"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試有效記錄的顯示...")
        
        # 讀取原始EPA匯出檔案
        original_csv_path = os.path.join(os.path.dirname(__file__), 'EPA匯出原始檔_1140923.csv')
        
        if os.path.exists(original_csv_path):
            print(f"✅ 找到原始EPA匯出檔案")
            df_original = pd.read_csv(original_csv_path, encoding='utf-8')
            print(f"📊 原始檔案形狀: {df_original.shape}")
            
            # 初始化處理器
            processor = FAMDataProcessor()
            
            # 清理資料
            cleaned_df = processor.clean_data(df_original, debug=True)
            print(f"\n✅ 資料清理完成: {cleaned_df.shape}")
            
            # 檢查鄧祖嶸的資料
            if '學員' in cleaned_df.columns:
                deng_records = cleaned_df[cleaned_df['學員'] == '鄧祖嶸'].copy()
                print(f"\n👥 鄧祖嶸的原始記錄數: {len(deng_records)}")
                
                if not deng_records.empty:
                    # 轉換日期格式
                    if '日期' in deng_records.columns:
                        deng_records['日期'] = pd.to_datetime(deng_records['日期'], errors='coerce')
                    
                    # 過濾有效記錄
                    valid_mask = (
                        deng_records['病歷號碼'].notna() | 
                        deng_records['個案姓名'].notna() | 
                        (deng_records['EPA項目'].notna() & (deng_records['EPA項目'] != ''))
                    )
                    valid_records = deng_records[valid_mask]
                    
                    print(f"📊 鄧祖嶸的有效記錄數: {len(valid_records)}")
                    
                    # 檢查有效記錄的EPA項目分佈
                    if 'EPA項目' in valid_records.columns:
                        epa_counts = valid_records['EPA項目'].value_counts()
                        print(f"\n📋 鄧祖嶸有效記錄的EPA項目分佈:")
                        for epa, count in epa_counts.items():
                            if epa and epa != '':
                                print(f"  ✅ '{epa}': {count} 筆")
                            else:
                                print(f"  ❌ 空EPA項目: {count} 筆")
                    
                    # 顯示前10筆有效記錄的詳細資訊
                    print(f"\n📋 鄧祖嶸的前10筆有效記錄詳情:")
                    for idx, (_, row) in enumerate(valid_records.head(10).iterrows()):
                        print(f"  {idx+1}. 記錄詳情:")
                        print(f"     日期: {row.get('日期', 'N/A')}")
                        print(f"     EPA項目: '{row.get('EPA項目', 'N/A')}'")
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
                    
                    # 檢查無效記錄
                    invalid_records = deng_records[~valid_mask]
                    print(f"❌ 鄧祖嶸的無效記錄數: {len(invalid_records)}")
                    if len(invalid_records) > 0:
                        print(f"  📋 無效記錄示例（前3筆）:")
                        for idx, (_, row) in enumerate(invalid_records.head(3).iterrows()):
                            print(f"    {idx+1}. 病歷號碼: {row.get('病歷號碼', 'N/A')}")
                            print(f"       個案姓名: {row.get('個案姓名', 'N/A')}")
                            print(f"       EPA項目: '{row.get('EPA項目', 'N/A')}'")
            
            print(f"\n🎉 有效記錄顯示測試完成！")
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
    result = test_valid_records_display()
    print("=" * 70)
    
    if result:
        print("🎉 有效記錄顯示測試成功！")
        print("\n💡 改進說明:")
        print("- 過濾掉完全無效的記錄（所有欄位都是NaN）")
        print("- 只顯示至少有病歷號碼、個案姓名或EPA項目的記錄")
        print("- 現在應該能看到所有有效的EPA項目記錄")
        print("- 提供記錄統計資訊幫助用戶了解資料狀況")
    else:
        print("❌ 有效記錄顯示測試失敗！")
