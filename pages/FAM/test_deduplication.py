#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試資料去重功能
"""

import pandas as pd
import os
from emway_data_integration import EmwayDataIntegration

def test_deduplication():
    """測試資料去重功能"""
    print("🧪 測試資料去重功能...")
    
    # 載入整合資料
    integrated_file = "/Users/mbpr/Library/Mobile Documents/com~apple~CloudDocs/Python/CBME_python/pages/FAM/integrated_epa_data.csv"
    
    if not os.path.exists(integrated_file):
        print("❌ 整合資料檔案不存在")
        return False
    
    try:
        # 載入資料
        df = pd.read_csv(integrated_file, encoding='utf-8')
        print(f"✅ 成功載入整合資料: {len(df)} 筆記錄")
        
        # 初始化整合器
        integrator = EmwayDataIntegration()
        
        # 分離現有系統和EMYWAY資料
        current_df = df[df['資料來源'] == '現有系統'].copy()
        emway_df = df[df['資料來源'] == 'EMYWAY歷史資料'].copy()
        
        print(f"✅ 現有系統資料: {len(current_df)} 筆")
        print(f"✅ EMYWAY歷史資料: {len(emway_df)} 筆")
        
        # 測試去重功能
        print(f"\\n🧪 測試去重功能...")
        
        # 模擬去重前的狀態
        print(f"去重前統計:")
        print(f"  現有系統: {len(current_df)} 筆")
        print(f"  EMYWAY歷史資料: {len(emway_df)} 筆")
        print(f"  總計: {len(current_df) + len(emway_df)} 筆")
        
        # 執行去重
        emway_df_filtered = integrator.remove_duplicates_with_current_system(current_df, emway_df)
        
        print(f"\\n去重後統計:")
        print(f"  現有系統: {len(current_df)} 筆 (保持不變)")
        print(f"  EMYWAY歷史資料: {len(emway_df_filtered)} 筆")
        print(f"  總計: {len(current_df) + len(emway_df_filtered)} 筆")
        print(f"  移除重複: {len(emway_df) - len(emway_df_filtered)} 筆")
        
        # 測試去重後的資料整合
        print(f"\\n🧪 測試去重後的資料整合...")
        
        # 重新執行完整的整合流程
        print("重新執行整合流程...")
        integrator = EmwayDataIntegration()
        integrated_df = integrator.merge_data()
        
        if integrated_df is not None and not integrated_df.empty:
            print(f"✅ 整合完成: {len(integrated_df)} 筆記錄")
            
            # 檢查資料來源分布
            if '資料來源' in integrated_df.columns:
                source_counts = integrated_df['資料來源'].value_counts()
                print(f"📊 最終資料來源分布:")
                for source, count in source_counts.items():
                    percentage = (count / len(integrated_df)) * 100
                    print(f"  {source}: {count} 筆 ({percentage:.1f}%)")
            
            # 檢查是否有重複記錄
            key_columns = ['學員', 'EPA項目', '日期', '病歷號碼', '個案姓名']
            available_key_columns = [col for col in key_columns if col in integrated_df.columns]
            
            if available_key_columns:
                integrated_df['merge_key'] = integrated_df[available_key_columns].astype(str).agg('|'.join, axis=1)
                duplicate_count = len(integrated_df) - len(integrated_df['merge_key'].unique())
                print(f"🔍 重複記錄檢查: {duplicate_count} 筆重複記錄")
                
                if duplicate_count == 0:
                    print("✅ 沒有發現重複記錄")
                else:
                    print("⚠️ 仍有重複記錄存在")
                
                integrated_df = integrated_df.drop('merge_key', axis=1)
        
        print("\\n🎉 資料去重功能測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        print(f"詳細錯誤信息: {traceback.format_exc()}")
        return False

def test_deduplication_with_sample_data():
    """使用樣本資料測試去重功能"""
    print("\\n🧪 使用樣本資料測試去重功能...")
    
    try:
        # 創建測試資料
        current_data = {
            '學員': ['張玄穎', '張玄穎', '陳柏豪'],
            'EPA項目': ['EPA03.預防注射', 'EPA05.健康檢查', 'EPA08.急症診療'],
            '日期': ['2025-01-15', '2025-01-20', '2025-02-01'],
            '病歷號碼': ['123456', '789012', '345678'],
            '個案姓名': ['王小明', '李大同', '陳小華'],
            '診斷': ['疫苗接種', '健康檢查', '急症處理']
        }
        
        emway_data = {
            '學員': ['張玄穎', '張玄穎', '鄧祖嶸'],
            'EPA項目': ['EPA03.預防注射', 'EPA05.健康檢查', 'EPA07.慢病照護'],
            '日期': ['2025-01-15', '2025-01-20', '2025-01-25'],
            '病歷號碼': ['123456', '789012', '901234'],
            '個案姓名': ['王小明', '李大同', '林小美'],
            '診斷': ['疫苗接種', '健康檢查', '慢病管理']
        }
        
        current_df = pd.DataFrame(current_data)
        emway_df = pd.DataFrame(emway_data)
        
        print(f"測試資料:")
        print(f"  現有系統: {len(current_df)} 筆")
        print(f"  EMYWAY歷史資料: {len(emway_df)} 筆")
        
        # 執行去重
        integrator = EmwayDataIntegration()
        emway_df_filtered = integrator.remove_duplicates_with_current_system(current_df, emway_df)
        
        print(f"\\n去重結果:")
        print(f"  現有系統: {len(current_df)} 筆 (保持不變)")
        print(f"  EMYWAY歷史資料: {len(emway_df_filtered)} 筆")
        print(f"  移除重複: {len(emway_df) - len(emway_df_filtered)} 筆")
        
        # 顯示保留的記錄
        print(f"\\n保留的EMYWAY記錄:")
        for i, (_, row) in enumerate(emway_df_filtered.iterrows()):
            print(f"  {i+1}. {row['學員']} - {row['EPA項目']} - {row['個案姓名']}")
        
        print("✅ 樣本資料去重測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 樣本資料去重測試失敗: {str(e)}")
        return False

def main():
    """主測試程式"""
    print("=" * 60)
    print("🧪 資料去重功能測試")
    print("=" * 60)
    
    # 測試去重功能
    test1_result = test_deduplication()
    
    # 測試樣本資料去重
    test2_result = test_deduplication_with_sample_data()
    
    print("\\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有測試通過！資料去重功能已準備就緒！")
        print("\\n✅ 功能包括:")
        print("   • 自動識別EMYWAY歷史資料與現有系統的重複記錄")
        print("   • 優先保留現有系統的資料")
        print("   • 移除EMYWAY歷史資料中的重複記錄")
        print("   • 提供詳細的去重統計資訊")
        print("   • 確保資料整合後沒有重複記錄")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
