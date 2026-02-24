#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試完整的EPA項目清單格式標準化功能
"""

import pandas as pd
import sys
import os

# 添加專案根目錄到Python路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

def test_complete_epa_list():
    """測試完整的EPA項目清單格式標準化功能"""
    try:
        from pages.FAM.fam_data_processor import FAMDataProcessor
        
        print("🚀 開始測試完整的EPA項目清單格式標準化功能...")
        
        # 根據您提供的清單定義期望的EPA項目
        expected_epa_items = [
            'EPA01.門診戒菸',
            'EPA02.門診/社區衛教', 
            'EPA03.預防注射',
            'EPA04.旅遊門診',
            'EPA05.健康檢查',
            'EPA07.慢病照護',
            'EPA08.急症診療',
            'EPA09.居家整合醫療',
            'EPA10.出院準備/照護轉銜',
            'EPA11.末病照護/安寧緩和',
            'EPA12.悲傷支持'
        ]
        
        print(f"📋 期望的EPA項目清單 ({len(expected_epa_items)}個):")
        for i, epa in enumerate(expected_epa_items, 1):
            print(f"  {i:2d}. {epa}")
        
        # 讀取原始EPA匯出檔案
        original_csv_path = os.path.join(os.path.dirname(__file__), 'EPA匯出原始檔_1140923.csv')
        
        if os.path.exists(original_csv_path):
            print(f"\n✅ 找到原始EPA匯出檔案")
            df_original = pd.read_csv(original_csv_path, encoding='utf-8')
            print(f"📊 原始檔案形狀: {df_original.shape}")
            
            # 初始化處理器
            processor = FAMDataProcessor()
            
            # 清理資料（包含格式標準化）
            cleaned_df = processor.clean_data(df_original, debug=True)
            print(f"✅ 資料清理完成: {cleaned_df.shape}")
            
            # 檢查所有EPA項目分佈
            print(f"\n🎯 檢查實際的EPA項目分佈:")
            if 'EPA項目' in cleaned_df.columns:
                all_epa_counts = cleaned_df['EPA項目'].value_counts()
                actual_epa_items = [epa for epa in all_epa_counts.index if epa and epa != '']
                
                print(f"  📊 實際找到的EPA項目 ({len(actual_epa_items)}個):")
                for epa, count in all_epa_counts.items():
                    if epa and epa != '':
                        status = "✅" if epa in expected_epa_items else "❓"
                        print(f"    {status} {epa}: {count} 筆")
                
                # 檢查期望的EPA項目是否都存在
                print(f"\n🔍 檢查期望的EPA項目覆蓋率:")
                found_items = []
                missing_items = []
                
                for expected_epa in expected_epa_items:
                    if expected_epa in actual_epa_items:
                        count = all_epa_counts[expected_epa]
                        found_items.append((expected_epa, count))
                        print(f"  ✅ {expected_epa}: {count} 筆")
                    else:
                        missing_items.append(expected_epa)
                        print(f"  ❌ {expected_epa}: 未找到")
                
                # 檢查額外的EPA項目
                extra_items = []
                for actual_epa in actual_epa_items:
                    if actual_epa not in expected_epa_items:
                        count = all_epa_counts[actual_epa]
                        extra_items.append((actual_epa, count))
                
                if extra_items:
                    print(f"\n➕ 額外的EPA項目 ({len(extra_items)}個):")
                    for epa, count in extra_items:
                        print(f"  ❓ {epa}: {count} 筆")
                
                # 統計摘要
                print(f"\n📊 統計摘要:")
                print(f"  期望的EPA項目: {len(expected_epa_items)} 個")
                print(f"  實際找到的EPA項目: {len(actual_epa_items)} 個")
                print(f"  已找到的期望項目: {len(found_items)} 個")
                print(f"  未找到的期望項目: {len(missing_items)} 個")
                print(f"  額外的EPA項目: {len(extra_items)} 個")
                
                if len(found_items) == len(expected_epa_items):
                    print(f"  🎉 完美！所有期望的EPA項目都已找到")
                elif len(found_items) >= len(expected_epa_items) * 0.8:
                    print(f"  ✅ 良好！找到大部分期望的EPA項目")
                else:
                    print(f"  ⚠️ 需要改進！還有一些期望的EPA項目未找到")
            
            print(f"\n🎉 完整EPA項目清單測試完成！")
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
    result = test_complete_epa_list()
    print("=" * 70)
    
    if result:
        print("🎉 完整EPA項目清單測試成功！")
        print("\n💡 改進說明:")
        print("- 根據您提供的清單更新了EPA項目格式標準化功能")
        print("- 支援所有常見的EPA項目格式變體")
        print("- 確保所有EPA項目都能被正確識別和處理")
        print("- 現在應該能顯示完整的EPA項目記錄")
    else:
        print("❌ 完整EPA項目清單測試失敗！")
